from flask import Flask
import google.generativeai as genai
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Blueprint registration
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
