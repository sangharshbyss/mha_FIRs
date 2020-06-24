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



# constants
URL = r'https://www.mhpolice.maharashtra.gov.in/Citizen/MH/PublishedFIRs.aspx'

options = FirefoxOptions()
# options.add_argument("--headless")
options.add_argument("--private-window")
driver = webdriver.Firefox(options=options)
# base dir path for downloading files:
Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage'

wait = WebDriverWait(driver, 180)
# empty list to store name of police stations where records were not found
record_not_found = []
# empty list to store name of police stations where records were found
record_found = []
# three_months_back = 'three months back from yesterday'
# yesterday = 'yesterday'
# open the page
driver.get(URL)
logger.info('page open')
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                           '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
driver.refresh()

view_record = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ucRecordView_ddlPageSize'))
view_record_max = view_record.select_by_value('50')
search = driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch')
# empty list

dataframes= []
COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year', 'FIR No.', 'Registration Date', 'FIR No', 'Sections']

# enter dates

def enter_start_date(three_months_back, yesterday):
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                               '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('start date')





def enter_police_station(number=0):
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_ddlPoliceStation')))
    police_stations = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlPoliceStation'))
    police_stations_names = [police.get_attribute("text") for police
                             in police_stations.options if police.get_attribute("value") != '']
    police_stations.select_by_index(number)
    police_stations_name = police_stations_names[number]
    return police_stations_name


def get_records(some_station):

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_lbltotalrecord')))
    number_of_records = driver.find_element_by_css_selector('#ContentPlaceHolder1_lbltotalrecord')
    if str(number_of_records.text) == str('0'):
        record_not_found.append(some_station)
        logger.info(f'no record @ {some_station}')
        return False
    else:
        record_found.append(some_station)

    number_of_pages = driver.find_elements_by_class_name("gridPager")
    for each_page in number_of_pages:
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")

        cy_data = []
        for row in rows:
            cells = row.find_all('td')
            cells = cells[0:9]
            cy_data.append([cell.text for cell in cells])
        dataframes.append(pd.DataFrame(cy_data, columns=COLUMNS))

    logger.debug('dataframe created')

    return dataframes



enter_start_date("01042020", "21062020")
time.sleep(8)

unit_names = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict")).options

for name in unit_names:

    unit_list = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlDistrict'))
    unit_list.select_by_index(unit_names.index(name))

    police_stations = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlPoliceStation'))
    police_stations_names = [police.get_attribute("text") for police
                             in police_stations.options if police.get_attribute("value") != '']

    time.sleep(6)
    for police_station in police_stations_names:
        enter_police_station(police_stations_names.index(police_station))
        driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
        if not get_records(police_station):
            continue
        else:
            pass
        logger.info(f'{police_station} data ready')
    district_data = pd.concat(dataframes)

    district_data.to_csv(os.path.join(Download_Directory, f'{name}.csv'))

driver.close()



