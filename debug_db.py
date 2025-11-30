from app.core.database import init_db, get_sqlite_conn, get_collection
import time

print("Starting DB Debug...")
start = time.time()

print("Initializing DBs...")
init_db()
print(f"DBs Initialized in {time.time() - start:.2f}s")

print("Testing SQLite Connection...")
conn = get_sqlite_conn()
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM articles")
print(f"SQLite Count: {cursor.fetchone()[0]}")
conn.close()

print("Testing ChromaDB Collection...")
col = get_collection()
print(f"Chroma Collection Count: {col.count()}")

print("Debug Complete.")
