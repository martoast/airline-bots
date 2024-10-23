import csv
import argparse
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

def safe_find_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        print(f"Element not found: {by}={value}")
        return None

def safe_click(driver, element):
    try:
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        print(f"Failed to click element: {str(e)}")

def handle_error_dialog(driver, max_attempts=3):
    close_button_xpath = "/html/body/app-dialog/div/div/app-notification-dialog/div/button"
    accept_button_xpath = "/html/body/app-dialog/div/div/app-notification-dialog/div/div[4]/button"

    for attempt in range(max_attempts):
        try:
            # Check if the dialog is present
            dialog = safe_find_element(driver, By.CSS_SELECTOR, "app-dialog", timeout=5)
            if not dialog:
                print("No error dialog found. Proceeding.")
                return True

            # Give the modal a moment to fully render
            time.sleep(2)
            
            # Try to close using the 'x' button first
            close_button = safe_find_element(driver, By.XPATH, close_button_xpath, timeout=5)
            if close_button:
                safe_click(driver, close_button)
            else:
                # If 'x' button is not found, try the 'Aceptar' button
                accept_button = safe_find_element(driver, By.XPATH, accept_button_xpath, timeout=5)
                if accept_button:
                    safe_click(driver, accept_button)
                else:
                    print("Neither close nor accept button found in error dialog")
                    return False
            
            # Wait for the dialog to disappear
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "app-dialog"))
            )
            
            print("Error dialog closed successfully")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} to handle error dialog failed: {str(e)}")
            time.sleep(2)  # Wait before retrying
    
    print("Failed to handle error dialog after maximum attempts")
    return False

def perform_checkin(driver, last_name, reservation_code, email):
    url = f'https://www.vivaaerobus.com/es-mx/check-in?pnr={reservation_code}&lastName={last_name}'
    
    print(f"Performing check-in for: {url}")
    
    driver.get(url)
    
    try:
        # Wait for the check-in page to load
        safe_find_element(driver, By.CSS_SELECTOR, "app-check-in-journey")
        
        # Check if check-in is already completed
        checkin_completed = safe_find_element(driver, By.XPATH, "//span[contains(text(), 'Check-in completado')]")
        
        if not checkin_completed:
            # Perform check-in process (omitted for brevity, keep your existing check-in logic here)
            pass
        else:
            print("Check-in already completed")
        
        # Wait for the confirmation page to load
        boarding_passes_button = safe_find_element(driver, By.XPATH, "//div[contains(@class, 'completed-btn')]/span[contains(text(), 'Pases de abordar')]")
        if boarding_passes_button:
            safe_click(driver, boarding_passes_button)
        else:
            print("Boarding passes button not found")
            return
        
        # Wait for the download button to appear
        download_button = safe_find_element(driver, By.XPATH, "//div[contains(@class, 'pass-available')]")
        if download_button:
            safe_click(driver, download_button)
        else:
            print("Download button not found")
            return
        
        # Handle potential error dialog
        dialog_handled = handle_error_dialog(driver)
        if dialog_handled:
            print("Error dialog handled or not present, proceeding with download")
        else:
            print("Failed to handle error dialog, but continuing with the process")
        
        # Wait for the modal to appear and fully load
        time.sleep(5)  # Give the modal time to fully render
        
       # Select and click the email option using the specific text content
        email_option_xpath = "//*[contains(text(), 'Enviar por correo')]"
        email_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, email_option_xpath))
        )
        if email_option:
            safe_click(driver, email_option)
            print("Clicked 'Enviar por correo' button")
            
            # Wait for the email input field to appear
            email_input_xpath = "//app-modal[13]/div[1]/div/div/div[2]/div[3]/form/div/input"
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, email_input_xpath))
            )
            if email_input:
                print("Email input field found")
                # Clear the field and enter the email
                driver.execute_script("arguments[0].value = '';", email_input)
                email_input.send_keys(email)
                print(f"Entered email: {email}")
                
                # Add a delay before clicking the send button
                time.sleep(3)
                
                # Click the send button using the correct XPath
                send_button_xpath = "//button[contains(@class, 'viva-btn') and contains(., 'Enviar')]"
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, send_button_xpath))
                )
                
                if send_button:
                    safe_click(driver, send_button)
                    print("Clicked 'Enviar' button")
                    # Wait for the email to be sent
                    time.sleep(15)  # Wait for 15 seconds to ensure the email is sent
                    print("Boarding passes sent to email")
                else:
                    print("Send button not found or not clickable")
            else:
                print("Email input field not found")
        else:
            print("Email option not found or not clickable")
    except Exception as e:
        print(f"Error during check-in: {str(e)}")
        # Capture a screenshot when an error occurs
        driver.save_screenshot(f"error_{reservation_code}.png")

def main():
    parser = argparse.ArgumentParser(description="Perform Viva Aerobus check-in")
    parser.add_argument("--last_name", required=True, help="Passenger's last name")
    parser.add_argument("--reservation_code", required=True, help="Reservation code")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--date_of_birth", required=True, help="Date of birth (DD-MM-YYYY)")
    args = parser.parse_args()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        success = perform_checkin(driver, args.last_name, args.reservation_code, args.email)
        return success
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)  # Exit with 0 for success, 1 for failure