#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

def strip_unwanted_tags(soup):
    for tag in soup(["script", "style", "noscript", "meta", "link", "header", "footer", "nav", "aside"]):
        tag.decompose()

def crawl_and_extract(url):
    """
    Crawls a given URL and extracts its main text content.
    Returns the title and the clean text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string.strip() if soup.title else "未命名網頁"
        
        # Try to find Open Graph tags as backup if article content is missing
        og_desc = soup.find("meta", property="og:description")
        og_title = soup.find("meta", property="og:title")
        
        if og_title and title == "未命名網頁":
            title = og_title.get("content", "").strip()

        # Remove unwanted elements
        strip_unwanted_tags(soup)
        
        # For certain sites like FB, mostly OG tags are useful since the JS renders the rest
        main_content = []
        if og_desc:
            main_content.append(og_desc.get("content", "").strip())
        
        # Extract text from p, h1-h6 tags
        elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article'])
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if text and text not in main_content:
                main_content.append(text)
                
        # If still empty (e.g. heavily JS driven), just get all text
        if not main_content:
            text = soup.get_text(separator='\n', strip=True)
            main_content.append(text)
            
        final_text = "\n\n".join(main_content)
        # Limit to 5000 characters to save tokens, usually enough for a summary
        return title, final_text[:5000]
        
    except requests.RequestException as e:
        print(f"Error crawling URL: {e}")
        return "無法載入的網頁", f"無法存取該網址：{url}\n錯誤訊息：{e}"
    except Exception as e:
        print(f"Unexpected error when parsing URL: {e}")
        return "網頁解析錯誤", f"無法解析網址內容：{url}\n錯誤訊息：{e}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Crawling {test_url} ...")
        t, c = crawl_and_extract(test_url)
        print(f"TITLE: {t}")
        print("-" * 50)
        print(c)
