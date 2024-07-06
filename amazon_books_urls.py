import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import TimeoutException
import time
from tqdm import tqdm
import pandas as pd
from bs4 import BeautifulSoup
import re
from collections import deque


options = uc.ChromeOptions()
driver = uc.Chrome(options=options)

url = "https://amazon.com"

driver.get(url)

time.sleep(30)

book_titles = []
book_urls = []
book_num_reviews = []

def scrape_data():
    cards = []
    max_cards = 50
    wait_time = 2
    driver.execute_script("return document.body.scrollHeight")
    counter = 0
    while True:
        # Scroll down by a small amount (e.g., 500 pixels)
        driver.execute_script("window.scrollBy(0, 500);")
        counter+=1
        # Wait for the new content to load
        time.sleep(wait_time)
        
        # Get the page source after scrolling
        html_content = driver.page_source
        
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            box = soup.find('div', class_="a-cardui _cDEzb_card_1L-Yx")
            new_cards = box.find_all('div', id="gridItemRoot")
        except Exception as e:
            print("Error parsing HTML content:", e)
            break
        
        # Check if new cards are found and update the list
        if new_cards:
            cards = new_cards
        
        # Check if we have reached the maximum number of cards
        if len(cards) >= max_cards:
            break
        if counter >= 10:
            break
        

    print("number of cards found: ", len(cards))
    for card in cards:
        try:
            num_rev=""
            href=""
            title=""
            a_row = card.find('div', class_="a-icon-row")
            if not a_row:
                continue
            rating = a_row.find('span', class_="a-icon-alt")
            rating = float(rating.text.strip().replace(" out of 5 stars", ""))
            if rating > 4:
                continue
            a_tag = card.find_all('a', class_="a-link-normal")
            if len(a_tag)>1:
                title = a_tag[1].text.strip()
                href = 'https://www.amazon.com' + a_tag[1].get('href')
            num_rev = a_row.find('span', class_="a-size-small")
            if num_rev:
                num_rev = num_rev.text.strip()
            book_titles.append(title)
            book_urls.append(href)
            book_num_reviews.append(num_rev)
        except Exception as e:
            continue




def find_child_categories(starting_url):
    visited_urls = set()

    # Create a queue to store URLs to visit
    queue = deque()
    queue.append(starting_url)

    while queue:
        # Dequeue a URL from the queue
        current_url = queue.popleft()

        # Skip if already visited
        if current_url in visited_urls:
            continue

        # Visit the URL
        driver.get(current_url)
        time.sleep(3.5)

        # Scroll down the page in middle speed
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)

        department = driver.find_element(By.CLASS_NAME, "_p13n-zg-nav-tree-all_style_zg-browse-group__88fbz")
        # Get the HTML code of the department element
        department_html = department.get_attribute("outerHTML")
        # Parse the HTML content
        soup_main = BeautifulSoup(department_html, 'html.parser')

        # Find the specific <div> with role="group" and the given class
        div_element = soup_main.find('div', role='group', class_='_p13n-zg-nav-tree-all_style_zg-browse-group__88fbz')

        if not div_element:
            continue
        
        selected = div_element.find('span', class_='_p13n-zg-nav-tree-all_style_zg-selected__1SfhQ')
        if selected:
            # Get the page source after waiting for dynamic content to load
            #html_content = driver.page_source
            scrape_data()
            driver.get(current_url + '&pg=2')
            time.sleep(3)
            scrape_data()
        else:
            all_subs = div_element.find_all('div', role='treeitem', class_='_p13n-zg-nav-tree-all_style_zg-browse-item__1rdKf _p13n-zg-nav-tree-all_style_zg-browse-height-large__1z5B8')
            for l in all_subs:
                try:
                    link_element = l.find('a')
                    href_value = link_element.get('href')
                    full_url = 'https://www.amazon.com' + href_value
                    if full_url not in visited_urls and full_url not in queue:
                        #print(full_url)
                        queue.append(full_url)
                except:
                    continue


        # Mark the current URL as visited
        visited_urls.add(current_url)

def write_excel(path):
    # Create DataFrame
    df = pd.DataFrame({
        'Book Title': book_titles,
        'Book URL': book_urls,
        'Number of reviews': book_num_reviews
    })
    # Write DataFrame to Excel
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        print("Data scraped successfully and saved.")
        print("Processing complete. Check the generated files.")

# Find all child categories starting from the main category
find_child_categories("https://www.amazon.com/Best-Sellers-Books-Self-Help/zgbs/books/4736/ref=zg_bs_nav_books_1")
#https://www.amazon.com/Best-Sellers-Books-Health-Fitness-Dieting/zgbs/books/10/ref=zg_bs_unv_books_2_4719_3
# Close the browser
driver.quit()

write_excel("Self.xlsx")