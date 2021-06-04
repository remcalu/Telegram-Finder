# Generate EXE with pyinstaller --onefile webscraper.py --hidden-import jinja2 --add-data C:\Users\RemCa\AppData\Local\Programs\Python\Python38-32\Lib\site-packages\pandas\io\formats\templates\html.tpl;pandas\io\formats\templates
import json
import os
import time
import re
import pygetwindow
import keyboard
import threading
from gtts import gTTS
from os import system
from decimal import *
from datetime import datetime
from playsound import playsound
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def check_if_string_in_file(file_name, string_to_search):
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                read_obj.close()
                return True
    read_obj.close()
    return False

def append_string_to_file(file_name, string_to_append):
    # Open the file in read only mode
    with open(file_name, 'a') as append_obj:
        append_obj.write(string_to_append)
        append_obj.close()
    return False

try:
    # Setting up window and colors
    system("title "+ "TGMonitor")
    print("\33[37m", end ="")

    # Getting data from options file
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(current_dir + "\options.json") as file:
        data = json.load(file)
    refresh_delay = 3
    #refresh_delay = data['refresh_delay']
    if data['autoload'] != "none":
        num_items = len(data['saved'])
        autoload_item = input("Select (0) for no autoload or (1-" + str(num_items) + ") to select a preset from options.txt file: ")
        print("Selected option " + autoload_item + ": " +  data['saved'][int(autoload_item)-1]['name'])

    # Getting input from user
    if data['autoload'] != "none" and data['saved'][int(autoload_item)-1]['static_link'] == "none":
        subreddit_link = input("Enter a subreddit link to monitor: ")
    else:
        subreddit_link = data['saved'][int(autoload_item)-1]['static_link']
        print("(AUTO) Enter a subreddit link to monitor: " + data['saved'][int(autoload_item)-1]['static_link'])

    if data['autoload'] != "none" and data['saved'][int(autoload_item)-1]['static_users'] == "none":
        num_users = input("Enter either a minimum amount of users: ")
    else:
        num_users = data['saved'][int(autoload_item)-1]['static_users']
        print("(AUTO) Enter either a minimum amount of users: " + data['saved'][int(autoload_item)-1]['static_users'])

    # Loading the chrome driver
    print("Loading chrome driver...")
    coptions = Options()
    coptions.add_argument('--headless')
    coptions.add_argument('--disable-gpu')  # Last I checked this was necessary.
    coptions.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(current_dir + "/chromedriver.exe", options=coptions)

    # Loading the webpage itself
    print("Loading webpage...")
    while True:
        try:
            driver.get(subreddit_link)
            myElem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//a[@class='title may-blank ']")))
            break
        except TimeoutException:
            print("Page didn't load after 30 seconds, trying again!")
            continue
    print("Done, starting the monitor...")
    time.sleep(3.0)

    # Main loop to scrape from webpage
    counter = 0
    fails = 0
    
    print("\n\n")
    while True:
        try:
            # Preparing data for printing usertext-body may-blank-within md-container 
            time.sleep(float(refresh_delay))
            now = datetime.now()
            scraped_time_long = now.strftime("%d/%m/%Y %H:%M:%S")
            scraped_time = now.strftime("%H:%M:%S")
            subreddit_data = driver.find_elements_by_xpath("//a[@class='title may-blank ']")
            url_list = []
            for posting in subreddit_data:
                url_list.append(posting.get_attribute('href'))
            for url in url_list:
                time.sleep(float(0.0))
                if "https://alb.reddit.com" not in url:
                    try:
                        #print("Redirecting to: " + url) 
                        driver.get(url)
                        outer_data = driver.find_elements_by_xpath("//div[@class='usertext-body may-blank-within md-container ']")
                        post_data = outer_data[1].get_attribute('innerHTML')
                        telegram_link = re.findall("(https?:\/\/(.+?\.)?t\.me(\/[A-Za-z0-9\-\._~:\/\?#\[\]@!$&'\(\)\*\+,;\=]*)?)", post_data)
                        driver.get(str(telegram_link[0][0]))
                        token_title = driver.find_element_by_xpath("//div[@class='tgme_page_title']")
                        token_members = driver.find_element_by_xpath("//div[@class='tgme_page_extra']")
                        num_members_compare = re.findall("\\d+", token_members.text.replace(" ", ""))
                        #output_string = "[" + scraped_time_long + "] (" + num_members_compare[0] + "): '" + str(token_title.text) + "' with " + str(token_members.text) + " | " + url
                        output_string = "[" + scraped_time_long + "] (" + str(num_members_compare[0]).rjust(6, '0') + "): " + str(token_title.text).ljust(45, ' ') +  " |   " + str(url)
                        if int(num_users) <= int(num_members_compare[0]):
                            color = "\033[1;32;40m"
                            if check_if_string_in_file(current_dir + "\\telegramlist.txt", str(token_title.text)) == False:
                                append_string_to_file(current_dir + "\\telegramlist.txt", output_string + "\n")
                                wav_file = current_dir + "/found.wav"
                                threading.Thread(target=playsound, args=(wav_file,), daemon=True).start()
                            else: 
                                color = "\033[1;33;40m"
                            print(color + output_string)
                            print("\33[37m", end ="")
                        else:
                            color = "\033[1;31;40m"
                            print(color + output_string) 
                            print("\33[37m", end ="")
                    except Exception as e3:
                        #print("Unknown Exception'", e3, "'caught, trying again!\n")
                        continue
            print("\nChecking the subreddit for new posts again!\n")
            driver.get(subreddit_link)
            time.sleep(float(10))
            counter += 1
        except Exception as e2:
            fails += 1
            send_email = False
            print("Unknown Exception'", e2, "'caught, trying again!\n")
            continue
    
    driver.quit()

except Exception as e:
    print("Unknown Exception", e, "caught, library error is likely")
    os.system('pause')
