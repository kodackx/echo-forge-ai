"""
Story graph implementation for managing branching narratives.
"""
from typing import Dict, List, Optional, Set, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime

from echoforgeai.core.llm_service import LLMResponse


class StoryBeat(BaseModel):
    """Represents a single beat of story progression."""
    text: str
    available_choices: List[str]
    generated_content: Optional[dict] = None
    next_node: "StoryNode"
    
    def to_memory(self) -> str:
        """Convert this beat to a memory entry."""
        return self.text


class StoryNode(BaseModel):
    """
    Represents a node in the story graph, containing content and branching logic.
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    tags: Set[str] = Field(default_factory=set)
    requirements: Optional[dict] = None
    branches: Dict[str, UUID] = Field(default_factory=dict)
    is_entry_point: bool = False
    user_input: Optional[str] = None  # Track the choice that led here
    depth: int = 0  # Track narrative depth
    story_thread: str = "main"  # For parallel storylines
    hidden_requirements: Dict[str, Any] = Field(default_factory=dict)
    player_inputs: List[Dict] = Field(default_factory=list)  # {player_id: str, input: str}
    collaborative_context: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)
    branching_strategy: str = Field(default="linear")  # Options: "save_point", "parallel", "time_jump"
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_branch(self, condition: str, target_node: "StoryNode") -> None:
        """Add a new branch from this node."""
        self.branches[condition] = target_node.id
        
    def meets_requirements(self, state: dict) -> bool:
        """Check if this node's requirements are met given the current state."""
        if not self.requirements:
            return True
            
        # TODO: Implement requirement checking logic
        return True


class StoryGraph:
    """
    Manages the graph of story nodes and handles navigation between them.
    """
    
    def __init__(self):
        """Initialize an empty story graph."""
        self.nodes: Dict[UUID, StoryNode] = {}
        self._entry_nodes: List[UUID] = []
        self.chapter_summaries: List[str] = []  # Store summarized chapters
        self.max_context_nodes = 20  # Configurable
        
    def add_node(self, node: StoryNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.is_entry_point:
            self._entry_nodes.append(node.id)
            
    def get_node(self, node_id: UUID) -> StoryNode:
        """Get a node by its ID."""
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found in graph")
        return self.nodes[node_id]
        
    def get_entry_node(self, node_id: Optional[UUID] = None) -> StoryNode:
        """Get the specified entry node or the default one."""
        if not self._entry_nodes:
            raise RuntimeError("No entry nodes defined in the graph")
            
        if node_id:
            if node_id not in self.nodes or node_id not in self._entry_nodes:
                raise KeyError(f"Entry node {node_id} not found")
            return self.nodes[node_id]
            
        return self.nodes[self._entry_nodes[0]]
        
    async def process_input(
        self,
        current_node: StoryNode,
        user_input: str,
        relevant_memories: List[str],
        llm_response: LLMResponse
    ) -> StoryBeat:
        """
        Process user input at the current node and determine the next story beat.
        
        Args:
            current_node: The current node in the story
            user_input: The user's input/choice
            relevant_memories: List of relevant memory strings
            llm_response: The generated content from the LLM
            
        Returns:
            A StoryBeat containing the next piece of narrative and available choices
        """
        # Before generating new beat
        if len(self.nodes) > self.max_context_nodes:
            await self._finalize_chapter()
        
        # Create a new node for this story beat
        new_node = StoryNode(
            title=f"Response to: {user_input[:50]}...",
            content=llm_response.text,
            tags=current_node.tags
        )
        self.add_node(new_node)
        
        # Add branches based on LLM-generated choices
        for choice in llm_response.choices:
            # Create a placeholder node for each choice
            choice_node = StoryNode(
                title=f"Choice: {choice[:50]}...",
                content="To be generated",
                tags=current_node.tags
            )
            self.add_node(choice_node)
            new_node.add_branch(choice, choice_node)
            
        return StoryBeat(
            text=llm_response.text,
            available_choices=llm_response.choices,
            generated_content=llm_response.metadata,
            next_node=new_node
        )
        
    async def get_initial_beat(self, entry_node: StoryNode) -> StoryBeat:
        """Get the initial story beat for an entry node."""
        return StoryBeat(
            text=entry_node.content,
            available_choices=list(entry_node.branches.keys()),
            next_node=entry_node
        )
        
    def export_state(self) -> dict:
        """Export the graph state for serialization."""
        return {
            "nodes": {
                str(node_id): node.model_dump()
                for node_id, node in self.nodes.items()
            },
            "entry_nodes": [str(node_id) for node_id in self._entry_nodes]
        }
        
    async def import_state(self, state: dict) -> None:
        """Import a previously exported graph state."""
        self.nodes.clear()
        self._entry_nodes.clear()
        
        # Restore nodes
        for node_id, node_data in state["nodes"].items():
            node = StoryNode(**node_data)
            self.nodes[UUID(node_id)] = node
            
        # Restore entry nodes
        self._entry_nodes = [UUID(node_id) for node_id in state["entry_nodes"]] 

    def get_narrative_path(self, max_depth=10) -> List[StoryNode]:
        """Get current narrative path for context"""
        path = []
        current = self.current_node
        while current and len(path) < max_depth:
            path.insert(0, current)
            current = self.get_previous_node(current.id)
        return path

    def get_previous_node(self, node_id: UUID) -> Optional[StoryNode]:
        """Find which node leads to this one"""
        for node in self.nodes.values():
            if node_id in node.branches.values():
                return node
        return None 

    async def _finalize_chapter(self):
        """Summarize and archive old nodes"""
        old_nodes = sorted(self.nodes.values(), key=lambda n: n.last_updated)[:self.max_context_nodes//2]
        summary = await self._summarize_nodes(old_nodes)
        self.chapter_summaries.append(summary)
        # Remove old nodes
        for node in old_nodes:
            del self.nodes[node.id] 

    async def create_save_point(self, node: StoryNode) -> UUID:
        """Create a restorable branch point"""
        save_node = StoryNode(
            title=f"Save Point: {node.title}",
            content=node.content,
            branching_strategy="save_point"
        )
        self.add_node(save_node)
        return save_node.id 