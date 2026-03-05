import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.orchestrator import run_orchestrator

SAMPLE_DOC = """# SmartSync Feature Launch
Launch Date: April 1, 2026

## What We're Shipping
SmartSync automatically syncs data across all your tools in real-time.

## Target Audience
Enterprise PMs who manage data across 5+ tools.

## Launch Goals
Drive 200 signups in the first month."""

@pytest.mark.asyncio
async def test_orchestrator_extracts_brief():
    mock_message = MagicMock()
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = '{"product_name": "SmartSync", "launch_date": "April 1, 2026", "key_features": [{"name": "SmartSync", "benefit": "Real-time sync", "differentiator": "No manual exports"}], "target_audience": "Enterprise PMs", "launch_goals": "Drive 200 signups", "tone_notes": ""}'
    mock_message.content = [mock_text_block]

    with patch("agents.orchestrator.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_orchestrator(SAMPLE_DOC, brand_kit_name="Acme", voice_tone="Professional")

    assert result["product_name"] == "SmartSync"
    assert result["launch_date"] == "April 1, 2026"
    assert len(result["key_features"]) == 1

@pytest.mark.asyncio
async def test_orchestrator_handles_null_fields():
    mock_message = MagicMock()
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = '{"product_name": "SmartSync", "launch_date": null, "key_features": [], "target_audience": "", "launch_goals": "", "tone_notes": ""}'
    mock_message.content = [mock_text_block]

    with patch("agents.orchestrator.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await run_orchestrator("minimal doc", brand_kit_name="Acme", voice_tone="Professional")

    assert result["launch_date"] is None
