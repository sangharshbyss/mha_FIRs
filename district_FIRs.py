"""This file is not fully ready, coz, selection act is not going well."""
import base64
from typing import List
from selenium import webdriver
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

logger.info('page open')





# empty list

dataframes= []
COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No', 'Sections']

# enter dates

def enter_date(driver, three_months_back, yesterday):
    WebDriverWait(driver, 160).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                               '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('start date')


def get_records(driver):


    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows = main_table.find_all("tr")

    cy_data = []
    for row in rows[0:(len(rows)-2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        cy_data.append([cell.text for cell in cells])
    dataframes.append(pd.DataFrame(cy_data, columns=COLUMNS))
    logger.info(dataframes)


    logger.debug('dataframe created')

    return dataframes







counter = 1

while counter < 49:
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
    time.sleep(2)

    driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
    try:
        WebDriverWait(driver, 160).until(EC.presence_of_element_located((
            By.ID, 'ContentPlaceHolder1_gdvDeadBody')))
        record_found.append(unit_names[counter])
        get_records(driver=driver)

    except TimeoutException:
        record_not_found.append(unit_names[counter])
        counter += 1
        continue

    district_data = pd.concat(dataframes)

    district_data.to_csv(os.path.join(Download_Directory, f'{unit_names[counter]}.csv'))
    counter += 1
    driver.close()
    print(record_found, record_not_found)





