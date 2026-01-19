from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.genai as genai
import json
import os
import numpy as np


API_KEY = "AIzaSyBJrqjBoZLQCSHiXlPxxD-S8ELIKMmEKEc"
client = genai.Client(api_key=API_KEY)
CHAT_MODEL = "models/gemini-2.5-flash"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Memory storage
MEMORY_FILE = "memory.json"
HISTORY_FILE = "conversation_history.json"

def load_memory():
    """Load memory with embeddings"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading memory: {e}")
    return []

def save_memory(memory):
    """Save memory with embeddings"""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def load_history():
    """Load conversation history"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
    except:
        return []
    return []

def save_history(history):
    """Save conversation history"""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[-50:], f, indent=2)
    except:
        pass

def get_embedding(text):
    """Generate embedding for text"""
    try:
        response = client.embeddings.create(
            model="models/embedding-001",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return [0.0] * 768

def cosine_similarity(a, b):
    """Calculate cosine similarity"""
    try:
        a_np = np.array(a)
        b_np = np.array(b)
        
        dot = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot / (norm_a * norm_b))
    except:
        return 0.0

def get_relevant_context(query, memory):
    """Get relevant context from memory - SIMPLIFIED"""
    if not memory:
        return ""
    
    try:
        query_embedding = get_embedding(query)
        best_match = None
        best_score = 0.0
        
        for item in memory:
            if "embedding" in item:
                sim = cosine_similarity(query_embedding, item["embedding"])
                if sim > 0.8 and sim > best_score:
                    best_score = sim
                    best_match = item["text"]
        
        if best_match:
            print(f"✅ Found relevant context (score: {best_score:.3f})")
            return f"[Related to previous conversation: {best_match[:300]}]"
        
        return ""
        
    except Exception as e:
        print(f"Context error: {e}")
        return ""

@app.post("/chat")
async def chat(payload: ChatRequest):
    user_message = payload.message.strip()
    
    if not user_message:
        return {"reply": "Please type a message."}
    
    memory = load_memory()
    history = load_history()
    
    try:
        # Add user message to history
        history.append({"role": "user", "content": user_message})
        
        # Get relevant context from memory
        context = get_relevant_context(user_message, memory)
        
        # SIMPLE PROMPT - FIXED
        prompt = f"""You are a helpful AI assistant.

{context if context else ""}

User: {user_message}

Answer in a helpful, natural way. If the context above is relevant, use it. Otherwise just answer normally."""

        # Generate response
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        
        if response.candidates:
            bot_response = response.candidates[0].content.parts[0].text
        else:
            bot_response = "I couldn't generate a response. Please try again."
        
        # Add bot response to history
        history.append({"role": "assistant", "content": bot_response})
        save_history(history)
        
        # Store in memory (simplified)
        if len(bot_response) > 20:
            bot_embedding = get_embedding(bot_response)
            memory.append({
                "id": len(memory),
                "text": bot_response[:400],
                "embedding": bot_embedding
            })
            save_memory(memory)
        
        return {"reply": bot_response}
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        
        if "429" in error_msg:
            return {"reply": "API limit reached. Try again later."}
        
        return {"reply": f"I'm having trouble. You asked: '{user_message}'"}

@app.get("/memory")
async def get_memory():
    """Get memory stats"""
    memory = load_memory()
    return {
        "total": len(memory),
        "recent": memory[-3:] if memory else []
    }

@app.get("/clear")
async def clear_memory():
    """Clear both memory and history"""
    save_memory([])
    save_history([])
    return {"message": "Memory cleared"}

@app.get("/")
async def root():
    memory = load_memory()
    return {
        "status": "running",
        "memory_entries": len(memory),
        "model": CHAT_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 AI Chatbot Backend")
    print("Port: 8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)