from utils.scraper_functions import initialize_driver, authenticate, scrape_subject


# This script will scrape the CTEC page for one subject
subj_name = input('Enter subject name: ')

print(f"Beginning Subject Scrape of {subj_name}...\n")
driver = initialize_driver()
authenticate(driver)

scrape_subject(driver, subj_name)

print(f'\nFinished scraping subject {subj_name}')
driver.quit()