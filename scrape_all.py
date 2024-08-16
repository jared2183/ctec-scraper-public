from utils.scraper_functions import get_all_subjects, initialize_driver, authenticate, scrape_subject

# This script will scrape the CTEC page across all subjects and update new CTECs
print("Beginning Database Scrape...\n")
driver = initialize_driver()
authenticate(driver)

# Finds all subject names
all_subject_names = get_all_subjects(driver)

for subj_name in all_subject_names:
    scrape_subject(driver, subj_name)

# Closes driver and quits program
print('\nScrape Complete!\n')
driver.quit()