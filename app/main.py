from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# Database connection function
def connect_db():
    return psycopg2.connect(
        host='timescaledb',
        database = 'postgres',
        user = 'postgres',
        password = 'password',
        port = '5432'
    )

# Request model
class QueryRequest(BaseModel):
    query: str

@app.post("/generate-response")
async def generate_response(request: QueryRequest):
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Execute the ollama_generate function in the database
        # Embed the query using the ollama_embed function
        cur.execute("""
            SELECT ollama_embed('nomic-embed-text', %s, _host=>'http://ollama_impact:11434');
        """, (request.query,))
        query_embedding = cur.fetchone()[0]

        # Retrieve relevant documents based on cosine distance
        cur.execute("""
            SELECT title, content, 1 - (embedding <=> %s) AS similarity
            FROM documents
            ORDER BY similarity DESC
            LIMIT 3;
        """, (query_embedding,))

        rows = cur.fetchall()
    
        # Prepare the context for generating the response
        context = "\n\n".join([f"Title: {row[0]}\nContent: {row[1]}" for row in rows])
        # print(context)

        # Generate the response using the ollama_generate function
        cur.execute("""
            SELECT ollama_generate('llama3.2', %s, _host=>'http://ollama_impact:11434');
        """, (f"Query: {request.query}\nContext: {context}",))
            
        model_response = cur.fetchone()[0]
        
   
        # Fetch the result
        # result = cur.fetchone()
        if not model_response:
            raise HTTPException(status_code=500, detail="Failed to fetch response from the model.")
        
        return {"response": model_response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cur.close()
        conn.close()