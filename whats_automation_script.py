#--------------------------------------------------------------------------------------------
# LIBRARIES

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException, \
                                        NoSuchElementException, \
                                        ElementNotInteractableException, \
                                        UnexpectedAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import warnings
import datetime
import logging
import urllib
import time
import re
#--------------------------------------------------------------------------------------------
# CODE CONFIGURATION

# Logging
logging.basicConfig(level = logging.INFO, 
                    filename='bot_history.log', 
                    format = '%(asctime)s - %(levelname)s - %(message)s')

# Warnings
warnings.simplefilter("ignore")

# State variables initialization
state_variable = 'send_msg_1'
skip_iteration = False

# Expected exceptions
exceptions = TimeoutException or NoSuchElementException or ElementNotInteractableException or UnexpectedAlertPresentException

#--------------------------------------------------------------------------------------------
# FUNCTIONS

def format_telephone_number(phone_number):
    phone_number = str(phone_number)
    phone_number = phone_number.replace(' ', '')
    if (len(phone_number) == 8) or (len(phone_number) == 9):
        phone_number = '41' + phone_number # Add 41 to numbers without area code
    phone_number = '55' + re.sub('[\(\)]', '', phone_number) # Remove '(', ')', ' ' and add '55'
    return phone_number

def clear_name(name):
    name = re.sub('[?]', '', name) # Removes '?'
    name = name.split()[0] if name else '' # Only first name
    name = name.capitalize()
    return name

#---------------------------------------------------------------------------------------------
# DATA IMPORT AND TREATMENT

# Data file path
path = r'*'

# DF columns
cols = ['Lead', 'Nome', 'Número', 'E-mail']

# Import list
lista = pd.read_excel(path, usecols=cols)

# All fields must be str
lista = lista.astype(str)

# Apply both functions
lista['First name'] = lista['Nome'].apply(lambda x: clear_name(x))
lista['Formatted number'] = lista['Número'].apply(format_telephone_number)

# Add a marker feature to df
lista['Already sent'] = 0

# Drop duplicates
lista = lista.drop_duplicates(subset=['Número'], keep='first')

# -------------------------------------------------------------------------------------------------------------------------------------
# FEATURE ENGINEERING (Customer categorization)

padroes = []

# Real state categories
alto = ['Montalsino','Montalcino', 'Beaumont', 'Saint Paul', 'Lumière', 'Luimiere', 'Vitra', 'Jardim Los Angeles', 'Chateau Latour', 'LANDSCAPE','oas ', 'OÁS', 'DUPLEX', 'Palazzo Lumini', 'Carminatti', 'Milano', 'vizione', 'CENTRO MÉDICO BATEL', 'Cadastro BIOOS - Ellas Digital', 'STAY BATEL', 'La Défense']
medio_alto = ['Vitória Régia', 'Aporé', 'Ed. Champagnat', 'The Five', 'Visionist', 'Chateau Boulevard', 'Unikko', 'Lp Oxygen','Nort Hill', 'Duet', 'Vivance', 'Explore', 'Sou', 'Equi Seminário', 'Lumière Condominium', 'Oasis']
mcmv = ['San Donato', 'LYX','Cabernet', 'Chievo', 'Oregon', 'PCVA', 'CORES DO OUTONO', 'Carminatti', 'PLURAL']

# Label column engineering
for descricao in lista['Lead']:
    if any(elemento.upper() in descricao.upper() for elemento in alto):
        padroes.append('Alto')
    elif any(elemento.upper() in descricao.upper() for elemento in medio_alto):
        padroes.append('Médio alto')
    elif any(elemento.upper() in descricao.upper() for elemento in mcmv):
        padroes.append('Econômico')
    else:
        padroes.append('Médio')

# Add new column
lista['Padrão'] = padroes

# -------------------------------------------------------------------------------------------------------------------------------------
# X PATHS

x_path_text_terminal = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p/span'

x_path_attachment_button = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div/div/div'

x_path_load_image_input = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/ul/div/div[2]/li/div/input'
                          
x_path_text_attachment_terminal = '//*[@id="app"]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div/p/span'

x_path_image_message = '//*[@id="app"]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]/p'

x_path_pop_up = '//*[@id="app"]/div/span[2]/div/span/div/div/div/div'

x_path_text_pop_up = '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[1]'

x_path_ok_button_error_pop_up = '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[2]/div/button'                             
# -------------------------------------------------------------------------------------------------------------------------------------
# CUSTOM CONTENT

# Mesages
custom_initial_message = 'Muito prazer, meu nome é Lunardi, sou consultor de investimentos especialista da MAP Imobiliária. Trabalho com todas as categorias de imóveis.'
image_message_economico = 'Soube aqui pela imobiliária que você teve interesse em imóveis há um tempo atrás. Agora com as novas condições do Minha Casa, Minha Vida, você pode estar mais perto do seu sonho que que imagina! O que acha do nosso lançamento?'
image_message_medio = 'Soube aqui pela imobiliária que você teve interesse em imóveis há um tempo atrás. Com nossas atuais oportunidades, você pode estar mais perto que do que imagina de fazer um excelente negócio! Gostaria de saber o que acha do nosso novo lançamento:'
image_message_medio_alto = 'Soube aqui pela imobiliária que você teve interesse em imóveis há um tempo atrás. Com nossas atuais oportunidades, você pode estar mais perto que do que imagina de fazer um excelente negócio! Gostaria de saber o que acha do nosso novo lançamento:'
image_message_alto = 'Soube aqui pela imobiliária que você teve interesse em imóveis há um tempo atrás. Estou aqui para atender você de forma diferenciada e exclusiva, com as melhores oportunidades do mercado. O que acha do nosso novo lançamento?'

# Images
path_image_alto = r'*'
path_image_medio_alto = r'*'
path_image_medio = r'*'
path_image_mcmv = r'*'

# ------------------------------------------------------------------------------------------------------------
# GREETING (Depending on day period)

# Check current time
real_time = datetime.datetime.now().time()

# Reference of daytime
morning = datetime.time(6, 0, 0)  # 6:00:00
afternoon = datetime.time(12, 0, 0)  # 12:00:00
evening = datetime.time(18, 0, 0)  # 18:00:00

# Select the message
if real_time < morning:
    greeting = 'Boa noite'
elif real_time < afternoon:
    greeting = 'Bom dia'
elif real_time < evening:
    greeting = 'Boa tarde'
else:
    greeting = 'Boa noite'

# -----------------------------------------------------------------------------------------------------------------
# WEB AUTOMATION PROCESS

# Open browser and load page
messager = webdriver.Chrome()
messager.get(url="https://web.whatsapp.com/")

# Timeout time exception
timeout = 5

# Webdriver function
wait = WebDriverWait(messager, timeout)

# Logging in and scanning wait time
while len(messager.find_elements(By.ID, 'side')) < 1:
    time.sleep(1)

# Web automation loop
for i in range(0, len(lista)):

    if (lista['Already sent'][i] == 1 or lista['Número'][i] == 'nan55' or lista['Nome'][i] == 'nan'):
        continue
    
    skip_iteration = False
    
    if state_variable == 'send_msg_1':
        name = lista['First name'][i]
        number = lista['Formatted number'][i]
        initial_text = urllib.parse.quote(f'{greeting}, {name}!!! Tudo bem?!\n{custom_initial_message}')
        link = f'https://web.whatsapp.com/send?phone={number}&text={initial_text}'
    
    if state_variable == 'send_msg_2':
        link = f'https://web.whatsapp.com/send?phone={number}'
    
    # Open the chat and write the text
    messager.get(link)

    try:
        # Wait it to load
        while len(messager.find_elements(By.XPATH, x_path_text_terminal)) < 1:
            time.sleep(1)
            
            #while len(messager.find_elements(By.XPATH, x_path_text_pop_up)) >= 1:
            while len(messager.find_elements(By.XPATH, x_path_text_pop_up)) >= 1:
                
                time.sleep(1) 
                if len(messager.find_elements(By.XPATH, x_path_ok_button_error_pop_up)) >= 1:
                    ok_button_error_pop_up = wait.until(EC.element_to_be_clickable((By.XPATH, x_path_ok_button_error_pop_up)))
                    ok_button_error_pop_up.click()
                    
                    
    except TimeoutException or NoSuchElementException or ElementNotInteractableException or UnexpectedAlertPresentException:
        i = i - 1
        continue
    
        
    try:
        # Message 1: Greeting text
        if state_variable == 'send_msg_1':
            # Press enter key to send msg 1
            text_message = messager.find_element(By.XPATH, x_path_text_terminal)
            text_message.send_keys(Keys.ENTER)
            state_variable = 'send_msg_2'
    except TimeoutException or NoSuchElementException or ElementNotInteractableException or UnexpectedAlertPresentException:
            #print('Exceção envio msg 1\n')                  
            continue
    
    
    try:
        # Message 2: Image and description sending
        if state_variable == 'send_msg_2':
            # Click on attachment button
            attachment_button = wait.until(EC.element_to_be_clickable((By.XPATH, x_path_attachment_button)))
            attachment_button.click()
            time.sleep(2)
        
        # Select image and message depending on customer category
            if lista['Padrão'][i] == 'Alto':
                path_image = path_image_alto
                image_message = image_message_alto
            elif lista['Padrão'][i] == 'Médio alto':
                path_image = path_image_medio_alto
                image_message = image_message_medio_alto
            elif lista['Padrão'][i] == 'Médio':
                path_image = path_image_medio
                image_message = image_message_medio
            else:
                path_image = path_image_mcmv
                image_message = image_message_economico
        
        # Load image
            load_image_input = messager.find_element(By.XPATH, x_path_load_image_input)
            load_image_input.send_keys(path_image)
            time.sleep(3)
        
        # Write image text
            text_attachment_terminal = wait.until(EC.visibility_of_element_located((By.XPATH, x_path_image_message)))
            text_attachment_terminal.send_keys(image_message)
            time.sleep(3)
        
        # Press enter and send img and text
            text_terminal = wait.until(EC.visibility_of_element_located((By.XPATH, x_path_text_attachment_terminal)))
            text_terminal.send_keys(Keys.ENTER)
            time.sleep(3)
            
    except TimeoutException or NoSuchElementException or ElementNotInteractableException or UnexpectedAlertPresentException:
            continue
                
    # Change state variable
    state_variable = 'send_msg_1'
    
    # Mark row as already sent
    lista['Already sent'][i] = 1
    
    # Wait time for the next msgs
    print(i)
    print(lista['Nome'][i])
    time.sleep(3)
    
messager.quit()
