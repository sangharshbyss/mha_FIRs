"""This file is not fully ready, coz, selection act is not going well."""
import base64
from typing import List
from selenium import webdriver
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
from bs4 import BeautifulSoup as BS
from FIR_logging import logger
import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from contextlib import contextmanager

# constants
URL = r'https://www.mhpolice.maharashtra.gov.in/Citizen/MH/PublishedFIRs.aspx'

# base dir path for downloading files:
Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage'

# empty list to store name of police stations where records were not found
record_not_found = []
# empty list to store name of police stations where records were found
record_found = []
# three_months_back = 'three months back from yesterday'
# yesterday = 'yesterday'
# open the page


COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No',
           'Sections']
state_dataframes = []


# enter dates

def enter_date(driver, three_months_back, yesterday):
    WebDriverWait(driver, 160).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                     '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('date entered')


def get_records(driver, district):
    # first extract the data from current page.

    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located
                                        ((By.CSS_SELECTOR, '#ContentPlaceHolder1_gdvDeadBody')))
        record_found.append(f"{unit_names[counter]}: {number_of_records_found}")
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

        all_pages_new = driver.find_elements_by_css_selector('.gridPager a')
        all_pages_new[each].click()
        logger.info(f'page clicked')
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

        district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))

    # if the pages are above 10 repeat the process....
    try:
        driver.find_element_by_css_selector(
            '.gridPager > td:nth-child(1) > table:nth-child(1) '
            '> tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(11) > a:nth-child(1)').click()

        logger.debug("looking for more pages")
    except NoSuchElementException:
        logger.debug(f"less than 10 pages.")
        logger.info(f"less than 10 pages @ {unit_names[counter]}")
        return
    try:
        wait_for_page_load(driver=driver, timeout=60)
    except TimeoutException:
        logger.debug("some error @ page 11")
        return
    logger.info("@ page 11")
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows = main_table.find_all("tr")
    for row in rows[0:(len(rows) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        page_data.append([cell.text for cell in cells])
    try:
        all_pages_after_10 = driver.find_elements_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return
    # iterate over each page
    # range method is used.

    for each in range(len(all_pages_after_10) - 2):

        all_pages_11 = driver.find_elements_by_css_selector('.gridPager a')
        all_pages_11[each].click()
        logger.info(f'@ page number: {all_pages_11[each].text}')
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            continue
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")
        for row in rows[0:(len(rows) - 2)]:

            cells = row.find_all('td')
            cells = cells[0:9]
            page_data.append([cell.text for cell in cells])

            district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))
    try:
        driver.find_element_by_css_selector(
            '.gridPager > td: nth - child(1) > table:nth - child(1) '
            '> tbody: nth - child(1) > tr:nth - child(1) '
            '> td: nth - child(12) > a:nth - child(1)').click()
    except NoSuchElementException:
        return
    try:
        wait_for_page_load(driver=driver, timeout=60)
    except TimeoutException:
        logger.debug("some error @ page 21")
        return
    logger.info("@ page 21")
    soup = BS(driver.page_source, 'html.parser')
    main_table_21 = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows_21 = main_table_21.find_all("tr")
    for row in rows[0:(len(rows_11) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        page_data.append([cell.text for cell in cells])
    try:
        all_pages_21 = driver.find_elements_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return
    # iterate over each page
    # range is selected for continuance.
    for each in range(len(all_pages_21) - 2):

        all_pages_21 = driver.find_elements_by_css_selector('.gridPager a')
        all_pages_21[each].click()
        logger.info(f'@ page number: {all_pages_21[each].text}')
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            continue
        soup = BS(driver.page_source, 'html.parser')
        main_table_21_new = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows_21 = main_table_21.find_all("tr")
        for row in rows_21[0:(len(rows) - 2)]:

            cells = row.find_all('td')
            cells = cells[0:9]
            page_data.append([cell.text for cell in cells])

            district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))
    # page number 31
    try:
        driver.find_element_by_css_selector(
            '.gridPager > td: nth - child(1) > table:nth - child(1) '
            '> tbody: nth - child(1) > tr:nth - child(1) '
            '> td: nth - child(12) > a:nth - child(1)').click()


    except NoSuchElementException:
        return
    try:
        wait_for_page_load(driver=driver, timeout=60)
    except TimeoutException:
        logger.debug("some error @ page 21")
        return
    logger.info("@ page 31")
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows = main_table.find_all("tr")
    for row in rows[0:(len(rows) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        page_data.append([cell.text for cell in cells])
    try:
        all_pages = driver.find_elements_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return
    # iterate over each page
    # range is selected for continuance.
    for each in range(len(all_pages) - 2):

        all_pages_new = driver.find_elements_by_css_selector('.gridPager a')
        all_pages_new[each].click()
        logger.info(f'@ page number: {all_pages_new[each].text}')
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            continue
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")
        for row in rows[0:(len(rows) - 2)]:

            cells = row.find_all('td')
            cells = cells[0:9]
            page_data.append([cell.text for cell in cells])

            district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))
    # for records above 40
    try:
        driver.find_element_by_css_selector(
            '.gridPager > td: nth - child(1) > table:nth - child(1) '
            '> tbody: nth - child(1) > tr:nth - child(1) '
            '> td: nth - child(12) > a:nth - child(1)').click()

    except NoSuchElementException:
        return
    try:
        wait_for_page_load(driver=driver, timeout=60)
    except TimeoutException:
        logger.debug("some error @ page 31")
        return
    logger.info("@ page 31")
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows = main_table.find_all("tr")
    for row in rows[0:(len(rows) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        page_data.append([cell.text for cell in cells])
    try:
        all_pages = driver.find_elements_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return
    # iterate over each page
    # range is selected for continuance.
    for each in range(len(all_pages) - 2):

        all_pages_new = driver.find_elements_by_css_selector('.gridPager a')
        all_pages_new[each].click()
        logger.info(f'@ page number: {all_pages_new[each].text}')
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            continue
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")
        for row in rows[0:(len(rows) - 2)]:
            cells = row.find_all('td')
            cells = cells[0:9]
            page_data.append([cell.text for cell in cells])

            district_dataframe.append(pd.DataFrame(page_data, columns=COLUMNS))

    district_data = pd.concat(district_dataframe)
    district_data.to_csv(os.path.join(Download_Directory, f'{district}_19_06_to_23_06.csv'))


@contextmanager
def wait_for_page_load(driver, timeout=10):
    """Wait till the old page is stale and old references are not working."""
    logger.debug("Waiting for page to load at {}.".format(driver.current_url))
    old_page = driver.find_element_by_tag_name('ctl00$lmgChrt')
    yield
    WebDriverWait(driver, timeout).until(staleness_of(old_page))


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
        enter_date(driver=driver, three_months_back='19062020', yesterday='23062020')
        unit_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
        unit_names = [o.get_attribute("text")
                      for o in unit_list.options]
        unit_values = [o.get_attribute("text")
                       for o in unit_list.options if o.get_attribute("value") != 'Select']
        unit_list.select_by_index(counter)
        # check - old page is stale and new page is loaded.
        try:
            wait_for_page_load(driver=driver, timeout=20)
        except TimeoutException:
            logger.debug(f'the page is not stale yet @ {unit_names[counter]}')
            logger.info(f'the page was not loaded @ {unit_names[counter]}')
            continue

        driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
        # check - old page is stale and new page is loaded. new method is used (decorator)
        try:
            wait_for_page_load(driver=driver, timeout=60)
        except TimeoutException:
            logger.debug("wait with wait_for_page_load function.")
            logger.info('page was not loaded. trying again')
            continue
        number_of_records_found = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_lbltotalrecord').text

        get_records(driver=driver, district=unit_names[counter])

        counter += 1
        driver.close()
        logger.info(record_found, record_not_found)
    except (NoSuchElementException, TimeoutException):
        logger.debug(f"some error retrying with same district")
        continue
summary_file = open(os.path.join(Download_Directory, 'records_summary.txt'), 'w')
summary_file.write(f'No records were found in following districts '
                   f'\ntotoal number of districts/unit where record was not found: {len(record_not_found)}'
                   f'\n{record_not_found} \nRecords were found in '
                   f'\ntotoal number of districts/unit where record was not found: {len(record_not_found)}'
                   f'\n{record_found}')
state_data_collection = pd.concat(state_dataframes)
state_data_collection.to_csv(os.path.join(Download_Directory, 'maharashtra_19_06_to_23_06.csv'))
