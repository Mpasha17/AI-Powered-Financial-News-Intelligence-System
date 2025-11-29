from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from app.models.article import Article
from app.agents.deduplication import DeduplicationAgent
from app.agents.extraction import ExtractionAgent
from app.core.database import save_article_to_sqlite

# Define State
class AgentState(TypedDict):
    article: Article

# Initialize Agents
dedup_agent = DeduplicationAgent()
extraction_agent = ExtractionAgent()

# Node Functions
def deduplication_node(state: AgentState):
    article = state['article']
    processed_article = dedup_agent.process(article)
    return {"article": processed_article}

def extraction_node(state: AgentState):
    article = state['article']
    # Only extract if not a duplicate (optimization)
    if not article.is_duplicate:
        processed_article = extraction_agent.process(article)
        return {"article": processed_article}
    return {"article": article}

def storage_node(state: AgentState):
    article = state['article']
    save_article_to_sqlite(article.model_dump())
    print(f"Stored article: {article.id}")
    return {"article": article}

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("deduplication", deduplication_node)
workflow.add_node("extraction", extraction_node)
workflow.add_node("storage", storage_node)

workflow.set_entry_point("deduplication")

workflow.add_edge("deduplication", "extraction")
workflow.add_edge("extraction", "storage")
workflow.add_edge("storage", END)

app_workflow = workflow.compile()
