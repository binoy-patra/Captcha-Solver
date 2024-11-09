import re
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import easyocr
import pandas as pd
import os

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Set the path to tesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\Personal Documents\CS\Tesseract\tesseract.exe'

image_folder = r'D:\Personal Documents\CS\images'  # Replace with your folder path
data = []

# Regex pattern to keep only alphanumeric characters
regex_pattern = re.compile('[^a-zA-Z0-9]')

# Loop through all images in the folder
for image_name in os.listdir(image_folder):
    image_path = os.path.join(image_folder, image_name)
    
    if image_name.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp')):
        try:
            # Open the image
            img = Image.open(image_path)

            # Convert to grayscale for better OCR
            img = img.convert("L")

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)

            # Apply a filter to reduce noise
            img = img.filter(ImageFilter.MedianFilter())

            # Perform OCR using Tesseract (Output 1)
            extracted_text_tesseract = pytesseract.image_to_string(img)
            
            # Use regex to remove any non-alphanumeric characters
            cleaned_text_tesseract = re.sub(regex_pattern, '', extracted_text_tesseract)

            # Perform OCR using EasyOCR (Output 2)
            extracted_text_easyocr = reader.readtext(image_path, detail=0)
            extracted_text_easyocr = ' '.join(extracted_text_easyocr)
            
            # Use regex to clean EasyOCR output
            cleaned_text_easyocr = re.sub(regex_pattern, '', extracted_text_easyocr)

            # Append results to data list
            data.append([image_name, cleaned_text_tesseract, cleaned_text_easyocr])

        except Exception as e:
            print(f"Error processing {image_name}: {e}")

# Create a pandas DataFrame from the extracted data
df = pd.DataFrame(data, columns=['Image Name', 'Output 1 (Tesseract)', 'Output 2 (EasyOCR)'])

# Save the DataFrame to an Excel file
excel_output = 'extracted_texts_with_regex.xlsx'
df.to_excel(excel_output, index=False)

print(f"Data has been saved to {excel_output}")
