from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# Database connection function
def connect_db():
    return psycopg2.connect(
        host='localhost',
        database = 'postgres',
        user = 'postgres',
        password = 'password',
        port = '5432'
    )

# Request model
class QueryRequest(BaseModel):
    query: str
    context: str

@app.post("/generate-response")
async def generate_response(request: QueryRequest):
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Execute the ollama_generate function in the database
        cur.execute("""
            SELECT ollama_generate('llama3.2', %s, _host=>'http://ollama_impact:11434');
        """, (f"Query: {request.query}\nContext: {request.context}",))
        
        # Fetch the result
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=500, detail="Failed to fetch response from the model.")
        
        response = result[0].get("response")
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cur.close()
        conn.close()