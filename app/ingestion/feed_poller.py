import time
import uuid
import random
from datetime import datetime
from typing import List
from app.models.article import ArticleCreate, Article
from app.core.database import save_article_to_sqlite

# Mock Data Sources
SOURCES = ["RBI", "MoneyControl", "Bloomberg", "NSE", "BSE"]
COMPANIES = ["HDFC Bank", "Reliance Industries", "TCS", "Infosys", "ICICI Bank", "SBI"]
SECTORS = ["Banking", "IT", "Energy", "Pharma", "Auto"]
ACTIONS = ["announces dividend", "reports Q3 earnings", "launches new product", "faces regulatory hurdle", "expands operations"]

class IngestionService:
    def __init__(self):
        self.running = False

    def generate_mock_article(self) -> ArticleCreate:
        company = random.choice(COMPANIES)
        action = random.choice(ACTIONS)
        sector = random.choice(SECTORS)
        source = random.choice(SOURCES)
        
        title = f"{company} {action} amid {sector} sector growth"
        content = f"{company} has announced significant developments today. {action.capitalize()} is expected to impact the {sector} sector positively. Analysts are watching closely."
        
        return ArticleCreate(
            title=title,
            content=content,
            source=source,
            published_at=datetime.now(),
            url=f"https://example.com/{uuid.uuid4()}"
        )

    def process_article(self, article_create: ArticleCreate) -> Article:
        # Create initial Article object
        article = Article(
            id=str(uuid.uuid4()),
            **article_create.model_dump()
        )
        
        # Invoke LangGraph Workflow
        from app.agents.workflow import app_workflow
        result = app_workflow.invoke({"article": article})
        processed_article = result["article"]
        
        print(f"Processed: {processed_article.title} (Duplicate: {processed_article.is_duplicate})")
        return processed_article

    def run_mock_stream(self, interval=5):
        """Generates a mock article every `interval` seconds."""
        self.running = True
        print("Starting mock ingestion stream...")
        try:
            while self.running:
                article_create = self.generate_mock_article()
                self.process_article(article_create)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopping ingestion stream.")
            self.running = False

if __name__ == "__main__":
    # Initialize DBs
    from app.core.database import init_db
    init_db()
    
    service = IngestionService()
    service.run_mock_stream()
