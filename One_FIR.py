"""This file is not fully ready, coz, selection act is not going well."""
import base64
from typing import List
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

# base dir path for downloading files:
Download_Directory = r'/home/sangharshmanuski/Documents/mha_FIRs/raw_footage'

dataframes = []
# empty list to store name of police stations where records were not found
record_not_found = []
# empty list to store name of police stations where records were found
record_found = []
# three_months_back = 'three months back from yesterday'
# yesterday = 'yesterday'
# open the page


# empty list

COLUMNS = ['Sr.No.', 'State', 'District', 'Police Station', 'Year',
           'FIR No.', 'Registration Date', 'FIR No', 'Sections']


# enter dates

def enter_date(driver, three_months_back, yesterday):
    WebDriverWait(driver, 160).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                     '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('date entered')


def enter_police_station(driver, number=0):
    WebDriverWait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_ddlPoliceStation')))
    police_stations = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlPoliceStation'))
    police_stations_names = [police.get_attribute("text") for police
                             in police_stations.options if police.get_attribute("value") != '']
    police_stations.select_by_index(number)
    police_stations_name = police_stations_names[number]
    return police_stations_name


def get_records(driver):

    soup = BS(driver.page_source, 'html.parser')
    main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
    rows = main_table.find_all("tr")

    cy_data = []
    for row in rows[0:(len(rows) - 2)]:
        cells = row.find_all('td')
        cells = cells[0:9]
        cy_data.append([cell.text for cell in cells])
    dataframes.append(pd.DataFrame(cy_data, columns=COLUMNS))

    try:
        second_page = driver.find_element_by_css_selector(
        '.gridPager > td: nth - child(1) > table:nth - child(1) '
        '> tbody: nth - child(1) > tr:nth - child(        1) '
        '> td: nth - child(2) > a:nth - child(1)')
        second_page.click()
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        rows = main_table.find_all("tr")

        cy_data = []
        for row in rows[0:(len(rows) - 2)]:
            cells = row.find_all('td')
            cells = cells[0:9]
            cy_data.append([cell.text for cell in cells])
        dataframes.append(pd.DataFrame(cy_data, columns=COLUMNS))
    except NoSuchElementException:
        return dataframes

    return dataframes


time.sleep(1)

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
    enter_date(driver=driver, three_months_back='19062020', yesterday='24062020')
    unit_list = Select(driver.find_element_by_css_selector("#ContentPlaceHolder1_ddlDistrict"))
    unit_names = [o.get_attribute("text")
                  for o in unit_list.options]
    unit_values = [o.get_attribute("text")
                   for o in unit_list.options if o.get_attribute("value") != 'Select']
    unit_list.select_by_index(counter)
    time.sleep(2)

    driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
    try:
        time.sleep(10)
        WebDriverWait(driver, 50).until(EC.presence_of_element_located((
        By.ID, 'ContentPlaceHolder1_gdvDeadBody')))
        number_of_records_found = driver.find_element_by_css_selector(
        '#ContentPlaceHolder1_lbltotalrecord').text

        record_found.append(number_of_records_found)
    except TimeoutException:
        logger.info(f'no record @ {unit_names[counter]}')
        record_not_found.append(unit_names[counter])
        counter += 1

        continue

    police_stations = Select(driver.find_element_by_css_selector(
        '#ContentPlaceHolder1_ddlPoliceStation'))
    police_stations_values = [police.get_attribute("values") for police
                              in police_stations.options if police.get_attribute("value") != '']
    police_stations_names = [police.get_attribute("text") for police
                             in police_stations.options if police.get_attribute("value") != '']
    for each in range(len(police_stations_names)):
        police_stations_again = Select(driver.find_element_by_css_selector(
            '#ContentPlaceHolder1_ddlPoliceStation'))
        police_stations_again.select_by_index(each)
        driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
        try:
            time.sleep(10)
            WebDriverWait(driver, 50).until(EC.presence_of_element_located((
                By.ID, 'ContentPlaceHolder1_gdvDeadBody')))
            number_of_records_found = driver.find_element_by_css_selector(
                '#ContentPlaceHolder1_lbltotalrecord').text
            logger.info(f'{police_stations_names[each]}: {number_of_records_found}')
            get_records(driver=driver)

        except TimeoutException:
            record_not_found.append(each)
            logger.info(record_not_found)

    district_data = pd.concat(dataframes)

    district_data.to_csv(os.path.join(Download_Directory, f'{unit_names[counter]}.csv'))
    counter += 1
    driver.close()
print(record_not_found, record_found)
