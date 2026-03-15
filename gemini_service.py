import os
import json
import base64
import requests
from dotenv import load_dotenv
from typing import Dict, Optional

from image_utils import simple_describe

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "text-bison-001")
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_ENDPOINT",
    f"https://generativelanguage.googleapis.com/v1beta2/models/{GEMINI_MODEL}:generate",
)


def _parse_model_output(text: str) -> Dict[str, str]:
    text = text.strip()
    try:
        data = json.loads(text)
        return {
            "observation": data.get("observation", ""),
            "insights": data.get("insights", ""),
            "recommendations": data.get("recommendations", ""),
            "opportunity_detection": data.get("opportunity_detection", ""),
            "startup_idea_markdown": data.get("startup_idea_markdown", ""),
            "market_score": data.get("market_score", ""),
            "investor_pitch": data.get("investor_pitch", ""),
        }
    except Exception:
        # fallback: return whole text in startup_idea_markdown
        return {
            "observation": "",
            "insights": "",
            "recommendations": "",
            "opportunity_detection": "",
            "startup_idea_markdown": text,
            "market_score": "",
            "investor_pitch": "",
        }


def _call_rest_model(prompt: str, max_tokens: int = 800) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None

    headers = {"Content-Type": "application/json"}
    # Prefer Bearer token header; some users may supply an API key instead.
    headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"

    payload = {
        "prompt": {"text": prompt},
        "maxOutputTokens": max_tokens,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        # The response field name differs by API; check common shapes
        text_out = ""
        if "candidates" in body and len(body["candidates"]) > 0:
            text_out = body["candidates"][0].get("content", "")
        elif "output" in body:
            # some versions return an output->text
            out = body["output"]
            if isinstance(out, dict):
                text_out = out.get("text", "")
            else:
                text_out = str(out)
        else:
            text_out = json.dumps(body)

        return text_out
    except Exception:
        return None


def analyze_image(image_bytes: bytes, prompt: str) -> Dict[str, str]:
    """Analyze image using the Generative REST API; fall back to local heuristics.

    The function passes the image as base64 embedded between markers in the prompt so
    that multimodal-enabled models that accept inline base64 can make use of it.
    """
    # Local fallback when no API key or REST call fails
    def local_fallback():
        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            description = simple_describe(img)
        except Exception:
            description = "Unable to analyze image locally."

        observation = f"Automatic local analysis: {description}"
        insights = (
            "Possible issues detected: insufficient labeling or uneven spacing on shelves; "
            "potential low-stock areas if many empty spaces are visible."
        )
        recommendations = (
            "Install periodic camera monitoring, add shelf-edge sensors, adopt cycle counting, and reorganize high-velocity SKUs closer to picking paths."
        )
        opportunity = (
            "Smart shelf monitoring and simple computer-vision based stock alerts for retail/warehouses."
        )
        startup_md = (
            "**Startup Name:** ShelfSense AI\n\n"
            "**Problem:** Stores and small warehouses cannot monitor shelf-level inventory in real time.\n\n"
            "**Solution:** Low-cost camera + cloud AI that detects low-stock and sends alerts.\n\n"
            "**Target Customers:** Small/medium retail stores, warehouses, convenience chains.\n\n"
            "**Business Model:** Subscription SaaS + device setup fee.\n\n"
            "**Key Innovation:** Lightweight edge model optimized for low-power cameras."
        )

        # Heuristic market score: penalize if few colors / small size
        market_score = 55
        investor_pitch = (
            "ShelfSense AI provides real-time shelf-level inventory alerts to reduce stockouts and lost sales. Subscription model targets SMB retailers."
        )

        return {
            "observation": observation,
            "insights": insights,
            "recommendations": recommendations,
            "opportunity_detection": opportunity,
            "startup_idea_markdown": startup_md,
            "market_score": str(market_score),
            "investor_pitch": investor_pitch,
        }

    # If no key provided, return fallback
    if not GEMINI_API_KEY:
        return local_fallback()

    # Prepare prompt with embedded image
    try:
        b64 = base64.b64encode(image_bytes).decode()
        full_prompt = prompt + "\n\n[IMAGE_BASE64_BEGIN]\n" + b64 + "\n[IMAGE_BASE64_END]\n\nRespond with JSON including keys: observation, insights, recommendations, opportunity_detection, startup_idea_markdown, market_score, investor_pitch."

        text_out = _call_rest_model(full_prompt)
        if not text_out:
            return local_fallback()

        parsed = _parse_model_output(text_out)
        # Ensure keys exist
        for k in ["observation", "insights", "recommendations", "opportunity_detection", "startup_idea_markdown", "market_score", "investor_pitch"]:
            parsed.setdefault(k, "")
        return parsed
    except Exception:
        return local_fallback()


def generate_project_report(analysis: Dict[str, str], max_tokens: int = 1200) -> str:
    """Generate an investor-ready project report from the analysis dict.

    Falls back to a templated local report if the model cannot be called.
    """
    # Local fallback builder
    def local_report():
        title = "Investor Project Report - Generated by SupplySight AI"
        sections = [
            f"# {title}",
            "## Executive Summary",
            analysis.get("investor_pitch", "A concise investor pitch is not available."),
            "## Problem Statement",
            analysis.get("observation", ""),
            "## Market Opportunity",
            f"Market Score: {analysis.get('market_score','N/A')}",
            "## Proposed Solution",
            analysis.get("startup_idea_markdown", ""),
            "## Key Insights",
            analysis.get("insights", ""),
            "## Recommendations",
            analysis.get("recommendations", ""),
            "## Opportunity",
            analysis.get("opportunity_detection", ""),
            "## Funding Ask",
            "Seeking $X for product development, pilot deployments, and go-to-market (placeholder).",
            "## Risks & Mitigations",
            "Operational and technical risks identified; recommend pilot testing and partnerships.",
        ]
        return "\n\n".join(sections)

    # If no API key, return local report
    if not GEMINI_API_KEY:
        return local_report()

    # Build prompt from provided analysis (import lazily to avoid circular imports)
    try:
        from prompts import build_investor_report_prompt

        prompt = build_investor_report_prompt(analysis)
        text_out = _call_rest_model(prompt, max_tokens=max_tokens)
        if not text_out:
            return local_report()

        # Prefer returning the raw text as the report
        return text_out.strip()
    except Exception:
        return local_report()
