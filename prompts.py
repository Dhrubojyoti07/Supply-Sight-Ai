def build_prompt() -> str:
    """Return the prompt template to send alongside the image.

    The model is asked to return JSON with the following keys:
      - observation
      - insights
      - recommendations
      - opportunity_detection
      - startup_idea_markdown

    The `startup_idea_markdown` value should be a short Markdown block that contains:
      Startup Name, Problem, Solution, Target Customers, Business Model, Key Innovation
    """

    prompt = (
        "You are an expert supply chain analyst and startup ideation assistant. "
        "Analyze the provided image and produce a JSON object with the following keys: "
        "`observation`, `insights`, `recommendations`, `opportunity_detection`, "
        "and `startup_idea_markdown`.\n\n"
        "SECTION A - Supply Chain Observation:\n"
        "Describe what you can visually detect (warehouse, retail shelf, packaging line, storage layout, etc.).\n\n"
        "SECTION B - Inventory or Logistics Insights:\n"
        "Identify supply chain issues or opportunities (low stock, overstock, poor organization, packaging issues, safety risks).\n\n"
        "SECTION C - Operational Recommendations:\n"
        "Give concise, actionable recommendations to improve efficiency, storage, picking, or display.\n\n"
        "SECTION D - Startup Opportunity Detection:\n"
        "From the observed issue, suggest one clear startup opportunity area (e.g., smart shelf monitoring, robotics, software).\n\n"
        "SECTION E - Startup Idea Generator:\n"
        "Return a short Markdown block with: Startup Name, Problem, Proposed Solution, Target Customers, Business Model, Key Innovation.\n\n"
        "Output only valid JSON with the keys exactly as described. Keep fields short but informative. "
        "If uncertain, be explicit about assumptions."
    )

    return prompt


def build_investor_report_prompt(analysis: dict) -> str:
    """Build a prompt asking the model to produce a polished, investor-ready project report.

    The `analysis` dict should include keys produced by `analyze_image`: observation, insights,
    recommendations, opportunity_detection, startup_idea_markdown, market_score, investor_pitch.
    """

    intro = (
        "You are an expert startup advisor and investor relations writer. "
        "Given the analysis of an image (supply chain / retail / warehouse), produce a polished, "
        "investor-ready project report suitable for submission to potential investors and supply-chain leaders. "
        "Include the following sections: Executive Summary, Problem Statement, Market Opportunity, "
        "Proposed Solution, Business Model, Go-to-Market Strategy, Technology Approach, Financial/Revenue Model (high-level), "
        "Risk & Mitigation, Team & Hiring Needs, and a clear Funding Ask (use placeholders if unknown). "
        "Keep the report professional, 700-1200 words, and include bullet points where appropriate."
    )

    # Summarize provided analysis into the prompt
    parts = []
    for key in [
        "observation",
        "insights",
        "recommendations",
        "opportunity_detection",
        "startup_idea_markdown",
        "market_score",
        "investor_pitch",
    ]:
        val = analysis.get(key, "")
        if val:
            parts.append(f"{key.replace('_', ' ').title()}:\n{val}\n")

    body = "\n\n".join(parts)

    prompt = intro + "\n\n" + "Provided Analysis:\n" + body + "\n\nRespond with only the full project report in Markdown format."
    return prompt
