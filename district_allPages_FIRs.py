"""
fucked up. some issues arised.
REMEMBER: Looping over 1 to 10 pages with link text as is used to go to page 11
fully ready state.
next step: add method for counting last 'n' days from yesterday so that dates can be filled automatically"""

import os
import time
from contextlib import contextmanager
import state_FIRs
import pandas as pd
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from FIR_logging import logger

# constants
URL = r'https://www.mhpolice.maharashtra.gov.in/Citizen/MH/PublishedFIRs.aspx'

# base dir path for downloading files:
Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage'
# lists and files
# 1. empty list to store name of police stations where records were not found
record_not_found = []
# 2. empty list to store name of police stations where records were found
record_found = []
# 3. to get data of entire state
state_dataframes = []
# 3. empty file in append mode to write the summary.
summary_file = open(os.path.join(Download_Directory, 'records_summary.txt'), 'a')
# columns for the data frame
COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No',
           'Sections']


# functions:
def enter_date(driver, three_months_back, yesterday):
    WebDriverWait(driver, 160).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                     '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('date entered')


def next_page(driver, link_text=11):
    try:
        link_to_new_page_setup = driver.find_element_by_link_text(f'Page${str(link_text)}')
        link_to_new_page_setup.click()
    except NoSuchElementException:
        return False


def get_records(driver, district):
    # define a variable for link_text parameter
    link_text_counter = 11
    # how many records are available?
    number_of_records_found = driver.find_element_by_css_selector(
        '#ContentPlaceHolder1_lbltotalrecord').text
    # first extract the data from current visible page.
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located
                                        ((By.CSS_SELECTOR, '#ContentPlaceHolder1_gdvDeadBody')))

        logger.info(f"{unit_names[counter]}: {number_of_records_found}")
    except NoSuchElementException:
        logger.debug(f"get records: no records found @ {unit_names[counter]}")
        logger.info(f"get records: no records found @ {unit_names[counter]}")
        record_not_found.append(f"{unit_names[counter]}")
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    page_data = []
    district_dataframe = []
    rows = main_table.find_all("tr")
    for row in rows[0:(len(rows) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        # store data in list
        page_data.append([cell.text for cell in cells])

        # convert in list of dataframe as append.
    # District record:
    district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))


    # now iterate over each page and extract the data.
    # 1. get all the clickable links
    try:
        all_pages = driver.find_elements_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return
    # iterate over each page
    # range is selected for continuance.
    for each in range(len(all_pages) - 1):

        all_pages = driver.find_elements_by_css_selector('.gridPager a')
        all_pages[each].click()
        logger.info(f'page clicked: {each}')
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            logger.debug(f" not loaded.")
            logger.info(f"not loaded properly @ {unit_names[counter]}")
            continue
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")
        for row in rows[0:(len(rows) - 2)]:
            cells = row.find_all('td')
            cells = cells[0:9]
            page_data.append([cell.text for cell in cells])
        # each district data
        district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))


    while next_page(driver, link_text_counter):
        get_records(driver, district)
        link_text_counter += 10
    else:
        logger.info(f'record for {district} completed.')
    # create districtwise record
    district_data = pd.concat(district_dataframe)
    district_data.to_csv(os.path.join(Download_Directory, f'{district}_26_05_to_25_06.csv'))


@contextmanager
def wait_for_page_load(driver, timeout=10):
    """Wait till the old page is stale and old references are not working."""
    logger.debug("Waiting for page to load at {}.".format(driver.current_url))
    old_page = driver.find_element_by_id('lnkDisclaimers')
    yield
    WebDriverWait(driver, timeout).until(staleness_of(old_page))


# main code

# Start with a variable created as integer for looping
counter = 1

while counter < 49:
    try:
        options = FirefoxOptions()
        # options.add_argument("--headless")
        options.add_argument("--private-window")
        driver = webdriver.Firefox(options=options)
        driver.get(URL)
        driver.refresh()
        time.sleep(3)
        view = Select(driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_ucRecordView_ddlPageSize'))
        view.select_by_value('50')
        enter_date(driver=driver, three_months_back='19052020', yesterday='25062020')
        unit_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
        unit_names = [o.get_attribute("text")
                      for o in unit_list.options]
        unit_values = [o.get_attribute("text")
                       for o in unit_list.options if o.get_attribute("value") != 'Select']
        unit_list.select_by_index(counter)
        # check - old page is stale and new page is loaded.
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            logger.debug(f'the page is not stale yet @ {unit_names[counter]}')
            logger.info(f'the page was not loaded @ {unit_names[counter]}')
            continue
        # click the search button
        driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
        # check - old page is stale and new page is loaded.
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            logger.debug("wait with wait_for_page_load function.")
            logger.info('page was not loaded. trying again')
            continue

        get_records(driver=driver, district=unit_names[counter])

        counter += 1
        driver.close()
        logger.info(f'record found in: {record_found}, \nRecord not found in: {record_not_found}')
    except (NoSuchElementException, TimeoutException):
        logger.debug(f"some error retrying with same district")
        continue

# append summary file with short summary.
summary_file.write(f'Time Period: 30/03/2020 to 25/03/2020'
                   f'\n FIRs filed in Maharashtra. (Based on published FIRs by Maharashtra Police'
                   f'\n {record_not_found} \n\n\nRecords were found in '
                   f'\n totoal number of districts/unit where record was not found: {len(record_not_found)}'
                   f'\n {record_found} \n\n No records were found in following districts '
                   f'\n total number of districts/unit where record was not found: {len(record_not_found)}')

state_FIRs.state_file()


