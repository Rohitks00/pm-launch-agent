import pytest, json
from unittest.mock import AsyncMock, patch, MagicMock
from agents.copy_agent import run_copy_agent

BRIEF = {"product_name": "SmartSync", "launch_date": "April 1, 2026", "key_features": [{"name": "SmartSync", "benefit": "Saves 2hrs/week", "differentiator": "No manual exports"}], "target_audience": "Enterprise PMs", "launch_goals": "Drive 200 signups", "tone_notes": ""}
BRAND_KIT = {"name": "Acme", "voice_tone": "Confident", "do_list": ["Lead with benefits"], "dont_list": ["No jargon"], "style_rules": "Short sentences."}
MOCK_COPY = {"email": {"subject": "Save 2 hours with SmartSync", "body": "Hi...", "alt_subjects": ["Try SmartSync free"]}, "landing_page": {"headline": "Sync Everything. Save Hours.", "subheadline": "Real-time sync across all your tools.", "cta": "Get Started Free"}, "social": [{"platform": "LinkedIn", "copy": "..."}, {"platform": "Twitter/X", "copy": "..."}], "compliance_flags": []}

@pytest.mark.asyncio
async def test_copy_agent_returns_valid_structure():
    mock_message = MagicMock()
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps(MOCK_COPY)
    mock_message.content = [mock_text_block]

    with patch("agents.copy_agent.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_copy_agent(BRIEF, BRAND_KIT)

    assert "email" in result
    assert "landing_page" in result
    assert "social" in result
    assert result["landing_page"]["headline"] == "Sync Everything. Save Hours."

@pytest.mark.asyncio
async def test_copy_agent_only_generates_selected_sections():
    mock_message = MagicMock()
    mock_message.stop_reason = "end_turn"
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps({"email": {"subject": "s", "body": "b", "alt_subjects": []}, "compliance_flags": []})
    mock_message.content = [mock_text_block]

    with patch("agents.copy_agent.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_copy_agent(BRIEF, BRAND_KIT, enabled_sections=["email"])

    assert "email" in result
    # The mock returns only email; landing_page + social should not be present
    assert "landing_page" not in result
    assert "social" not in result

@pytest.mark.asyncio
async def test_copy_agent_generates_press_release():
    pr_content = {"press_release": {"headline": "SmartSync Launches", "body": "Full PR text...", "boilerplate": "About Acme..."}, "compliance_flags": []}
    mock_message = MagicMock()
    mock_message.stop_reason = "end_turn"
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps(pr_content)
    mock_message.content = [mock_text_block]

    with patch("agents.copy_agent.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_copy_agent(BRIEF, BRAND_KIT, enabled_sections=["press_release"])

    assert "press_release" in result
    assert "headline" in result["press_release"]
    assert "body" in result["press_release"]
