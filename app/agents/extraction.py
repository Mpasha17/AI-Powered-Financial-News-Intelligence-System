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
    def get_ticker_from_llm(self, entity_name: str) -> str:
        try:
            from langchain_mistralai import ChatMistralAI
            llm = ChatMistralAI(
                model="mistral-large-latest",
                temperature=0,
                max_retries=2
            )
            prompt = f"What is the NSE/BSE stock symbol for '{entity_name}'? Return ONLY the symbol (e.g., RELIANCE). If not a public company, return 'NONE'."
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"LLM Error (Entity Mapping): {e}")
            return "NONE"

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
            
            # Impact Mapping Logic
            symbol = None
            confidence = 0.0
            impact_type = ImpactType.DIRECT
            
            # 1. Check Hardcoded Map
            if ent.text in STOCK_MAPPING:
                symbol = STOCK_MAPPING[ent.text]
                confidence = 1.0 if ent.label_ == "ORG" else 0.8
                if symbol == "BANKNIFTY":
                    impact_type = ImpactType.REGULATORY
                    confidence = 0.9
            
            # 2. Fallback to LLM for Companies
            elif entity_type == EntityType.COMPANY:
                symbol = self.get_ticker_from_llm(ent.text)
                if symbol and symbol != "NONE":
                    confidence = 0.7 # Lower confidence for LLM guess
            
            if symbol and symbol != "NONE":
                impacted_stocks.append(ImpactedStock(
                    symbol=symbol,
                    confidence=confidence,
                    type=impact_type
                ))

        # Consolidate duplicate impacts (keep max confidence)
        consolidated_stocks = {}
        for stock in impacted_stocks:
            if stock.symbol in consolidated_stocks:
                if stock.confidence > consolidated_stocks[stock.symbol].confidence:
                    consolidated_stocks[stock.symbol] = stock
            else:
                consolidated_stocks[stock.symbol] = stock
        
        article.entities = entities
        article.impacted_stocks = list(consolidated_stocks.values())
        print(f"Extracted {len(entities)} entities for: {article.title}")
        return article
