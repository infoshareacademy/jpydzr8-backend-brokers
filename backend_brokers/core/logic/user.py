from datetime import datetime

class User:
    def __init__(self, first_name: str, last_name: str, email: str, password: str, account_type: str,
                 date_of_birth: str, phone_number: str = None, address: str = None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.address = address
        self.account_type = account_type

        if date_of_birth:
            self.date_of_birth = self.validate_age(date_of_birth)
        else:
            self.date_of_birth = None

        if account_type == "Comfort":
            self.transaction_limit = 10
            self.wallet_limit = 5
        elif account_type == "Premium":
            self.transaction_limit = 50
            self.wallet_limit = 10

        self.wallets = {}  # currency_code as key, balance as value
        self.transaction_history = []  # user's transaction history

    def validate_age(self, date_of_birth: str) -> str:
        """Checks if the user is over 18 years old"""
        birth_date = datetime.strptime(date_of_birth, "%d-%m-%Y")  # "DD-MM-YYYY" format
        today = datetime.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1  # in case the user hasn't had birthday this year

        if age < 18:
            raise ValueError("User must be over 18 years old.")
        return date_of_birth

    def add_wallet(self, currency_code: str, balance: float = 0) -> None:
        """Adds a currency wallet to the user"""
        if len(self.wallets) < self.wallet_limit:
            self.wallets[currency_code] = balance
        else:
            print(f"Wallet limit ({self.wallet_limit}) reached.")

    def view_wallets(self) -> dict:
        """Display the user's wallets with balances"""
        return self.wallets

    def deposit_to_wallet(self, currency_code: str, amount: float) -> None:
        """Deposit funds into the wallet"""
        if currency_code in self.wallets:
            self.wallets[currency_code] += amount
        else:
            print(f"Wallet for {currency_code} does not exist.")

    def update_user_info(self, first_name: str = None, last_name: str = None, email: str = None,
                         phone_number: str = None, address: str = None) -> None:
        """Updates the user's information"""
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name
        if email:
            self.email = email
        if phone_number:
            self.phone_number = phone_number
        if address:
            self.address = address

    def add_transaction(self, transaction_details: str) -> None:
        """Adds a transaction to user's history"""
        if len(self.transaction_history) < self.transaction_limit:
            self.transaction_history.append(transaction_details)
        else:
            print(f"Transaction limit ({self.transaction_limit}) reached.")