import os
import uuid
from pathlib import Path
from typing import List

from app.config import Settings, get_logger, get_settings
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import Document, VectorStore

logger = get_logger(__name__)


class DocumentRetriever:
    """Retrieves relevant documents using RAG."""
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.embedding_service = EmbeddingService(settings)
        self.vector_store = VectorStore(settings)
        self._initialized = False
    
    async def initialize(self, force_rebuild: bool = False) -> None:
        """Initialize the retriever, loading or building the vector store."""
        if self._initialized and not force_rebuild:
            return
        
        if not force_rebuild and self.vector_store.load():
            self._initialized = True
            logger.info("Loaded existing vector store")
            return
        
        await self._build_vector_store()
        self._initialized = True
    
    async def _build_vector_store(self) -> None:
        """Build the vector store from K8s documentation files."""
        docs_path = Path(self.settings.k8s_docs_path)
        
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Created empty docs directory: {docs_path}")
        
        documents = self._load_and_chunk_documents(docs_path)
        
        if not documents:
            logger.warning("No documents found to index")
            self.vector_store.initialize(self.embedding_service.embedding_dimension)
            return
        
        texts = [doc.content for doc in documents]
        embeddings = await self.embedding_service.embed_texts(texts)
        
        self.vector_store.initialize(self.embedding_service.embedding_dimension)
        self.vector_store.add_documents(documents, embeddings)
        self.vector_store.save()
        
        logger.info(f"Built vector store with {len(documents)} document chunks")
    
    def _load_and_chunk_documents(self, docs_path: Path) -> List[Document]:
        """Load documents from files and split into chunks."""
        documents = []
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        for file_path in docs_path.glob("**/*.txt"):
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = self._split_text(content, chunk_size, chunk_overlap)
                
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        id=f"{file_path.stem}_{i}_{uuid.uuid4().hex[:8]}",
                        content=chunk,
                        metadata={
                            "source": str(file_path),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    documents.append(doc)
                
                logger.debug(f"Loaded {len(chunks)} chunks from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        for file_path in docs_path.glob("**/*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = self._split_text(content, chunk_size, chunk_overlap)
                
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        id=f"{file_path.stem}_{i}_{uuid.uuid4().hex[:8]}",
                        content=chunk,
                        metadata={
                            "source": str(file_path),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    documents.append(doc)
                
                logger.debug(f"Loaded {len(chunks)} chunks from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        return documents
    
    def _split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(para) > chunk_size:
                    words = para.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 <= chunk_size:
                            current_chunk = f"{current_chunk} {word}".strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = word
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        if overlap > 0 and len(chunks) > 1:
            overlapped_chunks = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                overlapped_chunks.append(f"{overlap_text}...{chunks[i]}")
            chunks = overlapped_chunks
        
        return chunks
    
    async def retrieve(self, query: str, top_k: int | None = None) -> List[str]:
        """Retrieve relevant document chunks for a query."""
        if not self._initialized:
            await self.initialize()
        
        if not self.vector_store.is_ready:
            logger.warning("Vector store is not ready, returning empty results")
            return []
        
        k = top_k or self.settings.top_k_results
        
        query_embedding = await self.embedding_service.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=k)
        
        chunks = [doc.content for doc, score in results]
        logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
        
        return chunks
    
    @property
    def is_ready(self) -> bool:
        """Check if the retriever is ready to serve queries."""
        return self._initialized and self.vector_store.is_ready
