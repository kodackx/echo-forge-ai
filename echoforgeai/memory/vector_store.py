"""
Vector-based memory storage implementation using FAISS.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import faiss
from pydantic import BaseModel, Field


class Memory(BaseModel):
    """A single memory entry with its metadata."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None


class MemoryBank:
    """
    Manages storage and retrieval of memories using vector embeddings.
    """
    
    def __init__(
        self,
        backend: str = "faiss",
        embedding_dim: int = 1536,  # OpenAI ada-002 dimension
        max_items: int = 1000
    ):
        """Initialize the memory bank."""
        self.backend = backend
        self.embedding_dim = embedding_dim
        self.max_items = max_items
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(embedding_dim)
        
        # Memory storage
        self.memories: List[Memory] = []
        
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text string."""
        # TODO: Implement actual embedding generation using OpenAI or alternative
        # For now, return random embedding
        return list(np.random.rand(self.embedding_dim))
        
    def store_sync(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Synchronous version of store for initialization."""
        embedding = self._get_embedding(content)
        memory = Memory(
            content=content,
            metadata=metadata or {},
            embedding=embedding
        )
        
        # Add to FAISS index
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Add to memory list
        self.memories.append(memory)
        
        # Maintain max size
        if len(self.memories) > self.max_items:
            # Remove oldest memory
            self.index.remove_ids(np.array([0]))
            self.memories.pop(0)
            
    async def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store a new memory."""
        self.store_sync(content, metadata)
        
    async def retrieve_relevant(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Memory]:
        """
        Retrieve memories relevant to the query.
        
        Args:
            query: The query string
            filter_metadata: Optional metadata filters
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant Memory objects
        """
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        # Search in FAISS
        D, I = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            min(limit * 2, len(self.memories))  # Get extra results for filtering
        )
        
        # Filter and sort results
        results = []
        for idx in I[0]:
            memory = self.memories[idx]
            
            # Apply metadata filters
            if filter_metadata:
                matches_filter = all(
                    memory.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not matches_filter:
                    continue
                    
            results.append(memory)
            if len(results) >= limit:
                break
                
        return results
        
    def export_state(self) -> dict:
        """Export memory state for serialization."""
        return {
            "memories": [
                {
                    "content": m.content,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat(),
                    "embedding": m.embedding
                }
                for m in self.memories
            ],
            "config": {
                "backend": self.backend,
                "embedding_dim": self.embedding_dim,
                "max_items": self.max_items
            }
        }
        
    async def import_state(self, state: dict) -> None:
        """Import a previously exported memory state."""
        # Reset current state
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.memories.clear()
        
        # Update config
        config = state["config"]
        self.backend = config["backend"]
        self.embedding_dim = config["embedding_dim"]
        self.max_items = config["max_items"]
        
        # Restore memories
        embeddings = []
        for memory_data in state["memories"]:
            memory = Memory(
                content=memory_data["content"],
                metadata=memory_data["metadata"],
                timestamp=datetime.fromisoformat(memory_data["timestamp"]),
                embedding=memory_data["embedding"]
            )
            self.memories.append(memory)
            embeddings.append(memory.embedding)
            
        # Restore FAISS index
        if embeddings:
            self.index.add(np.array(embeddings, dtype=np.float32)) 