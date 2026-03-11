import pytest, json
from unittest.mock import AsyncMock, patch, MagicMock
from agents.brief_agent import run_brief_agent

BRIEF = {"product_name": "SmartSync", "launch_date": "April 1, 2026", "key_features": [], "target_audience": "Enterprise PMs", "launch_goals": "Drive signups via LinkedIn and email", "tone_notes": ""}
BRAND_KIT = {"name": "Acme", "colors": {"primary": "#1A1A2E", "accent": "#E94560"}, "typography": {"heading": "Söhne", "body": "Inter"}, "logo_url": "/assets/logo.png"}
MOCK_SPECS = {"assets": [{"name": "Launch Hero Banner", "format": "PNG", "dimensions": "1920x1080", "placement": "Website homepage", "notes": "Primary blue background"}, {"name": "LinkedIn Social Card", "format": "PNG", "dimensions": "1200x627", "placement": "LinkedIn post", "notes": "Accent color, logo top-left"}, {"name": "Email Header", "format": "PNG", "dimensions": "600x200", "placement": "Email campaign", "notes": "White background, centered logo"}]}

@pytest.mark.asyncio
async def test_brief_agent_returns_asset_list():
    mock_message = MagicMock()
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps(MOCK_SPECS)
    mock_message.content = [mock_text_block]

    with patch("agents.brief_agent.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_brief_agent(BRIEF, BRAND_KIT)

    assert "assets" in result
    assert len(result["assets"]) == 3
    assert result["assets"][0]["name"] == "Launch Hero Banner"
    assert "dimensions" in result["assets"][0]

@pytest.mark.asyncio
async def test_brief_agent_only_generates_selected_types():
    hero_only = {"assets": [{"name": "Hero Image", "format": "PNG", "dimensions": "1440x800", "placement": "Landing page", "notes": "Primary color background"}]}
    mock_message = MagicMock()
    mock_message.stop_reason = "end_turn"
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps(hero_only)
    mock_message.content = [mock_text_block]

    with patch("agents.brief_agent.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_brief_agent(BRIEF, BRAND_KIT, enabled_asset_types=["hero_image"])

    assets = result.get("assets", [])
    assert len(assets) >= 1
    # Verify the instruction was passed — check the prompt content
    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs.get("messages") or call_args.args[0] if call_args.args else []
    user_content = next((m["content"] for m in (call_args.kwargs.get("messages", [])) if m["role"] == "user"), "")
    assert "hero_image" in user_content
