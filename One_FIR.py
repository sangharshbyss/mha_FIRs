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
import html2csv

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
unit_list = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlDistrict'))
unit_names = [o.get_attribute(
    "text") for o in unit_list.options if o.get_attribute("value") != 'Select']
view_record = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ucRecordView_ddlPageSize'))
view_record_max = view_record.select_by_value('50')
search = driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch')
# empty list
act_column = []
FIR_column = []

# enter dates

def enter_start_date(three_months_back, yesterday):
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                               '#ContentPlaceHolder1_txtDateOfRegistrationFrom')))
    datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationFrom')

    end_datefield = driver.find_element_by_css_selector('#ContentPlaceHolder1_txtDateOfRegistrationTo')

    ActionChains(driver).click(datefield).send_keys(
        three_months_back).move_to_element(end_datefield).click().send_keys(yesterday).perform()

    logger.info('start date')



def enter_unit(unit_number=0):
    unit_list = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlDistrict'))
    unit_list.select_by_index(unit_number)
    unit_name = unit_names[unit_number]
    return unit_name


def enter_police_station(number=0):
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_ddlPoliceStation')))
    police_stations = Select(driver.find_element_by_css_selector('#ContentPlaceHolder1_ddlPoliceStation'))
    police_stations_names = [police.get_attribute("text") for police
                             in police_stations.options if police.get_attribute("value") != '']
    police_stations.select_by_index(number)
    police_stations_name = police_stations_names[number]
    return police_stations_name


def get_records():

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_lbltotalrecord')))

    number_of_pages = driver.find_elements_by_class_name("gridPager")
    for each_page in number_of_pages:
        soup = BS(driver.page_source, 'html.parser')
        main_table = soup.find("table", {"id": "ContentPlaceHolder1_gdvDeadBody"})
        df = pd.read_html(str(main_table))
        df.drop(columns="Download")
    return print(df)


'''
def list_poa_caes():
    list_of_poa = []
    for act, FIR_number in zip(act_column, FIR_column):
        list_of_poa.append(FIR_number)
    return print(list_of_poa)
'''

enter_start_date("01042020", "21062020")


enter_unit(2)
time.sleep(5)
enter_police_station(4)
driver.find_element_by_css_selector('#ContentPlaceHolder1_btnSearch').click()
get_records()
driver.close()



