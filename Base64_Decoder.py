""" 
Flow of the code : 
1. URL >> SEARCH 
2. Find the Capcha by Id/Name: 'captchaImage'
3. Extract the Base64 Encoded String 
4. Decode the string 
5. Save as it is as PNG File
"""
import base64
import requests
from bs4 import BeautifulSoup

# Define the URL of the website
url = "https://etenders.gov.in/eprocure/app?page=FrontEndAdvancedSearch&service=page"

# Send a GET request to fetch the page content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the captcha image by its 'id' or 'name'
    captcha_image_tag = soup.find('img', {'id': 'captchaImage'})  # Can also use 'name': 'captchaImage'
    
    if captcha_image_tag:
        # Get the base64 encoded string from the 'src' attribute
        captcha_base64 = captcha_image_tag['src']
        
        # Check if the 'src' attribute contains the base64 encoded string
        if captcha_base64.startswith("data:image/png;base64,"):
            # Extract the base64 string (remove the prefix)
            base64_str = captcha_base64.split(",")[1]
            
            # Decode the base64 string to binary data
            img_data = base64.b64decode(base64_str)
            
            # Save the binary data as a PNG image
            with open("decoded_captcha_image.png", "wb") as f:
                f.write(img_data)
            
            print("Captcha image has been saved as 'decoded_captcha_image.png'.")
        else:
            print("The captcha image 'src' does not contain a valid base64 encoded string.")
    else:
        print("Captcha image not found on the page.")
else:
    print(f"Failed to fetch the webpage. Status code: {response.status_code}")
