# Smart Menu Search Application

A smart menu search application featuring authentic Indian cuisine with intelligent, typo-tolerant search capabilities.

## Features

- **Smart Search**: Finds menu items even with spelling mistakes (e.g., "dsoa" finds "dosa")
- **Indian Cuisine**: 15 authentic Indian dishes with prices in Indian Rupees
- **Real-time Search**: Instant search results with autocomplete suggestions
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **No Database Required**: Uses JSON file for data storage

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Create a new directory and navigate to it:**
   ```bash
   mkdir smart-menu-search
   cd smart-menu-search
   ```

2. **Copy all the provided files into this directory** (see file structure below)

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend server:**
   ```bash
   python simple_main.py
   ```

5. **In a new terminal, run the frontend server:**
   ```bash
   python server.py
   ```

6. **Open your browser and visit:**
   ```
   http://localhost:5000
   ```

## File Structure

```
smart-menu-search/
├── simple_main.py          # Main application server
├── data/
│   └── menu.json          # Indian menu data
├── src/
│   ├── App.js             # Main React component
│   ├── index.js           # React entry point
│   └── components/
│       ├── SearchBar.js   # Search component
│       └── MenuCard.js    # Menu item display
├── public/
│   └── index.html         # HTML entry point
└── README.md              # This file
```

## Usage

- **Search**: Type any dish name in the search bar
- **Typo Tolerance**: Try searching with misspellings like "chiken" for "chicken"
- **Quick Search**: Click on suggested terms like "dosa", "biryani", "paneer"
- **Browse All**: Leave search empty to see all menu items

## Menu Categories

- **North Indian**: Butter Chicken, Palak Paneer, Chole Bhature
- **South Indian**: Masala Dosa, Idli Sambar, Fish Curry
- **Biryani**: Mutton Biryani with aromatic spices
- **Tandoori**: Tandoori Chicken from clay oven
- **Street Food**: Pani Puri and other favorites
- **Desserts**: Gulab Jamun and sweet treats

## Technical Details

- **Backend**: FastAPI with fuzzy string matching
- **Frontend**: React with Tailwind CSS (served via CDN)
- **Search Algorithm**: Multi-factor similarity scoring
- **Data**: JSON-based storage for simplicity
- **Port**: Runs on localhost:8000

## Customization

### Adding New Menu Items

Edit `data/menu.json` and add items following this structure:

```json
{
  "id": 16,
  "name": "New Dish",
  "description": "Description of the dish",
  "category": "North Indian",
  "price": 250,
  "ingredients": ["ingredient1", "ingredient2"],
  "dietary_info": ["vegetarian"]
}
```

### Modifying Search Behavior

Edit the similarity threshold in `simple_main.py`:

```python
if final_score > 0.3:  # Change this value (0.3) to adjust sensitivity
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `simple_main.py`:
   ```python
   uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
   ```

2. **Module not found**: Install missing dependencies:
   ```bash
   pip install fastapi uvicorn
   ```

3. **File not found**: Ensure all files are in the correct directory structure

### Development Mode

For development with auto-reload:

```bash
uvicorn simple_main:app --reload --host 0.0.0.0 --port 8000
```

## License

This project is for educational and personal use.