from app import app, db
from sqlalchemy import text
from routes import create_initial_data

with app.app_context():
    # Drop the package table if it exists
    db.session.execute(text('DROP TABLE IF EXISTS package'))
    db.session.commit()
    
    # Create all tables
    db.create_all()
    
    # Create initial data
    create_initial_data()
    
    print("Database reset and initial data created successfully!")