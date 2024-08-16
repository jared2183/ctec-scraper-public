from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from pathlib import Path
from dotenv import load_dotenv
import os

# Initializes driver and loads dotenv variables
def initialize_driver():
    load_dotenv()
    manage_classes_url = os.getenv('MANAGE_CLASSES_URL')
    # driver = webdriver.Chrome(ChromeDriverManager().install())
    driver = webdriver.Chrome(executable_path='/Users/jaredmyang/Downloads/chromedriver-mac-arm64/chromedriver')
    driver.get(manage_classes_url)
    return driver

# Authenticates user through Duo using the .env file
def authenticate(driver):
    netid_field = WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.ID, "idToken1"))
    password_field = driver.find_element(By.ID, "idToken2")
    netid = os.getenv('NET_ID')
    password = os.getenv('PASSWORD')

    netid_field.send_keys(netid)
    password_field.send_keys(password)
    driver.find_element(By.NAME, "callback_2").click()

    print("Waiting for Duo Mobile Authentication...")
    trust_btn = WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.ID, 'trust-browser-button'))
    trust_btn.click()
    print("Authentication Successful\n")

# Returns the index of the course in the table
def get_selected_course_index(driver, courses):
    for i in range(len(courses)):
        name_div = courses[i].find_elements(By.TAG_NAME, 'td')[0].find_element(By.TAG_NAME, 'div')
        if name_div.get_attribute('class').find('ctec-row-selected') != -1: # could use IN keyword here
            return i

# Returns the generated path to the file
def file_path(subj_name, sec_id, instr, term):
    instr = instr.replace(' ', '_')
    term = '_'.join(term)
    return f'data/{subj_name}/{subj_name}_{sec_id}--{instr}--{term}.html'

# Scrapes a single section in a list of sections
# Ideally won't have subj_name as a parameter
def scrape_section(driver, section, subj_name):
    # Gathering some basic metadata (already split)
    WebDriverWait(driver, timeout=100).until(lambda d: section.find_element(By.CSS_SELECTOR, "td[class='ps_grid-cell MYDESCR']").find_element(By.TAG_NAME, 'span').text != '')
    desc = section.find_element(By.CSS_SELECTOR, "td[class='ps_grid-cell MYDESCR']").find_element(By.TAG_NAME, 'span').text.split(' ')
    term = section.find_element(By.CSS_SELECTOR, "td[class='ps_grid-cell MYDESCR2']").find_element(By.TAG_NAME, 'span').text.split(' ')
    instr = section.find_element(By.CSS_SELECTOR, "td[class='ps_grid-cell CTEC_INSTRUCTOR']").find_element(By.TAG_NAME, 'span').text       
    sec_id = desc[1]
    ctec_path = file_path(subj_name, sec_id, instr, term)
    # Will skip scrape if it has already been scraped or if study group
    if Path(ctec_path).exists() or ('SG' in sec_id): return

    # Opens the CTEC file
    original_window = driver.current_window_handle
    section.click()
    WebDriverWait(driver, timeout=100).until(EC.number_of_windows_to_be(2))
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break
    # Waits until CTEC page loads
    WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.TAG_NAME, 'div'))

    # Dumps CTEC source HTML to file and returns to original window with sections
    ctec_html = driver.page_source
    with open(ctec_path, 'w') as f:
        f.write(ctec_html)
        print('    Wrote to file: ' + ctec_path)
    driver.close()
    driver.switch_to.window(original_window)

def get_all_subjects(driver): #undergraduate only
    WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.XPATH, '//option[@value="UGRD"]')).click() # Selects undergraduate courses only for now
    WebDriverWait(driver, timeout=100).until(lambda d: len(d.find_element(By.ID, 'NW_CT_PB_SRCH_SUBJECT').find_elements(By.TAG_NAME, 'option')) > 1)
    all_subject_names = list(map(lambda x: x.get_attribute('value'), driver.find_element(By.ID, 'NW_CT_PB_SRCH_SUBJECT').find_elements(By.TAG_NAME, 'option')[1:]))
    return all_subject_names

# Scrapes a single subject with subject name input (string)
def scrape_subject(driver, subj_name):
    # Creates directory for subject if it doesn't exist
    Path(f'data/{subj_name}').mkdir(exist_ok=True)

    # Navigating CTEC subject search page
    career_select = WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.ID, 'NW_CT_PB_SRCH_ACAD_CAREER'))
    career_select.find_element(By.XPATH, '//option[@value="UGRD"]').click()    # Selects Undergraduate only for now
    search_btn = driver.find_element(By.ID, 'NW_CT_PB_SRCH_SRCH_BTN')

    # Waits for the subject option to load in 
    try:
        subject = WebDriverWait(driver, timeout=5).until(lambda d: d.find_element(By.XPATH, f'//option[@value="{subj_name}"]'))
    except:
        print(f"Subject {subj_name} not found.")
        return

    # Searches and waits for the subject course table to load in
    subject.click()
    search_btn.click()
    WebDriverWait(driver, timeout=100).until(EC.element_to_be_clickable((By.ID, 'NW_CTEC_WRK_BUTTON')))

    # Skips subject if there are no courses to be found
    try: 
        courses = driver.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        courses[0].click()
    except:
        change_search_btn = driver.find_element(By.ID, 'NW_CTEC_WRK_BUTTON')
        change_search_btn.click()
        print(f'No courses found for {subj_name}\n')
        return

    # Waits for the sections page to load in (takes around a minute or two not even kidding)
    while True:
        try:
            WebDriverWait(driver, timeout=60).until(lambda d: d.find_element(By.XPATH, "//div[@class='ps_grid-col-label']").text == 'Description') # Waits for description table to load in
            break
        except:
            driver.refresh()

    # Loops over every course in the left hand table
    course_table = driver.find_elements(By.TAG_NAME, 'tbody')[0]
    courses = course_table.find_elements(By.TAG_NAME, 'tr')

    for course in courses:
        # Gathering course number and name
        desc = course.find_elements(By.TAG_NAME, 'td')[0].find_element(By.TAG_NAME, 'span').text.split(': ')
        print(f'Scraping {subj_name} {desc[0]}: {desc[1]}...')
        if desc[1] == 'Special Topics in International Studies': continue # For some reason this single course gives an error

        # Waits for section table to load
        prev_index = get_selected_course_index(driver, courses)
        # Does not click first course because it's already loaded in 
        if course != courses[0]:
            course.click()
            WebDriverWait(driver, timeout=100).until(lambda d: get_selected_course_index(d, courses) != prev_index)
        # Skips blank CTEC Pages
        if len(WebDriverWait(driver, timeout=100).until(lambda d: d.find_elements(By.TAG_NAME, 'tbody'))) != 2: continue

        section_table = driver.find_elements(By.TAG_NAME, 'tbody')[1]
        sections = section_table.find_elements(By.TAG_NAME, 'tr')

        # Loops over every section in the right hand table
        for section in sections:
            try:
                scrape_section(driver, section, subj_name)
            except:
                desc = section.find_element(By.CSS_SELECTOR, "td[class='ps_grid-cell MYDESCR']").find_element(By.TAG_NAME, 'span').text
                print(f'ERROR: Unable to scrape section {desc}')

    # Navigates back to search page
    driver.find_element(By.ID, 'PT_WORK_PT_BUTTON_BACK').click()
    WebDriverWait(driver, timeout=100).until(lambda d: d.find_element(By.ID, 'NW_CTEC_WRK_BUTTON')).click()
