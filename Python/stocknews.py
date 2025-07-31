import os
import smtplib
import ssl
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time

import requests
import google.generativeai as genai
from dotenv import load_dotenv
import schedule

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

def check_environment():
    """Verify all required environment variables are set."""
    required_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "NEWS_API_KEY": NEWS_API_KEY,
        "SENDER_EMAIL": SENDER_EMAIL,
        "SENDER_PASSWORD": SENDER_PASSWORD,
        "RECIPIENT_EMAIL": RECIPIENT_EMAIL
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
MAX_ARTICLES_TO_PROCESS = 5 # Number of recent articles to consider for summary

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,  # Increased for better summaries
}

# Simplified model configuration
model = genai.GenerativeModel('gemini-1.5-pro')  # Using the stable version identifier

# --- Functions ---
def test_gemini_connection():
    """Test the Gemini API connection"""
    try:
        # for model in genai.list_models():
        #     if "gemini" in model.name:
        #         print(f"\nModel: {model.name}")
        #         print(f"Display Name: {model.display_name}")
        #         print(f"Description: {model.description}")
        #         print(f"Generation Methods: {model.supported_generation_methods}")
        #         print("-" * 50)
        response = model.generate_content("Test connection to Gemini API")
        if response and response.text:
            print("✓ Gemini API connection successful")
            return True
        return False
    except Exception as e:
        print(f"✗ Gemini API connection failed: {e}")
        return False


def get_latest_stock_news(COMPANY_NAME, COMPANY_TICKER):
    """Fetches the latest news articles for the specified company."""
    print(f"Fetching news for {COMPANY_NAME}...")
    articles_data = []
    today = datetime.now()
    yesterday = today - timedelta(days=1) # Fetch news from the last 24 hours
    NEWS_SEARCH_QUERY = f'"{COMPANY_NAME}" OR "{COMPANY_TICKER}"' # Search for exact phrase or ticker
    params = {
        'q': NEWS_SEARCH_QUERY,
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'publishedAt', # Get the most recent articles
        'pageSize': MAX_ARTICLES_TO_PROCESS * 2, # Fetch a bit more to filter
        'from': yesterday.strftime('%Y-%m-%dT%H:%M:%S'), # News from the last 24h
        'to': today.strftime('%Y-%m-%dT%H:%M:%S')
    }
    try:
        response = requests.get(NEWS_API_ENDPOINT, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors
        news_data = response.json()

        if news_data.get("status") == "ok" and news_data.get("totalResults", 0) > 0:
            for article in news_data.get("articles", []):
                # Basic relevance check (can be improved)
                title = article.get('title', '')
                description = article.get('description', '')
                if COMPANY_NAME.lower() in title.lower() or \
                   COMPANY_NAME.lower() in (description.lower() if description else "") or \
                   (COMPANY_TICKER and COMPANY_TICKER.lower() in title.lower()) or \
                   (COMPANY_TICKER and COMPANY_TICKER.lower() in (description.lower() if description else "")):
                    articles_data.append({
                        "title": title,
                        "description": description,
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt")
                    })
                    if len(articles_data) >= MAX_ARTICLES_TO_PROCESS:
                        break
            print(f"Found {len(articles_data)} relevant articles.")
            return articles_data
        else:
            print("No articles found or API error.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while fetching news: {e}")
        return []

def summarize_news_with_gemini(articles,COMPANY_NAME):
    """Summarizes a list of articles using Gemini API."""
    if not articles:
        return None

    print("Summarizing news with Gemini...")
    
    try:
        prompt = f"""Summarize these news articles about {COMPANY_NAME}:
        Focus on key financial and market-moving information.
        Keep it concise and professional using 3 to 5 lines per article.
        Use bullet points for clarity.
        Articles to summarize:
        """
        
        for i, article in enumerate(articles):
            prompt += f"\n{i+1}. {article['title']}\n"
            if article.get('description'):
                prompt += f"   {article['description']}\n"

        response = model.generate_content(prompt)
        
        if response and response.text:
            print("Summary generated successfully.")
            return response.text.strip()
        else:
            print("No valid response from Gemini API.")
            return None
    except Exception as e:
        print(f"Error during Gemini summarization: {e}")
        return None

def send_email(subject, body, recipient_email, sender_email, sender_password):
    """Sends an email."""
    print(f"Preparing to send email to {recipient_email}...")
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Check your email and app password.")
    except Exception as e:
        print(f"Error sending email: {e}")

def job(COMPANY_NAME, COMPANY_TICKER):
    """The main job to be scheduled."""
    print(f"\n--- Running job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not all([GEMINI_API_KEY, NEWS_API_KEY, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        print("Missing one or more required environment variables. Exiting.")
        return

    articles = get_latest_stock_news(COMPANY_NAME, COMPANY_TICKER)

    if not articles:
        print(f"No new relevant news found for {COMPANY_NAME}. No email will be sent.")
        return

    summary = summarize_news_with_gemini(articles,COMPANY_NAME)

    if summary:
        email_subject = f"Executive News Summary: {COMPANY_NAME} - {datetime.now().strftime('%Y-%m-%d')}"
        email_body = f"Good morning,\n\nHere is your executive summary of the latest stock market news for {COMPANY_NAME}:\n\n"
        email_body += f"{summary}\n\n"
        email_body += "Sources:\n"
        for article in articles:
            email_body += f"- {article['title']}: {article['url']}\n"
        email_body += f"\nBest regards,\nYour Automated News Bot"

        send_email(email_subject, email_body, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)
    else:
        print(f"Could not generate summary for {COMPANY_NAME}. No email will be sent.")
    print("--- Job finished ---")

def print_env_vars():
    """Debug function to print environment variables"""
    print("\nChecking environment variables:")
    env_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "NEWS_API_KEY": NEWS_API_KEY,
        "SENDER_EMAIL": SENDER_EMAIL,
        "SENDER_PASSWORD": "********" if SENDER_PASSWORD else None,
        "RECIPIENT_EMAIL": RECIPIENT_EMAIL
    }
    
    for var_name, var_value in env_vars.items():
        status = "✓ Set" if var_value else "✗ Missing"
        print(f"{var_name}: {status} : {var_value}")
    print()


# --- Scheduler ---
if __name__ == "__main__":
    try:
        check_environment()
        print_env_vars()
        # Test Gemini connection before proceeding
        if not test_gemini_connection():
            raise Exception("Failed to connect to Gemini API")
           
        print("Script started. Running daily stock news job...")
        # --- DAILY JOB EXECUTION ---
        job("United Healthcare","UNH" ) 
        job("Palantir Technologies Inc","PLTR" ) 
        job("NVIDIA Corp","NVDA" ) 
        job("Lockheed Martin Corp","LMT" ) 
        job("Rivian Automotive Inc","RIVN" )
        job("Alphabet Inc Class C","GOOG" ) 
        job("Tesla Inc","TSLA" ) 
        print("--- ALL JOBS COMPLETED ---")
        
        # For more concise weekday scheduling:
        # for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        #     schedule.every().day.at("09:00").tag(day).do(job) # This schedules for ALL days
        # A better way for weekdays:
        # schedule.every().weekday.at("09:00").do(job) # This is simpler but 'weekday' isn't a direct method
        # The individual .monday, .tuesday etc. is most explicit and reliable with the `schedule` library

        #print("Scheduler is running. Jobs scheduled for 9:00 AM weekdays.")
        #print(f"Next run for a job: {schedule.next_run()}")

        #while True:
        #    schedule.run_pending()
        #    time.sleep(60) # Check every 60 seconds
    except Exception as e:
        print(f"Startup error: {e}")
        exit(1)


