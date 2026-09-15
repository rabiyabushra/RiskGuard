"""
Gemini Recommendation Service for RiskGuard.
Integrates Google Generative AI (Gemini 1.5 Flash) to synthesize actionable,
context-rich mitigation strategies driven by ML risk scores and SHAP feature drivers.
"""

import os
import re
import warnings
from typing import Dict, Any, List, Optional
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

# Supported and active model identifiers
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
CANDIDATE_GEMINI_MODELS = ["gemini-flash-latest", "gemini-pro-latest", "gemini-2.5-pro"]


def format_factor_plain_english(feature_name: str) -> str:
    """Translate raw model/SHAP feature names into clear, everyday English terms."""
    clean = feature_name.lower().strip()
    mapping = {
        "progress_to_expenditure_gap": "Money spent without matching physical construction progress",
        "cost_overrun_percent": "Project budget overrun (spending exceeded original budget)",
        "cost_overrun": "Extra costs beyond the approved budget",
        "expenditure_ratio": "Fast pace of budget expenditure",
        "expenditure_to_original_ratio": "High expenditure compared to initial estimate",
        "is_mega_project": "Very large project size and logistical complexity",
        "has_cost_overrun": "Recorded cost increases",
        "num_cases_per_10k_population": "High local court/legal disputes in the district",
        "total_cases": "Local land dispute lawsuits or stay orders",
        "physical_progress": "Lagging physical construction progress",
        "schedule_delay_days": "Already existing timeline delays",
    }
    for k, v in mapping.items():
        if k in clean:
            return v
    return feature_name.replace("_", " ").title()


def build_recommendation_prompt(
    project_name: str,
    sector: str,
    state: str,
    delay_probability: float,
    risk_score: float,
    risk_category: str,
    top_risk_factors: List[str],
    top_mitigating_factors: Optional[List[str]] = None,
    custom_context: Optional[str] = None
) -> str:
    """
    Constructs a plain-language prompt asking Gemini for simple, clear, actionable suggestions.
    """
    friendly_risks = [format_factor_plain_english(f) for f in top_risk_factors] if top_risk_factors else ["General project coordination"]
    friendly_mitigating = [format_factor_plain_english(f) for f in top_mitigating_factors] if top_mitigating_factors else ["None recorded"]

    factors_str = "\n".join([f"  - {factor}" for factor in friendly_risks])
    mitigating_str = "\n".join([f"  - {factor}" for factor in friendly_mitigating])

    prompt = f"""You are a helpful and practical infrastructure project advisor. Your goal is to give plain-English, easy-to-understand recommendations that any site engineer or manager can immediately put into practice.

Here is the project summary:
- Project Name: {project_name}
- Sector: {sector}
- Location: {state}
- Delay Risk: {risk_category} ({delay_probability:.0%} chance of delay, Risk Score: {risk_score:.0f}/100)
- Main Causes of Risk:
{factors_str}
- Positive Factors (Helping prevent delays):
{mitigating_str}
"""
    if custom_context:
        prompt += f"- Field Notes: {custom_context}\n"

    prompt += """
================ TASK ================
Provide exactly 3 to 4 simple, practical, and easy-to-understand suggestions to prevent project delays.

CRITICAL RULES FOR SIMPLICITY:
1. USE SIMPLE, EVERYDAY WORDS: Avoid complex bureaucratic jargon, legal terms, confusing acronyms, and heavy technical phrases (do NOT use words like 'concessionaire', 'encumbrance', 'liquidated damages', 'statutory', 'arbitration', 'ex-gratia'). Speak simply and clearly.
2. STRUCTURE: Each suggestion MUST follow this exact format:
   - **[Short 3-5 Word Action Title]**: [1 or 2 short, clear sentences explaining exactly what simple step to take and why it helps].
3. ACTION-ORIENTED: Tell the team who to talk to, what to inspect, or what practical steps to take next (e.g., adding more work shifts, double-checking contractor bills, settling local land disputes, or pre-ordering materials).
4. KEEP IT BITE-SIZED: Keep each suggestion under 35 words.

Format each item starting with '- **Title**: Description'."""
    return prompt


def generate_gemini_recommendations(
    project_name: str,
    sector: str,
    state: str,
    delay_probability: float,
    risk_score: float,
    risk_category: str,
    top_risk_factors: List[str],
    top_mitigating_factors: Optional[List[str]] = None,
    custom_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invokes Google Gemini API with analytical context, or falls back to
    deterministic domain heuristics if the API key is not configured.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    prompt = build_recommendation_prompt(
        project_name=project_name,
        sector=sector,
        state=state,
        delay_probability=delay_probability,
        risk_score=risk_score,
        risk_category=risk_category,
        top_risk_factors=top_risk_factors,
        top_mitigating_factors=top_mitigating_factors,
        custom_context=custom_context
    )

    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        # Graceful domain-driven fallback when no API key is supplied
        fallback_recs = generate_heuristic_recommendations(risk_category, top_risk_factors)
        return {
            "recommendations": fallback_recs,
            "model_used": "domain-heuristic-fallback",
            "status": "offline_fallback",
            "notes": "GEMINI_API_KEY not configured. Set GEMINI_API_KEY in .env for live AI generation."
        }

    try:
        genai.configure(api_key=api_key)
        response = None
        used_model = DEFAULT_GEMINI_MODEL
        for model_name in CANDIDATE_GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                used_model = model_name
                break
            except Exception:
                continue

        if response is None:
            raise RuntimeError("None of the candidate Gemini models were reachable.")

        text = response.text.strip()

        # Parse bullets into clean list
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        recs = []
        for line in lines:
            if line.startswith(("-", "*", "•")) or (len(line) > 2 and line[0].isdigit() and line[1] in (".", ")")):
                clean_line = re.sub(r"^(\d+[\.\)]|\-|\*|\•)\s*", "", line).strip()
                if len(clean_line) > 10:
                    recs.append(clean_line)

        if not recs:
            recs = [line.strip() for line in text.split("\n") if len(line.strip()) > 15]

        return {
            "recommendations": recs[:4] if recs else [text],
            "model_used": used_model,
            "status": "gemini_live",
            "notes": None
        }
    except Exception as e:
        # Fallback on network or auth failure
        fallback_recs = generate_heuristic_recommendations(risk_category, top_risk_factors)
        return {
            "recommendations": fallback_recs,
            "model_used": "domain-heuristic-fallback",
            "status": "error_fallback",
            "notes": "Gemini API request failed. Returned simplified fallback recommendations."
        }


def generate_heuristic_recommendations(risk_category: str, top_factors: List[str]) -> List[str]:
    """Generates simplified, easy-to-understand recommendations in plain English."""
    recs = []
    top_lower = " ".join(top_factors).lower()

    if any(k in top_lower for k in ["expenditure", "cost", "gap", "money", "budget", "spending"]):
        recs.append(
            "**Check Spending Against Real Work**: Review recent contractor bills on-site to ensure payments are only released for completed milestones."
        )

    if any(k in top_lower for k in ["duration", "schedule", "progress", "delay", "timeline"]):
        recs.append(
            "**Speed Up Behind-Schedule Work**: Add extra labor shifts or equipment to lagging tasks, and set strict weekly targets for contractors."
        )

    if any(k in top_lower for k in ["court", "case", "legal", "dispute", "law"]):
        recs.append(
            "**Settle Land & Legal Issues Early**: Meet directly with local authorities and land owners to resolve pending disputes and speed up compensation."
        )

    if any(k in top_lower for k in ["power", "energy", "utility", "water", "pipe", "wire"]):
        recs.append(
            "**Clear Utility Roadblocks Fast**: Coordinate with local electricity and water boards to quickly relocate power poles and pipes out of the way."
        )

    if any(k in top_lower for k in ["clearance", "forest", "environment", "permit", "approval"]):
        recs.append(
            "**Fast-Track Site Clearances**: Follow up in person with regional clearance offices to get pending environmental and tree-cutting permits approved."
        )

    # General practical recommendations if specific triggers are missing
    if len(recs) < 3:
        if risk_category == "HIGH":
            recs.append(
                "**Hold Weekly Quick-Action Meetings**: Meet every week with project heads and contractors to solve any roadblocks within 48 hours."
            )
            recs.append(
                "**Give Underperforming Teams 30 Days**: Set an urgent 30-day turnaround deadline for any contractor lagging behind schedule."
            )
        elif risk_category == "MEDIUM":
            recs.append(
                "**Hold Regular Progress Check-Ins**: Meet every two weeks with site engineers to catch and fix small delays before they grow."
            )
            recs.append(
                "**Order Key Materials in Advance**: Double-check delivery dates for steel, cement, and fuel so workers never sit idle waiting for supplies."
            )
        else:
            recs.append(
                "**Track Monthly Milestones Closely**: Check off monthly target dates to ensure the project stays on track and within budget."
            )
            recs.append(
                "**Conduct Routine Quality Checks**: Inspect finished sections regularly to avoid costly repairs or delays later."
            )

    return recs[:4]
