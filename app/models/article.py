from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    COMPANY = "COMPANY"
    SECTOR = "SECTOR"
    REGULATOR = "REGULATOR"
    PERSON = "PERSON"
    EVENT = "EVENT"

class ImpactType(str, Enum):
    DIRECT = "direct"
    SECTOR = "sector"
    REGULATORY = "regulatory"

class Entity(BaseModel):
    name: str
    type: EntityType

class ImpactedStock(BaseModel):
    symbol: str
    confidence: float
    type: ImpactType

class Article(BaseModel):
    id: str = Field(..., description="Unique ID of the article")
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    
    # Metadata
    entities: List[Entity] = []
    impacted_stocks: List[ImpactedStock] = []
    
    # Deduplication
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    
    # Embedding (optional to store here, usually in Vector DB)
    embedding_id: Optional[str] = None

class ArticleCreate(BaseModel):
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
