import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_iob_branches():
    url = 'https://www.iob.in/Branch.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Referer': url,
        'cookie': '__uzma=930b9d7c-e784-4c05-b454-40f1ee1f23d0; __uzmb=1747867787; __uzme=0156; ASP.NET_SessionId=q3znmqhry5wk2ozg1fh2rem3; _ga=GA1.1.1473551281.1747867816; _fbp=fb.1.1747867816521.418678542718800069; lhc_per=vid|2e8fd429c013f65dbd4e; __ssds=2; __ssuzjsr2=a9be0cd8e; __uzmbj2=1747867819; __uzmlj2=PYRR6sjuygjrFUMPzcko108bqSSmc8i6hYj9RAbPvVw=; __uzmaj2=930b9d7c-e784-4c05-b454-40f1ee1f23d0; __uzmc=672428297588; __uzmd=1747868749; __uzmf=7f6000fb69e276-bf6b-4435-b005-4e66ad97335a1747867787947961479-6a6f5343e9f98b4282; uzmx=7f9000ddec34a9-5a0b-4729-9045-219977acf6051-1747867787947961479-1dfdf3b156c4826c82; _ga_CX9029SF81=GS2.1.s1747867816$o1$g1$t1747868750$j0$l0$h0; __uzmcj2=229276756597; __uzmdj2=1747868750; __uzmfj2=7f6000fb69e276-bf6b-4435-b005-4e66ad97335a1747867819089931747-0564f8318da8075f67; uzmxj=7f9000ddec34a9-5a0b-4729-9045-219977acf6051-1747867819089931747-fc6fe8abbaef2a8067',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    with requests.Session() as s:
        data_list = []
        viewstate = ''
        eventvalidation = ''
        viewstategenerator = ''

        try:
            # Initial request to get the first page
            print("Fetching page 1...")
            response = s.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Ensure correct encoding (force UTF-8 if needed)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')  # Use .text instead of .content
            
            # Debug: Save readable HTML
            with open('debug_page1.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))  # Use str() to avoid BeautifulSoup formatting issues
            
            print("Saved debug_page1.html. Open it in a browser to check structure.")
            
            # Extract hidden fields safely
            viewstate_input = soup.find('input', {'id': '__VIEWSTATE'})
            eventvalidation_input = soup.find('input', {'id': '__EVENTVALIDATION'})
            viewstategenerator_input = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})
            
            if not all([viewstate_input, eventvalidation_input, viewstategenerator_input]):
                print("ERROR: Missing hidden fields. Check debug_page1.html for changes.")
                return
            
            viewstate = viewstate_input.get('value', '')
            eventvalidation = eventvalidation_input.get('value', '')
            viewstategenerator = viewstategenerator_input.get('value', '')
            
            # Parse table data
            table = soup.find('table', {'id': 'dgBranch'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 5:
                        data_list.append([col.get_text(strip=True) for col in cols])
                print(f"Page 1: Scraped {len(rows)} rows.")
            else:
                print("ERROR: Table 'dgBranch' not found. Check debug_page1.html.")
                return

            # Test pagination (scrape 2 pages only for debugging)
            for page in range(2, 3):
                print(f"Fetching page {page}...")
                form_data = {
                    '__VIEWSTATE': viewstate,
                    '__EVENTVALIDATION': eventvalidation,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                    '__EVENTTARGET': 'dgBranch',
                    '__EVENTARGUMENT': f'Page${page}'
                }
                response = s.post(url, data=form_data, headers=headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Update hidden fields
                viewstate = soup.find('input', {'id': '__VIEWSTATE'}).get('value', '')
                eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'}).get('value', '')
                viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'}).get('value', '')
                
                # Parse table
                table = soup.find('table', {'id': 'dgBranch'})
                if table:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) == 5:
                            data_list.append([col.get_text(strip=True) for col in cols])
                    print(f"Page {page}: Scraped {len(rows)} rows.")
                else:
                    print(f"ERROR: Table not found on page {page}.")
                
                time.sleep(2)  # Avoid rate-limiting

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        # Save to Excel
        if data_list:
            df = pd.DataFrame(data_list, columns=['Sr. No.', 'Branch Name', 'Branch Code', 'IFSC Code', 'Address'])
            df.to_excel('iob_branches.xlsx', index=False)
            print(f"Success! Saved {len(data_list)} rows to 'iob_branches.xlsx'.")
        else:
            print("FAILED: No data scraped.")

if __name__ == "__main__":
    scrape_iob_branches()    