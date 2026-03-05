import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
MODEL = "claude-opus-4-6"

OUTPUT_SCHEMA = {
    "email": {"subject": "Primary subject line", "body": "Full email body (3-4 paragraphs, CTA at end)", "alt_subjects": ["alt 1", "alt 2", "alt 3"]},
    "landing_page": {"headline": "Hero headline (under 10 words)", "subheadline": "Supporting subheadline (1-2 sentences)", "cta": "CTA button text"},
    "social": [{"platform": "LinkedIn", "copy": "..."}, {"platform": "Twitter/X", "copy": "..."}],
    "compliance_flags": ["any brand violations, empty if none"]
}

async def run_copy_agent(brief: dict, brand_kit: dict, feedback: str = "") -> dict:
    system = f"""You are a marketing copywriter. Write release-ready copy for this launch.
BRAND KIT — {brand_kit["name"]}
Voice & Tone: {brand_kit["voice_tone"]}
DO: {", ".join(brand_kit.get("do_list", []))}
DON'T: {", ".join(brand_kit.get("dont_list", []))}
Style: {brand_kit.get("style_rules", "")}
Return ONLY valid JSON matching the schema. No markdown."""

    user_prompt = f"""Generate marketing copy for this launch:
Product: {brief["product_name"]}
Launch Date: {brief.get("launch_date", "TBD")}
Target Audience: {brief["target_audience"]}
Key Features: {json.dumps(brief["key_features"], indent=2)}
Launch Goals: {brief["launch_goals"]}
Tone Notes: {brief.get("tone_notes", "")}
{f"Reviewer feedback to address: {feedback}" if feedback else ""}

Schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}"""

    response = await client.messages.create(
        model=MODEL, max_tokens=6000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
