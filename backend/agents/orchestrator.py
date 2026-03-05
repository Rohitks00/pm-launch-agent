import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
MODEL = "claude-opus-4-6"

SYSTEM = """You are a product launch analyst. Extract a structured brief from raw PM documents.
Be conservative: if a field is not clearly stated, set it to null or empty string. Do not infer or hallucinate.
Return ONLY valid JSON with this exact schema:
{
  "product_name": "string or null",
  "launch_date": "string or null",
  "key_features": [{"name": "string", "benefit": "string", "differentiator": "string"}],
  "target_audience": "string",
  "launch_goals": "string",
  "tone_notes": "string"
}"""

async def run_orchestrator(raw_input: str, brand_kit_name: str, voice_tone: str) -> dict:
    user_prompt = f"Brand context: {brand_kit_name} — {voice_tone}\n\nDocument:\n{raw_input}"

    response = await client.messages.create(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
