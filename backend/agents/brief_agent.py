import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
MODEL = "claude-opus-4-6"

OUTPUT_SCHEMA = {"assets": [{"name": "Asset name", "format": "PNG or SVG", "dimensions": "WxH in pixels", "placement": "Where it will be used", "notes": "Designer notes: colors, typography, content direction"}]}

async def run_brief_agent(brief: dict, brand_kit: dict, feedback: str = "") -> dict:
    system = f"""You are a creative producer. Specify exactly what design assets a designer needs for this product launch.
Infer assets from the launch goals and channels mentioned. Be precise — designers act on these specs directly.
Brand colors: {json.dumps(brand_kit.get("colors", {}))}
Typography: {json.dumps(brand_kit.get("typography", {}))}
Logo: {brand_kit.get("logo_url", "not provided")}
Return ONLY valid JSON matching the schema. No markdown."""

    user_prompt = f"""Generate asset specs for this launch:
Product: {brief["product_name"]}
Target Audience: {brief["target_audience"]}
Launch Goals: {brief["launch_goals"]}
Key Features: {json.dumps(brief["key_features"], indent=2)}
{f"Reviewer feedback to address: {feedback}" if feedback else ""}

Schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}"""

    response = await client.messages.create(
        model=MODEL, max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError("Brief agent response was truncated (max_tokens reached).")

    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
