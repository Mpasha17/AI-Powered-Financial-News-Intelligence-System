import time
import uuid
import feedparser
from datetime import datetime
from typing import List
from app.models.article import ArticleCreate, Article
from app.core.database import save_article_to_sqlite

# Real RSS Feed Sources
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://www.livemint.com/rss/news",
    "https://www.business-standard.com/rss/latest-news",
    "https://www.financialexpress.com/feed/"
]

class IngestionService:
    def __init__(self):
        self.running = False

    def fetch_from_feeds(self) -> List[ArticleCreate]:
        articles = []
        for url in RSS_FEEDS:
            try:
                print(f"Fetching from {url}...")
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]: # Limit to 5 per feed for demo speed
                    # Basic parsing
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '')
                    summary = entry.get('summary', '')
                    published = entry.get('published', str(datetime.now()))
                    
                    # Try to parse date, else use now
                    try:
                        # feedparser usually returns struct_time
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        else:
                            dt = datetime.now()
                    except:
                        dt = datetime.now()

                    # Clean HTML from summary/content
                    from bs4 import BeautifulSoup
                    import hashlib
                    
                    raw_content = summary if summary else title
                    # Parse with BS4 to remove tags
                    soup = BeautifulSoup(raw_content, "html.parser")
                    clean_content = soup.get_text(separator=" ", strip=True)
                    
                    # Clean title as well just in case
                    clean_title = BeautifulSoup(title, "html.parser").get_text(separator=" ", strip=True)

                    # Generate stable ID based on URL
                    article_id = hashlib.md5(link.encode()).hexdigest()

                    articles.append(ArticleCreate(
                        title=clean_title,
                        content=clean_content,
                        source=feed.feed.get('title', 'Unknown Source'),
                        published_at=dt,
                        url=link
                    ))
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        return articles

    def process_article(self, article_create: ArticleCreate) -> Article:
        # Create initial Article object with stable ID
        # We use the URL hash as the ID to prevent duplicates on re-ingestion
        import hashlib
        article_id = hashlib.md5(article_create.url.encode()).hexdigest()
        
        article = Article(
            id=article_id,
            **article_create.model_dump()
        )
        
        # Invoke LangGraph Workflow
        from app.agents.workflow import app_workflow
        result = app_workflow.invoke({"article": article})
        processed_article = result["article"]
        
        print(f"Processed: {processed_article.title} (Duplicate: {processed_article.is_duplicate})")
        return processed_article

    def run_real_stream(self, interval=60):
        """Polls RSS feeds every `interval` seconds."""
        self.running = True
        print("Starting Real RSS Ingestion Stream...")
        try:
            while self.running:
                articles = self.fetch_from_feeds()
                print(f"Fetched {len(articles)} articles. Processing...")
                for art in articles:
                    self.process_article(art)
                print(f"Sleeping for {interval} seconds...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopping ingestion stream.")
            self.running = False

if __name__ == "__main__":
    # Initialize DBs
    from app.core.database import init_db
    init_db()
    
    service = IngestionService()
    service.run_real_stream()
