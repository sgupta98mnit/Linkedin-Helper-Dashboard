#!/usr/bin/env python
"""Test script to verify database models work correctly."""
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_app
from models import db
from models.user import User
from models.job_posting import JobPosting
from models.resume_version import ResumeVersion
from models.job_application import JobApplication
from models.job_match import JobMatch
from models.visa_sponsorship_data import VisaSponsorshipData

def test_models():
    """Test all database models."""
    app = create_app('testing')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("Testing User model...")
        user = User(
            email='test@example.com',
            visa_status='F1',
            preferred_locations=['San Francisco', 'New York'],
            skills=['Python', 'JavaScript', 'SQL'],
            experience_level='Mid'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        
        assert user.check_password('testpassword')
        assert not user.check_password('wrongpassword')
        print("✓ User model works correctly")
        
        print("Testing JobPosting model...")
        job = JobPosting(
            title='Software Engineer',
            company='Test Company',
            location='San Francisco, CA',
            description='Great job opportunity',
            requirements=['Python', 'Flask'],
            visa_sponsorship=True,
            visa_types=['H1B', 'L1'],
            salary_min=100000,
            salary_max=150000,
            source='Indeed'
        )
        db.session.add(job)
        db.session.commit()
        
        assert job.salary_range_str == '$100,000 - $150,000'
        print("✓ JobPosting model works correctly")
        
        print("Testing ResumeVersion model...")
        resume = ResumeVersion(
            user_id=user.id,
            name='Software Engineer Resume',
            latex_content='\\documentclass{article}\\begin{document}Test Resume\\end{document}',
            category='Engineering'
        )
        db.session.add(resume)
        db.session.commit()
        print("✓ ResumeVersion model works correctly")
        
        print("Testing JobApplication model...")
        application = JobApplication(
            user_id=user.id,
            job_id=job.id,
            resume_version_id=resume.id,
            status='applied',
            notes='Applied through company website'
        )
        db.session.add(application)
        db.session.commit()
        
        assert application.status_display == 'Applied'
        print("✓ JobApplication model works correctly")
        
        print("Testing JobMatch model...")
        match = JobMatch(
            user_id=user.id,
            job_id=job.id,
            compatibility_score=0.85,
            match_reasons=['Skills match', 'Location preference', 'Visa sponsorship available']
        )
        db.session.add(match)
        db.session.commit()
        
        assert match.compatibility_percentage == 85
        assert match.compatibility_level == 'Excellent Match'
        print("✓ JobMatch model works correctly")
        
        print("Testing VisaSponsorshipData model...")
        visa_data = VisaSponsorshipData(
            company_name='Test Company',
            visa_types_sponsored=['H1B', 'L1'],
            h1b_approvals=100,
            h1b_denials=10
        )
        db.session.add(visa_data)
        db.session.commit()
        
        assert visa_data.h1b_approval_rate == 90.90909090909091
        assert visa_data.sponsors_visas == True
        print("✓ VisaSponsorshipData model works correctly")
        
        print("\n🎉 All models tested successfully!")
        
        # Test relationships
        print("\nTesting relationships...")
        assert len(user.resume_versions.all()) == 1
        assert len(user.job_applications.all()) == 1
        assert len(user.job_matches.all()) == 1
        assert len(job.job_applications.all()) == 1
        assert len(job.job_matches.all()) == 1
        print("✓ All relationships work correctly")
        
        print("\n✅ Database models are working perfectly!")

if __name__ == '__main__':
    test_models()