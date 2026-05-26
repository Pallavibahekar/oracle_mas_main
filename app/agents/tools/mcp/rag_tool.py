import json
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("rag-tool", port=8092)

# Initialize Qdrant client
qdrant_client = None

def get_qdrant_client():
    """Get or create Qdrant client instance."""
    global qdrant_client
    if qdrant_client is None:
        from app.core.config import settings
        qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=30
        )
        logger.info(f"Initialized Qdrant client: {settings.qdrant_host}:{settings.qdrant_port}")
    return qdrant_client


def ensure_collection_exists(client: QdrantClient, collection_name: str, vector_size: int = 384):
    """
    Ensure the collection exists in Qdrant, create if it doesn't.
    
    Args:
        client: Qdrant client instance
        collection_name: Name of the collection
        vector_size: Size of the vector embeddings (default: 384 for all-MiniLM-L6-v2)
    """
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            # Create collection with vector configuration
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created new collection: {collection_name}")
        else:
            logger.info(f"Collection already exists: {collection_name}")
            
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {str(e)}")
        raise


class AdditionalContext(BaseModel):
    tags: list[str] = Field(description="Tags to search for", default=[])
    entities: list[str] = Field(description="Entities to search for", default=[])


@mcp.prompt(
    name="search-prompt",
    title="Search prompt",
    description="Search for relevant documents, based on ",
)
def search_prompt(query: str, additional_context: AdditionalContext, ctx: Context) -> str:
    return f"""Find me all the documents that are relevant to the query {query}, here is some additional context
    {additional_context.model_dump_json(indent=2)}"""



@mcp.tool(name="query-vector-db", title="Query vector database", description="Query the vector database for relevant documents")
def query_vector_db(query: str, top_k: int = 10) -> str:
    """
    Query the Qdrant vector database for relevant documents.
    
    Args:
        query: The search query text
        top_k: Number of top results to return (default: 10)
        score_threshold: Minimum similarity score threshold (default: 0.5)
    
    Returns:
        List of dictionaries containing document content and metadata
    """
    try:
        print("querying vector db")
        from app.core.config import settings
        from sentence_transformers import SentenceTransformer
        
        # Get Qdrant client
        client = get_qdrant_client()
        
        # Ensure collection exists (create if needed)
        ensure_collection_exists(client, settings.qdrant_collection_name)
        
        # Initialize embedding model (using sentence-transformers which is already in requirements)
        # You can change this to match your actual embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search in Qdrant
        search_results = client.search(
            collection_name=settings.qdrant_collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        results = []
        for hit in search_results:
            result = {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload if hit.payload else {},
            }
            
            # Extract text content if available in payload
            if hit.payload:
                if "text" in hit.payload:
                    result["text"] = hit.payload["text"]
                elif "content" in hit.payload:
                    result["text"] = hit.payload["content"]
                elif "chunk" in hit.payload:
                    result["text"] = hit.payload["chunk"]
                
                # Include metadata
                if "metadata" in hit.payload:
                    result["metadata"] = hit.payload["metadata"]
                    
            results.append(result)
        
        logger.info(f"Found {len(results)} relevant documents for query: '{query}'")
        return json.dumps(results, indent=2) 
        
    except Exception as e:
        logger.error(f"Error querying Qdrant: {str(e)}")
        # Return empty list on error, but you could also raise the exception
        return json.dumps([], indent=2)


@mcp.tool(name="ingest-document", title="Ingest document", description="Ingest a document into the vector database")
def ingest_document(
    document: str, 
    metadata: Dict[str, Any] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> str:
    """
    Ingest a document into the vector database.
    
    Args:
        document: The document text to ingest
        metadata: Optional metadata to associate with the document (e.g., {"source": "file.pdf", "author": "John"})
        chunk_size: Maximum size of each text chunk (default: 500 characters)
        chunk_overlap: Number of characters to overlap between chunks (default: 50)
    
    Returns:
        Success message with number of chunks ingested
    """
    try:
        from app.core.config import settings
        from sentence_transformers import SentenceTransformer
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        import uuid
        from datetime import datetime, timezone
        
        # Get Qdrant client
        client = get_qdrant_client()
        
        # Ensure collection exists
        ensure_collection_exists(client, settings.qdrant_collection_name)
        
        # Initialize embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Split document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_text(document)
        
        if not chunks:
            return "No content to ingest"
        
        # Prepare points for batch upload
        points = []
        
        for i, chunk in enumerate(chunks):
            # Generate unique ID for each chunk
            chunk_id = str(uuid.uuid4())
            
            # Generate embedding for the chunk
            embedding = model.encode(chunk).tolist()
            
            # Prepare payload with chunk text and metadata
            payload = {
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Add custom metadata if provided
            if metadata:
                payload["metadata"] = metadata
            
            # Create point
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        # Batch upload all points to Qdrant
        client.upsert(
            collection_name=settings.qdrant_collection_name,
            points=points,
            wait=True  # Wait for indexing to complete
        )
        
        logger.info(f"Successfully ingested {len(chunks)} chunks into collection: {settings.qdrant_collection_name}")
        
        return f"Successfully ingested document: {len(chunks)} chunks created and stored in {settings.qdrant_collection_name}"
        
    except Exception as e:
        error_msg = f"Error ingesting document: {str(e)}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    mcp.run(transport="streamable-http")