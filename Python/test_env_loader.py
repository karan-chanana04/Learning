import os
from pathlib import Path

# Method 1: Using python-dotenv (recommended)
try:
    from dotenv import load_dotenv
    
    # Load from your home directory
    env_path = Path.home() / ".env"
    print(f"Loading .env from: {env_path}")
    
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ .env file loaded successfully!")
        
        # Test accessing your variables
        gemini_key = os.getenv('GEMINI_API_KEY')
        news_key = os.getenv('NEWS_API_KEY')
        sender_email = os.getenv('SENDER_EMAIL')
        
        print(f"GEMINI_API_KEY: {gemini_key[:20]}..." if gemini_key else "GEMINI_API_KEY: Not found")
        print(f"NEWS_API_KEY: {news_key[:10]}..." if news_key else "NEWS_API_KEY: Not found")
        print(f"SENDER_EMAIL: {sender_email}" if sender_email else "SENDER_EMAIL: Not found")
        
    else:
        print(f"❌ .env file not found at {env_path}")
        
except ImportError:
    print("python-dotenv not installed. Using manual loading...")
    
    # Method 2: Manual loading (fallback)
    def load_env_manually(env_file_path):
        env_vars = {}
        env_path = Path(env_file_path)
        
        if not env_path.exists():
            print(f"❌ .env file not found at {env_path}")
            return env_vars
        
        with open(env_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Handle comments in value
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    env_vars[key] = value
                    os.environ[key] = value
        
        return env_vars
    
    # Load manually
    env_path = Path.home() / ".env"
    env_vars = load_env_manually(env_path)
    
    if env_vars:
        print("✅ .env file loaded manually!")
        for key, value in env_vars.items():
            if 'KEY' in key or 'PASSWORD' in key:
                print(f"{key}: {value[:10]}...")
            else:
                print(f"{key}: {value}")
    else:
        print("❌ Failed to load .env file")
