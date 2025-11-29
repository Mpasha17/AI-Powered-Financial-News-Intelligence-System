from fastapi import FastAPI
from app.api.endpoints import router
from app.core.database import init_db
from dotenv import load_dotenv
load_dotenv()          # reads .env in the project root
app = FastAPI(title="AI-Powered Financial News Intelligence System")

@app.on_event("startup")
async def startup_event():
    print("STARTUP: Initializing application...")
    try:
        init_db()
        print("STARTUP: Database initialized successfully.")
    except Exception as e:
        print(f"STARTUP ERROR: {e}")

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
