import json
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from difflib import SequenceMatcher
import os


app = FastAPI(title="Menu Search API", description="Smart menu search with typo tolerance")

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/src", StaticFiles(directory="src"), name="src")
app.mount("/public", StaticFiles(directory="public"), name="public")

# Global variables for data
menu_items = []

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_results: int

def load_menu_data():
    """Load menu data from JSON file"""
    global menu_items
    
    try:
        with open('data/menu.json', 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        menu_items = menu_data.get('items', [])
        print(f"Loaded {len(menu_items)} menu items")
        
    except FileNotFoundError:
        print("Menu data file not found. Please ensure data/menu.json exists.")
        menu_items = []
    except json.JSONDecodeError:
        print("Invalid JSON in menu data file.")
        menu_items = []

def similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity between two strings using SequenceMatcher"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fuzzy_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Perform fuzzy search with typo tolerance"""
    if not query.strip() or len(menu_items) == 0:
        return []
    
    query_lower = query.lower()
    scored_items = []
    
    for item in menu_items:
        # Create searchable text for each item
        searchable_text = f"{item['name']} {item['description']} {' '.join(item.get('ingredients', []))}"
        
        # Calculate multiple similarity scores
        name_similarity = similarity_ratio(query_lower, item['name'].lower())
        description_similarity = similarity_ratio(query_lower, item['description'].lower())
        
        # Check for partial matches in ingredients
        ingredient_similarity = 0
        for ingredient in item.get('ingredients', []):
            ingredient_sim = similarity_ratio(query_lower, ingredient.lower())
            if ingredient_sim > ingredient_similarity:
                ingredient_similarity = ingredient_sim
        
        # Check for exact substring matches (higher score)
        exact_match_bonus = 0
        if query_lower in searchable_text.lower():
            exact_match_bonus = 0.3
        
        # Calculate final score (weighted combination)
        final_score = max(
            name_similarity * 1.0,  # Name matches are most important
            description_similarity * 0.7,  # Description matches
            ingredient_similarity * 0.8  # Ingredient matches
        ) + exact_match_bonus
        
        # Only include items with reasonable similarity
        if final_score > 0.3:  # Threshold for inclusion
            item_copy = item.copy()
            item_copy['similarity_score'] = final_score
            scored_items.append(item_copy)
    
    # Sort by similarity score (descending) and limit results
    scored_items.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_items[:limit]

def keyword_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Enhanced keyword search for exact matches"""
    if not query.strip():
        return []
    
    query_words = query.lower().split()
    matches = []
    
    for item in menu_items:
        # Check name, description, and ingredients for keyword matches
        searchable_text = f"{item['name']} {item['description']} {' '.join(item.get('ingredients', []))}"
        searchable_lower = searchable_text.lower()
        
        # Count how many query words are found
        word_matches = sum(1 for word in query_words if word in searchable_lower)
        
        if word_matches > 0:
            item_copy = item.copy()
            # Score based on proportion of words matched
            item_copy['similarity_score'] = word_matches / len(query_words)
            matches.append(item_copy)
    
    # Sort by match quality
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    return matches[:limit]

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("Starting Menu Search API...")
    load_menu_data()
    print("Menu Search API ready!")

@app.get("/")
async def serve_index():
    """Serve the main application page"""
    return FileResponse('public/index.html')

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Smart Menu Search API is running", "status": "healthy", "items_loaded": len(menu_items)}

@app.get("/menu")
async def get_menu():
    """Get all menu items"""
    return {"items": menu_items, "total": len(menu_items)}

@app.post("/search", response_model=SearchResponse)
async def search_menu(request: SearchRequest):
    """Search menu items with typo tolerance"""
    try:
        if not request.query.strip():
            return SearchResponse(items=[], total_results=0)
        
        # Try fuzzy search first
        fuzzy_results = fuzzy_search(request.query, request.limit)
        
        # If fuzzy search doesn't return enough results, try keyword search
        if len(fuzzy_results) < request.limit:
            keyword_results = keyword_search(request.query, request.limit - len(fuzzy_results))
            
            # Combine results, avoiding duplicates
            seen_ids = {item['id'] for item in fuzzy_results}
            for item in keyword_results:
                if item['id'] not in seen_ids:
                    fuzzy_results.append(item)
        
        return SearchResponse(
            items=fuzzy_results,
            total_results=len(fuzzy_results)
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
    results = fuzzy_search(query, limit)
    suggestions = [item['name'] for item in results]
    
    return {"suggestions": suggestions}

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )