import requests
import json
from prettytable import PrettyTable


def get_current_rates():
    """
    Retrieves current 'mid' exchange rates from NBP (Polish National Bank)
    and saves them to current_rates.json file for future use.
    No parameters accepted.
    """
    api_url = "https://api.nbp.pl/api/exchangerates/tables/A?format=json"
    response = requests.get(api_url)
    if response.status_code != 200:
        return f"Exchange rates have NOT been updated. Received code {response.status_code}."
    else:
        with open('current_rates.json', 'w') as write_file:
            json.dump(response.json(), write_file)
        return "Exchange rates have been updated."

# print(get_current_rates())


def calculate_exchange_rates(spread=0.00, currencies_list=['THB', 'USD', 'AUD', 'HKD', 'CAD', 'NZD', 'SGD', 'EUR', 'HUF', 'CHF', 'GBP', 'UAH', 'JPY', 'CZK', 'DKK', 'ISK', 'NOK', 'SEK', 'RON', 'BGN', 'TRY', 'ILS', 'CLP', 'PHP', 'MXN', 'ZAR', 'BRL', 'MYR', 'IDR', 'INR', 'KRW', 'CNY', 'XDR']):
    """
    Uses 'mid' exchange rates stored in current_rates.json file. Run get_current_rates() to update exchange rates from NBP API.
    :param spread: difference between Sell and Buy prices (percent). Assumes 0 if left blank.
    :param currencies_list: list containing currency codes (ISO 4217) to be processed. Returns table for all currencies if left blank.
    :return: formatted table containing listed currencies and Sell/Buy prices calculated by adding/subtracting spread value from 'mid' price.
    """
    table = [["Symbol", "Waluta", "Skup", "Sprzedaż"]] # this is a table header
    with open('current_rates.json', 'r') as current_rates:
        current_rates_dict = {}
        data = json.load(current_rates)[0]["rates"]
        for n in data:
            code = n["code"]
            mid_rate = n["mid"]
            currency = n["currency"]
            current_rates_dict[code] = [mid_rate, currency]

    try:
        for curr in currencies_list:
            curr_calc = [curr, current_rates_dict[curr][1], round(current_rates_dict[curr][0] * (1 - spread/200), 4), round(current_rates_dict[curr][0] * (1 + spread/200), 4)]
            table.append(curr_calc) #adds rows to the table
    except KeyError:
       print("Currency not found. Please choose from 'THB', 'USD', 'AUD', 'HKD', 'CAD', 'NZD', 'SGD', 'EUR', 'HUF', 'CHF', 'GBP', 'UAH', 'JPY', 'CZK', 'DKK', 'ISK', 'NOK', 'SEK', 'RON', 'BGN', 'TRY', 'ILS', 'CLP', 'PHP', 'MXN', 'ZAR', 'BRL', 'MYR', 'IDR', 'INR', 'KRW', 'CNY', 'XDR'.")

    tab = PrettyTable(table[0]) # formats header
    tab.add_rows(table[1:])     # formats rows with currencies
    return tab

# print(calculate_exchange_rates(1.725, ))
