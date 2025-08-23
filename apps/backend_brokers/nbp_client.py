import requests


class NBPClient:
    def __init__(self):
        self.base_url = "https://api.nbp.pl/api/exchangerates/tables/A/"
        self.rates = self.get_exchange_rates()

    def get_exchange_rates(self):
        """
        Fetches current exchange rates from NBP table A and returns them in a dictionary.
        """
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            data = response.json()
            rates = {rate["code"]: rate["mid"] for rate in data[0]["rates"]}
            rates["PLN"] = 1.0  # Set PLN rate to 1 for easier calculations
            return rates
        except requests.exceptions.RequestException as e:
            print(f"Error fetching exchange rates: {e}")
            return None

    def show_current_rates(self):
        """
        Displays the current exchange rates from NBP.
        """
        if not self.rates:
            return "Could not fetch exchange rates. Please try again later."

        output = "Current Exchange Rates (as of today):\n"
        for currency, rate in self.rates.items():
            if currency == "PLN":
                continue
            output += f"• 1 {currency} = {rate:.4f} PLN\n"
        return output
