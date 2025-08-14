import os

class Config:
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GEMINI_MODEL = 'gemini-2.0-flash'
