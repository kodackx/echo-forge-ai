"""
HearthKin 2 - A flexible Python library for creating immersive, dynamic story-driven experiences with LLMs.
"""

__version__ = "0.1.0"

from echoforgeai.core.story import Story, StoryConfig
from echoforgeai.core.character import Character, PersonalityModel, PersonalityTrait, CharacterGoal
from echoforgeai.graph.story_graph import StoryGraph, StoryNode
from echoforgeai.memory.vector_store import MemoryBank
from echoforgeai.core.llm_service import LLMResponse

__all__ = [
    "Story", 
    "StoryConfig", 
    "Character", 
    "StoryGraph", 
    "StoryNode", 
    "MemoryBank", 
    "LLMResponse",
    "PersonalityModel",
    "PersonalityTrait",
    "CharacterGoal"
] 