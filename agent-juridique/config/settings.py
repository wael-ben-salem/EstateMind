import os
from dotenv import load_dotenv

# This automatically finds the .env file and loads the variables
load_dotenv()

# We save them to Python variables with clear names
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# A quick safety check (Proper indentation used here!)
if not QDRANT_URL or not COHERE_API_KEY:
    raise ValueError("⚠️ Missing API Keys! Please check your .env file.")