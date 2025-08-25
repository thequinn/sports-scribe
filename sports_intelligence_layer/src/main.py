from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from query_parser import SoccerQueryParser


app = FastAPI(title="Soccer Intelligence Layer")
parser = SoccerQueryParser()


# Defines a Pydantic model to validate and structure incoming data — especially for APIs or NLP pipelines.
class QueryRequest(BaseModel):
    question: str
    context: dict = {}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SIL"}


@app.post("/parse")
async def parse_query(request: QueryRequest):
    try:
        parsed = parser.parse_query(request.question)
        return {
            "original_query": parsed.original_query,
            "intent": parsed.query_intent,
            "entities": [
                {"name": e.name, "type": e.entity_type.value} for e in parsed.entities
            ],
            "confidence": parsed.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
