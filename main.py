import os
import requests
import re
from collections import Counter
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
API_KEY = os.getenv("RAPID_API_KEY")

def setup_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def verify_and_navigate(driver):
    driver.get("https://elpais.com/")
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "html"))
    )
    
    lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
    if "es" not in lang.lower():
        print(f"Warning: Language is {lang}")
    else:
        print("Confirmed: Spanish language detected.")

    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        accept_button.click()
    except:
        pass


def scrape_opinion_section(driver):
    print("Navigating to Opinion section...")
    driver.get("https://elpais.com/opinion/")
    
    
    if not os.path.exists("cover_images"):
        os.makedirs("cover_images")

    
    articles = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )

    scraped_data = []

    for i in range(5):
        article = articles[i]
        data = {}
        
        try:
            
            title_element = article.find_element(By.TAG_NAME, "h2")
            data['title'] = title_element.text
            
            
            try:
                content_element = article.find_element(By.TAG_NAME, "p")
                data['content'] = content_element.text
            except:
                data['content'] = "No content available"
            
            
            try:
                img_element = article.find_element(By.TAG_NAME, "img")
                img_url = img_element.get_attribute("src")
                data['image_url'] = img_url
                
                
                img_response = requests.get(img_url)
                if img_response.status_code == 200:
                    file_path = f"cover_images/article_{i+1}.jpg"
                    with open(file_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"Downloaded image for article {i+1}")
            except:
                data['image_url'] = None
                print(f"No image found for article {i+1}")

            scraped_data.append(data)
            print(f"Title {i+1}: {data['title']}")
            print("-" * 20)

        except Exception as e:
            print(f"Error processing article {i+1}: {e}")

    return scraped_data

def translate_articles(scraped_data):
    print("\n Starting Translation ")
    translated_headers = []
    
    url = "https://google-translate113.p.rapidapi.com/api/v1/translator/json"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "google-translate113.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    for i, item in enumerate(scraped_data):
        
        payload = {
            "from": "es",
            "to": "en",
            "json": {
                "title": item["title"],
                "content": item["content"]
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            
           
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                translated_headers.append(item["title"])
                continue

            result = response.json()
           
            en_title = result.get("trans", {}).get("title", item["title"])
            translated_headers.append(en_title)
            print(f"Success {i+1}: {en_title}")

        except Exception as e:
            print(f"Code Error: {e}")
            translated_headers.append(item["title"])

    return translated_headers

def analyze_words(titles):
    print("\n Word Frequency Analysis ")
    all_text = " ".join(titles).lower()
    words = re.findall(r'\b\w+\b', all_text)
    counts = Counter(words)
    repeated = {word: count for word, count in counts.items() if count > 2}
    if repeated:
        for word, count in repeated.items():
            print(f"Word: '{word}' | Count: {count}")
    else:
        print("No words repeated more than twice.")


if __name__ == "__main__":
    driver = setup_driver()
    try:
        verify_and_navigate(driver)
        articles_list = scrape_opinion_section(driver)
        print(f"\nSuccessfully scraped {len(articles_list)} articles.")
        
       
        english_titles = translate_articles(articles_list)
        analyze_words(english_titles)
        
    finally:
        driver.quit()