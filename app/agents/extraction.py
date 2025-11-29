import spacy
from app.models.article import Article, Entity, EntityType, ImpactedStock, ImpactType
from typing import List

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Mock mapping for demonstration
STOCK_MAPPING = {
    "HDFC Bank": "HDFCBANK",
    "HDFC": "HDFCBANK",
    "Reliance Industries": "RELIANCE",
    "Reliance": "RELIANCE",
    "TCS": "TCS",
    "Tata Consultancy Services": "TCS",
    "Infosys": "INFY",
    "ICICI Bank": "ICICIBANK",
    "SBI": "SBIN",
    "State Bank of India": "SBIN",
    "RBI": "BANKNIFTY", # Proxy for sector
    "Reserve Bank of India": "BANKNIFTY"
}

class ExtractionAgent:
    def process(self, article: Article) -> Article:
        doc = nlp(article.content)
        
        entities = []
        impacted_stocks = []
        
        seen_entities = set()

        for ent in doc.ents:
            if ent.text in seen_entities:
                continue
            seen_entities.add(ent.text)
            
            entity_type = None
            if ent.label_ == "ORG":
                entity_type = EntityType.COMPANY
            elif ent.label_ == "GPE":
                entity_type = EntityType.REGULATOR # Simplification
            elif ent.label_ == "PERSON":
                entity_type = EntityType.PERSON
            else:
                continue # Skip others for now

            entities.append(Entity(name=ent.text, type=entity_type))
            
            # Impact Mapping Logic (Heuristic)
            if ent.text in STOCK_MAPPING:
                symbol = STOCK_MAPPING[ent.text]
                confidence = 1.0 if ent.label_ == "ORG" else 0.8
                impact_type = ImpactType.DIRECT
                
                if symbol == "BANKNIFTY":
                    impact_type = ImpactType.REGULATORY
                    confidence = 0.9
                
                impacted_stocks.append(ImpactedStock(
                    symbol=symbol,
                    confidence=confidence,
                    type=impact_type
                ))

        article.entities = entities
        article.impacted_stocks = impacted_stocks
        print(f"Extracted {len(entities)} entities for: {article.title}")
        return article
