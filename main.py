import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

from agents.generator_agent import GeneratorAgent
from agents.reviewer_agent  import ReviewerAgent
from utils.pdf_exporter     import export_pdf
from utils.docx_exporter    import export_docx


BENCHMARKS = [
    "https://www.scworld.com/resource-library",
    "https://www.sans.org/white-papers",
    "https://www.forrester.com/predictions/",
    "https://www.gartner.com/en/cybersecurity",
    "https://thehackernews.com/",
    "https://krebsonsecurity.com/",
    "https://www.bleepingcomputer.com/",
    "https://www.csoonline.com/",
    "https://www.sans.org/blog",
    "https://www.verizon.com/business/",
    "https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html",
    "https://www.ibm.com/us-en",
    "https://netwrix.com/en/resources/blog/",
    "https://www.paloaltonetworks.com/blog/",
    "https://medium.com/",
    "https://unit42.paloaltonetworks.com/",
]


def print_banner():
    print("\n" + "=" * 65)
    print("  CONTENT MARKETING AGENT")
    print("  LLM-1: Groq · Llama 3.3 70B  →  LLM-2: Claude Sonnet")
    print("=" * 65 + "\n")


def print_step(step, total, message):
    print(f"\n[Step {step}/{total}] {message}")
    print("-" * 50)


def get_user_input():
    print("Please provide the following details:\n")
    content_type = input(
        "Content type (blog post / datasheet / whitepaper / case study / marketing email): "
    ).strip() or "blog post"
    audience = input(
        "Target audience (e.g., CISOs, SOC analysts, IT managers): "
    ).strip() or "CISOs and Security Leaders"
    requirements = input(
        "Special requirements (tone, keywords — press Enter to skip): "
    ).strip()
    output_dir = input(
        "Output directory (press Enter for ./output): "
    ).strip() or "./output"
    return {
        "content_type": content_type,
        "topic":        "",
        "audience":     audience,
        "requirements": requirements,
        "output_dir":   output_dir,
        "benchmarks":   BENCHMARKS,
        "timestamp":    datetime.now().strftime("%Y%m%d_%H%M%S"),
    }


def _load_keys():
    groq_key      = os.environ.get("GROQ_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    missing = []
    if not groq_key:
        missing.append("GROQ_API_KEY      — get it at https://console.groq.com/keys")
    if not anthropic_key:
        missing.append("ANTHROPIC_API_KEY — get it at https://console.anthropic.com/")
    if missing:
        raise EnvironmentError(
            "Missing API keys:\n  " + "\n  ".join(missing) +
            "\n\nRun:\n  $env:GROQ_API_KEY='gsk_...'\n  $env:ANTHROPIC_API_KEY='sk-ant-...'"
        )
    return groq_key, anthropic_key


def run_pipeline(request):
    groq_key, anthropic_key = _load_keys()
    total_steps = 5
    result = {}

    # Step 1 — Groq discovers trends + generates draft
    print_step(1, total_steps, "LLM-1 [Groq · Llama 3.3 70B] Scraping benchmarks + discovering trends…")
    generator = GeneratorAgent(api_key=groq_key)
    draft = generator.generate(request)

    chosen     = draft.get("chosen_topic", {})
    word_count = draft.get("word_count") or len(draft.get("content", "").split())
    if chosen.get("topic"):
        print(f"  ✓ Chosen topic     : {chosen['topic']}")
    print(f"  ✓ Draft generated  ({word_count} words)")
    if draft.get("keywords"):
        print(f"  ✓ Keywords         : {', '.join(draft['keywords'][:5])}")
    result["draft"] = draft

    # Step 2 — Claude reviews + validates
    print_step(2, total_steps, "LLM-2 [Claude Sonnet] Reviewing & validating…")
    reviewer = ReviewerAgent(api_key=anthropic_key)
    review   = reviewer.review(request, draft)

    approved   = review.get("approved", False)
    score      = review.get("score", 0)
    feedback   = review.get("feedback", "")
    final_text = review.get("final_content", draft.get("content", ""))

    print(f"  ✓ Quality score    : {score}/100")
    print(f"  ✓ Decision         : {'APPROVED ✓' if approved else 'REVISED BY REVIEWER'}")
    if feedback:
        print(f"  ✓ Feedback         : {feedback[:200]}{'…' if len(feedback) > 200 else ''}")
    result.update({"review": review, "approved": approved, "final_content": final_text})

    # Step 3 — Prepare output directory
    print_step(3, total_steps, "Preparing output directory…")
    out_dir = Path(request["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    topic_for_slug = chosen.get("topic") or request.get("topic") or "content"
    slug = topic_for_slug[:40].lower().replace(" ", "_").replace("/", "-")
    base_name = f"{request['timestamp']}_{slug}"
    print(f"  ✓ Output dir       : {out_dir.resolve()}")

    # Update request topic for exporters
    request["topic"] = chosen.get("topic") or request.get("topic") or "Content"

    # Step 4 — Export PDF
    print_step(4, total_steps, "Exporting PDF…")
    pdf_path = out_dir / f"{base_name}.pdf"
    export_pdf(content=final_text, metadata=request, review=review, path=str(pdf_path))
    print(f"  ✓ PDF saved        : {pdf_path}")
    result["pdf_path"] = str(pdf_path)

    # Step 5 — Export DOCX
    print_step(5, total_steps, "Exporting Word document…")
    docx_path = out_dir / f"{base_name}.docx"
    export_docx(content=final_text, metadata=request, review=review, path=str(docx_path))
    print(f"  ✓ DOCX saved       : {docx_path}")
    result["docx_path"] = str(docx_path)

    return result


def main():
    print_banner()

    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        with open(sys.argv[1]) as f:
            request = json.load(f)
        request.setdefault("benchmarks", BENCHMARKS)
        request.setdefault("timestamp",  datetime.now().strftime("%Y%m%d_%H%M%S"))
        request.setdefault("output_dir", "./output")
        request.setdefault("topic",      "")
    else:
        request = get_user_input()

    print(f"\n{'─'*65}")
    print(f"  Content type : {request['content_type']}")
    print(f"  Audience     : {request['audience']}")
    if request.get("requirements"):
        print(f"  Requirements : {request['requirements']}")
    print(f"{'─'*65}")

    try:
        t0     = time.time()
        result = run_pipeline(request)
        elapsed = time.time() - t0

        print(f"\n{'='*65}")
        print("  PIPELINE COMPLETE")
        print(f"{'='*65}")
        print(f"  LLM-1 (Generator) : Groq · Llama 3.3 70B Versatile")
        print(f"  LLM-2 (Reviewer)  : Anthropic · Claude Sonnet")
        print(f"  Status            : {'APPROVED' if result['approved'] else 'REVISED BY REVIEWER'}")
        print(f"  PDF               : {result['pdf_path']}")
        print(f"  DOCX              : {result['docx_path']}")
        print(f"  Duration          : {elapsed:.1f}s")
        print(f"{'='*65}\n")

    except EnvironmentError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()