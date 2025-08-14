from . import db
from datetime import datetime

class ResumeVersion(db.Model):
    """Resume version model for storing multiple resume variations."""
    __tablename__ = 'resume_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # e.g., "Software Engineer", "Data Scientist"
    latex_content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # e.g., "Engineering", "Data Science", "Product"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    job_applications = db.relationship('JobApplication', backref='resume_version', lazy='dynamic')
    
    def __repr__(self):
        return f'<ResumeVersion {self.name} for User {self.user_id}>'