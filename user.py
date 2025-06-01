class User:
    def __init__(self, first_name, last_name, email, password, date_of_birth=None, phone_number=None, address=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.date_of_birth = date_of_birth # do weryfikacji wieku użytkownika, zakładamy, że z kantoru mogą korzystać osoby pełnoletnie
        self.phone_number = phone_number
        self.address = address
        self.wallets = {}
        self.created_at = None  # data utworzenia konta
        self.updated_at = None  # data ostatniej aktualizacji
        self.transaction_history = []  # historia transakcji użytkownika
        self.verification_status = "unverified"  # status weryfikacji użytkownika - czy potrzebujemy tego?

    def add_wallet(self, balance=0):
        """Dodaje portfel walutowy do użytkownika"""
        """do metody przekażemy currency_code z klasy Currency np."""

    def view_wallets(self):
        """wyświetla portfele użytkownika i ich salda"""

    def deposit_to_wallet(self):
        """Wpłata środków do portfela użytkownika"""
        """amount jako atrybut"""
        """do metody przekażemy currency_code z klasy Currency np."""

    def update_user_info(self):
        """Aktualizuje dane użytkownika, tj. imie, nazwisko, email, nr tel, adres?"""

    def add_transaction(self):
        """Dodaje transakcję do historii"""
        """do metody przekażemy currency_code, transaction_details z klasy Transaction np."""

    def verify_user(self):
        """Zmienia status weryfikacji użytkownika"""
        """Czy potrzebujemy tego?"""
