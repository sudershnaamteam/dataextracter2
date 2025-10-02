import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------
# Helper: sanitize filename
# ---------------------------
def sanitize_filename(s: str) -> str:
    return re.sub(r'[\\\/:*?"<>|]', '', s.strip().replace(" ", "_")) or "output"

# ---------------------------
# Scraper Function
# ---------------------------
def main():
    keyword = input("🔍 Enter keyword to search on Google Maps: ")

    # Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Open Google Maps
    driver.get("https://www.google.com/maps")
    time.sleep(5)

    # Search keyword
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)
    time.sleep(8)

    # Scroll results
    try:
        scrollable_div = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Results for')]")
    except:
        scrollable_div = driver.find_element(By.XPATH, "//div[contains(@role,'main')]")

    prev_height, same_scroll_count = 0, 0
    while True:
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
        time.sleep(2)
        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        if new_height == prev_height:
            same_scroll_count += 1
            if same_scroll_count >= 2:
                break
        else:
            same_scroll_count = 0
        prev_height = new_height

    # Collect profile links
    results = driver.find_elements(By.XPATH, "//a[contains(@href, '/place/')]")
    profile_links = list(dict.fromkeys([r.get_attribute("href") for r in results if r.get_attribute("href")]))
    print(f"🔍 Total Profiles Found: {len(profile_links)}")

    # Save CSV
    filename = f"{sanitize_filename(keyword)}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header (dynamic fields)
        header = ["Name", "Profile Link", "Details"]
        writer.writerow(header)

        for idx, link in enumerate(profile_links, start=1):
            driver.get(link)
            time.sleep(5)

            # Name
            try:
                name = driver.find_element(By.XPATH, '//h1[contains(@class,"fontHeadlineLarge")]').text
            except:
                name = ""

            # Extract details (icon-based rows)
            details = []
            try:
                info_blocks = driver.find_elements(By.XPATH, '//button[contains(@class,"hh2c6") or contains(@data-item-id,"")]')
                for block in info_blocks:
                    txt = block.text.strip()
                    if txt:
                        details.append(txt)
            except:
                pass

            # Join all details
            all_details = " | ".join(details)

            # Write row
            writer.writerow([name, link, all_details])
            print(f"✅ {idx}. {name} | {all_details[:60]}...")

    print(f"📁 Data saved in {filename}")
    driver.quit()


if __name__ == "__main__":
    main()
