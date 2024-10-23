import csv
import argparse
import time
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_element_and_input(driver, xpath, value, timeout=30):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        element.clear()
        element.send_keys(value)
        return True
    except Exception as e:
        print(f"Failed to input value: {str(e)}")
        return False

def wait_for_element_and_click(driver, xpath, timeout=30):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        print(f"Failed to click element: {str(e)}")
        return False

def perform_checkin(driver, reservation_code, last_name, email):
    print(f"Performing check-in for: {last_name} - {reservation_code}")
    
    url = "https://www.volaris.com/"
    driver.uc_open_with_reconnect(url, 3)
    
    try:
        # Click on the "Pase de abordar" tab
        boarding_pass_tab_xpath = "//div[@role='tab' and contains(., 'Pase de abordar')]"
        if not wait_for_element_and_click(driver, boarding_pass_tab_xpath):
            raise Exception("Failed to click 'Pase de abordar' tab")
        
        # Wait for the form to load
        time.sleep(2)
        
        # Input reservation code
        reservation_code_xpath = "//input[@formcontrolname='reservationCode']"
        if not wait_for_element_and_input(driver, reservation_code_xpath, reservation_code):
            raise Exception("Failed to input reservation code")
        
        # Input last name
        last_name_xpath = "//input[@formcontrolname='lastName']"
        if not wait_for_element_and_input(driver, last_name_xpath, last_name):
            raise Exception("Failed to input last name")
        
        # Click the "Ir a mis viajes" button
        login_button_xpath = "//button[contains(@class, 'btn-large') and contains(., 'Ir a mis viajes')]"
        if not wait_for_element_and_click(driver, login_button_xpath):
            raise Exception("Failed to click 'Ir a mis viajes' button")
        
        # Wait for the check-in page to load
        time.sleep(10)
        
        # Click the "Enviar por correo electrónico" button
        email_button_xpath = "//button[contains(@class, 'btn-small') and contains(., 'Enviar por correo electrónico')]"
        if not wait_for_element_and_click(driver, email_button_xpath):
            raise Exception("Failed to click 'Enviar por correo electrónico' button")
        
        # Wait for the email modal to appear
        time.sleep(2)
        
        # Input email address
        email_input_xpath = "//input[@placeholder='Email']"
        if not wait_for_element_and_input(driver, email_input_xpath, email):
            raise Exception("Failed to input email address")
        
        # Click the "Enviar pase de abordar" button
        send_button_xpath = "//button[contains(@class, 'btn-large') and contains(., 'Enviar pase de abordar')]"
        if not wait_for_element_and_click(driver, send_button_xpath):
            raise Exception("Failed to click 'Enviar pase de abordar' button")
        
        # Wait for the email to be sent
        time.sleep(10)
        
        print(f"Check-in completed and boarding pass sent to {email} for {last_name} - {reservation_code}")
    except Exception as e:
        print(f"An error occurred during check-in: {str(e)}")
        driver.save_screenshot(f"error_{reservation_code}.png")

def main():
    parser = argparse.ArgumentParser(description="Perform Volaris check-in")
    parser.add_argument("--last_name", required=True, help="Passenger's last name")
    parser.add_argument("--reservation_code", required=True, help="Reservation code")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--date_of_birth", required=True, help="Date of birth (DD-MM-YYYY)")
    args = parser.parse_args()

    driver = Driver(uc=True)
    
    try:
        perform_checkin(driver, args.reservation_code, args.last_name, args.email)
        return True  # Return True to indicate success
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False  # Return False to indicate failure
    finally:
        driver.quit()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)  # Exit with 0 for success, 1 for failure