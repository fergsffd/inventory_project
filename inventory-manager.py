import sqlite3
from datetime import datetime
import cmd
import os

class InventoryDatabase:
    def __init__(self, db_name="inventory.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        """Create the necessary database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                quantity INTEGER DEFAULT 1,
                date_added TIMESTAMP,
                last_modified TIMESTAMP
            )
        ''')
        
        # Categories table for future expansion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        self.conn.commit()

    def add_item(self, name, description=None, location=None, quantity=1):
        """Add a new item to the inventory."""
        cursor = self.conn.cursor()
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO items (name, description, location, quantity, date_added, last_modified)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, location, quantity, current_time, current_time))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_item(self, item_id):
        """Retrieve an item by its ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        return cursor.fetchone()

    def update_item(self, item_id, **kwargs):
        """Update an item's information."""
        allowed_fields = {'name', 'description', 'location', 'quantity'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False

        updates['last_modified'] = datetime.now().isoformat()
        
        set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
        values = list(updates.values())
        values.append(item_id)

        cursor = self.conn.cursor()
        cursor.execute(f'''
            UPDATE items 
            SET {set_clause}
            WHERE id = ?
        ''', values)
        
        self.conn.commit()
        return True

    def delete_item(self, item_id):
        """Delete an item from the inventory."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def search_items(self, search_term):
        """Search for items by name or description."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM items 
            WHERE name LIKE ? OR description LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))
        return cursor.fetchall()

    def list_items(self):
        """List all items in the inventory."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM items')
        return cursor.fetchall()

class InventoryShell(cmd.Cmd):
    intro = 'Welcome to the Inventory Management System. Type help or ? to list commands.\n'
    prompt = 'inventory> '

    def __init__(self):
        super().__init__()
        self.db = InventoryDatabase()

    def do_add(self, arg):
        """Add a new item: add <name> [description] [location] [quantity]"""
        args = arg.split(maxsplit=3)
        if not args:
            print("Error: Item name is required")
            return
        
        name = args[0]
        description = args[1] if len(args) > 1 else None
        location = args[2] if len(args) > 2 else None
        quantity = args[3] if len(args) > 3 else 1
        
        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        item_id = self.db.add_item(name, description, location, quantity)
        print(f"Added item with ID: {item_id}")

    def do_list(self, arg):
        """List all items in inventory"""
        items = self.db.list_items()
        if not items:
            print("No items in inventory")
            return
        
        print("\nCurrent Inventory:")
        print("-" * 80)
        print(f"{'ID':4} | {'Name':20} | {'Location':15} | {'Quantity':8} | {'Description'}")
        print("-" * 80)
        
        for item in items:
            item_id, name, desc, location, qty, _, _ = item
            desc = desc if desc else ''
            location = location if location else ''
            print(f"{item_id:<4} | {name[:20]:<20} | {location[:15]:<15} | {qty:<8} | {desc[:30]}")

    def do_search(self, arg):
        """Search for items: search <term>"""
        if not arg:
            print("Error: Search term is required")
            return
        
        items = self.db.search_items(arg)
        if not items:
            print(f"No items found matching '{arg}'")
            return
        
        print(f"\nSearch results for '{arg}':")
        print("-" * 80)
        print(f"{'ID':4} | {'Name':20} | {'Location':15} | {'Quantity':8} | {'Description'}")
        print("-" * 80)
        
        for item in items:
            item_id, name, desc, location, qty, _, _ = item
            desc = desc if desc else ''
            location = location if location else ''
            print(f"{item_id:<4} | {name[:20]:<20} | {location[:15]:<15} | {qty:<8} | {desc[:30]}")

    def do_delete(self, arg):
        """Delete an item: delete <item_id>"""
        try:
            item_id = int(arg)
            if self.db.delete_item(item_id):
                print(f"Deleted item {item_id}")
            else:
                print(f"No item found with ID {item_id}")
        except ValueError:
            print("Error: Please provide a valid item ID")

    def do_quit(self, arg):
        """Exit the program"""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    InventoryShell().cmdloop()

