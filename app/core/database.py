import sqlite3
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any
import json
from datetime import datetime

# SQLite Setup
SQLITE_DB_PATH = os.path.abspath("articles.db")

def get_sqlite_conn():
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            
            # Fail-safe: Ensure table exists
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    published_at TIMESTAMP,
                    url TEXT,
                    is_duplicate BOOLEAN DEFAULT 0,
                    duplicate_of_id TEXT,
                    entities_json TEXT,
                    impacted_stocks_json TEXT,
                    sector TEXT
                )
            """)
            conn.commit()
            return conn
        except sqlite3.OperationalError as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.5)

def init_sqlite():
    print(f"Initializing SQLite at {SQLITE_DB_PATH}")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            published_at TIMESTAMP,
            url TEXT,
            is_duplicate BOOLEAN DEFAULT 0,
            duplicate_of_id TEXT,
            entities_json TEXT,
            impacted_stocks_json TEXT,
            sector TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("SQLite initialized.")

# ChromaDB Setup
CHROMA_DB_PATH = "chroma_db_v2"

# Global client to avoid re-initializing
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        print(f"Initializing ChromaDB client at {os.path.abspath(CHROMA_DB_PATH)}")
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client

def get_collection(name="articles"):
    client = get_chroma_client()
    # Always use get_or_create_collection to ensure it exists
    col = client.get_or_create_collection(name=name)
    return col

def init_db():
    init_sqlite()
    # Initialize ChromaDB collection
    get_collection()
    print("Databases initialized.")

# Helper to save article to SQLite
def save_article_to_sqlite(article: Dict[str, Any]):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    entities_json = json.dumps(article.get('entities', []))
    impacted_stocks_json = json.dumps(article.get('impacted_stocks', []))
    
    cursor.execute('''
    INSERT OR REPLACE INTO articles (id, title, content, source, published_at, url, is_duplicate, duplicate_of_id, entities_json, impacted_stocks_json, sector)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        article['id'],
        article['title'],
        article['content'],
        article['source'],
        article['published_at'],
        article.get('url'),
        article.get('is_duplicate', False),
        article.get('duplicate_of_id'),
        entities_json,
        impacted_stocks_json,
        article.get('sector', 'General')
    ))
    
    conn.commit()
    conn.close()

def get_article_from_sqlite(article_id: str) -> Dict[str, Any]:
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        article = dict(row)
        # Parse JSON fields
        if article.get('entities_json'):
            article['entities'] = json.loads(article['entities_json'])
        if article.get('impacted_stocks_json'):
            article['impacted_stocks'] = json.loads(article['impacted_stocks_json'])
        return article
    return None
