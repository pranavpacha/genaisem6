import json
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import uvicorn
import os

app = FastAPI(title="Menu Search API", description="AI-powered menu search with typo tolerance")

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and data    
model = None
menu_items = []
menu_embeddings = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class MenuItem(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: float
    ingredients: List[str]
    dietary_info: List[str]

class SearchResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_results: int

def load_model():
    """Load the sentence transformer model for embeddings"""
    global model
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded successfully!")

def load_menu_data():
    """Load menu data from JSON file and generate embeddings"""
    global menu_items, menu_embeddings
    
    try:
        with open('data/menu.json', 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        menu_items = menu_data.get('items', [])
        print(f"Loaded {len(menu_items)} menu items")
        
        # Generate embeddings for all menu items
        generate_embeddings()
        
    except FileNotFoundError:
        print("Menu data file not found. Please ensure data/menu.json exists.")
        menu_items = []
    except json.JSONDecodeError:
        print("Invalid JSON in menu data file.")
        menu_items = []

def generate_embeddings():
    """Generate embeddings for all menu items"""
    global menu_embeddings
    
    if not menu_items or model is None:
        return
    
    print("Generating embeddings for menu items...")
    
    # Create searchable text for each item (name + description + ingredients)
    searchable_texts = []
    for item in menu_items:
        text = f"{item['name']} {item['description']} {' '.join(item.get('ingredients', []))}"
        searchable_texts.append(text)
    
    # Generate embeddings
    menu_embeddings = model.encode(searchable_texts)
    print(f"Generated embeddings for {len(searchable_texts)} items")

def semantic_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Perform semantic search using embeddings and cosine similarity"""
    if not query.strip() or menu_embeddings is None or len(menu_items) == 0:
        return []
    
    # Generate embedding for the query
    query_embedding = model.encode([query])
    
    # Calculate cosine similarities
    similarities = cosine_similarity(query_embedding, menu_embeddings)[0]
    
    # Get top matches with their scores
    scored_items = []
    for i, score in enumerate(similarities):
        if score > 0.1:  # Minimum similarity threshold
            item = menu_items[i].copy()
            item['similarity_score'] = float(score)
            scored_items.append(item)
    
    # Sort by similarity score (descending) and limit results
    scored_items.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_items[:limit]

def keyword_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fallback keyword search for exact matches"""
    if not query.strip():
        return []
    
    query_lower = query.lower()
    matches = []
    
    for item in menu_items:
        # Check name, description, and ingredients for keyword matches
        searchable_text = f"{item['name']} {item['description']} {' '.join(item.get('ingredients', []))}".lower()
        
        if query_lower in searchable_text:
            item_copy = item.copy()
            item_copy['similarity_score'] = 1.0  # Perfect match
            matches.append(item_copy)
    
    return matches[:limit]

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    load_model()
    load_menu_data()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Menu Search API is running", "status": "healthy"}

@app.get("/menu")
async def get_menu():
    """Get all menu items"""
    return {"items": menu_items, "total": len(menu_items)}

@app.post("/search", response_model=SearchResponse)
async def search_menu(request: SearchRequest):
    """Search menu items with AI-powered typo tolerance"""
    try:
        if not request.query.strip():
            return SearchResponse(items=[], total_results=0)
        
        # Try semantic search first
        semantic_results = semantic_search(request.query, request.limit)
        
        # If semantic search doesn't return enough results, try keyword search
        if len(semantic_results) < request.limit:
            keyword_results = keyword_search(request.query, request.limit - len(semantic_results))
            
            # Combine results, avoiding duplicates
            seen_ids = {item['id'] for item in semantic_results}
            for item in keyword_results:
                if item['id'] not in seen_ids:
                    semantic_results.append(item)
        
        return SearchResponse(
            items=semantic_results,
            total_results=len(semantic_results)
        )
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/search/suggestions")
async def get_search_suggestions(query: str = "", limit: int = 5):
    """Get search suggestions for autocomplete"""
    if not query.strip():
        return {"suggestions": []}
    
    # Get top matches for suggestions
    results = semantic_search(query, limit)
    suggestions = [item['name'] for item in results]
    
    return {"suggestions": suggestions}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
