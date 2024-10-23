import csv
import argparse
import time
import logging
from datetime import datetime
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_button_and_click(driver, xpath, timeout=30):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].click();", element)
        logging.info(f"Clicked button: {xpath}")
        return True
    except Exception as e:
        logging.error(f"Failed to click button: {xpath}. Error: {str(e)}")
        return False

def check_checkbox(driver, name, timeout=30):
    try:
        checkbox = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, name))
        )
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)
        logging.info(f"Checked checkbox: {name}")
        return True
    except Exception as e:
        logging.error(f"Failed to check checkbox: {name}. Error: {str(e)}")
        return False

def parse_date(date_string):
    """
    Parse the date string into day, month, year.
    Expects format: DD-MM-YYYY
    """
    try:
        date = datetime.strptime(date_string, "%d-%m-%Y")
        return date.day, date.month, date.year
    except ValueError as e:
        logging.error(f"Error parsing date: {e}")
        raise

def input_date_of_birth(driver, date_of_birth, timeout=30):
    try:
        day, month, year = parse_date(date_of_birth)
        
        # Select day
        day_select = Select(WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "bday bday-day"))
        ))
        day_select.select_by_value(str(day))
        logging.info(f"Selected day: {day}")
        
        # Select month
        month_select = Select(WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "bday bday-month"))
        ))
        month_select.select_by_value(str(month))
        logging.info(f"Selected month: {month}")
        
        # Select year
        year_select = Select(WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "bday bday-year"))
        ))
        year_select.select_by_value(str(year))
        logging.info(f"Selected year: {year}")
        
        logging.info(f"Input date of birth: {date_of_birth}")
        return True
    except Exception as e:
        logging.error(f"Failed to input date of birth: {date_of_birth}. Error: {str(e)}")
        return False

def input_email(driver, email, timeout=30):
    try:
        email_input = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.clear()
        email_input.send_keys(email)
        logging.info(f"Input email: {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to input email: {email}. Error: {str(e)}")
        return False

def check_for_error_message(driver):
    try:
        error_message = driver.find_element(By.XPATH, "//div[contains(@class, 'error-message')]")
        if error_message:
            logging.error(f"Error message found: {error_message.text}")
            return True
    except NoSuchElementException:
        return False
    return False

def perform_checkin(driver, last_name, reservation_code, date_of_birth, email):
    logging.info(f"Performing check-in for: {last_name} - {reservation_code}")
    
    url = "https://aeromexico.com/es-mx/check-in"
    driver.uc_open_with_reconnect(url, 3)
    
    try:
        # Wait for the check-in form to load and fill it
        driver.wait_for_element("#ticketNumber", timeout=10)
        driver.type("#ticketNumber", reservation_code)
        driver.type("#lastName", last_name)
        logging.info("Filled in reservation details")
        
        # Click the "Buscar reservación" button
        if not wait_for_button_and_click(driver, "//button[@aria-label='Buscar reservación' and contains(@class, 'Btn--filledRed')]"):
            raise Exception("Failed to click 'Buscar reservación' button")
        
        # Check for error message
        if check_for_error_message(driver):
            raise Exception("Error message found after searching for reservation")
        
        # Wait for and click the "Pase de abordar" button
        boarding_pass_xpath = "//button[@aria-label='Pase de abordar' and contains(@class, 'btn-for-checkin')]"
        if not wait_for_button_and_click(driver, boarding_pass_xpath):
            raise Exception("Failed to click 'Pase de abordar' button")
        
        # Check the privacy policy checkbox
        if not check_checkbox(driver, "privacyPolicy"):
            raise Exception("Failed to check privacy policy checkbox")
        
        
        # Wait for 1 second after checking the checkbox
        time.sleep(1)
        
        # Click the "Completar el Check-in" button
        complete_checkin_xpath = "/html/body/div[2]/div/div/div[1]/div[2]/div/div[2]/div/main/div[3]/section/div/div/div/section/form/section/section[2]/div[2]/button"
        if not wait_for_button_and_click(driver, complete_checkin_xpath):
            raise Exception("Failed to click 'Completar el Check-in' button")
        
        # Input date of birth
        if not input_date_of_birth(driver, date_of_birth):
            raise Exception("Failed to input date of birth")
        
        # Input email
        if not input_email(driver, email):
            raise Exception("Failed to input email")
        
        # Click the final "Enviar" button
        enviar_button_xpath = "//button[@aria-label='Enviar' and contains(@class, 'Btn--filledRed') and contains(@class, 'main-send-button')]"
        if not wait_for_button_and_click(driver, enviar_button_xpath):
            raise Exception("Failed to click 'Enviar' button")
        
        # Wait for the check-in process to complete and verify email sent
        time.sleep(10)  # Wait for a shorter time before checking for confirmation
        
        # Check for a confirmation message or element
        confirmation_xpath = "//div[contains(text(), 'Tu pase de abordar ha sido enviado')]"  # Adjust this XPath based on the actual confirmation message
        try:
            confirmation_element = WebDriverWait(driver, 50).until(
                EC.presence_of_element_located((By.XPATH, confirmation_xpath))
            )
            logging.info(f"Check-in completed and boarding pass sent for {last_name} - {reservation_code}")
        except TimeoutException:
            logging.error("Confirmation message not found. Email might not have been sent.")
            driver.save_screenshot(f"error_no_confirmation_{reservation_code}.png")
            raise Exception("Email sending confirmation not found")
        
    except Exception as e:
        logging.error(f"An error occurred during check-in: {str(e)}")
        driver.save_screenshot(f"error_{reservation_code}.png")
        raise

def main():
    parser = argparse.ArgumentParser(description="Perform Aeromexico check-in")
    parser.add_argument("--last_name", required=True, help="Passenger's last name")
    parser.add_argument("--reservation_code", required=True, help="Reservation code")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--date_of_birth", required=True, help="Date of birth (DD-MM-YYYY)")
    args = parser.parse_args()

    driver = Driver(uc=True)
    
    try:
        perform_checkin(driver, args.last_name, args.reservation_code, args.date_of_birth, args.email)
        return True  # Return True to indicate success
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return False  # Return False to indicate failure
    finally:
        driver.quit()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)  # Exit with 0 for success, 1 for failure