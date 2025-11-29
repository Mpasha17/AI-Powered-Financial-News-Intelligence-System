from sentence_transformers import SentenceTransformer
from app.core.database import get_collection, get_sqlite_conn
from typing import List, Dict, Any
import json

# Reuse model (should be singleton)
model = SentenceTransformer('all-MiniLM-L6-v2')

class QueryAgent:
    def __init__(self):
        self.collection = get_collection()

    def expand_query(self, query: str) -> List[str]:
        """
        Expands query with related terms (Mock implementation).
        Real implementation would use LLM or Knowledge Graph.
        """
        expanded = [query]
        query_lower = query.lower()
        
        if "hdfc" in query_lower:
            expanded.append("Banking Sector")
            expanded.append("HDFC Bank")
        if "banking" in query_lower:
            expanded.extend(["HDFC Bank", "ICICI Bank", "SBI", "RBI"])
        if "rbi" in query_lower:
            expanded.append("Monetary Policy")
            
        return list(set(expanded))

    def search(self, query: str) -> Dict[str, Any]:
        # 1. Expand Query
        expanded_queries = self.expand_query(query)
        print(f"Expanded Query: {expanded_queries}")
        
        # 2. Semantic Search (Vector DB)
        # We search for the original query and maybe expanded terms
        # For simplicity, let's just search the original query but use expanded terms for filtering if we had metadata
        
        embedding = model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=5,
            include=["metadatas", "distances", "documents"]
        )
        
        # 3. Retrieve full details from SQLite
        article_ids = results['ids'][0] if results['ids'] else []
        articles = []
        
        if article_ids:
            conn = get_sqlite_conn()
            placeholders = ','.join('?' for _ in article_ids)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM articles WHERE id IN ({placeholders})", article_ids)
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                article = dict(row)
                # Parse JSON fields
                if article['entities_json']:
                    article['entities'] = json.loads(article['entities_json'])
                if article['impacted_stocks_json']:
                    article['impacted_stocks'] = json.loads(article['impacted_stocks_json'])
                articles.append(article)
                
        return {
            "query": query,
            "expanded_context": expanded_queries,
            "results": articles
        }
