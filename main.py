from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import pandas as pd
import os
import requests
import re
import time


# Extract monetary values from the text
def extract_money(text):
    return re.findall(r'\$\d+(?:\.\d+)?|\d+ dollars|\d+ USD', text)


# Download image
def download_image(url, folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(folder, url.split("/")[-1])
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None


# User inputs to search news
search_phrase = input("Please insert the news you want to look for: ")
topic = input("Please insert the news topic: ")
time_period = int(input("Please insert the time period you want the news: "))


# Selenium setup
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Left it commented, so I could check the scrip working :)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Open Yahoo News
    driver.get("https://news.yahoo.com/")

    # Locate search field
    search_box = driver.find_element(By.NAME, "p")
    search_box.send_keys(search_phrase)
    search_box.send_keys(Keys.RETURN)

    # Wait for the page to loaf the results
    WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CSS_SELECTOR, "li.js-stream-content")))

    # Count number of results found
    results = driver.find_elements(By.CSS_SELECTOR, "li.js-stream-content")
    number_of_results = len(results)

    # Open the first link that is found
    first_article = results[0].find_element(By.TAG_NAME, "a")
    driver.execute_script("arguments[0].scrollIntoView();", first_article)
    time.sleep(1)  # Wait a second to guarantee the roll down happened
    driver.execute_script("arguments[0].click();", first_article)

    # Wait for the news page to load
    WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.TAG_NAME, "article")))

    # Extract info from the news
    title = driver.find_element(By.TAG_NAME, "h1").text
    date = driver.find_element(By.CSS_SELECTOR, "time").text

    description = ""
    try:
        description_element = driver.find_element(By.CSS_SELECTOR, "div.caas-body")
        description = description_element.text
    except Exception as e:
        print(f"Description not found: {e}")

    # Find news image
    try:
        image_element = driver.find_element(By.CSS_SELECTOR, "img")
        image_url = image_element.get_attribute("src")
        picture_filename = download_image(image_url, "output")
    except Exception as e:
        print(f"Image not found: {e}")
        picture_filename = None

    # Check for any monetary information on the news
    money_values = extract_money(title + " " + description)
    contains_money = len(money_values) > 0

    # Create a dataframe using pandas to save the data
    data = {
        "Title": [title],
        "Date": [date],
        "Description": [description],
        "Picture Filename": [picture_filename],
        "Number of Results": [number_of_results],
        "Contains Money": [contains_money],
        "Money Values": [", ".join(money_values)]
    }

    df = pd.DataFrame(data)

    # Save the dataframe into an Excel file
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file_path = os.path.join(output_folder, "news_data.xlsx")
    df.to_excel(output_file_path, index=False)

    print(f"Process completed successfully. Data saved in: '{output_file_path}'.")

except Exception as e:
    print(f"An error occurred during execution, please try again: {e}")

finally:
    # Close browser
    driver.quit()
