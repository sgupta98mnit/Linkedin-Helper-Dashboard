from . import db
from datetime import datetime
from sqlalchemy import String, JSON

class JobMatch(db.Model):
    """Job match model for storing compatibility scores and matches."""
    __tablename__ = 'job_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    compatibility_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    match_reasons = db.Column(JSON, default=list)  # Reasons for the match
    viewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<JobMatch {self.user_id} -> {self.job_id} ({self.compatibility_score:.2f})>'
    
    @property
    def compatibility_percentage(self):
        """Return compatibility score as percentage."""
        return int(self.compatibility_score * 100)
    
    @property
    def compatibility_level(self):
        """Return compatibility level description."""
        if self.compatibility_score >= 0.8:
            return "Excellent Match"
        elif self.compatibility_score >= 0.6:
            return "Good Match"
        elif self.compatibility_score >= 0.4:
            return "Fair Match"
        else:
            return "Poor Match"