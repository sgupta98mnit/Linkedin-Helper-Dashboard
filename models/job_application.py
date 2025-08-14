from . import db
from datetime import datetime

class JobApplication(db.Model):
    """Job application model for tracking application status."""
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    status = db.Column(db.String(50), default='applied')  # applied, interview, rejected, offer, withdrawn
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    resume_version_id = db.Column(db.Integer, db.ForeignKey('resume_versions.id'))
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<JobApplication {self.user_id} -> {self.job_id} ({self.status})>'
    
    @property
    def status_display(self):
        """Return human-readable status."""
        status_map = {
            'applied': 'Applied',
            'interview': 'Interview Scheduled',
            'rejected': 'Rejected',
            'offer': 'Offer Received',
            'withdrawn': 'Withdrawn'
        }
        return status_map.get(self.status, self.status.title())