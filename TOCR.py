import os
import pytesseract
from PIL import Image
import pandas as pd

# Set the correct path to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\Personal Documents\CS\Tesseract\tesseract.exe'

# Set the TESSDATA_PREFIX environment variable if needed
os.environ['TESSDATA_PREFIX'] = r'D:\Personal Documents\CS\Tesseract'

# Path to the folder containing the images
image_folder = r'D:\Personal Documents\CS\images'  # Replace with your folder path on D drive

# Initialize an empty list to hold the image names and extracted text
data = []

# Loop through all images in the folder (assuming all files in the folder are images)
for image_name in os.listdir(image_folder):
    image_path = os.path.join(image_folder, image_name)

    # Check if the file is an image (optional check based on file extension)
    if image_name.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp')):
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Perform OCR on the image to extract text
            extracted_text = pytesseract.image_to_string(img)
            
            # Append the result (image name and extracted text) to the data list
            data.append([image_name, extracted_text])
        except Exception as e:
            # If there's an error, log it
            print(f"Error processing {image_name}: {e}")

# Create a pandas DataFrame from the extracted data
df = pd.DataFrame(data, columns=['Image Name', 'Extracted Text'])

# Save the DataFrame to an Excel file
excel_output = 'extracted_texts.xlsx'
df.to_excel(excel_output, index=False)

print(f"Data has been saved to {excel_output}")
