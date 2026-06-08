"""
Content Marketing Agent — Streamlit Dashboard
LLM-1: Groq · Llama 3.3 70B  |  LLM-2: Claude Opus
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Marketing Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .hero {
    background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 50%, #0d1117 100%);
    border: 1px solid #1e2a3a;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }
  .hero h1 { color: #00c2ff; font-size: 2rem; font-weight: 700; margin: 0; }
  .hero p  { color: #6b7280; font-size: 0.95rem; margin: 0.4rem 0 0; }
  .llm-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0.2rem;
  }
  .badge-groq   { background: #1a2a1a; color: #4ade80; border: 1px solid #4ade80; }
  .badge-claude { background: #1a1a2a; color: #a78bfa; border: 1px solid #a78bfa; }
  .metric-card {
    background: #1a1f2e;
    border: 1px solid #1e2a3a;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
  }
  .metric-card .val { font-size: 2rem; font-weight: 700; color: #00c2ff; }
  .metric-card .lbl { font-size: 0.8rem; color: #6b7280; margin-top: 0.2rem; }
  .topic-card {
    background: #1a1f2e;
    border: 1px solid #1e2a3a;
    border-left: 4px solid #00c2ff;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
  }
  .topic-card h4 { color: #f3f4f6; margin: 0 0 0.3rem; font-size: 0.95rem; }
  .topic-card p  { color: #9ca3af; margin: 0; font-size: 0.82rem; line-height: 1.4; }
  .topic-card .src { color: #4b5563; font-size: 0.75rem; margin-top: 0.4rem; }
  .selected-topic { border-left-color: #7b61ff !important; background: #1e1a2e !important; }
  .qa-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1e2a3a;
    font-size: 0.88rem;
  }
  .qa-row .label { color: #9ca3af; }
  .qa-row .score { color: #00c2ff; font-weight: 600; }
  .log-box {
    background: #0d1117;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    padding: 1rem;
    font-family: monospace;
    font-size: 0.8rem;
    color: #4ade80;
    max-height: 220px;
    overflow-y: auto;
  }
  .stButton > button {
    background: linear-gradient(135deg, #00c2ff, #7b61ff);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    width: 100%;
  }
  .content-preview {
    background: #1a1f2e;
    border: 1px solid #1e2a3a;
    border-radius: 10px;
    padding: 1.5rem;
    color: #d1d5db;
    font-size: 0.9rem;
    line-height: 1.7;
    max-height: 500px;
    overflow-y: auto;
  }
  div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e2a3a; }
</style>
""", unsafe_allow_html=True)

BENCHMARKS = [
    "https://thehackernews.com/",
    "https://krebsonsecurity.com/",
    "https://www.bleepingcomputer.com/",
    "https://www.csoonline.com/",
    "https://www.sans.org/blog",
    "https://netwrix.com/en/resources/blog/",
    "https://www.scworld.com/resource-library",
    "https://www.sans.org/white-papers",
    "https://www.forrester.com/predictions/",
    "https://www.gartner.com/en/cybersecurity",
    "https://www.verizon.com/business/",
    "https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html",
    "https://www.ibm.com/us-en",
    "https://www.paloaltonetworks.com/blog/",
    "https://medium.com/",
    "https://unit42.paloaltonetworks.com/",
]

# ── Read API keys from environment — never shown in UI ─────────────────
groq_key      = os.environ.get("GROQ_API_KEY", "")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Session state defaults ─────────────────────────────────────────────
for key, default in {
    "stage":          "config",
    "trends":         [],
    "selected_topic": None,
    "custom_topic":   "",
    "draft":          {},
    "review":         {},
    "final_content":  "",
    "pdf_path":       "",
    "docx_path":      "",
    "logs":           [],
    "request":        {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")


def reset():
    for key in ["stage","trends","selected_topic","custom_topic",
                "draft","review","final_content","pdf_path","docx_path","logs","request"]:
        del st.session_state[key]
    st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### API Keys")
    groq_status   = "Loaded" if groq_key   else "Not set"
    claude_status = "Loaded" if anthropic_key else "Not set"
    st.markdown(f"Groq API Key: **{groq_status}**")
    st.markdown(f"Claude API Key: **{claude_status}**")
    if not groq_key or not anthropic_key:
        st.error("Set keys in PowerShell before running:\n\n`$env:GROQ_API_KEY='gsk_...'`\n\n`$env:ANTHROPIC_API_KEY='sk-ant-...'`")

    st.markdown("---")
    st.markdown("### Models")
    st.markdown("""
<span class='llm-badge badge-groq'>LLM-1: Groq · Llama 3.3 70B</span><br><br>
<span class='llm-badge badge-claude'>LLM-2: Claude Opus</span>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Benchmark Sources")
    for b in BENCHMARKS[:8]:
        domain = b.replace("https://","").replace("http://","").split("/")[0]
        st.markdown(f"<span style='color:#4b5563;font-size:0.78rem'>• {domain}</span>",
                    unsafe_allow_html=True)
    st.markdown(f"<span style='color:#4b5563;font-size:0.78rem'>+ {len(BENCHMARKS)-8} more</span>",
                unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Start Over"):
        reset()


# ── Hero ───────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero'>
  <h1>Content Marketing Agent</h1>
  <p>Dual-LLM pipeline · Benchmark-driven trend discovery · PDF & DOCX export</p>
</div>
""", unsafe_allow_html=True)

# ── Block everything if keys missing ──────────────────────────────────
if not groq_key or not anthropic_key:
    st.warning("API keys not found. Please set them in PowerShell and restart the dashboard.")
    st.code('$env:GROQ_API_KEY="gsk_your_key_here"\n$env:ANTHROPIC_API_KEY="sk-ant-your_key_here"')
    st.stop()


# ════════════════════════════════════════════════════════════════════════
# STAGE 1 — Configuration
# ════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "config":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Content Brief")
        content_type = st.selectbox(
            "Content Type",
            ["Blog Post", "Whitepaper", "Datasheet", "Case Study", "Marketing Email"],
        )
        audience = st.text_input("Target Audience",
                                 placeholder="e.g. CISOs, SOC analysts, IT managers")
        requirements = st.text_area("Special Requirements (optional)",
                                    placeholder="tone, keywords, length, frameworks...",
                                    height=100)
        output_dir = st.text_input("Output Directory", value="./output")

    with col2:
        st.markdown("#### Benchmark Sources to Scrape")
        selected_benchmarks = st.multiselect(
            "Select sources",
            BENCHMARKS,
            default=BENCHMARKS[:6],
            format_func=lambda u: u.replace("https://","").split("/")[0],
        )
        st.markdown("---")
        st.markdown("#### 💡 How it works")
        st.markdown("""
1. **Scrape** selected benchmark sites for signals  
2. **Groq LLM** identifies top 5 trending topics  
3. **You pick** a topic or enter your own  
4. **Groq** writes the full content draft  
5. **Claude Opus** reviews & scores (0–100)  
6. Output saved as **PDF + DOCX**
""")

    st.markdown("---")
    if st.button("Discover Trending Topics"):
        if not audience:
            st.error("Please enter a target audience.")
        elif not selected_benchmarks:
            st.error("Please select at least one benchmark source.")
        else:
            st.session_state.request = {
                "content_type": content_type.lower(),
                "topic":        "",
                "audience":     audience,
                "requirements": requirements,
                "output_dir":   output_dir,
                "benchmarks":   selected_benchmarks,
                "timestamp":    datetime.now().strftime("%Y%m%d_%H%M%S"),
            }
            st.session_state.stage = "trends"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STAGE 2 — Trending topics
# ════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "trends":

    if not st.session_state.trends:
        with st.spinner("Scraping benchmark sources and identifying trending topics…"):
            try:
                from agents.generator_agent import GeneratorAgent
                gen    = GeneratorAgent(api_key=groq_key)
                log("Scraping benchmark sources…")
                trends = gen.discover_trends(st.session_state.request)
                st.session_state.trends = trends
                log(f"Found {len(trends)} trending topics")
            except Exception as e:
                st.error(f"Error discovering trends: {e}")
                st.stop()

    st.markdown("## Trending Topics from Benchmark Sources")
    st.markdown("*Select a topic below, or enter your own.*")

    trends = st.session_state.trends
    col_a, col_b = st.columns(2)

    for i, t in enumerate(trends):
        col = col_a if i % 2 == 0 else col_b
        with col:
            is_selected = st.session_state.selected_topic == i
            card_class  = "topic-card selected-topic" if is_selected else "topic-card"
            st.markdown(f"""
<div class='{card_class}'>
  <h4>[{t['rank']}] {t['topic']}</h4>
  <p><b>Why trending:</b> {t['why_trending']}</p>
  <p><b>Angle:</b> {t['suggested_angle']}</p>
  <p class='src'>Source: {t['source_hint']}</p>
</div>
""", unsafe_allow_html=True)
            if st.button(f"Select Topic {t['rank']}", key=f"topic_{i}"):
                st.session_state.selected_topic = i
                st.session_state.custom_topic   = ""
                st.rerun()

    st.markdown("---")
    col_x, col_y = st.columns([2, 1])
    with col_x:
        custom = st.text_input("Or enter a custom topic:",
                               value=st.session_state.custom_topic,
                               placeholder="Type your own topic here…")
        if custom != st.session_state.custom_topic:
            st.session_state.custom_topic   = custom
            st.session_state.selected_topic = None

    with col_y:
        if st.session_state.custom_topic:
            chosen_label = st.session_state.custom_topic
        elif st.session_state.selected_topic is not None:
            chosen_label = trends[st.session_state.selected_topic]["topic"]
        else:
            chosen_label = "None selected"
        st.markdown(f"**Selected:** `{chosen_label}`")

    st.markdown("")
    if st.button("Generate Content"):
        if st.session_state.selected_topic is None and not st.session_state.custom_topic:
            st.warning("Please select a topic or enter a custom one.")
        else:
            st.session_state.stage = "generating"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STAGE 3 — Generating
# ════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "generating":

    st.markdown("## Generating Content…")
    progress = st.progress(0)
    status   = st.empty()

    try:
        from agents.generator_agent import GeneratorAgent
        from agents.reviewer_agent  import ReviewerAgent
        from utils.pdf_exporter     import export_pdf
        from utils.docx_exporter    import export_docx

        request = st.session_state.request
        trends  = st.session_state.trends

        if st.session_state.custom_topic:
            chosen = {
                "topic":       st.session_state.custom_topic,
                "angle":       request.get("requirements", ""),
                "source_hint": "User custom topic",
            }
        else:
            t = trends[st.session_state.selected_topic]
            chosen = {
                "topic":       t["topic"],
                "angle":       t["suggested_angle"],
                "source_hint": t["source_hint"],
            }

        status.markdown("**[1/4]** Groq · Llama 3.3 70B generating draft…")
        progress.progress(10)
        log(f"Generating draft for: {chosen['topic']}")
        gen   = GeneratorAgent(api_key=groq_key)
        draft = gen.generate_content(request, chosen)
        st.session_state.draft = draft
        progress.progress(40)
        log(f"Draft complete — {draft.get('word_count', 0)} words")

        status.markdown("**[2/4]** Claude Opus reviewing & scoring…")
        progress.progress(50)
        log("Sending to Claude Opus for review…")
        reviewer = ReviewerAgent(api_key=anthropic_key)
        request["topic"] = chosen["topic"]
        review   = reviewer.review(request, draft)
        st.session_state.review        = review
        st.session_state.final_content = review.get("final_content", draft.get("content",""))
        progress.progress(70)
        log(f"Review complete — {review.get('score',0)}/100 — {'APPROVED' if review.get('approved') else 'REVISED'}")

        status.markdown("**[3/4]** 📄 Exporting PDF…")
        progress.progress(80)
        out_dir   = Path(request["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        slug      = chosen["topic"][:40].lower().replace(" ","_").replace("/","-")
        base_name = f"{request['timestamp']}_{slug}"
        pdf_path  = out_dir / f"{base_name}.pdf"
        export_pdf(content=st.session_state.final_content,
                   metadata=request, review=review, path=str(pdf_path))
        st.session_state.pdf_path = str(pdf_path)
        log(f"PDF saved: {pdf_path}")

        status.markdown("**[4/4]** 📝 Exporting Word document…")
        progress.progress(90)
        docx_path = out_dir / f"{base_name}.docx"
        export_docx(content=st.session_state.final_content,
                    metadata=request, review=review, path=str(docx_path))
        st.session_state.docx_path = str(docx_path)
        log(f"DOCX saved: {docx_path}")

        progress.progress(100)
        status.markdown("**Pipeline complete!**")
        st.session_state.stage = "done"
        time.sleep(0.5)
        st.rerun()

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        if st.button("← Go Back"):
            st.session_state.stage = "trends"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STAGE 4 — Results
# ════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "done":

    review       = st.session_state.review
    draft        = st.session_state.draft
    request      = st.session_state.request
    approved     = review.get("approved", False)
    score        = review.get("score", 0)
    criteria     = review.get("criteria_scores", {})
    chosen_topic = draft.get("chosen_topic", {}).get("topic", request.get("topic",""))

    status_color  = "#052e16" if approved else "#2d1515"
    status_border = "#4ade80" if approved else "#f87171"
    status_text   = "APPROVED" if approved else "🔄 REVISED BY REVIEWER"

    st.markdown(f"""
<div style='background:{status_color};border:1px solid {status_border};border-radius:10px;
padding:1rem 1.5rem;margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center'>
  <div>
    <span style='color:{status_border};font-weight:700;font-size:1.1rem'>{status_text}</span>
    <span style='color:#9ca3af;font-size:0.85rem;margin-left:1rem'>{chosen_topic}</span>
  </div>
  <span style='color:#00c2ff;font-size:1.5rem;font-weight:700'>{score}/100</span>
</div>
""", unsafe_allow_html=True)

    wc = draft.get("word_count", len(st.session_state.final_content.split()))
    kw = len(draft.get("keywords", []))
    m1, m2, m3, m4 = st.columns(4)
    for col, val, label in [
        (m1, f"{score}/100",                   "Quality Score"),
        (m2, f"{wc:,}",                        "Word Count"),
        (m3, str(kw),                          "Keywords"),
        (m4, request["content_type"].title(),  "Content Type"),
    ]:
        with col:
            st.markdown(f"""
<div class='metric-card'>
  <div class='val'>{val}</div>
  <div class='lbl'>{label}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("")
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### QA Scorecard")
        labels = [
            ("technical_accuracy", "Technical Accuracy"),
            ("relevance",          "Relevance & Value"),
            ("seo",                "SEO Compliance"),
            ("brand_tone",         "Brand & Tone"),
            ("quality",            "Quality & Clarity"),
        ]
        for key, label in labels:
            val = criteria.get(key, 0)
            pct = int(val) * 5 if isinstance(val, int) else 0
            st.markdown(f"""
<div class='qa-row'>
  <span class='label'>{label}</span>
  <span class='score'>{val}/20</span>
</div>
""", unsafe_allow_html=True)
            st.progress(pct / 100)

        st.markdown("")
        st.markdown("**Reviewer Feedback**")
        st.markdown(f"<div style='color:#9ca3af;font-size:0.85rem;line-height:1.6'>{review.get('feedback','')}</div>",
                    unsafe_allow_html=True)

        if draft.get("keywords"):
            st.markdown("")
            st.markdown("**Keywords**")
            kw_html = " ".join([
                f"<span style='background:#1a2a3a;color:#00c2ff;padding:2px 8px;border-radius:12px;"
                f"font-size:0.78rem;margin:2px;display:inline-block'>{k}</span>"
                for k in draft["keywords"]
            ])
            st.markdown(kw_html, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 📄 Generated Content")
        st.markdown(
            f"<div class='content-preview'>{st.session_state.final_content.replace(chr(10), '<br>')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### 💾 Download Outputs")
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        if st.session_state.pdf_path and Path(st.session_state.pdf_path).exists():
            with open(st.session_state.pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", data=f.read(),
                                   file_name=Path(st.session_state.pdf_path).name,
                                   mime="application/pdf")

    with dl2:
        if st.session_state.docx_path and Path(st.session_state.docx_path).exists():
            with open(st.session_state.docx_path, "rb") as f:
                st.download_button("📥 Download Word", data=f.read(),
                                   file_name=Path(st.session_state.docx_path).name,
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with dl3:
        st.download_button("📥 Download Markdown",
                           data=st.session_state.final_content,
                           file_name=f"{request['timestamp']}_content.md",
                           mime="text/markdown")

    with st.expander("🔧 Pipeline Activity Log"):
        st.markdown(
            f"<div class='log-box'>{'<br>'.join(st.session_state.logs)}</div>",
            unsafe_allow_html=True,
        )