import requests
import pandas as pd

def fetch_and_format_offers(api_url="https://api-v3.lennysbundle.com/offers/"):
    # Step 1: Fetch the JSON data
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    
    data = response.json()
    
    # Step 2: Parse and format the offers into a structured list
    offers = []
    for offer in data.get("offers", []):
        offers.append({
            "ID": offer.get("id"),
            "Title": offer.get("title"),
            "Heading": offer.get("heading"),
            "Subheading": offer.get("subheading"),
            "Description": offer.get("description"),
            "Partner": offer.get("partner_name"),
            "Priority Tier": offer.get("priority_tier"),
            "Available Inventory": offer.get("available_inventory"),
            "Insider Inventory": offer.get("inventory", {}).get("insider", 0),
            "Paid Inventory": offer.get("inventory", {}).get("paid", 0),
            "Insider Only": offer.get("insider_only", False),
            "Cover Image URL": offer.get("cover_image")
        })
    
    # Step 3: Convert to DataFrame
    df = pd.DataFrame(offers)
    return df

# Example usage:
if __name__ == "__main__":
    df = fetch_and_format_offers()
    print(df.head())  # Show first few rows
    # Optionally, save to CSV
    df.to_csv("offers_list_lenny.csv", index=False)
