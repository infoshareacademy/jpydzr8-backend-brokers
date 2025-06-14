import json
from schwifty import IBAN
import random


class Wallet:
    def  __init__(self, wallet_id: str, owner_id: str, currency: str, iban: int, balance: float):
        self.wallet_id = wallet_id
        self.currency = currency
        self.iban = iban #International Bank Account Number
        self.balance = balance
        self.owner = owner_id
        self.history = {}


    @staticmethod
    def create_wallet(owner_id: str, currency: str):
        """
        Creates a new wallet of currency *currency* for user *owner_id*, random wallet_id, valid IBAN, saves data to file.
        :param owner_id: user identifier
        :param currency: currency code. TODO: set a list of available currencies?
        :return: saves new wallet to wallets.json and returns a confirmation.
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)
        while True:    # makes sure there are no duplicate wallet ids
            wallet_id = str(random.randint(1, 999999999)).zfill(9) #generates random id and adds leading zeros up to 9 digits
            if wallet_id not in data:
                break
        iban = IBAN.generate("PL", bank_code='25263241', account_code=wallet_id) #generates valid IBAN
        data[wallet_id] = [owner_id, currency, iban, 0] #creates new wallet with balance = 0
        with open('wallets.json', 'w') as write_file:
            json.dump(data, write_file, indent=4)
        return f"Wallet {wallet_id} for user {owner_id} created successfully."


    @staticmethod
    def check_balance(wallet_id: str) -> float|str:
        """
        returns current balance for wallet of *wallet_id* id
        :param wallet_id: int
        :return: wallet balance (float) or None if wallet does not exist
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)
        if str(wallet_id) in data.keys():
            return data[wallet_id][3]
        else:
            return f"Wallet {wallet_id} was not found in the DB."


    @staticmethod
    def transfer_funds(wallet_id: int|str, amount: float):
        """
        changes balance on the account linked to wallet of *wallet_id* by amount *amount*
        :param wallet_id:
        :param amount: amount to be transferred in the wallet's currency.
                        Use positive values for deposits and negative values for withdrawals.
        :return:
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)
        if str(wallet_id) in data.keys():
            if data[wallet_id][3] + amount > 0:
                data[wallet_id][3] += amount
                with open('wallets.json', 'w') as write_file:
                    json.dump(data, write_file, indent=4)
            else:
                raise Exception(f"Wallet {wallet_id} has a balance of {data[wallet_id][3]} {data[wallet_id][1]}. This is insufficient to withdraw {amount * -1} {data[wallet_id][1]}.")
        else:
            raise Exception(f"Wallet {wallet_id} was not found in the DB.")


print(Wallet.check_balance('018315965'))
Wallet.transfer_funds('018315965', 21.25)
print(Wallet.check_balance('090957373'))
print(Wallet.create_wallet('jkowalski123', 'PLN'))
# Wallet.transfer_funds('018315965', -221.25)