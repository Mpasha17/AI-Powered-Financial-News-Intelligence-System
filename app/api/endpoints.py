from fastapi import APIRouter, HTTPException
from app.models.article import ArticleCreate
from app.ingestion.feed_poller import IngestionService
from app.agents.query import QueryAgent
from typing import List, Dict, Any

router = APIRouter()
query_agent = QueryAgent()
ingestion_service = IngestionService() # Note: In a real app, this should be a background task/singleton

@router.post("/ingest", response_model=Dict[str, str])
async def trigger_ingestion():
    """
    Triggers a single mock ingestion cycle.
    """
    article_create = ingestion_service.generate_mock_article()
    article = ingestion_service.process_article(article_create)
    return {"message": f"Ingested article: {article.title}", "id": article.id}

@router.get("/query")
async def query_news(q: str):
    """
    Natural language query for financial news.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query string is required")
    
    results = query_agent.search(q)
    return results

@router.get("/stats")
async def get_stats():
    """
    Returns system statistics.
    """
    from app.core.database import get_sqlite_conn
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE is_duplicate = 1")
    duplicates = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_articles": total,
        "duplicates_detected": duplicates,
        "unique_articles": total - duplicates
    }
