from app.models.article import Article, Entity, EntityType, ImpactedStock, ImpactType
from typing import List
import json
from langchain_mistralai import ChatMistralAI

class ExtractionAgent:
    def __init__(self):
        self.llm = ChatMistralAI(
            model="mistral-small-latest",
            temperature=0,
            max_retries=5
        )

    def process(self, article: Article) -> Article:
        try:
            prompt = f"""
            Analyze the following financial news article and extract structured intelligence.
            
            Article Title: "{article.title}"
            Article Content: "{article.content[:2000]}"... (truncated)

            Tasks:
            1. **Identify the Primary Sector**: e.g., Banking, IT, Energy, Pharma, Auto, Economy.
            2. **Extract Entities**: Identify key Companies, Persons, and Regulators.
               - For Companies, provide the NSE/BSE stock ticker (e.g., HDFC Bank -> HDFCBANK). If not listed, use NONE.
               - Classify correctly: "Pakistan" is NOT a Regulator. "SEBI" is a Regulator.
            3. **Analyze Impact**: For each company, determine the sentiment and impact score (-100 to 100).
               - "Buy", "Target Raised", "Good Results" -> Positive (Score > 0).
               - "Sell", "Reduce", "Penalty" -> Negative (Score < 0).
               - "Neutral", "No Change" -> Neutral (Score 0).

            Return ONLY a valid JSON object with this structure:
            {{
                "sector": "Sector Name",
                "entities": [
                    {{
                        "name": "Entity Name",
                        "type": "COMPANY/PERSON/REGULATOR",
                        "ticker": "TICKER_OR_NONE",
                        "sentiment": "POSITIVE/NEGATIVE/NEUTRAL",
                        "impact_score": 50,
                        "reasoning": "Brief reason"
                    }}
                ]
            }}
            """
            
            response = self.llm.invoke(prompt)
            # Clean response to ensure valid JSON
            content = response.content.replace("```json", "").replace("```", "").strip()
            # Basic JSON repair if needed (simple case)
            if content.startswith("{{") and not content.startswith("{"): # Mistral sometimes double braces
                 content = content.replace("{{", "{").replace("}}", "}")
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to find the first { and last }
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    content = content[start:end+1]
                    data = json.loads(content)
                else:
                    raise
            
            article.sector = data.get("sector", "General")
            
            entities = []
            impacted_stocks = []
            
            for item in data.get("entities", []):
                # Map string type to Enum
                etype_str = item.get("type", "COMPANY").upper()
                if "COMPANY" in etype_str: etype = EntityType.COMPANY
                elif "REGULATOR" in etype_str: etype = EntityType.REGULATOR
                elif "PERSON" in etype_str: etype = EntityType.PERSON
                else: etype = EntityType.COMPANY
                
                entities.append(Entity(name=item.get("name"), type=etype))
                
                ticker = item.get("ticker")
                if ticker and ticker != "NONE" and etype == EntityType.COMPANY:
                    # Determine ImpactType based on score
                    score = item.get("impact_score", 0)
                    impact_type = ImpactType.DIRECT
                    if abs(score) < 10: impact_type = ImpactType.SECTOR
                    
                    impacted_stocks.append(ImpactedStock(
                        symbol=ticker,
                        confidence=0.9, # High confidence as it's LLM inferred
                        type=impact_type,
                        sentiment=item.get("sentiment", "NEUTRAL"),
                        impact_score=score,
                        reasoning=item.get("reasoning", "")
                    ))
            
            article.entities = entities
            article.impacted_stocks = impacted_stocks

            with open("extraction.log", "a") as f:
                f.write(f"Extracted {len(entities)} entities, Sector: {article.sector}\n")
            print(f"Extracted {len(entities)} entities, Sector: {article.sector}")
            
        except Exception as e:
            with open("extraction.log", "a") as f:
                f.write(f"Extraction Error: {e}\n")
            print(f"Extraction Error: {e}")
            # Fallback
            article.sector = "General"
            
        return article
