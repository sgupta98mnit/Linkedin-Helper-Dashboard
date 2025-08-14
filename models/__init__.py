from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, Text

db = SQLAlchemy()

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .job_posting import JobPosting
from .resume_version import ResumeVersion
from .job_application import JobApplication
from .job_match import JobMatch
from .visa_sponsorship_data import VisaSponsorshipData