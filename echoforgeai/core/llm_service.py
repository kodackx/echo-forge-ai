"""
LLM service for handling interactions with language models.
"""
from typing import Dict, List, Optional, Union, Any
import json
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMResponse(BaseModel):
    """Response from an LLM call."""
    text: str
    choices: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class LLMService:
    """
    Service for interacting with language models.
    Currently supports OpenAI's API, but can be extended for other providers.
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """Initialize the LLM service."""
        self.provider = provider
        if provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_story_beat(
        self,
        current_content: str,
        user_input: str,
        memories: List[str],
        character_contexts: Optional[Dict[str, dict]] = None
    ) -> LLMResponse:
        """
        Generate the next story beat based on current context and user input.
        
        Args:
            current_content: The current story node's content
            user_input: The user's input/choice
            memories: List of relevant memory strings
            character_contexts: Optional dict of character contexts
            
        Returns:
            LLMResponse containing generated text and choices
        """
        # Build the prompt
        memory_context = "\n".join(f"- {m}" for m in memories)
        
        # Separate player character from NPCs for clearer context
        player_context = ""
        npc_contexts = ""
        if character_contexts:
            for name, ctx in character_contexts.items():
                if ctx["personality"].get("archetype") == "Player Character":
                    player_context = f"Player ({name}):\n{json.dumps(ctx, indent=2)}"
                else:
                    npc_contexts += f"\n{name}:\n{json.dumps(ctx, indent=2)}"
        
        # Define metadata format separately to avoid deep nesting in f-string
        metadata_format = """
{
    "character_updates": {
        "character_name": {
            "relationships": {"other_character": sentiment_value},
            "goal_updates": [{"description": "goal text", "progress": progress_value}],
            "new_knowledge": ["new fact learned"]
        }
    }
}"""
            
        prompt = f"""You are an expert storyteller. Based on the current story state and user input, generate the next story beat.

Current Story State:
{current_content}

Relevant Memories:
{memory_context}

Player Character Information:
{player_context}

NPC Information:
{npc_contexts}

User Input:
{user_input}

Generate an engaging continuation of the story that:
1. Responds naturally to the user's input, taking into account the player character's personality and background
2. Maintains consistency with previous events and character knowledge
3. Has NPCs react appropriately based on their personalities and relationships
4. Advances character relationships and story development naturally

Format your response as JSON with:
- "text": The story continuation (written in second person, addressing the player character directly)
- "metadata": {metadata_format}
"""
        
        # Call the LLM
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Using GPT-4 for better storytelling
            messages=[
                {"role": "system", "content": "You are a master storyteller."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse the response
        try:
            result = json.loads(response.choices[0].message.content)
            return LLMResponse(**result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_dialogue(
        self,
        character_name: str,
        personality: dict,
        topic: str,
        memories: List[str],
        context: Optional[dict] = None,
        style: Optional[str] = None
    ) -> str:
        """
        Generate dialogue for a character.
        
        Args:
            character_name: Name of the speaking character
            personality: Character's personality data
            topic: The topic/prompt for dialogue
            memories: Character's relevant memories
            context: Optional additional context
            style: Optional style override
            
        Returns:
            Generated dialogue string
        """
        # Build the prompt
        memory_context = "\n".join(f"- {m}" for m in memories)
        style_info = f"\nStyle: {style}" if style else ""
        context_info = f"\nContext: {json.dumps(context, indent=2)}" if context else ""
        
        prompt = f"""Generate dialogue for {character_name} based on their personality and memories.

Character Personality:
{json.dumps(personality, indent=2)}

Relevant Memories:
{memory_context}
{context_info}
{style_info}

Topic/Prompt:
{topic}

Generate dialogue that:
1. Matches the character's personality traits
2. References relevant memories naturally
3. Maintains consistent character voice
4. Responds appropriately to the topic/prompt
"""
        
        # Call the LLM
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert dialogue writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding 