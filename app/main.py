from fastapi import FastAPI
from app.api.endpoints import router
from app.core.database import init_db

app = FastAPI(title="AI-Powered Financial News Intelligence System")

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
