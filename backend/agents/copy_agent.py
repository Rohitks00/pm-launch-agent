import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
MODEL = "claude-opus-4-6"

ALL_COPY_SECTIONS = {
    "email": {"subject": "Primary subject line", "body": "Full email body (3-4 paragraphs, CTA at end)", "alt_subjects": ["alt 1", "alt 2", "alt 3"]},
    "landing_page": {"headline": "Hero headline (under 10 words)", "subheadline": "Supporting subheadline (1-2 sentences)", "cta": "CTA button text"},
    "social": [{"platform": "LinkedIn", "copy": "..."}, {"platform": "Twitter/X", "copy": "..."}],
    "press_release": {"headline": "Press release headline", "body": "Full press release (400-600 words, inverted pyramid structure)", "boilerplate": "About [Company] boilerplate paragraph"},
    "fact_sheet": {"company": "Company name", "product": "Product name and one-line description", "key_facts": ["fact 1", "fact 2", "fact 3"], "contact": "Press contact name and email"},
    "compliance_flags": ["any brand violations, empty if none"],
}

# Always include compliance check if any copy is being generated
ALWAYS_INCLUDE = {"compliance_flags"}

async def run_copy_agent(brief: dict, brand_kit: dict, feedback: str = "", enabled_sections: list = None) -> dict:
    # Default: generate email + landing_page + social (backwards compat, no PR sections)
    if enabled_sections is None:
        enabled_sections = ["email", "landing_page", "social"]

    # Always include compliance_flags when generating any copy
    sections_to_generate = list(set(enabled_sections) | ALWAYS_INCLUDE)

    schema = {k: ALL_COPY_SECTIONS[k] for k in sections_to_generate if k in ALL_COPY_SECTIONS}

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
{json.dumps(schema, indent=2)}"""

    response = await client.messages.create(
        model=MODEL, max_tokens=10000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError("Copy agent response was truncated (max_tokens reached).")

    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
