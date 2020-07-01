"""
reaching to all pages. BUT after end of all pages, it comes back to some of the pages.  """

import os
import time
from contextlib import contextmanager
import state_FIRs
import pandas as pd
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, \
    TimeoutException, StaleElementReferenceException
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
options = FirefoxOptions()
options.add_argument("--headless")
options.add_argument("--private-window")
driver = webdriver.Firefox(options=options)
driver.get(URL)
driver.refresh()
page_data = []
district_dataframe = []
Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage'
# lists and files

no_records = []
records_found = []

COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No',
           'Sections']


def districts():
    unit_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
    values = [o.get_attribute("value")
              for o in unit_list.options if o.get_attribute("value") != 'Select']
    names = [o.get_attribute("text")
             for o in unit_list.options if o.get_attribute("value") != 'Select']
    return values, names


@contextmanager
def wait_for_page_load(driver, timeout=30):
    """Wait till the old page is stale and old references are not working."""
    logger.debug("Waiting for page to load at {}.".format(driver.current_url))
    old_page = driver.find_element_by_id('lnkDisclaimers')
    yield
    WebDriverWait(driver, timeout).until(staleness_of(old_page))


def search():
    driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
    time.sleep(7)
    wait_for_page_load(driver)


def number_of_records():
    try:
        number_of_records_found = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_lbltotalrecord').text
        return number_of_records_found
    except (NoSuchElementException, TimeoutException):
        logger.info("page is not loaded")
        return False


def extract_table_current(single):
    # entire table of record to be taken to the list.
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})

    rows = main_table.find_all("tr")
    for row in rows:
        if '...' not in row.text:
            cells = row.find_all('td')
            cells = cells[0:9]  # drop the last column

            # store data in list
            single.append([cell.text for cell in cells])


def extract_table_multipage(single):
    # when there are more pages, last row should be excluded and rest needs extraction to list.
    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})

    rows = main_table.find_all("tr")

    for row in rows[0:(len(rows)) - 2]:
        cells = row.find_all('td')
        cells = cells[0:9]  # drop the last column

        # store data in list
        single.append([cell.text for cell in cells])


def next_page(clicks):
    # check if any link to next page is available
    # iterate every page.
    try:
        link_for_page = driver.find_element_by_css_selector('.gridPager a')
    except NoSuchElementException:
        return False
    links_for_pages = driver.find_elements_by_css_selector('.gridPager a')
    for page in range(len(links_for_pages)):
        time.sleep(5)

        # new list, to by pass stale element exception
        links_for_pages_new = driver.find_elements_by_css_selector('.gridPager a')
        # do not click on link for new page
        if links_for_pages_new[page].text != '...':
            click_it = links_for_pages_new[page].click()
            clicks.append(click_it)
            time.sleep(7)
            logger.info(f'page {page}')
            soup = BS(driver.page_source, 'html.parser')
            main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})

            rows = main_table.find_all("tr")

            for row in rows[0:(len(rows)) - 2]:
                cells = row.find_all('td')
                cells = cells[0:9]  # drop the last column

                # store data in list
                page_data.append([cell.text for cell in cells])


def second_page_slot():
    # find specific link for going to page 11 and click.
    try:
        link_for_page_slot = driver.find_element_by_link_text('...')
        link_for_page_slot.click()
    except NoSuchElementException:
        return False


def next_to_second_page_slot():
    try:
        link_for_page_slot = driver.find_element_by_css_selector(
            '.gridPager > td:nth-child(1) > table:nth-child(1) > tbody:nth-child(1) '
            '> tr:nth-child(1) > td:nth-child(12) > a:nth-child(1)')
        link_for_page_slot.click()
        time.sleep(5)
    except NoSuchElementException:
        return False


class Search:
    driver = driver

    def __init__(self, start_date, end_date, district_value, district_name):
        self.start_date = start_date
        self.end_date = end_date
        self.district_value = district_value
        self.district_name = district_name

    def enter_date(self):
        # enters start as well as end dates with "action chains."
        WebDriverWait(driver, 160).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
        from_datefield = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_txtDateOfRegistrationFrom')

        to_datefield = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_txtDateOfRegistrationTo')

        ActionChains(driver).click(from_datefield).send_keys(
            self.start_date).move_to_element(to_datefield).click().send_keys(
            self.end_date).perform()

        logger.info('date entered')

    def search_the_district(self):
        dist_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
        dist_names = [o.get_attribute("text")
                      for o in dist_list.options if o.get_attribute("value") != 'Select']
        dist_values = [o.get_attribute("value")
                       for o in dist_list.options if o.get_attribute("value") != 'Select']
        dist_list.select_by_value(self.district_value)
        time.sleep(6)
        search()

    def record_found(self):
        # 1. checks if the page has information table
        # 2 and the district name matches with selected options from units.
        try:
            wait_for_page_load(driver)
            data_table = driver.find_element_by_css_selector(
                '#ContentPlaceHolder1_gdvDeadBody_Label2_0')
            if data_table.text != self.district_name:
                return False
            else:
                return True
        except NoSuchElementException:
            logger.info("no record found")
            return False
        except StaleElementReferenceException:
            logger.info("page not loaded.")


# main code
# wait till page is fully loaded after refresh
wait_for_page_load(driver)

unit_values, unit_names = districts()
driver.close()

# loop to iterate over each unit
for unit in unit_values:
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--private-window")
    driver = webdriver.Firefox(options=options)
    driver.get(URL)
    # refresh immediately as the page is of no use without it.
    driver.refresh()
    page_data = []
    district_dataframe = []
    clicks = []
    wait_for_page_load(driver)
    view = Select(driver.find_element_by_css_selector(
        '#ContentPlaceHolder1_ucRecordView_ddlPageSize'))
    view.select_by_value('50')

    # create district object
    this = Search(15062020, 25062020, unit, unit_names[unit_values.index(unit)])
    this.enter_date()
    wait_for_page_load(driver)
    this.search_the_district()
    wait_for_page_load(driver)
    if not this.record_found():
        logger.info(f"no records were found @ {unit_names[unit_values.index(unit)]}")
        no_records.append(unit_names[unit_values.index(unit)])
        continue
    else:
        logger.info("record available and page is loaded")
    if not number_of_records():
        logger.info(f"some issues yet. skip @ {unit_names[unit_values.index(unit)]}")

        continue
    else:
        numbers = number_of_records()
        logger.info(f"number of records @ {unit_names[unit_values.index(unit)]}:"
                    f" {number_of_records()}")
        records_found.append(f'{unit_names[unit_values.index(unit)]}:'
                             f' {numbers}')
        # deciding number of pages on basis of number of records
        total_pages = int(numbers)/50
        if type(total_pages) is not float:

            total_pages = int(numbers)//50 + 1
        logger.info(f'{total_pages}')


    extract_table_current(page_data)
    try:
        next_page(clicks)
    except:
        district_data = pd.DataFrame(page_data, columns=COLUMNS)
        district_data.to_csv(os.path.join(Download_Directory, f'{unit_names[unit_values.index(unit)]}'
                                                              f'_15_06_to_25_06.csv'))
        driver.close()
        continue

    try:

        link_for_page_slot = driver.find_element_by_link_text('...')
        link_for_page_slot.click()
        clicks.append(clicks)
        extract_table_multipage(page_data)
        next_page(clicks)
    except:
        district_data = pd.DataFrame(page_data, columns=COLUMNS)
        district_data.to_csv(os.path.join(Download_Directory, f'{unit_names[unit_values.index(unit)]}'
                                                              f'_15_06_to_25_06.csv'))

        continue
    try:
        next_page_slot = driver.find_element_by_css_selector(
            '.gridPager > td:nth-child(1) > table:nth-child'
            '(1) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(12) > a:nth-child(1)')
        next_page_slot.click()
        clicks.append(clicks)
        extract_table_multipage(page_data)
        next_page(clicks)
        district_data = pd.DataFrame(page_data, columns=COLUMNS)
        district_data.to_csv(os.path.join(Download_Directory, f'{unit_names[unit_values.index(unit)]}'
                                                              f'_15_06_to_25_06.csv'))
        driver.close()
    except:
        continue
