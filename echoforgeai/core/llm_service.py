"""
LLM service for handling interactions with language models.
"""
from typing import Dict, List, Optional, Union, Any
import json
import logging
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMResponse(BaseModel):
    """Response from an LLM call."""
    text: str
    choices: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dialogues: Dict[str, str] = Field(default_factory=dict)  # {character_name: dialogue_text}
    internal_monologues: Dict[str, str] = Field(default_factory=dict)  # Add internal thoughts

    class Config:
        arbitrary_types_allowed = True


class LLMService:
    """
    Service for interacting with language models.
    Currently supports OpenAI's API, but can be extended for other providers.
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, debug_mode: bool = False):
        """Initialize the LLM service."""
        self.provider = provider
        self.debug_mode = debug_mode
        
        if debug_mode:
            self.logger = logging.getLogger("echoforgeai.llm")
            self.logger.info(f"Initializing LLM service with provider: {provider}")
            
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
        character_contexts: Optional[Dict[str, dict]] = None,
        chapter_summaries: List[str] = None,
        internal_monologues: Dict[str, str] = None
    ) -> LLMResponse:
        """Enhanced story beat generation with professional writing guidance"""
        if self.debug_mode:
            self.logger.debug(f"Generating story beat for input: {user_input}")
            self.logger.debug(f"Current content length: {len(current_content)}")
            self.logger.debug(f"Number of memories: {len(memories)}")
            self.logger.debug(f"Character contexts: {list(character_contexts.keys()) if character_contexts else None}")
        
        # Build context sections
        memory_context = "\n".join(f"- {m}" for m in memories)
        chapter_context = "\n\n".join(chapter_summaries) if chapter_summaries else "No previous chapters"
        
        # Character handling
        player_context = ""
        npc_contexts = []
        present_characters = []
        if character_contexts:
            for name, ctx in character_contexts.items():
                if ctx["personality"].get("archetype") == "Player Character":
                    player_context = f"## Player Character\n{self._format_character(ctx)}"
                    present_characters.append(name)
                else:
                    npc_contexts.append(f"## {name}\n{self._format_character(ctx)}")
                    present_characters.append(name)
        
        # Professional writing guidance
        writing_advice = """## Storytelling Guidelines (Brandon Sanderson-inspired)
1. **Character Motivations**: Ensure character actions align with their stated goals and personality
2. **World-Building Details**: Include 1-2 sensory details that reinforce the setting
3. **Progression**: Advance at least one character relationship or plot thread
4. **Pacing**: Vary sentence structure between short impactful statements and longer descriptive ones
5. **Foreshadowing**: Include subtle hints about future plot developments
6. **Voice**: Maintain a tone suitable for the current scene (e.g., ominous for tense moments)
7. **Sanderson's First Law**: Ensure magic/unique elements solve problems in established ways"""
        
        # Update prompt template to include character thoughts
        character_thoughts = "\n".join([f"{name}: {thought}" for name, thought in internal_monologues.items()])
        
        prompt = f"""# Storyteller Instructions
You are a professional novelist crafting an immersive story experience. Below is the story context and your guidelines.

# Story Context
## Story History (Summarized)
{chapter_context}

## Current Scene
{current_content}

## Present Characters
{', '.join(present_characters) if present_characters else 'No known characters present'}

# Character Contexts
{player_context}
{"\n".join(npc_contexts)}

# Relevant Memories
{memory_context}

# Player Input
{user_input}

# Updated Context with Character Thoughts
{character_thoughts}

{writing_advice}

# Output Requirements
- Respond naturally to the input while advancing the overall narrative
- Include character-appropriate dialogue and reactions
- Provide 3 meaningful choices that reflect different approaches
- Use vivid, sensory language while maintaining readability

# Response Format
{{
    "text": "Your narrative text...",
    "metadata": {metadata_format}
}}"""
        
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

    async def generate_story_beat(self, context: Dict) -> LLMResponse:
        """Enhanced context handling"""
        prompt_template = """
        Current Story State: {history}
        Characters Present: {characters}
        Recent Events: {recent_events}
        Player Action: {input}
        
        Generate 2-3 paragraph response that:
        - Advances the main story thread
        - Develops character relationships
        - Introduces 1-2 new plot hooks
        - Provides 3 meaningful choices
        
        Style: {style_guidelines}
        """
        # Add style guidelines based on story genre
        context['style_guidelines'] = "Medieval fantasy, dramatic pacing, player agency"
        return await self.generate_story_beat(context['history'], context['input'], context['characters'], context['recent_events']) 

    async def compress_context(self, context: str) -> str:
        """Reduce context size while preserving key info"""
        return await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "Compress this narrative context while preserving characters, key events, and relationships."
            }]
        ) 

    def _format_character(self, ctx: dict) -> str:
        """Format character context for prompts"""
        return f"""- Personality: {ctx['personality'].get('archetype', 'Unknown')}
- Key Traits: {', '.join(ctx['personality'].get('traits', []))}
- Current Goals: {', '.join(g['description'] for g in ctx.get('goals', []))}
- Recent Knowledge: {', '.join(ctx.get('new_knowledge', []))[-3:]}
- Key Relationships: {', '.join(f"{k}: {v}" for k,v in ctx.get('relationships', {}).items())}""" 

    async def generate_character_reflection(
        self,
        character_name: str,
        personality: dict,
        current_scene: str,
        relevant_memories: List[str],
        relationships: Dict[str, float]
    ) -> str:
        """Generate a character's internal monologue about the current situation."""
        memory_context = "\n".join(f"- {m}" for m in relevant_memories)
        relationship_context = "\n".join([f"{name}: {sentiment}" for name, sentiment in relationships.items()])
        
        prompt = f"""You are {character_name}. Given the current situation, your personality, and memories, 
        what are you thinking privately? 

        Personality:
        {json.dumps(personality, indent=2)}

        Relevant Memories:
        {memory_context}

        Relationships:
        {relationship_context}

        Current Scene:
        {current_scene}

        Respond with a brief internal monologue (1-2 sentences) that:
        1. Reflects your personality traits
        2. Considers your goals and relationships
        3. Suggests potential actions or reactions
        """

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a method actor deeply immersed in your character."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip() 