from sentence_transformers import SentenceTransformer
from app.core.database import get_collection
from app.models.article import Article
import uuid

# Load model once (global for now, better in a singleton or dependency injection)
model = SentenceTransformer('all-MiniLM-L6-v2')

class DeduplicationAgent:
    def __init__(self):
        self.collection = get_collection()
        self.threshold = 0.85 # Similarity threshold

    def process(self, article: Article) -> Article:
        """
        Checks if the article is a duplicate.
        If unique, adds to vector DB.
        If duplicate, marks it and links to original.
        """
        # Generate embedding
        text_to_embed = f"{article.title} {article.content}"
        embedding = model.encode(text_to_embed).tolist()
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["metadatas", "distances"]
        )
        
        is_duplicate = False
        duplicate_of_id = None
        
        if results['ids'] and results['ids'][0]:
            # Chroma returns distance. For cosine similarity, distance = 1 - similarity (approx for normalized)
            # But default is L2. Let's assume we want low distance.
            # Actually, let's check the distance. If it's very small, it's a duplicate.
            # For L2, 0 is identical. 
            # Let's assume < 0.3 distance is duplicate for now (needs tuning).
            distance = results['distances'][0][0]
            if distance < (1 - self.threshold): # Rough approximation
                is_duplicate = True
                duplicate_of_id = results['ids'][0][0]
                print(f"Duplicate found! {article.title} is similar to {duplicate_of_id} (Dist: {distance:.4f})")

        article.is_duplicate = is_duplicate
        article.duplicate_of_id = duplicate_of_id
        
        if not is_duplicate:
            # Add to Vector DB
            self.collection.add(
                documents=[text_to_embed],
                metadatas=[{"title": article.title, "source": article.source}],
                ids=[article.id],
                embeddings=[embedding]
            )
            print(f"New unique article added: {article.title}")
            
        return article
