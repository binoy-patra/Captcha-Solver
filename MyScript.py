from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoAlertPresentException
from dateutil.relativedelta import relativedelta
import xlsxwriter
import requests
import pdfplumber
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import time
import sys
import json
import os
import math
from datetime import datetime
from bs4 import BeautifulSoup
import subprocess
import re
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from scraping_library import skip_zones
from scraping_library import countdown_timer
from scraping_library import packaging
from scraping_library import get_current_device_serial


# -------------------------------------------------------------------------------------------------------

# Returns the OTP value 
def load_otp():
    try:
        with open("Program_Files/Configration.json", "r") as file:
            data = json.load(file)
            return data.get("otp")
    except FileNotFoundError:
        return None
    

# Returns the OTP date value
def load_otp_date():
    try:
        with open("Program_Files/Configration.json", "r") as file:
            data = json.load(file)
            return data.get("otp_date")
    except FileNotFoundError:
        return None
    

# The function checks if the OTP for today is valid by comparing the current date with the date stored in the configuration file.
# Return True and OTP
def is_otp_valid():
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    otp_date = load_otp_date()
    otp = load_otp()
    # Check if the dates match
    if current_date == otp_date: # date
        print(f"The OTP for today is: {otp}")
        return True
    else:
        print("No atching OTP found for today's date.")
        return False
    

# ----------------------------------------------------------------------------------------------------------------


# Check if the website is under maintenance or not
def is_under_maintenance(driver, url):
    # Check if the page contains the specified text
    if "Module under maintenance" in driver.page_source:
        print(f"{url}  -  Module under maintenance")
    else:
        print(f"{url} link is Accessible ")
    return driver

# ----------------------------------------------------------------------------------------------------------------


# Extracts the first 6 characters from the URL of a CAPTCHA image to retrieve the verification code.
def get_verification(driver): # blue #3BB9FF & red #640A0A
    # Find all img elements inside the span with id "verimage" using XPath
    img_tags = driver.find_elements(By.XPATH, "//span[@id='verimage']//img")

    # Iterate through the img elements
    for img_tag in img_tags:
        src = img_tag.get_attribute("src")
        if "Captcha.jpg?r=" in src:
            six_chars = src.split('Captcha.jpg?r=')[1][:6]
            # print("Image Source:", src)
            print("verification Code: ", six_chars)
    return driver, six_chars


# Refreshes the page, handle Captcha And Login as Guest
def login(driver, mobile_no):

    retries = 0
    while retries < 3:
        try:
            driver.refresh()
            # If the refresh succeeds, break out of the loop
            break
        except TimeoutException:
            print("Timeout exception occurred. Retrying...")
            retries += 1
            # Add some delay before retrying to avoid overwhelming the server
            time.sleep(2)
    else:
        # If all retries fail, raise the TimeoutException
        raise TimeoutException("Exceeded maximum retries. Unable to refresh.")

    time.sleep(3)

    # Retry login process up to 3 times
    for attempt in range(3):
        try:

            try:
                alert = Alert(driver)
                alert.accept()
            except:
                pass

            driver, ver_code = get_verification(driver)

            if ver_code is None:
                return None

            otp = load_otp()  
            # Fill in login details and proceed
            driver.execute_script("document.getElementById('mobileNo').value='" + mobile_no + "'")
            time.sleep(1)
            driver.execute_script("document.getElementById('verification').value='" + ver_code + "'")
            time.sleep(1)
            driver.execute_script("document.getElementById('otp').value='" + otp + "'")
            time.sleep(2)
            driver.find_element("xpath", "//input[@value='Proceed']").click()

            # WebDriverWait block to wait for the presence of the element with ID "customSearchId"
            driver.find_element(By.ID, "custumSearchId").click()
            # If everything is successful, break out of the loop
            return driver

        except Exception as e:
            # Handle other exceptions while clicking 'Custom Search' button
            print(f"Attempt {attempt + 1} login or Custom Search button  -  Exception") # {e}")
            driver.get("https://www.ireps.gov.in/epsn/guestLogin.do")
            time.sleep(5)

    return driver



# Used to detect if the page contains a "No Results Found" message
def is_no_result_found_present_in_page(driver):
    # Get the page source using Selenium
    page_source = driver.page_source

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find the element containing the text
    result_element = soup.find('td', {'class': 'formLabel', 'style': 'color: #C00000'})

    # Check if the text is present
    if result_element and "No Results Found" in result_element.get_text():
        # Text found, continue the loop
        print("No Results Found. in the page.\n")
        return True, driver
    return False, driver


# ---------------------------------------------------------------------------------------------------------

# The function tries to download a PDF file from a given URL, saving it to 'Program_Files/tenderpdf/tender.pdf'

def download_pdf(url, retries=5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            with open('Program_Files/tenderpdf/tender.pdf', 'wb') as output_file:
                output_file.write(response.content)
            print("Download successful")
            return True
        except Exception as e:
            print(f"Attempt ({i+1}/{retries}) failed. Retrying... to Download")
            time.sleep(0.5)  # wait for 1 second before retrying
    else:
        print("All Download attempts failed.")
        return False

#----------------------------------------------------------------------------------------------------

# PDF Processing >> Text Extraction and Parsing >> Returning Data

def getpdfdata():
    file_path = os.path.join('Program_Files/tenderpdf', 'tender.pdf')

    # Extract PDF heading
    with pdfplumber.open(file_path) as pdf_heading:
        first_page = pdf_heading.pages[0]
        pdf_heading_text = first_page.extract_text()
        # Extract the first line assuming it contains the main heading
        dept_rly = pdf_heading_text.split('\n')[0].strip()


    # Extract table data
    with pdfplumber.open(file_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]
        # Extracting table data
        table = [[value for value in sublist if value is not None] for sublist in table]
        new_table = [row[i*2:i*2+2] for row in table for i in range(len(row) // 2)] + [row for row in table if len(row) <= 2]

        extracted_info = {}
        keys_to_extract = ['Name of Work', 'Bidding type', 'Tender Type', 'Bidding System', 'Tender Closing Date Time', 'Date Time Of Uploading Tender', 'Pre-Bid Conference Date Time', 'Advertised Value', 'Earnest Money (Rs.)', 'Contract Type']

        for item in new_table:
            if item[0] in keys_to_extract and len(item) > 1:
                extracted_info[item[0]] = item[1]

        # Extracting text data
        with pdfplumber.open(file_path) as pdf_text:
            page_text = pdf_text.pages[0].extract_text()
            tender_no_index = page_text.find("Tender No:")
            if tender_no_index != -1:
                tender_no_text = page_text[tender_no_index + len("Tender No:"):].strip()
                tender_no = tender_no_text.split('\n')[0].strip() if '\n' in tender_no_text else tender_no_text
                tender_no = tender_no[:-36]
        # Extracted information
        name_of_work = extracted_info.get('Name of Work', '')
        bidding_type = extracted_info.get('Bidding type', '')
        tender_type = extracted_info.get('Tender Type', '')
        bidding_system = extracted_info.get('Bidding System', '')
        tender_closing_date_time = extracted_info.get('Tender Closing Date Time', '')
        date_time_of_uploading_tender = extracted_info.get('Date Time Of Uploading Tender', '')
        pre_bid_conference_date_time = extracted_info.get('Pre-Bid Conference Date Time', '')
        advertised_value = extracted_info.get('Advertised Value', '')
        earnest_money = extracted_info.get('Earnest Money (Rs.)', '')
        contract_type = extracted_info.get('Contract Type', '')

        print(dept_rly, tender_no, name_of_work, bidding_type, tender_type, bidding_system, tender_closing_date_time, date_time_of_uploading_tender, pre_bid_conference_date_time, advertised_value, earnest_money, contract_type)

        return dept_rly, tender_no, name_of_work, bidding_type, tender_type, bidding_system, tender_closing_date_time, date_time_of_uploading_tender, pre_bid_conference_date_time, advertised_value, earnest_money, contract_type

# --------------------------------------------------------------------------------------------------

# 

def tender(driver, script_number, script_name, program_file_dir):
    driver, script_number, script_name, program_file_dir = driver, script_number, script_name, program_file_dir
    for _ in range(3):  # Try the action three times
        try:
            # Locate the dropdown element using an appropriate selector
            dropdown_element = driver.find_element(By.ID, "organization")
            # Create a Select object and interact with the dropdown
            select = Select(dropdown_element)

            # Select option by value
            select.select_by_value(script_number)

            time.sleep(1)

            # Double select organization
            # Check if the element is still present
            if dropdown_element:
                driver.execute_script("document.getElementById('organization').value='"+ script_number +"'")
            else:
                print("Element with ID 'organization' not found")
            
            # If everything is successful, break out of the loop
            break

        except Exception as e:
            # Handle other exceptions while clicking organization dropdown button
            print(f"organization dropdown  -  Exception")
            driver.refresh()
            time.sleep(2)


    """Stores all options in a dictionary. then print the zone list"""

    time.sleep(2)
    railway_zone_dropdown = Select(driver.find_element(By.XPATH, "//*[@id='railwayZone']"))
    # print(railway_zone_dropdown)
    time.sleep(2)
    options = railway_zone_dropdown.options
    # print(options)

    options_dict = {}
    for option in options:
        value = option.get_attribute("value")
        text = option.get_attribute("innerText")
        options_dict[value] = text

    # Print the options dictionary
    print("\n--------- ZONE LIST ---------")
    for zone in options_dict.values():
        if zone in skip_zones:
            continue  # Skip the current iteration and move to the next one
        print(zone)

    """ End """

    
    for zone_number, zone in options_dict.items():
        last_tender = False
        if zone in skip_zones: # this condition skip all zones inside skip_zones
            continue  # Skip the current iteration and move to the next one
        print(f"\nScraping ZONE -> {zone}")
        print("----------------")

        for _ in range(3):  # Try the action three times
            try:
                # filling search criteria
                driver.execute_script("document.getElementById('organization').value='"+ script_number +"'")
                driver.execute_script("document.getElementById('workArea').value='WT'") # works
                driver.execute_script("document.getElementById('railwayZone').value='"+ zone_number +"'")
                driver.execute_script("document.getElementById('tenderType').value=2") # open
                driver.execute_script("document.getElementById('tenderStage').value=1") # published
                driver.execute_script("document.getElementsByName('selectDate')[0].value = 'TENDER_OPENING_DATE'") # Tender Closing Date
                # Get the current date
                current_date = datetime.now()
                # Add four months to the current date
                four_months_later = current_date + relativedelta(months=4)
                # Format the date as a string (optional)
                formatted_date = four_months_later.strftime("%d/%m/%Y")
                driver.execute_script("document.getElementById('ddmmyyDateformat2').value='" + formatted_date + "'")
                time.sleep(0.5)
                driver.find_element(By.XPATH, "//input[@value='Show Results']").click()
                # If everything is successful, break out of the loop
                break

            except Exception as e:
                # Handle other exceptions while clicking 'Custom Search' button
                print(f"Show Results button  -  Exception")
                driver.refresh()
                time.sleep(2)

        # checkpoint
        # time.sleep(500)
        # return "False"
    
        result, driver = is_no_result_found_present_in_page(driver)
        packages = packaging()
        if result:
            continue

        try:
            time.sleep(3.5)
            
            # Get the page source and parse it with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all 'b' tags within 'tr' tags
            b_tags = soup.find_all('b')
            
            # Iterate over the 'b' tags
            for i in range(len(b_tags)):
                # If the 'b' tag contains "Tender search results"
                if "Tender search results" in b_tags[i].text:
                    # If there is a next 'b' tag, print it
                    if i + 1 < len(b_tags):
                        tender_count = b_tags[i + 1].text
                        print("Tender search results ", tender_count)
                    break

        except Exception as e:
            print(f"An error occurred: Tender search results")
            break

        # # Get the page source and parse it with BeautifulSoup
        # soup = BeautifulSoup(driver.page_source, 'html.parser')
        # # Find all 'b' tags within 'tr' tags
        # b_tags = soup.find_all('b')
        # # Iterate over the 'b' tags
        # for i in range(len(b_tags)):
        #     # If the 'b' tag contains "Tender search results"
        #     if "Tender search results" in b_tags[i].text:
        #         # If there is a next 'b' tag, print it
        #         if i+1 < len(b_tags):
        #             tender_count = b_tags[i+1].text
        #             print("Tender search results ", tender_count)
        #         break


        # Get the current date and time
        current_date = datetime.now()
        # Format the date and time string
        fname = current_date.strftime("%d-%m-%Y %H_%M_%S")
        # Create a file name using the value and the formatted date and time
        file_name = f'{zone}_{fname}.xlsx'
        # Create a file path for the new Excel workbook
        file_path = os.path.join(program_file_dir, script_name, file_name)
        # Create a new Excel workbook and a worksheet within it
        workbook = xlsxwriter.Workbook(file_path)
        worksheet1 = workbook.add_worksheet("ListOfTenders")
        # Write the column headers in the worksheet
        headers = ["Zone", "Dept.", "Tender No.", "Tender Title", "Type", "Due Date/Time", "Due Days", "Advertised Value", "Doc Link", "Bidding type", "Bidding System", "Date Time Of Uploading Tender", "Pre-Bid Conference Date Time", "Earnest Money (Rs.)", "Contract Type"]
        for index, header in enumerate(headers):
            worksheet1.write(0, index, header)


        # Calculate the number of pages based on the tender count
        tender_count = int(tender_count)
        decimal_number = tender_count / 25
        # Round up to the nearest integer to get the page count
        page_count = math.ceil(decimal_number)
        # Print the number of pages
        print("Pages = ", page_count)


        cnt = 1
        k = 0
        # Loop through all the pages
        while cnt <= page_count:
            for _ in range(3):  # Try the action three times
                try:
                    # If the element is found, you can perform further actions here
                    a_tags = driver.find_elements(By.CSS_SELECTOR, "a[onclick]")      
                    # If everything is successful, break out of the loop
                    break
                except Exception as e:
                    # Handle other exceptions while clicking 'Custom Search' button
                    print(f"a_tags tender link - Exception")
                    time.sleep(2)
                    continue

            if not a_tags:
                break

            filtered_a_tags = [tag for tag in a_tags if 'postRequestNewWindow(\'/epsn/nitViewAnonyms/rfq/nitPublish.do?' in tag.get_attribute('onclick')]

            # Get the initial window handle
            initial_handle = driver.current_window_handle
            for a_tag in filtered_a_tags:
                k += 1
                print('\r' + "Tender  : " + str(k) + " ", end='')

                try:
                    a_tag.click()
                    # WebDriverWait(driver, 20).until(lambda x: x.execute_script('return document.readyState') == 'complete')
                except Exception as e:
                    print("Result page a_tags tender link click - Exception")
                    driver.switch_to.window(initial_handle)
                    time.sleep(2)
                    continue
            

                handles = driver.window_handles
                time.sleep(0.25)
                driver.switch_to.window(handles[1])

                # # checkpoint
                # temp_url = driver.current_url
                # print(" >> ", temp_url)


                try:
                    time.sleep(1)
                    download_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Download Tender Doc. (Pdf)')]")
                    download_button.click()
                except Exception as e:
                    # Handle other exceptions while clicking 'Custom Search' button
                    print(f"Download Tender Doc. (Pdf) button - Exception")
                    for window_handle in filter(lambda handle: handle != initial_handle, handles):
                        driver.switch_to.window(window_handle)
                        time.sleep(0.25)
                        driver.close()
                    driver.switch_to.window(initial_handle)
                    time.sleep(2)
                    continue

                handles = driver.window_handles
                time.sleep(0.25)
                driver.switch_to.window(handles[2])


                # # Define a function to wait for the page to fully load
                def page_fully_loaded(driver):
                    return driver.execute_script("return document.readyState") == "complete"

                # # Wait for the page to fully load
                WebDriverWait(driver, 10).until(page_fully_loaded)

                pdf_url = driver.current_url
                print(" ", pdf_url)

                # # Execute JavaScript to get the current window's URL
                window_url = driver.execute_script("return window.location.href;")
                url_pattern = re.compile(r'^https:\/\/www\.ireps\.gov\.in\/ireps\/works\/pdfdocs\/.*\.pdf$')

                while True:
                    if url_pattern.match(pdf_url):
                        print("URL is valid. ", pdf_url)
                        break
                    else:
                        print("URL is not valid.")
                        time.sleep(0.25)
                        pdf_url = driver.current_url
                        continue

                if pdf_url.endswith(".pdf"):
                    download_pdf(pdf_url)
                else:
                    for window_handle in filter(lambda handle: handle != initial_handle, handles):
                        driver.switch_to.window(window_handle)
                        time.sleep(0.25)
                        driver.close()
                    driver.switch_to.window(initial_handle)
                    continue

                dept_rly, tender_no, name_of_work, bidding_type, tender_type, bidding_system, tender_closing_date_time, date_time_of_uploading_tender, pre_bid_conference_date_time, advertised_value, earnest_money, contract_type = getpdfdata()

                try:
                    # Calculate due_days
                    closing_datetime = datetime.strptime(tender_closing_date_time, '%d/%m/%Y %H:%M')
                    uploading_datetime = datetime.strptime(date_time_of_uploading_tender, '%d/%m/%Y %H:%M')
                    due_days = (closing_datetime - uploading_datetime).days
                except ValueError as e:
                    due_days = " " 
                    pass

                worksheet1.write(k, 0, zone)
                worksheet1.write(k, 1, dept_rly)
                worksheet1.write(k, 2, tender_no)
                worksheet1.write(k, 3, name_of_work)
                worksheet1.write(k, 4, tender_type)
                worksheet1.write(k, 5, tender_closing_date_time)
                worksheet1.write(k, 6, due_days)
                worksheet1.write(k, 7, advertised_value)
                worksheet1.write(k, 8, pdf_url)
                worksheet1.write(k, 9, bidding_type)
                worksheet1.write(k, 10, bidding_system)
                worksheet1.write(k, 11, date_time_of_uploading_tender)
                worksheet1.write(k, 12, pre_bid_conference_date_time)
                worksheet1.write(k, 13, earnest_money)
                worksheet1.write(k, 14, contract_type)

                # Switch back to the initial window
                for window_handle in filter(lambda handle: handle != initial_handle, handles):
                    driver.switch_to.window(window_handle)
                    time.sleep(0.25)
                    driver.close()
                driver.switch_to.window(initial_handle)

                if k == tender_count:
                    last_tender = True
                else:
                    last_tender = False

            print("\n")

            if last_tender == True:
                break
            else:
                try:
                    driver.find_element(By.XPATH, F"//a[text()='{cnt + 1}']").click()
                except Exception as e:
                    # print(f"Page {cnt + 1} button  -  Exception")
                    break

            if i % 10 == 0:
                print("\n")
                try:
                    driver.find_element(By.XPATH, f"//a[font[text()='next']]").click()
                except Exception as e:
                    print(f"Element with text 'next' not found")
                    break

            cnt += 1

        # Create the folder if it doesn't exist
        file_path = f"{program_file_dir}/{script_name}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        # Close the workbook and print a message
        workbook.close()
        print("Zone data Saved.")

    return "True"




#-------------------------------------------------------------------------------------------
    
# extract message from adb device connected
# Extracting SMS message from an ADB-connected device
def get_sms_message():
    message = ""
    device_serial = get_current_device_serial()
    command = f'adb -s {device_serial} shell content query --uri content://sms/inbox'
    try:
        output = subprocess.check_output(command, shell=True, encoding='utf-8').strip()
        lines = output.split('\n')
        # print(lines)
        for line in lines:
            # Extract the date from the message
            match_date = re.search(r'date=(\d+)', line)
            if match_date:
                timestamp = int(match_date.group(1)) / 1000  # Convert from milliseconds to seconds
                message_date = datetime.fromtimestamp(timestamp).date()
                # Compare the message date with today's date
                if message_date == datetime.today().date():  # Use datetime.today() instead of datetime.date.today()
                    # print(line) 
                    if 'IREPS' in line:
                        match_otp = re.search(r'body=(\d{6})', line)
                        if match_otp:
                            six_digits = match_otp.group(1)
                            print(f"OTP: {six_digits}")

                            # Get the current working directory
                            current_path = os.getcwd()

                            # File name and path
                            file_name = 'Program_Files/Configration.json'

                            file_path = os.path.join(current_path, file_name)
                            # print(file_path)

                            # print(type(message_date))
                            # countdown_timer(10)

                            # Read the JSON file
                            with open(file_path, 'r') as file:
                                config_data = json.load(file)

                            # Update the OTP date and OTP
                            config_data['otp_date'] = message_date.strftime("%Y-%m-%d")
                            config_data['otp'] = six_digits

                            # Write the updated data back to the file
                            with open(file_path, 'w') as file:
                                json.dump(config_data, file, indent=4)

                            # with open(otp_full_path, "w") as file:
                            #     file.write(f"Date: {message_date}\n")
                            #     file.write(f"OTP: {six_digits}\n")
                            return False
                        else:
                            print("Pattern not found.")
                    else:
                        message = "Messages not yet received; retring to access the OTP"
        print(message)               
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return True
    

# generate OTP
# Generating and submitting an OTP

def generate_otp(driver, mobile_no):
    driver.refresh()
    time.sleep(3)
    
    # print("Current Mobile No. :", mobile_no)
    driver, Verification_code = get_verification(driver)
    # mobile_no = input("Enter 10 digit Mobile No: ")
    driver.execute_script("document.getElementById('mobileNo').value='" + mobile_no + "'")

    driver.execute_script("document.getElementById('verification').value='" + Verification_code + "'")
    

    driver.find_element("xpath", "//input[@value='Get OTP']").click()
    time.sleep(3)

    try:
        # Check if an alert is present
        alert = driver.switch_to.alert
        print("Alert Text:", alert.text)
        alert.accept()  # Close the alert (Accept/Dismiss)
    except NoAlertPresentException:
        print("No alert present after clicking 'Get OTP'")
    return driver


# ----------------------------------------------------------------------------

def main():
    
    mail_triger = False
    chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                        # and if it doesn't exist, download it automatically,
                                        # then add chromedriver to path

    org_number, org_name, mobile_no, otp_file_location, program_file_dir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[4]
    # print(org_number, org_name, mobile_no, otp_file_location)

    options = Options()
    options.add_argument("--disable-application-cache")  # Disable application cache
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument("--headless")  
    options.add_argument("--disable-gpu")  
    options.add_argument("--log-level=3")
    # # Set the download path
    # options.add_experimental_option("prefs", {
    #     "download.default_directory": initial_download,
    #     "download.prompt_for_download": False,
    #     "download.directory_upgrade": True,
    #     "safebrowsing.enabled": True
    #     })

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)  
    driver.implicitly_wait(10) # Wait for a few seconds to see the results  

    # Open a website
    # Open the URL and wait for the page title to be "IREPS - Guest Login"
    url = "https://www.ireps.gov.in/epsn/guestLogin.do"
    

    while True:
        try:
            driver.get(url)
            break # break the loop if no exception occurs
        except Exception as e:
            print(f"{url} - url exception") # - {e}") # print the exception message
            print("Retrying...") # print a retry message
            time.sleep(2)

    driver = is_under_maintenance(driver, url)
    print("Current Mobile NO. ", mobile_no)

    if is_otp_valid():
        driver = login(driver, mobile_no)
        mail_triger = tender(driver, org_number, org_name, program_file_dir)
    else:
        driver = generate_otp(driver, mobile_no)
        countdown_timer("generate_otp", 60)

        while get_sms_message():
            countdown_timer("get_sms_message", 20)
            get_sms_message()

        driver = login(driver, mobile_no)
        mail_triger = tender(driver, org_number, org_name, program_file_dir)
    print(f"\n\nExeting.... From {org_name}.\n\n")




    countdown_timer("Closing the browser window", 3)
    # Close the browser window
    driver.quit()

    # Get the current working directory
    current_path = os.getcwd()
    # File name and path
    file_name = 'Program_Files/Configration.json'
    file_path = os.path.join(current_path, file_name)
    # Read the JSON file
    with open(file_path, 'r') as file:
        config_data = json.load(file)
    # Update the email_flag
    config_data['email_flag'] = mail_triger
    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(config_data, file, indent=4)
    


# Check if the script is being run directly
if __name__ == "__main__":
    main()
    sys.exit()  # This will exit the Python interpreter
    
