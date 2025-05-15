import os
import google.generativeai as genai

# Set up the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

# Generate a response
response = model.generate_content("Hello world!")
print(response.text)