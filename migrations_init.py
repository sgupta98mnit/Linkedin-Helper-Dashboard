"""Initialize Flask-Migrate for database migrations."""
import os
from flask_migrate import init, migrate, upgrade
from database import create_app

def setup_migrations():
    """Set up Flask-Migrate for the application."""
    app = create_app()
    
    with app.app_context():
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            print("Initializing Flask-Migrate...")
            init()
            print("Flask-Migrate initialized!")
        
        # Create initial migration
        print("Creating initial migration...")
        migrate(message='Initial migration')
        print("Initial migration created!")
        
        # Apply migration
        print("Applying migration...")
        upgrade()
        print("Migration applied successfully!")

if __name__ == '__main__':
    setup_migrations()