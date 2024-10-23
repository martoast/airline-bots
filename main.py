import csv
import subprocess
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_airline_script(airline, last_name, reservation_code, email, date_of_birth):
    script_path = os.path.join(airline.lower().replace(" ", ""), "main.py")
    if not os.path.exists(script_path):
        logging.error(f"Script not found for airline: {airline}")
        return False

    cmd = [
        "python3.10",
        script_path,
        "--last_name", last_name,
        "--reservation_code", reservation_code,
        "--email", email,
        "--date_of_birth", date_of_birth
    ]

    try:
        logging.info(f"Starting process for {last_name} with {airline}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Successfully processed reservation for {last_name} with {airline}")
        logging.debug(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing reservation for {last_name} with {airline}: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False

def main():
    with open('reservations.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            last_name = row['last_name']
            reservation_code = row['reservation_code']
            email = row['email']
            date_of_birth = row['date_of_birth']
            airline = row['airline']

            success = run_airline_script(airline, last_name, reservation_code, email, date_of_birth)
            
            if success:
                logging.info(f"Completed processing for {last_name}. Waiting before next reservation...")
                time.sleep(10)  # Wait for 10 seconds before processing the next reservation
            else:
                logging.warning(f"Failed to process reservation for {last_name}. Moving to next reservation...")

    logging.info("All reservations processed.")

if __name__ == "__main__":
    main()