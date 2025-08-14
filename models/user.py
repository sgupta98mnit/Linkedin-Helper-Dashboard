from . import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import String, Text, JSON
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    visa_status = db.Column(db.String(50))  # e.g., 'F1', 'H1B', 'Green Card', 'Citizen'
    preferred_locations = db.Column(JSON, default=list)
    skills = db.Column(JSON, default=list)
    experience_level = db.Column(db.String(50))  # e.g., 'Entry', 'Mid', 'Senior'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resume_versions = db.relationship('ResumeVersion', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    job_applications = db.relationship('JobApplication', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    job_matches = db.relationship('JobMatch', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'