"""
Tests for the tavern adventure example.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch

from echoforgeai import Story, StoryNode, LLMResponse, StoryConfig
from tavern_adventure import create_characters, create_initial_node


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return LLMResponse(
        text="Old Tom greets you warmly. 'Welcome to the Silver Flagon! What can I get you?'",
        choices=[
            "Order a drink",
            "Ask about recent gossip",
            "Inquire about the mysterious stranger"
        ],
        metadata={
            "character_updates": {
                "Old Tom": {
                    "relationships": {"player": 0.2},
                    "new_knowledge": ["A new patron has arrived at the tavern"]
                }
            }
        }
    )


@pytest.mark.asyncio
async def test_create_characters():
    """Test character creation."""
    characters = await create_characters()
    assert len(characters) == 2
    
    bartender = next(c for c in characters if c.name == "Old Tom")
    stranger = next(c for c in characters if c.name == "The Stranger")
    
    # Check bartender traits
    assert "friendly" in bartender.personality.traits
    assert bartender.personality.traits["friendly"].intensity == 0.8
    assert len(bartender._initial_knowledge) == 4
    
    # Check stranger goals
    assert len(stranger.personality.goals) == 1
    assert "Find a trustworthy adventurer" in stranger.personality.goals[0].description


def test_create_initial_node():
    """Test initial node creation."""
    node = create_initial_node()
    assert node.is_entry_point
    assert "tavern" in node.tags
    assert "Silver Flagon" in node.content


@pytest.mark.asyncio
async def test_story_flow(mock_llm_response):
    """Test the basic story flow."""
    with patch("echoforgeai.core.llm_service.LLMService") as MockLLM:
        # Set up mock LLM
        mock_llm = AsyncMock()
        mock_llm.generate_story_beat.return_value = mock_llm_response
        MockLLM.return_value = mock_llm
        
        # Initialize story
        story = Story(StoryConfig(
            title="Test Story",
            api_key="dummy_key"
        ))
        
        # Add characters and initial node
        for character in await create_characters():
            await story.add_character(character)
        story.graph.add_node(create_initial_node())
        
        # Start story
        start_result = await story.start()
        assert "Silver Flagon" in start_result["text"]
        
        # Test interaction
        advance_result = await story.advance("Approach the bar")
        assert "Old Tom" in advance_result["text"]
        assert len(advance_result["choices"]) == 3
        assert any("drink" in choice.lower() for choice in advance_result["choices"])
        
        # Verify character updates
        bartender = story.characters["Old Tom"]
        assert bartender.personality.relationships.get("player") == 0.2 