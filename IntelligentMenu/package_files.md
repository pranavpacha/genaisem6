# Complete File Package for Smart Menu Search

Copy these files to your local machine to run the application.

## 1. simple_main.py
```python
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

@app.get("/api/")
async def root():
    """Health check endpoint"""
    return {"message": "Smart Menu Search API is running", "status": "healthy", "items_loaded": len(menu_items)}

@app.get("/api/menu")
async def get_menu():
    """Get all menu items"""
    return {"items": menu_items, "total": len(menu_items)}

@app.post("/api/search", response_model=SearchResponse)
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

@app.get("/api/search/suggestions")
async def get_search_suggestions(query: str = "", limit: int = 5):
    """Get search suggestions for autocomplete"""
    if not query.strip():
        return {"suggestions": []}
    
    # Get top matches for suggestions
    results = fuzzy_search(query, limit)
    suggestions = [item['name'] for item in results]
    
    return {"suggestions": suggestions}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 2. data/menu.json
```json
{
  "restaurant": "Spice Palace",
  "date": "2025-07-08",
  "items": [
    {
      "id": 1,
      "name": "Masala Dosa",
      "description": "Crispy South Indian crepe filled with spiced potato curry",
      "category": "South Indian",
      "price": 180,
      "ingredients": ["rice", "urad dal", "potatoes", "onions", "mustard seeds", "curry leaves", "turmeric"],
      "dietary_info": ["vegetarian", "gluten-free", "vegan"]
    },
    {
      "id": 2,
      "name": "Chicken Tikka Masala",
      "description": "Tender marinated chicken in rich creamy tomato curry",
      "category": "North Indian",
      "price": 320,
      "ingredients": ["chicken", "tomatoes", "cream", "onions", "garlic", "ginger", "garam masala", "cashews"],
      "dietary_info": ["contains dairy"]
    },
    {
      "id": 3,
      "name": "Biryani",
      "description": "Fragrant basmati rice cooked with spiced mutton and aromatic herbs",
      "category": "Biryani",
      "price": 450,
      "ingredients": ["basmati rice", "mutton", "onions", "yogurt", "saffron", "mint", "biryani masala"],
      "dietary_info": ["contains dairy"]
    },
    {
      "id": 4,
      "name": "Palak Paneer",
      "description": "Fresh cottage cheese cooked in creamy spinach gravy",
      "category": "North Indian",
      "price": 280,
      "ingredients": ["spinach", "paneer", "cream", "onions", "garlic", "ginger", "cumin"],
      "dietary_info": ["vegetarian", "contains dairy"]
    },
    {
      "id": 5,
      "name": "Idli Sambar",
      "description": "Steamed rice cakes served with lentil curry and coconut chutney",
      "category": "South Indian",
      "price": 120,
      "ingredients": ["rice", "urad dal", "toor dal", "vegetables", "tamarind", "curry leaves", "coconut"],
      "dietary_info": ["vegetarian", "gluten-free", "vegan"]
    },
    {
      "id": 6,
      "name": "Butter Chicken",
      "description": "Succulent chicken in silky tomato-butter sauce",
      "category": "North Indian",
      "price": 350,
      "ingredients": ["chicken", "tomatoes", "butter", "cream", "cashews", "fenugreek", "garam masala"],
      "dietary_info": ["contains dairy"]
    },
    {
      "id": 7,
      "name": "Chole Bhature",
      "description": "Spiced chickpea curry with fluffy fried bread",
      "category": "North Indian",
      "price": 200,
      "ingredients": ["chickpeas", "wheat flour", "onions", "tomatoes", "ginger-garlic", "chole masala"],
      "dietary_info": ["vegetarian", "contains gluten"]
    },
    {
      "id": 8,
      "name": "Fish Curry",
      "description": "Kerala-style fish cooked in coconut milk with curry leaves",
      "category": "South Indian",
      "price": 380,
      "ingredients": ["fish", "coconut milk", "curry leaves", "mustard seeds", "turmeric", "green chilies"],
      "dietary_info": ["pescatarian", "gluten-free"]
    },
    {
      "id": 9,
      "name": "Aloo Gobi",
      "description": "Dry curry of potatoes and cauliflower with aromatic spices",
      "category": "North Indian",
      "price": 160,
      "ingredients": ["potatoes", "cauliflower", "onions", "tomatoes", "turmeric", "cumin", "coriander"],
      "dietary_info": ["vegetarian", "vegan", "gluten-free"]
    },
    {
      "id": 10,
      "name": "Gulab Jamun",
      "description": "Soft milk dumplings soaked in cardamom-flavored sugar syrup",
      "category": "Desserts",
      "price": 80,
      "ingredients": ["milk powder", "flour", "sugar", "cardamom", "rose water", "ghee"],
      "dietary_info": ["vegetarian", "contains dairy", "contains gluten"]
    },
    {
      "id": 11,
      "name": "Tandoori Chicken",
      "description": "Marinated chicken roasted in traditional clay oven",
      "category": "Tandoori",
      "price": 400,
      "ingredients": ["chicken", "yogurt", "red chili", "garam masala", "ginger-garlic", "lemon"],
      "dietary_info": ["contains dairy", "gluten-free"]
    },
    {
      "id": 12,
      "name": "Rajma Rice",
      "description": "Kidney bean curry served with steamed basmati rice",
      "category": "North Indian",
      "price": 220,
      "ingredients": ["kidney beans", "basmati rice", "onions", "tomatoes", "ginger-garlic", "rajma masala"],
      "dietary_info": ["vegetarian", "vegan", "gluten-free"]
    },
    {
      "id": 13,
      "name": "Pani Puri",
      "description": "Crispy hollow shells filled with spiced water and chutneys",
      "category": "Street Food",
      "price": 100,
      "ingredients": ["semolina", "tamarind water", "mint chutney", "chickpeas", "potatoes", "spices"],
      "dietary_info": ["vegetarian", "vegan"]
    },
    {
      "id": 14,
      "name": "Malai Kofta",
      "description": "Fried cottage cheese balls in rich creamy curry",
      "category": "North Indian",
      "price": 300,
      "ingredients": ["paneer", "potatoes", "cream", "tomatoes", "cashews", "raisins", "garam masala"],
      "dietary_info": ["vegetarian", "contains dairy"]
    },
    {
      "id": 15,
      "name": "Rava Uttapam",
      "description": "Thick South Indian pancake made with semolina and vegetables",
      "category": "South Indian",
      "price": 150,
      "ingredients": ["semolina", "yogurt", "onions", "tomatoes", "green chilies", "curry leaves", "mustard seeds"],
      "dietary_info": ["vegetarian", "contains dairy"]
    }
  ]
}
```

## 3. public/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Menu Search</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: {
                            50: '#fff7ed',
                            100: '#ffedd5',
                            200: '#fed7aa',
                            300: '#fdba74',
                            400: '#fb923c',
                            500: '#f97316',
                            600: '#ea580c',
                            700: '#c2410c',
                            800: '#9a3412',
                            900: '#7c2d12'
                        }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .glass-effect {
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.1);
        }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .food-pattern {
            background-image: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23f97316' fill-opacity='0.05' fill-rule='evenodd'%3E%3Cpath d='m0 40l40-40h-40v40zm40 0v-40h-40l40 40z'/%3E%3C/g%3E%3C/svg%3E");
        }
    </style>
</head>
<body class="bg-gray-50 food-pattern">
    <div id="root"></div>
    <script type="text/babel" src="/src/index.js"></script>
</body>
</html>
```

## 4. src/index.js
```javascript
// Load all components and render the app
Promise.all([
    import('/src/App.js'),
    import('/src/components/SearchBar.js'),
    import('/src/components/MenuCard.js')
]).then(() => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(App));
}).catch(error => {
    console.error('Error loading components:', error);
});
```

## 5. src/App.js
```javascript
const { useState, useEffect } = React;

const App = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadMenuItems();
  }, []);

  const loadMenuItems = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/menu');
      setMenuItems(response.data.items || []);
      setSearchResults(response.data.items || []);
    } catch (error) {
      console.error('Error loading menu items:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    
    if (!query.trim()) {
      setSearchResults(menuItems);
      return;
    }

    try {
      setIsLoading(true);
      const response = await axios.post('/api/search', {
        query: query,
        limit: 10
      });
      setSearchResults(response.data.items || []);
    } catch (error) {
      console.error('Error searching:', error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    React.createElement('div', { className: 'min-h-screen bg-gray-50' },
      // Header
      React.createElement('header', { className: 'bg-white shadow-sm border-b border-gray-100' },
        React.createElement('div', { className: 'container mx-auto px-4 py-6' },
          React.createElement('div', { className: 'text-center mb-8' },
            React.createElement('h1', { className: 'text-4xl font-bold text-gray-900 mb-2 flex items-center justify-center' },
              React.createElement('span', { className: 'mr-3' }, '🍽️'),
              'Smart Menu Search',
              React.createElement('span', { className: 'ml-3' }, '🔍')
            ),
            React.createElement('p', { className: 'text-gray-600 text-lg' },
              'Discover authentic Indian dishes with intelligent, typo-tolerant search'
            )
          ),
          
          React.createElement(SearchBar, { 
            onSearch: handleSearch,
            initialValue: searchQuery
          })
        )
      ),

      // Main Content
      React.createElement('main', { className: 'container mx-auto px-4 py-8' },
        // Search Results Header
        React.createElement('div', { className: 'flex justify-between items-center mb-6' },
          React.createElement('h2', { className: 'text-2xl font-semibold text-gray-900' },
            searchQuery ? `Search Results for "${searchQuery}"` : 'All Menu Items'
          ),
          React.createElement('span', { className: 'text-gray-500' },
            `${searchResults.length} items found`
          )
        ),

        // Loading State
        isLoading && React.createElement('div', { className: 'text-center py-12' },
          React.createElement('div', { className: 'animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4' }),
          React.createElement('p', { className: 'text-gray-600' }, 'Searching delicious dishes...')
        ),

        // Empty State
        !isLoading && searchResults.length === 0 && React.createElement('div', { className: 'text-center py-12' },
          React.createElement('div', { className: 'text-6xl mb-4' }, '🔍'),
          React.createElement('h3', { className: 'text-xl font-medium text-gray-900 mb-2' }, 
            searchQuery ? 'No dishes found' : 'No menu items available'
          ),
          React.createElement('p', { className: 'text-gray-600 mb-4' },
            searchQuery 
              ? 'Try a different search term or check for typos.'
              : 'Please check back later for menu updates.'
          ),
          searchQuery && React.createElement('button', {
            onClick: () => handleSearch(''),
            className: 'bg-primary-500 hover:bg-primary-600 text-white px-6 py-2 rounded-lg font-medium transition-colors'
          }, 'Show All Menu Items')
        ),

        // Search Results
        !isLoading && searchResults.length > 0 && React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' },
          searchResults.map(item => React.createElement(MenuCard, { key: item.id, item: item }))
        ),

        // Search Tips
        React.createElement('div', { className: 'mt-16 bg-gradient-to-r from-primary-50 to-orange-50 rounded-2xl p-8 text-center' },
          React.createElement('h3', { className: 'text-2xl font-bold text-gray-900 mb-4' },
            '🧠 Smart Search Tips'
          ),
          React.createElement('p', { className: 'text-gray-700 mb-4' },
            'Our AI search is very forgiving with spelling mistakes!'
          ),
          React.createElement('div', { className: 'space-y-2 text-sm text-gray-400' },
            React.createElement('p', null, '💡 Try searching for:'),
            React.createElement('div', { className: 'flex flex-wrap justify-center gap-2 mt-2' },
              ['dosa', 'biryani', 'chicken', 'paneer', 'curry', 'tandoori'].map(term =>
                React.createElement('button', {
                  key: term,
                  onClick: () => handleSearch(term),
                  className: 'bg-gray-100 hover:bg-primary-100 text-gray-600 hover:text-primary-700 px-3 py-1 rounded-full text-sm transition-colors'
                }, term)
              )
            )
          )
        )
      ),

      // Footer
      React.createElement('footer', { className: 'bg-gray-50 border-t border-gray-100 mt-16' },
        React.createElement('div', { className: 'container mx-auto px-4 py-8 text-center' },
          React.createElement('p', { className: 'text-gray-600 mb-2' },
            '🚀 Powered by PostgreSQL database and intelligent search'
          ),
          React.createElement('p', { className: 'text-sm text-gray-500' },
            'Try searching with typos like "dsoa" for "dosa" or "chiken" for "chicken" - all prices in Indian Rupees'
          )
        )
      )
    )
  );
};

window.App = App;
```

## 6. src/components/SearchBar.js
```javascript
const { useState, useEffect, useRef } = React;

const SearchBar = ({ onSearch, initialValue = '' }) => {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const searchTimeoutRef = useRef(null);
  const suggestionsTimeoutRef = useRef(null);

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  const fetchSuggestions = async (searchQuery) => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      setIsLoadingSuggestions(true);
      const response = await axios.get(`/api/search/suggestions?query=${encodeURIComponent(searchQuery)}&limit=5`);
      setSuggestions(response.data.suggestions || []);
      setShowSuggestions(response.data.suggestions?.length > 0);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    // Clear existing timeouts
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (suggestionsTimeoutRef.current) clearTimeout(suggestionsTimeoutRef.current);

    // Debounce search
    searchTimeoutRef.current = setTimeout(() => {
      onSearch(value);
    }, 300);

    // Debounce suggestions (shorter delay)
    suggestionsTimeoutRef.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 150);
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSearch(suggestion);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setShowSuggestions(false);
    onSearch('');
  };

  return (
    React.createElement('div', { className: 'relative max-w-2xl mx-auto' },
      React.createElement('div', { className: 'relative' },
        React.createElement('div', { className: 'absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none' },
          React.createElement('i', { className: 'fas fa-search text-gray-400' })
        ),
        React.createElement('input', {
          type: 'text',
          value: query,
          onChange: handleInputChange,
          onKeyDown: handleKeyDown,
          placeholder: 'Search for dishes... (try "dsoa" for dosa, "chiken" for chicken)',
          className: 'w-full pl-10 pr-12 py-4 text-lg border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 shadow-sm'
        }),
        query && React.createElement('button', {
          onClick: clearSearch,
          className: 'absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors'
        },
          React.createElement('i', { className: 'fas fa-times' })
        )
      ),

      // Suggestions Dropdown
      showSuggestions && React.createElement('div', { className: 'absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg' },
        isLoadingSuggestions && React.createElement('div', { className: 'px-4 py-2 text-gray-500 text-sm' },
          React.createElement('i', { className: 'fas fa-spinner fa-spin mr-2' }),
          'Loading suggestions...'
        ),
        !isLoadingSuggestions && suggestions.map((suggestion, index) =>
          React.createElement('button', {
            key: index,
            onClick: () => handleSuggestionClick(suggestion),
            className: 'w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 focus:outline-none focus:bg-gray-50'
          },
            React.createElement('i', { className: 'fas fa-search text-gray-400 mr-3' }),
            suggestion
          )
        )
      )
    )
  );
};

window.SearchBar = SearchBar;
```

## 7. src/components/MenuCard.js
```javascript
const { useState } = React;

const MenuCard = ({ item }) => {
  const [imageError, setImageError] = useState(false);

  const getCategoryColor = (category) => {
    const colors = {
      'North Indian': 'bg-orange-100 text-orange-800',
      'South Indian': 'bg-green-100 text-green-800',
      'Biryani': 'bg-yellow-100 text-yellow-800',
      'Tandoori': 'bg-red-100 text-red-800',
      'Street Food': 'bg-purple-100 text-purple-800',
      'Desserts': 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getDietaryColor = (dietary) => {
    const colors = {
      'vegetarian': 'bg-green-100 text-green-700',
      'vegan': 'bg-emerald-100 text-emerald-700',
      'gluten-free': 'bg-blue-100 text-blue-700',
      'contains dairy': 'bg-yellow-100 text-yellow-700',
      'contains gluten': 'bg-orange-100 text-orange-700',
      'pescatarian': 'bg-cyan-100 text-cyan-700',
      'contains shellfish': 'bg-red-100 text-red-700',
      'contains nuts': 'bg-amber-100 text-amber-700',
      'contains pork': 'bg-pink-100 text-pink-700',
    };
    return colors[dietary] || 'bg-gray-100 text-gray-700';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'North Indian': '🍛',
      'South Indian': '🥞',
      'Biryani': '🍚',
      'Tandoori': '🔥',
      'Street Food': '🥟',
      'Desserts': '🍰',
    };
    return icons[category] || '🍽️';
  };

  return (
    React.createElement('div', { className: 'bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-100 group hover:scale-[1.02]' },
      // Category Badge
      React.createElement('div', { className: 'px-4 pt-4 pb-2' },
        React.createElement('div', { className: 'flex items-center justify-between mb-3' },
          React.createElement('span', { className: `inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(item.category)}` },
            React.createElement('span', { className: 'mr-1' }, getCategoryIcon(item.category)),
            item.category
          ),
          item.similarity_score && React.createElement('span', { className: 'text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full' },
            `${Math.round(item.similarity_score * 100)}% match`
          )
        ),

        // Title and Description
        React.createElement('h3', { className: 'text-xl font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors' },
          item.name
        ),
        React.createElement('p', { className: 'text-gray-600 text-sm leading-relaxed mb-4' },
          item.description
        )
      ),

      // Ingredients
      item.ingredients && item.ingredients.length > 0 && React.createElement('div', { className: 'px-4 pb-3' },
        React.createElement('h4', { className: 'text-sm font-medium text-gray-700 mb-2 flex items-center' },
          React.createElement('i', { className: 'fas fa-leaf mr-2 text-green-500' }),
          'Ingredients'
        ),
        React.createElement('div', { className: 'flex flex-wrap gap-1' },
          item.ingredients.slice(0, 4).map((ingredient, index) =>
            React.createElement('span', {
              key: index,
              className: 'inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-md'
            }, ingredient)
          ),
          item.ingredients.length > 4 && React.createElement('span', { className: 'inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-md' },
            `+${item.ingredients.length - 4} more`
          )
        )
      ),

      // Dietary Information
      item.dietary_info && item.dietary_info.length > 0 && React.createElement('div', { className: 'px-4 pb-4' },
        React.createElement('h4', { className: 'text-sm font-medium text-gray-700 mb-2 flex items-center' },
          React.createElement('i', { className: 'fas fa-info-circle mr-2 text-blue-500' }),
          'Dietary Info'
        ),
        React.createElement('div', { className: 'flex flex-wrap gap-1' },
          item.dietary_info.map((info, index) =>
            React.createElement('span', {
              key: index,
              className: `inline-block text-xs px-2 py-1 rounded-md ${getDietaryColor(info)}`
            }, info)
          )
        )
      ),

      // Price
      React.createElement('div', { className: 'px-4 py-3 bg-gray-50 border-t border-gray-100' },
        React.createElement('div', { className: 'flex justify-between items-center' },
          React.createElement('span', { className: 'text-2xl font-bold text-primary-600' },
            `₹${item.price}`
          ),
          React.createElement('button', { className: 'bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center' },
            React.createElement('i', { className: 'fas fa-plus mr-2' }),
            'Add to Cart'
          )
        )
      )
    )
  );
};

window.MenuCard = MenuCard;
```