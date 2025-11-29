from sentence_transformers import SentenceTransformer
from app.core.database import get_collection, get_sqlite_conn
from typing import List, Dict, Any
import json

# Reuse model (should be singleton)
model = SentenceTransformer('all-MiniLM-L6-v2')

class QueryAgent:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def expand_query(self, query: str) -> List[str]:
        """
        Real AI expansion using an LLM (Mistral).
        """
        try:
            from langchain_mistralai import ChatMistralAI
            # Using mistral-large-latest as requested
            llm = ChatMistralAI(
                model="mistral-large-latest",
                temperature=0,
                max_retries=2
            )
            
            prompt = f"""
            You are a financial trading assistant. The user is searching for: "{query}".
            Generate a list of 3-5 related search terms, including:
            1. The specific company ticker (if applicable, e.g., HDFC -> HDFCBANK).
            2. The relevant sector (e.g., Banking, IT).
            3. Key regulatory bodies (e.g., RBI, SEBI).
            4. Synonyms for the event (e.g., "rates up" -> "repo rate hike").
            
            Return ONLY a comma-separated list of terms.
            """
            
            response = llm.invoke(prompt)
            expanded_terms = [term.strip() for term in response.content.split(",")]
            # Add original query to ensure we search for exact match too
            expanded_terms.append(query) 
            return list(set(expanded_terms))
            
        except Exception as e:
            print(f"LLM Error (Context Expansion): {e}")
            # Fallback to simple heuristic if LLM fails
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
        from app.core.database import get_collection, get_article_from_sqlite
        collection = get_collection()
        
        # 1. Expand Query
        expanded_queries = self.expand_query(query)
        print(f"Expanded Query: {expanded_queries}")
        
        # 2. Vector Search (using the original query + expanded terms combined or just original?)
        # Better approach: Search for original query, but use expanded terms for re-ranking or multiple searches.
        # For simplicity: Search for the original query, but maybe append top expanded term.
        
        search_text = query + " " + " ".join(expanded_queries[:2])
        query_embedding = self.model.encode(search_text).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
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
