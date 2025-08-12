import os
from dotenv import load_dotenv
from pathlib import Path

#load_dotenv(dotenv_path="/Users/karanchanana/Repos/Learning/learning.env")
#load_dotenv("learning_python.env")
load_dotenv()
#print("Environment file path:", os.path.abspath('.env'))
# Make sure the path is correct
from pathlib import Path
env_path = Path(".env")
#print("current path:", os.getcwd())
if not env_path.exists():
    print(f"Error: .env file not found at {env_path.absolute()}")
    global_env_path = Path.home() / ".env"
    load_dotenv(global_env_path)
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print("OpenAI API Key loaded successfully.")
else:
    print("OpenAI API Key not found. Please set the OPENAI_API_KEY environment variable.")
print(openai_key)