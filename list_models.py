"""List available Gemini models"""
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

api_key = os.getenv('GOOGLE_API_KEY')
client = genai.Client(api_key=api_key)

print("Available Gemini models:")
print("=" * 80)

try:
    models = client.models.list()

    for model in models:
        print(f"Model: {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Supported methods: {model.supported_generation_methods}")
        if hasattr(model, 'description'):
            print(f"  Description: {model.description}")
        print()

except Exception as e:
    print(f"Error: {e}")
