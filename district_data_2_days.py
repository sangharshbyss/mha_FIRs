from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, \
    TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from FIR_logging import logger
import os
import time
import pandas as pd


# base function

def get_url(some_url):
    try:
        driver.get(some_url)
        driver.refresh()
    except WebDriverException:
        time.sleep(600)
        driver.get(some_url)
        driver.refresh()


# Some constants:

URL = r'https://www.mhpolice.maharashtra.gov.in/Citizen/MH/PublishedFIRs.aspx'
options = FirefoxOptions()
options.add_argument("--headless")
options.add_argument("--private-window")
driver = webdriver.Firefox(options=options)
get_url(URL)
time.sleep(10)

Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage/raw_footage7'

COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No',
           'Sections']


# other functions

def districts():
    unit_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
    values = [o.get_attribute("value")
              for o in unit_list.options if o.get_attribute("text") in (
                  'AKOLA')]
    names = [o.get_attribute("text")
             for o in unit_list.options if o.get_attribute("text") in (
                 'AKOLA')]
    return values, names


def search():
    driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
    time.sleep(9)


def second_page_slot():
    # find specific link for going to page 11 and click.
    try:
        link_for_page_slot = driver.find_element_by_link_text('...')
        link_for_page_slot.click()
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
        from_date_field = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_txtDateOfRegistrationFrom')

        to_date_field = driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_txtDateOfRegistrationTo')

        ActionChains(driver).click(from_date_field).send_keys(
            self.start_date).move_to_element(to_date_field).click().send_keys(
            self.end_date).perform()

        logger.info(f'date entered: {self.start_date} to {self.end_date}')

    def search_the_district(self):
        dist_list = Select(driver.find_element_by_css_selector(
            "#ContentPlaceHolder1_ddlDistrict"))

        dist_list.select_by_value(self.district_value)
        time.sleep(8)
        something = 0
        while True:
            if something < 6:
                try:
                    search()
                    break
                except (NoSuchElementException, TimeoutException):
                    time.sleep(1)
                    logger.info("search was not loaded")

                    something += 1
                    continue
            else:

                logger.info(f"{self.district_name} - broken link")

    def number_of_records(self):
        """captures the text indicating number of records.
        converts it to integer. if 0 returns and appends name of district to the list
        if page is not loaded. it tries one more time for 15 secs."""
        time_counter = 1
        while time_counter < 16:
            try:
                records_number = driver.find_element_by_css_selector(
                    '#ContentPlaceHolder1_lbltotalrecord').text
                if records_number == '':
                    continue
                else:
                    records_number = int(records_number)
                if records_number != 0:
                    logger.info(f"{self.district_name}: {records_number}")

                    return records_number
                else:
                    logger.info(f"no records @ {this.district_name}")

                    return False
            except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
                logger.info("page is not loaded")
                time_counter += 1
                continue

    def record_found(self):
        # giving guarantee that the table we are downloading is from same district
        # 1. checks if the page has information table
        # 2 and the district name matches with selected options from units.
        try:

            data_table = driver.find_element_by_css_selector(
                '#ContentPlaceHolder1_gdvDeadBody_Label2_0')
            if data_table.text != self.district_name:
                time.sleep(5)
                data_table = driver.find_element_by_css_selector(
                    '#ContentPlaceHolder1_gdvDeadBody_Label2_0')
                if data_table.text != self.district_name:
                    logger.info(f"no record found @ {self.district_name}")

                    return False
            else:
                return True
        except NoSuchElementException:
            logger.info(f"no record found @ {self.district_name}: Broken")

            return False
        except StaleElementReferenceException:
            logger.info("page not loaded. Broken")

            return False

    def extract_table_current(self, single):
        # entire table of record to be taken to the list.
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        time_counter = 1
        while main_table is None:
            if time_counter < 16:
                logger.info(f"the table did not load @ {self.district_name}")
                time_counter += 1
            else:
                logger.info(f"the table did not load @ {self.district_name}."
                            f"stopped trying")

                return
        rows = main_table.find_all("tr")
        for row in rows:
            if '...' not in row.text:
                cells = row.find_all('td')
                cells = cells[0:9]  # drop the last column
                # store data in list
                single.append([cell.text for cell in cells])

    def extract_table_multi_page(self, single):
        # when there are more pages, last row should be excluded and rest needs extraction to list.
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        time_counter = 1
        while main_table is None:
            if time_counter < 16:
                logger.info(f"the table did not load @ {self.district_name}")
                time_counter += 1
            else:
                logger.info(f"the table did not load @ {self.district_name}."
                            f"stopped trying")

                return

        rows = main_table.find_all("tr")

        for row in rows[0:(len(rows)) - 2]:
            cells = row.find_all('td')
            cells = cells[0:9]  # drop the last column

            # store data in list
            single.append([cell.text for cell in cells])

    def next_page(self, data):
        # check if any link to next page is available
        # iterate every page.
        try:
            driver.find_element_by_css_selector('.gridPager a')
        except NoSuchElementException:
            return False
        links_for_pages = driver.find_elements_by_css_selector('.gridPager a')
        for page in range(len(links_for_pages)):
            # new list, to by pass stale element exception
            links_for_pages_new = driver.find_elements_by_css_selector('.gridPager a')
            # do not click on link for new page slot
            if links_for_pages_new[page].text != '...':
                links_for_pages_new[page].click()
                # if this can be replaced with some other wait method to save the time
                time.sleep(13)
                self.extract_table_multi_page(data)


# main code
unit_values, unit_names = districts()
driver.close()
# outer loop to iterate over each unit
a = "29"
b = "06"
c = "2020"
x = "30"
y = "06"
z = "2020"

while int(a) != 0:

    page_data = []
    district_data_frame = []

    if int(a) < 10 or int(x) < 10:
        a = str(a)
        a = f"{str(0)}{a}"
        x = str(x)
        x = f"{str(0)}{x}"

    for unit in unit_values:
        date_from = str(a) + b + c
        date_to = str(x) + y + z
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--private-window")
        driver = webdriver.Firefox(options=options)
        time.sleep(8)
        driver.get(URL)
        # refresh immediately as the page is of no use without it.
        driver.refresh()
        time.sleep(5)

        view = Select(driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_ucRecordView_ddlPageSize'))
        view.select_by_value('50')
        # create district object
        this = Search(date_from, date_to, unit, unit_names[unit_values.index(unit)])
        this.enter_date()
        this.search_the_district()
        time.sleep(5)
        this.number_of_records()
        if not this.record_found():
            continue
        this.extract_table_current(page_data)
        this.next_page(page_data)
        if second_page_slot():
            this.extract_table_multi_page(page_data)
            this.next_page(page_data)

        driver.close()
        time.sleep(8)
        a = int(a)
        x = int(x)
        if a < 10 or x < 10:
            a = str(a)
            a = a.strip("0")
            a = int(a)
            a -= 2
            x = str(x)
            x = x.strip('0')
            x = int(x)
            x -= 2
        else:
            a -= 2
            x -= 2

    district_data = pd.DataFrame(page_data, columns=COLUMNS)
    district_data.to_csv(os.path.join(Download_Directory, f'AKOLA{b}{c}.csv'))
