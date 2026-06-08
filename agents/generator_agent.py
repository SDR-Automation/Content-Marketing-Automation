"""
Generator Agent — LLM-1: Groq · Llama 3.3 70B Versatile
Phase 1: Scrapes benchmark URLs and surfaces trending topics
Phase 2: User picks a topic (or provides their own)
Phase 3: Generates full content draft
"""

import json
import urllib.request
import urllib.error
import re
from groq import Groq


# ── Prompts ────────────────────────────────────────────────────────────

TREND_SYSTEM = """You are a cybersecurity content intelligence analyst.
You will be given raw text scraped from leading cybersecurity websites.
Your job is to identify the TOP 5 trending topics most relevant to the
specified audience and content type.

Return ONLY a JSON array of exactly 5 objects, no preamble:
[
  {
    "rank": 1,
    "topic": "Concise topic title",
    "why_trending": "1-2 sentences on why this is hot right now",
    "suggested_angle": "Specific content angle for the target audience",
    "source_hint": "Which benchmark site(s) signal this trend"
  }
]"""

CONTENT_SYSTEM = """You are an expert cybersecurity content strategist and writer.
You write technically accurate, audience-targeted, SEO-optimised content
for B2B cybersecurity buyers.

Return ONLY a valid JSON object, no preamble, no markdown fences:
{
  "title": "Final content title",
  "summary": "2-3 sentence executive summary",
  "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "content": "Full markdown content with # ## ### headings, **bold**, - bullets",
  "word_count": 1050,
  "seo_notes": "Brief SEO strategy note"
}"""


# ── Helpers ────────────────────────────────────────────────────────────

def _fetch_text(url: str, max_chars: int = 4000) -> str:
    """Fetch a URL and return plain text (strips HTML tags)."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ContentAgent/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", " ", raw)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"[could not fetch {url}: {e}]"


def _scrape_benchmarks(benchmarks: list, max_sites: int = 6) -> str:
    """Scrape a subset of benchmark URLs and return combined text."""
    # Prioritise news/blog sites for trend signals
    priority = [u for u in benchmarks if any(
        k in u for k in ["hacker", "krebs", "bleeping", "sans.org/blog",
                         "paloalto", "unit42", "csoonline", "netwrix"]
    )]
    others = [u for u in benchmarks if u not in priority]
    selected = (priority + others)[:max_sites]

    chunks = []
    for url in selected:
        print(f"    → scraping {url} …")
        text = _fetch_text(url)
        chunks.append(f"=== {url} ===\n{text}\n")
    return "\n".join(chunks)


def _strip_json(raw: str) -> str:
    """Remove markdown fences and leading/trailing whitespace."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _present_topics(topics: list) -> None:
    print("\n" + "=" * 60)
    print("  TRENDING TOPICS FROM BENCHMARK SOURCES")
    print("=" * 60)
    for t in topics:
        print(f"\n  [{t['rank']}] {t['topic']}")
        print(f"      Why trending : {t['why_trending']}")
        print(f"      Angle        : {t['suggested_angle']}")
        print(f"      Source       : {t['source_hint']}")
    print("\n" + "=" * 60)


# ── Main class ─────────────────────────────────────────────────────────

class GeneratorAgent:
    """LLM-1: Groq Llama 3.3 70B — trend discovery + content generation."""

    MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    # ── Phase 1: discover trends ───────────────────────────────────────
    def discover_trends(self, request: dict) -> list:
        print("  Scraping benchmark sources for trending topics…")
        scraped = _scrape_benchmarks(request["benchmarks"])

        user_msg = f"""Benchmark content scraped from leading cybersecurity sites:

{scraped}

---
TARGET AUDIENCE : {request['audience']}
CONTENT TYPE    : {request['content_type']}
FOCUS AREA      : {request.get('topic') or 'any relevant cybersecurity topic'}

Identify the TOP 5 trending topics most relevant to this audience right now."""

        resp = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=1500,
            temperature=0.4,
            messages=[
                {"role": "system", "content": TREND_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
        )
        raw = _strip_json(resp.choices[0].message.content)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: single generic topic
            return [{
                "rank": 1,
                "topic": request.get("topic") or "Cybersecurity Trends 2025",
                "why_trending": "Derived from benchmark sources.",
                "suggested_angle": "Practical guide for the target audience.",
                "source_hint": "Multiple benchmark sources",
            }]

    # ── Phase 2: user picks topic ──────────────────────────────────────
    def pick_topic(self, trends: list, request: dict) -> dict:
        _present_topics(trends)
        print(f"  Enter a number (1-{len(trends)}) to select a suggested topic,")
        print("  or press Enter to use your original topic, or type a custom topic:\n")
        choice = input("  Your choice: ").strip()

        if not choice:
            return {
                "topic": request.get("topic", ""),
                "angle": request.get("requirements", ""),
                "source_hint": "User-specified topic",
            }
        elif choice.isdigit() and 1 <= int(choice) <= len(trends):
            t = trends[int(choice) - 1]
            return {
                "topic": t["topic"],
                "angle": t["suggested_angle"],
                "source_hint": t["source_hint"],
            }
        else:
            return {
                "topic": choice,
                "angle": request.get("requirements", ""),
                "source_hint": "User custom topic",
            }

    # ── Phase 3: generate full content ────────────────────────────────
    def generate_content(self, request: dict, chosen: dict) -> dict:
        length_guide = {
            "blog post":       "800-1,200 words",
            "whitepaper":      "1,500-2,500 words",
            "datasheet":       "400-700 words, feature-focused and punchy",
            "case study":      "800-1,200 words",
            "marketing email": "200-400 words",
        }.get(request["content_type"].lower(), "800-1,200 words")

        user_msg = f"""Write a high-quality {request['content_type']}:

TOPIC           : {chosen['topic']}
CONTENT ANGLE   : {chosen['angle'] or 'Professional cybersecurity marketing tone'}
TARGET AUDIENCE : {request['audience']}
CONTENT TYPE    : {request['content_type']}
TARGET LENGTH   : {length_guide}
EXTRA REQUIREMENTS: {request.get('requirements') or 'None'}
SOURCE SIGNALS  : {chosen['source_hint']}

Requirements:
- Technically accurate, grounded in real cybersecurity concepts
- Reference frameworks like NIST, MITRE ATT&CK, CIS Controls where relevant
- Include specific statistics or findings where appropriate
- Clear H1 / H2 / H3 structure, bullet lists, bold key terms
- SEO-optimised with natural keyword usage
- No vendor promotion unless specifically requested

Return ONLY the JSON object."""

        resp = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=4096,
            temperature=0.7,
            messages=[
                {"role": "system", "content": CONTENT_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
        )
        raw = _strip_json(resp.choices[0].message.content)
        try:
            result = json.loads(raw)
            result["chosen_topic"] = chosen
            return result
        except json.JSONDecodeError:
            return {
                "title":        chosen["topic"],
                "summary":      "",
                "keywords":     [],
                "content":      raw,
                "word_count":   len(raw.split()),
                "seo_notes":    "",
                "chosen_topic": chosen,
            }

    # ── Public entry point ────────────────────────────────────────────
    def generate(self, request: dict) -> dict:
        """Full pipeline: discover → pick → generate."""
        trends = self.discover_trends(request)
        chosen = self.pick_topic(trends, request)
        print(f"\n  Generating content for: {chosen['topic']}")
        return self.generate_content(request, chosen)
