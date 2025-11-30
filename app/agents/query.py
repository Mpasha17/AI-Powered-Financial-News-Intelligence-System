from sentence_transformers import SentenceTransformer
from app.core.database import get_collection, get_sqlite_conn
from typing import List, Dict, Any
import json

# Reuse model (should be singleton)
model = SentenceTransformer('all-MiniLM-L6-v2')

class QueryAgent:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def expand_query(self, query: str) -> Dict[str, Any]:
        """
        Real AI expansion using an LLM (Mistral).
        Returns dict with expanded terms and target sector.
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
            
            Task:
            1. Identify the Target Sector (e.g., Banking, IT, Energy, Auto, Pharma). If unclear, use "General".
            2. Generate 3-5 related search terms (synonyms, tickers, regulators).
            
            Return ONLY a valid JSON object:
            {{
                "sector": "Sector Name",
                "terms": ["term1", "term2", "term3"]
            }}
            """
            
            response = llm.invoke(prompt)
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            terms = data.get("terms", [])
            terms.append(query)
            
            return {
                "terms": list(set(terms)),
                "sector": data.get("sector", "General")
            }
            
        except Exception as e:
            print(f"LLM Error (Context Expansion): {e}")
            # Fallback
            return {
                "terms": [query],
                "sector": "General"
            }

    def search(self, query: str) -> Dict[str, Any]:
        from app.core.database import get_collection, get_article_from_sqlite
        collection = get_collection()
        
        # 1. Expand Query
        expansion_result = self.expand_query(query)
        expanded_queries = expansion_result["terms"]
        target_sector = expansion_result["sector"]
        
        print(f"Expanded Query: {expanded_queries}, Target Sector: {target_sector}")
        
        # 2. Vector Search with Sector Filter
        search_text = query + " " + " ".join(expanded_queries[:2])
        query_embedding = self.model.encode(search_text).tolist()
        
        # Construct filter
        where_filter = None
        if target_sector != "General":
            # We use $or to allow articles from the specific sector OR General (optional, but strict filtering is better for relevance)
            # For now, let's try strict filtering if sector is detected, but maybe relax if no results?
            # Let's stick to strict filtering as per requirements to reduce noise.
            where_filter = {"sector": target_sector}
            
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where=where_filter,
                include=["metadatas", "distances", "documents"]
            )
        except Exception as e:
            print(f"Query Error with filter: {e}. Retrying without filter.")
            results = None

        # Fallback if no results found with filter
        if not results or not results['ids'] or not results['ids'][0]:
            print("No results with filter. Retrying without filter.")
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
            
            # Sort rows by the order of article_ids (to maintain relevance rank)
            row_dict = {row['id']: dict(row) for row in rows}
            
            for aid in article_ids:
                if aid in row_dict:
                    article = row_dict[aid]
                    # Parse JSON fields
                    if article['entities_json']:
                        article['entities'] = json.loads(article['entities_json'])
                    if article['impacted_stocks_json']:
                        article['impacted_stocks'] = json.loads(article['impacted_stocks_json'])
                    articles.append(article)
                
        return {
            "query": query,
            "expanded_context": expanded_queries,
            "target_sector": target_sector,
            "results": articles
        }
