import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the page
url = 'https://eprocure.gov.in/epublish/app?page=FrontEndParticipatingSites&service=page'

# Send a request to the website
response = requests.get(url)
response.raise_for_status()  # Check if the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find the table on the page
table = soup.find('table', class_='list_table')  # Ensure the correct table is selected

# Check if table is found
if table is None:
    print("Table not found!")
else:
    print("Table found!")

# Initialize lists to store scraped data
eProcurement_sites = []
links = []

# Section headers to skip
section_headers = [
    "Central Government eProcurement Links",
    "Public Sector Units/Others eProcurement links",
    "State Government/UT eProcurement Portal links"
]

# Flag to track whether we're in a valid data section
in_section = False

# Loop through all rows in the table
for row in table.find_all('tr'):
    columns = row.find_all('td')

    # Skip empty rows or irrelevant rows
    if not columns:
        continue

    # Handle section headers (these rows contain just one column, like "Central Government eProcurement Links")
    row_text = [col.get_text(strip=True) for col in columns]
    if len(columns) == 1 and row_text[0] in section_headers:
        print(f"Found section header: {row_text[0]}")
        # Set flag to indicate we are in a valid data section
        in_section = True
        continue  # Skip section header row

    # Skip the first header row with column names
    if len(columns) == 3 and columns[0].get_text(strip=True) == "S.No":
        continue  # Skip the header row

    # Now check for valid data rows (rows with 3 columns and in_section flag active)
    if len(columns) == 3 and in_section:
        serial_number = columns[0].get_text(strip=True)
        eProcurement_site = columns[1].get_text(strip=True)

        # Extract the link safely by checking for the <a> tag
        link_tag = columns[2].find('a')
        link = link_tag['href'] if link_tag else None

        # Ensure data is valid
        if serial_number and eProcurement_site and link:
            print(f"Found site: {eProcurement_site}, Link: {link}")
            eProcurement_sites.append(eProcurement_site)
            links.append(link)

# Check if there is any data to print
if len(eProcurement_sites) == 0:
    print("No valid data found.")

# Create a DataFrame for better visualization
df = pd.DataFrame({
    'eProcurement Site': eProcurement_sites,
    'Link': links
})

# Display the DataFrame
print(df)

# Optional: Save the data to an Excel file
df.to_excel('eProcurement_sites.xlsx', index=False)

print("Data has been successfully saved to eProcurement_sites.xlsx")