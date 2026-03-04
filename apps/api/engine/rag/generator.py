"""RAG — Narrative generation using Anthropic Claude API."""

from __future__ import annotations

import json
import logging

from apps.api.app.core.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clinical decision support system grounded in Harrison's Principles of Internal Medicine.

RULES:
- You do NOT diagnose patients.
- You identify patterns, suggest differentials, and cite Harrison's chapter references.
- You provide evidence-based clinical reasoning.
- Always include a disclaimer that this is decision support only.
- Output structured JSON.

Output format:
{
  "narrative": "Clinical narrative text...",
  "differentials": ["Differential 1", "Differential 2"],
  "confidence": 0.85,
  "harrison_citations": ["Ch. 93: Iron Deficiency Anemia", ...],
  "caveats": ["Caveat 1", ...]
}"""


def generate_narrative(
    patient_context: dict,
    retrieved_chunks: list[dict],
    patterns: list[dict],
) -> dict | None:
    """Generate a clinical narrative using Claude API.

    Returns None if API key is not configured.
    """
    if not ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY not set — skipping RAG narrative generation")
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed — skipping RAG narrative")
        return None

    # Build the user prompt
    context_texts = [chunk.get("text", "")[:500] for chunk in retrieved_chunks[:5]]
    context_block = "\n\n---\n\n".join(context_texts)

    pattern_summary = "\n".join(
        f"- {p.get('name', '')}: {p.get('interpretation', '')[:150]}"
        for p in patterns
    )

    user_prompt = f"""Patient: Age {patient_context.get('age', 'unknown')}, Sex: {patient_context.get('sex', 'unknown')}

Detected Clinical Patterns:
{pattern_summary}

Relevant Harrison's Reference Text:
{context_block}

Based on the detected patterns and Harrison's reference material, provide a clinical narrative with differentials, confidence assessment, Harrison's citations, and important caveats. Remember: you are identifying patterns and suggesting differentials, NOT diagnosing."""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = response.content[0].text

        # Try to parse as JSON
        try:
            # Find JSON block in response
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "{" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
            else:
                json_str = text

            result = json.loads(json_str)
            return result
        except (json.JSONDecodeError, ValueError):
            return {
                "narrative": text,
                "differentials": [],
                "confidence": 0.5,
                "harrison_citations": [],
                "caveats": ["Response could not be parsed as structured JSON"],
            }

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None
