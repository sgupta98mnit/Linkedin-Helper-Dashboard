from . import db
from datetime import datetime
from sqlalchemy import String, Text, JSON

class JobPosting(db.Model):
    """Job posting model for storing job opportunities."""
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False, index=True)
    location = db.Column(db.String(255))
    description = db.Column(Text)
    requirements = db.Column(JSON, default=list)
    visa_sponsorship = db.Column(db.Boolean, default=False, index=True)
    visa_types = db.Column(JSON, default=list)  # e.g., ['H1B', 'L1', 'O1']
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    posted_date = db.Column(db.DateTime)
    source = db.Column(db.String(50))  # e.g., 'Indeed', 'LinkedIn', 'Handshake'
    external_id = db.Column(db.String(255))  # ID from the source platform
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    job_applications = db.relationship('JobApplication', backref='job_posting', lazy='dynamic')
    job_matches = db.relationship('JobMatch', backref='job_posting', lazy='dynamic')
    
    def __repr__(self):
        return f'<JobPosting {self.title} at {self.company}>'
    
    @property
    def salary_range_str(self):
        """Return formatted salary range string."""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} - ${self.salary_max:,}"
        elif self.salary_min:
            return f"${self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,}"
        return "Salary not specified"