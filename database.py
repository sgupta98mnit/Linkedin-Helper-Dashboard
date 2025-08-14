"""Database initialization and utility functions."""
import os
from flask import Flask
from flask_migrate import Migrate
from models import db
from config import config

migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app

def init_db(app):
    """Initialize database with tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def seed_db(app):
    """Seed database with initial data."""
    with app.app_context():
        # Import models to ensure they're available
        from models.visa_sponsorship_data import VisaSponsorshipData
        
        # Check if we already have seed data
        if VisaSponsorshipData.query.first():
            print("Database already seeded!")
            return
        
        # Add some initial visa sponsorship data for well-known companies
        companies_data = [
            {
                'company_name': 'Google',
                'visa_types_sponsored': ['H1B', 'L1', 'O1'],
                'h1b_approvals': 1500,
                'h1b_denials': 100
            },
            {
                'company_name': 'Microsoft',
                'visa_types_sponsored': ['H1B', 'L1', 'O1'],
                'h1b_approvals': 1200,
                'h1b_denials': 80
            },
            {
                'company_name': 'Amazon',
                'visa_types_sponsored': ['H1B', 'L1'],
                'h1b_approvals': 2000,
                'h1b_denials': 150
            },
            {
                'company_name': 'Meta',
                'visa_types_sponsored': ['H1B', 'L1', 'O1'],
                'h1b_approvals': 800,
                'h1b_denials': 60
            },
            {
                'company_name': 'Apple',
                'visa_types_sponsored': ['H1B', 'L1'],
                'h1b_approvals': 600,
                'h1b_denials': 40
            }
        ]
        
        for company_data in companies_data:
            company = VisaSponsorshipData(**company_data)
            db.session.add(company)
        
        db.session.commit()
        print(f"Database seeded with {len(companies_data)} companies!")

if __name__ == '__main__':
    app = create_app()
    init_db(app)
    seed_db(app)