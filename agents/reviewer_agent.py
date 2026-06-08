"""
Reviewer Agent — LLM-2: Anthropic Claude Opus
Scores the draft, then rewrites it until technical accuracy >= 19/20 (95%).
"""

import json
import re
import anthropic

MODEL = "claude-opus-4-8"          # change if your key uses a different Opus string
MIN_TECH_ACCURACY = 19             # 19/20 = 95%
MAX_REVISIONS = 2
MAX_TOKENS = 8192

SCORE_SYSTEM_PROMPT = """You are a senior cybersecurity content editor and technical fact-checker.
Score the content on five criteria, each out of 20, using these bands:

  18-20 : expert-level. Precise, correct, cites specific frameworks/techniques
          (e.g. named NIST control families, MITRE ATT&CK technique IDs), no errors.
  16-17 : technically solid and accurate, good concrete specifics, only minor gaps.
  13-15 : generally correct but vague or shallow in places.
  10-12 : noticeable hand-waving, missing specifics, or weak structure.
  below 10 : factual errors or largely generic filler.

Criteria: technical_accuracy, relevance, seo, brand_tone, quality.
Grade fairly against the bands — do not artificially suppress scores for content
that genuinely meets a band. Reward correct, specific, framework-grounded writing.

Return ONLY a valid JSON object, no markdown fences, no commentary:
{
  "criteria_scores": {"technical_accuracy": 0, "relevance": 0, "seo": 0, "brand_tone": 0, "quality": 0},
  "feedback": "one short paragraph",
  "issues": ["specific fix", "..."]
}"""

REWRITE_SYSTEM_PROMPT = """You are a senior cybersecurity editor rewriting content to reach
EXPERT technical depth (target: at least 19/20 on technical accuracy) for the stated audience.

Do all of the following:
- Replace every vague claim with a precise, correct, specific statement.
- Cite established frameworks with real specifics, e.g. relevant MITRE ATT&CK technique IDs
  (such as T1078.004 Valid Accounts: Cloud Accounts for identity threats), specific NIST SP
  800-207 / 800-53 control ideas, CIS Controls, ISO 27001 domains — only where genuinely relevant.
- Add concrete, accurate examples, detection signals, and remediation steps a CISO can act on.
- Deepen any shallow section; fix heading hierarchy (one H1, logical H2/H3 nesting).
- Do NOT invent precise statistics or fake citations. If a number isn't verifiable, either
  use a well-known correctly-attributed figure or rephrase it qualitatively.

Return ONLY the rewritten content in markdown. No preamble, no JSON, no commentary."""


def _extract_json(text):
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1:
        text = text[s:e + 1]
    return json.loads(text)


class ReviewerAgent:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call(self, system, user_msg):
        resp = self.client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def _score(self, request, content):
        msg = ("Review this " + request.get("content_type", "content")
               + " for: " + request.get("audience", "security professionals") + ".\n\n")
        if request.get("requirements"):
            msg += "Special requirements: " + request["requirements"] + "\n\n"
        msg += "CONTENT:\n\n" + content + "\n\nScore it now. Return ONLY the JSON."
        try:
            data = _extract_json(self._call(SCORE_SYSTEM_PROMPT, msg))
        except Exception:
            data = _extract_json(self._call(SCORE_SYSTEM_PROMPT, msg + "\n\nReturn ONLY valid JSON."))
        cs = data.get("criteria_scores", {})
        for k in ("technical_accuracy", "relevance", "seo", "brand_tone", "quality"):
            cs[k] = int(cs.get(k, 0))
        data["criteria_scores"] = cs
        return data

    def _rewrite(self, request, content, scores):
        cs = scores["criteria_scores"]
        msg = ("Rewrite this " + request.get("content_type", "content")
               + " to reach at least 19/20 technical accuracy.\n"
               + "Audience: " + request.get("audience", "security professionals") + "\n"
               + "Current scores out of 20 — technical_accuracy: %d, relevance: %d, seo: %d, "
                 "brand_tone: %d, quality: %d\n" % (
                     cs["technical_accuracy"], cs["relevance"], cs["seo"],
                     cs["brand_tone"], cs["quality"]))
        if scores.get("feedback"):
            msg += "Editor feedback: " + scores["feedback"] + "\n"
        if scores.get("issues"):
            msg += "Fix these specifically:\n- " + "\n- ".join(scores["issues"]) + "\n"
        msg += "\nORIGINAL:\n\n" + content + "\n\nRewrite it now."
        return self._call(REWRITE_SYSTEM_PROMPT, msg).strip()

    def review(self, request, draft):
        content = draft.get("content", "")
        scores = self._score(request, content)
        tech = scores["criteria_scores"]["technical_accuracy"]

        revisions, action = 0, "approved"
        while tech < MIN_TECH_ACCURACY and revisions < MAX_REVISIONS:
            print(f"    technical accuracy {tech}/20 < 19 — rewriting (attempt {revisions + 1})…")
            content = self._rewrite(request, content, scores)
            scores = self._score(request, content)
            new_tech = scores["criteria_scores"]["technical_accuracy"]
            print(f"      -> now {new_tech}/20")
            tech, action, revisions = new_tech, "revised", revisions + 1

        cs = scores["criteria_scores"]
        return {
            "score": sum(cs.values()),
            "approved": tech >= MIN_TECH_ACCURACY,
            "criteria_scores": cs,
            "feedback": scores.get("feedback", ""),
            "issues": scores.get("issues", []),
            "final_content": content,
            "reviewer_action": action,
            "revisions": revisions,
        }