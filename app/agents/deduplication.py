from sentence_transformers import SentenceTransformer
from app.core.database import get_collection
from app.models.article import Article
import uuid

# Load model once (global for now, better in a singleton or dependency injection)
model = SentenceTransformer('all-MiniLM-L6-v2')

class DeduplicationAgent:
    def __init__(self):
        self.collection = get_collection()
        # self.collection = get_collection() # Moved to process method
        self.model = SentenceTransformer('all-MiniLM-L6-v2') # Model initialized here
        self.threshold = 0.85 # Similarity threshold

    def process(self, article: Article) -> Article:
        """
        Checks if the article is a duplicate.
        If unique, adds to vector DB.
        If duplicate, marks it and links to original.
        """
        from app.core.database import get_collection # Import moved here
        collection = get_collection() # Collection initialized here
        
        # Generate embedding
        text_to_embed = f"{article.title} {article.content}"
        embedding = self.model.encode(text_to_embed).tolist() # Use self.model
        
        # Query ChromaDB
        results = collection.query( # Use local collection
            query_embeddings=[embedding],
            n_results=1,
            include=["metadatas", "distances"]
        )
        
        is_duplicate = False
        duplicate_of_id = None
        
        if results['ids'] and results['ids'][0]:
            # Chroma returns distance. Default is L2.
            # L2 Distance of 0 means identical. 0.3 is usually a good threshold for "very similar".
            distance = results['distances'][0][0]
            if distance < 0.3: 
                is_duplicate = True
                duplicate_of_id = results['ids'][0][0]
                print(f"Duplicate found! {article.title} is similar to {duplicate_of_id} (Dist: {distance:.4f})")

        article.is_duplicate = is_duplicate
        article.duplicate_of_id = duplicate_of_id
        
        return article

    def add_to_chroma(self, article: Article):
        """
        Adds the article to ChromaDB with full metadata.
        """
        if article.is_duplicate:
            return

        text_to_embed = f"{article.title} {article.content}"
        embedding = self.model.encode(text_to_embed).tolist()
        
        self.collection.add(
            documents=[text_to_embed],
            metadatas=[{"title": article.title, "source": article.source, "sector": article.sector}],
            ids=[article.id],
            embeddings=[embedding]
        )
        print(f"Added to ChromaDB: {article.title} (Sector: {article.sector})")
