from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os

# Set up Chrome options for full screen
chrome_options = Options()
chrome_options.add_argument("--start-fullscreen")

# URLs and configuration
urls = [
    "https://eprocure.gov.in/eprocure/app?page=FrontEndAdvancedSearch&service=page",
    "https://etenders.gov.in/eprocure/app?page=FrontEndAdvancedSearch&service=page"
]
captcha_img_id = "captchaImage"
refresh_button_id = "captcha"

# Folder to save the CAPTCHA images
save_folder = r"D:\Personal Documents\CS\images"  # Use raw string for Windows path
os.makedirs(save_folder, exist_ok=True)

# Set up the WebDriver (replace 'chromedriver' with the path to your ChromeDriver)
driver = webdriver.Chrome(options=chrome_options)

# Variable to keep track of the screenshot number
screenshot_number = 81

# Loop through each URL
for url in urls:
    driver.get(url)
    time.sleep(3)  # Allow the page to load completely
    
    # Take 10 CAPTCHA screenshots per URL
    for _ in range(10):
        # Locate the CAPTCHA image and take a screenshot
        
        captcha_image = driver.find_element(By.ID, captcha_img_id)
        screenshot_path = os.path.join(save_folder, f"captcha{screenshot_number}.png")
        captcha_image.screenshot(screenshot_path)
        print(f"Screenshot {screenshot_number} taken and saved as {screenshot_path}")
        
        # Increment the screenshot number
        screenshot_number += 1
        
        # Locate the refresh button and click it to load a new CAPTCHA
        refresh_button = driver.find_element(By.ID, refresh_button_id)
        refresh_button.click()
        time.sleep(2)  # Wait a moment for the new CAPTCHA to load
    
# Close the browser
driver.quit()
