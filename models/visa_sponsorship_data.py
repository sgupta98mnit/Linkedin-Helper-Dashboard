from . import db
from datetime import datetime
from sqlalchemy import String, JSON

class VisaSponsorshipData(db.Model):
    """Visa sponsorship data model for tracking company visa history."""
    __tablename__ = 'visa_sponsorship_data'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    visa_types_sponsored = db.Column(JSON, default=list)  # e.g., ['H1B', 'L1', 'O1']
    h1b_approvals = db.Column(db.Integer, default=0)
    h1b_denials = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VisaSponsorshipData {self.company_name}>'
    
    @property
    def h1b_approval_rate(self):
        """Calculate H1B approval rate."""
        total = self.h1b_approvals + self.h1b_denials
        if total == 0:
            return None
        return (self.h1b_approvals / total) * 100
    
    @property
    def sponsors_visas(self):
        """Check if company sponsors any visas."""
        return len(self.visa_types_sponsored) > 0