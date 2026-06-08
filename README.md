# Content Marketing Agent — Dual-LLM Pipeline

A production-ready Python system that automates cybersecurity content creation using **two Claude LLMs** in a generator → reviewer pipeline, with automatic PDF and Word document export.

---

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────┐
│  LLM-1: Generator Agent         │
│  • Researches benchmark sources │
│  • Produces topic + outline     │
│  • Writes full content draft    │
└──────────────┬──────────────────┘
               │ Draft (JSON)
               ▼
┌─────────────────────────────────┐
│  LLM-2: Reviewer Agent          │
│  • Scores on 5 criteria (0–20)  │
│  • Technical Accuracy           │
│  • Relevance & Value            │
│  • SEO Compliance               │
│  • Brand & Tone                 │
│  • Quality & Clarity            │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
     ≥75/100          <75/100
  APPROVED           REVISED
  (pass-through)   (rewritten)
       │               │
       └───────┬────────┘
               ▼
        ┌─────────────┐
        │  Exporters  │
        │  PDF + DOCX │
        └─────────────┘
```

---

## Benchmark Sources

The agents reference 16 authoritative cybersecurity sources:

| Category | Sources |
|----------|---------|
| Research & Reports | SC World, SANS White Papers, Forrester, Gartner |
| Threat Intel | The Hacker News, Krebs on Security, BleepingComputer |
| Industry | CSO Online, SANS Blog, Verizon Business, IBM |
| Technical | OWASP AI Security, Unit 42, Palo Alto Networks |
| Community | Medium, Netwrix Blog |

---

## Quick Start

### 1. Install dependencies

```bash
pip install anthropic reportlab python-docx
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Run interactively

```bash
python main.py
```

You will be prompted for:
- Content type (blog post / whitepaper / datasheet / case study / marketing email)
- Topic / title
- Target audience
- Special requirements (tone, keywords, length)
- Output directory

### 4. Run with a JSON request file

```bash
python main.py request.json
```

**Example `request.json`:**
```json
{
  "content_type": "blog post",
  "topic": "AI-Powered Threat Detection: What CISOs Need to Know in 2025",
  "audience": "CISOs and Security Directors",
  "requirements": "800-1000 words, vendor-neutral, include MITRE ATT&CK references",
  "output_dir": "./output"
}
```

### 5. Preview demo output (no API key needed)

```bash
python demo_output.py
```

---

## Project Structure

```
content_agent/
├── main.py                     # Orchestrator & CLI entrypoint
├── demo_output.py              # Demo runner (no API key required)
├── agents/
│   ├── generator_agent.py      # LLM-1: content creation
│   └── reviewer_agent.py       # LLM-2: quality validation + revision
├── utils/
│   ├── pdf_exporter.py         # ReportLab-based PDF generator
│   └── docx_exporter.py        # python-docx Word document generator
└── output/                     # Generated files land here
```

---

## Output Format

Both the PDF and DOCX include:

1. **Branded cover block** — content type, topic, audience, timestamp
2. **QA Report table** — scores for all 5 review criteria, approval status, reviewer notes
3. **Full content** — headings, paragraphs, bullet lists, horizontal rules
4. **Footer** — page numbers, pipeline attribution

---

## Supported Content Types

| Type | Target Length |
|------|---------------|
| Blog post | 800–1,200 words |
| Whitepaper | 1,500–2,500 words |
| Datasheet | 400–700 words |
| Case study | 800–1,200 words |
| Marketing email | 200–400 words |

---

## Review Criteria

| Criterion | Max Score | What Is Checked |
|-----------|-----------|-----------------|
| Technical Accuracy | 20 | Claims verifiable against benchmark sources |
| Relevance & Value | 20 | Matches audience needs and pain points |
| SEO Compliance | 20 | Keywords used naturally; title/structure optimized |
| Brand & Tone | 20 | Professional, authoritative, industry-appropriate |
| Quality & Clarity | 20 | Clear structure, no fluff, well-written |
| **Total** | **100** | **Approval threshold: ≥ 75** |

---

## Extending the Agent

### Add more benchmark sources
Edit the `BENCHMARKS` list in `main.py`.

### Change the approval threshold
Edit the `APPROVAL THRESHOLD` value in `agents/reviewer_agent.py` (currently 75).

### Swap models
Change `self.model` in either agent class. LLM-1 uses `llama-3.3-70b-versatile` (Groq); LLM-2 uses `claude-sonnet-4-20250514` (Anthropic).

### Add output formats
Create a new exporter in `utils/` and call it from `main.py`'s `run_pipeline()`.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |

---

## Dependencies

```
anthropic>=0.25.0
reportlab>=4.0.0
python-docx>=1.1.0
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Your Groq API key — get it at https://console.groq.com/keys |
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key — get it at https://console.anthropic.com/ |

## Quick Start (updated)

```bash
pip install groq anthropic reportlab python-docx

export GROQ_API_KEY=gsk_...
export ANTHROPIC_API_KEY=sk-ant-...

python main.py
```
