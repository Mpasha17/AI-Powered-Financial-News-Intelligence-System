import os
import shutil
import sqlite3
from app.core.database import init_db

def reset():
    print("Resetting databases...")
    
    # Remove SQLite
    if os.path.exists("articles.db"):
        os.remove("articles.db")
        print("Removed articles.db")
        
    # Remove ChromaDB
    if os.path.exists("chroma_db_v2"):
        shutil.rmtree("chroma_db_v2")
        print("Removed chroma_db_v2")
        
    # Initialize
    print("Initializing new databases...")
    try:
        init_db()
        print("Success!")
    except Exception as e:
        print(f"Failed to init DB: {e}")

if __name__ == "__main__":
    reset()
