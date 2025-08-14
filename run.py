from app import create_app
import google.generativeai as genai
from config import Config

# Configure the Gemini API once at startup
if not Config.GOOGLE_API_KEY:
    raise ValueError("No GOOGLE_API_KEY set in config.py")
genai.configure(api_key=Config.GOOGLE_API_KEY)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
