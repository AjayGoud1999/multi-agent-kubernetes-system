import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np

from app.config import Settings, get_logger, get_settings

logger = get_logger(__name__)


@dataclass
class Document:
    """Represents a document chunk with metadata."""
    id: str
    content: str
    metadata: dict


class VectorStore:
    """FAISS-based vector store for document retrieval."""
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.store_path = Path(self.settings.vector_store_path)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: List[Document] = []
        self._dimension: int = 1536
    
    def initialize(self, dimension: int) -> None:
        """Initialize a new FAISS index."""
        self._dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []
        logger.info(f"Initialized new FAISS index with dimension {dimension}")
    
    def add_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]]
    ) -> None:
        """Add documents and their embeddings to the store."""
        if not documents or not embeddings:
            return
        
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        if self.index is None:
            self.initialize(len(embeddings[0]))
        
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)
        
        self.index.add(embeddings_array)
        self.documents.extend(documents)
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents."""
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty, returning no results")
            return []
        
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        logger.info(f"Found {len(results)} similar documents")
        return results
    
    def save(self) -> None:
        """Persist the vector store to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        index_path = self.store_path / "index.faiss"
        faiss.write_index(self.index, str(index_path))
        
        docs_path = self.store_path / "documents.json"
        docs_data = [
            {"id": doc.id, "content": doc.content, "metadata": doc.metadata}
            for doc in self.documents
        ]
        with open(docs_path, "w") as f:
            json.dump(docs_data, f)
        
        meta_path = self.store_path / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump({"dimension": self._dimension}, f)
        
        logger.info(f"Saved vector store to {self.store_path}")
    
    def load(self) -> bool:
        """Load the vector store from disk."""
        index_path = self.store_path / "index.faiss"
        docs_path = self.store_path / "documents.json"
        meta_path = self.store_path / "metadata.json"
        
        if not all(p.exists() for p in [index_path, docs_path, meta_path]):
            logger.info("No existing vector store found")
            return False
        
        try:
            self.index = faiss.read_index(str(index_path))
            
            with open(docs_path, "r") as f:
                docs_data = json.load(f)
            self.documents = [
                Document(id=d["id"], content=d["content"], metadata=d["metadata"])
                for d in docs_data
            ]
            
            with open(meta_path, "r") as f:
                meta = json.load(f)
            self._dimension = meta["dimension"]
            
            logger.info(f"Loaded vector store with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    @property
    def is_ready(self) -> bool:
        """Check if the vector store is initialized and has documents."""
        return self.index is not None and self.index.ntotal > 0
    
    @property
    def document_count(self) -> int:
        """Return the number of documents in the store."""
        return len(self.documents)
