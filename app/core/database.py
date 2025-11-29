import sqlite3
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any
import json
from datetime import datetime

# SQLite Setup
SQLITE_DB_PATH = "articles.db"

def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite():
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # Articles Table
    cursor.execute('''
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
        impacted_stocks_json TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# ChromaDB Setup
CHROMA_DB_PATH = "chroma_db"

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)

def get_collection(name="financial_news"):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)

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
    INSERT OR REPLACE INTO articles (id, title, content, source, published_at, url, is_duplicate, duplicate_of_id, entities_json, impacted_stocks_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        impacted_stocks_json
    ))
    
    conn.commit()
    conn.close()
