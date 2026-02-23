import json
from sqlalchemy.orm import Session
from models import MenuItem, get_db, SessionLocal

def load_menu_data_to_database():
    """Load menu data from JSON file into the database"""
    
    # Check if data is already loaded
    db = SessionLocal()
    existing_count = db.query(MenuItem).count()
    
    if existing_count > 0:
        print(f"Database already has {existing_count} menu items. Skipping data load.")
        db.close()
        return existing_count
    
    try:
        with open('data/menu.json', 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        menu_items = menu_data.get('items', [])
        
        # Add items to database
        for item_data in menu_items:
            menu_item = MenuItem(
                id=item_data['id'],
                name=item_data['name'],
                description=item_data['description'],
                category=item_data['category'],
                price=item_data['price'],
                ingredients=item_data.get('ingredients', []),
                dietary_info=item_data.get('dietary_info', [])
            )
            db.add(menu_item)
        
        db.commit()
        count = db.query(MenuItem).count()
        print(f"Successfully loaded {count} menu items into database")
        db.close()
        return count
        
    except FileNotFoundError:
        print("Menu data file not found. Please ensure data/menu.json exists.")
        db.close()
        return 0
    except json.JSONDecodeError:
        print("Invalid JSON in menu data file.")
        db.close()
        return 0
    except Exception as e:
        print(f"Error loading menu data: {e}")
        db.rollback()
        db.close()
        return 0

def get_all_menu_items(db: Session):
    """Get all menu items from database"""
    return db.query(MenuItem).all()

def search_menu_items(db: Session, query: str, limit: int = 10):
    """Search menu items in database"""
    if not query.strip():
        return []
    
    query_lower = query.lower()
    
    # Search by name, description, or ingredients
    results = db.query(MenuItem).filter(
        MenuItem.name.ilike(f'%{query}%') |
        MenuItem.description.ilike(f'%{query}%') |
        MenuItem.category.ilike(f'%{query}%')
    ).limit(limit).all()
    
    return results

def get_menu_suggestions(db: Session, query: str, limit: int = 5):
    """Get menu name suggestions based on query"""
    if not query.strip():
        return []
    
    results = db.query(MenuItem.name).filter(
        MenuItem.name.ilike(f'%{query}%')
    ).limit(limit).all()
    
    return [result[0] for result in results]