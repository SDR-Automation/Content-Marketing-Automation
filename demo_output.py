import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from datetime import datetime
from utils.pdf_exporter import export_pdf
from utils.docx_exporter import export_docx

MOCK_CONTENT = """# Zero Trust Security Architecture

## Executive Summary

Zero Trust is the foundational security model for modern enterprises. This guide equips CISOs with an actionable implementation roadmap grounded in NIST SP 800-207.

## What Is Zero Trust?

Traditional perimeter-based security assumed everything inside the network could be trusted. Zero Trust operates on one principle: never trust, always verify.

## The Five Pillars

### 1. Identity
- MFA enforced for all users
- Privileged Access Management for admin accounts
- Just-In-Time access provisioning

### 2. Devices
- Endpoint detection and response on all devices
- Device compliance policies via MDM
- Controls extended to BYOD

### 3. Networks
Implement micro-segmentation and replace legacy VPN with Zero Trust Network Access.

### 4. Applications
Application-level access controls independent of network location with OAuth 2.0 enforcement.

### 5. Data
Data classification, encryption at rest and in transit, and DLP policies at all egress points.

## Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
- Zero Trust readiness assessment against NIST SP 800-207
- Inventory all identities, devices, and applications
- Deploy MFA universally

### Phase 2: Identity and Access (Months 4-6)
- Implement PAM for all privileged access
- Deploy ZTNA as VPN replacement
- Enforce least-privilege across cloud IAM

### Phase 3: Automate and Scale (Months 7-12)
- Continuous monitoring with UEBA
- Automate access reviews
- Expand micro-segmentation to production

## Conclusion

Zero Trust is a continuous journey of reducing implicit trust across your entire attack surface.
"""

MOCK_REVIEW = {
    "score": 88,
    "approved": True,
    "criteria_scores": {
        "technical_accuracy": 18,
        "relevance": 18,
        "seo": 17,
        "brand_tone": 18,
        "quality": 17,
    },
    "feedback": "Excellent technical depth. Clear structure and actionable roadmap for CISOs.",
    "issues": [],
    "final_content": MOCK_CONTENT,
    "reviewer_action": "approved",
}

MOCK_METADATA = {
    "content_type": "Whitepaper",
    "topic": "Zero Trust Security Architecture: A CISO Implementation Guide",
    "audience": "CISOs and Senior Security Leaders",
    "requirements": "Authoritative, technical depth, vendor-neutral",
    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "benchmarks": [],
}

if __name__ == "__main__":
    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = MOCK_METADATA["timestamp"]
    pdf_path  = out_dir / f"{ts}_zero_trust_guide.pdf"
    docx_path = out_dir / f"{ts}_zero_trust_guide.docx"
    print("Generating demo PDF...")
    export_pdf(content=MOCK_CONTENT, metadata=MOCK_METADATA, review=MOCK_REVIEW, path=str(pdf_path))
    print(f"  done: {pdf_path}")
    print("Generating demo DOCX...")
    export_docx(content=MOCK_CONTENT, metadata=MOCK_METADATA, review=MOCK_REVIEW, path=str(docx_path))
    print(f"  done: {docx_path}")
    print("\nDemo complete. Check the output folder!")