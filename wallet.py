import json
from schwifty import IBAN
import random


class Wallet:
    def __init__(self, wallet_id: str, owner_id: str, currency: str, iban: int, balance: float):
        self.wallet_id = wallet_id
        self.currency = currency
        self.iban = iban  # International Bank Account Number
        self.balance = balance
        self.owner = owner_id
        self.history = {}

    @staticmethod
    def create_wallet(email: str, currency: str):
        """
        Creates a new wallet of currency *currency* for user *owner_id*, random wallet_id, valid IBAN, saves data to file.
        :param owner_id: user identifier
        :param currency: currency code. TODO: set a list of available currencies?
        :return: saves new wallet to wallets.json and returns a confirmation.
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)
        
        #create new user, if not exist
        if "users" not in data:
            data["users"] = {}
        if email not in data["users"]:
            data["users"][email] = []
        
        #get existing wallet IDs of this user
        existing_wallet_ids = {
            wallet["wallet_id"]
            for wallets in data["users"].values()
            for wallet in wallets
    }

        while True:    # makes sure there are no duplicate wallet ids
            wallet_id = str(random.randint(1, 999999999)).zfill(9) #generates random id and adds leading zeros up to 9 digits
            if wallet_id not in existing_wallet_ids:
                break

        iban = IBAN.generate("PL", bank_code='252', account_code=wallet_id) #generates valid IBAN

         #creates new wallet with balance = 0
        new_wallet = {
            "wallet_id": wallet_id,
            "currency": currency,
            "iban": iban,
            "balance": 0
        }

        data["users"][email].append(new_wallet)

        with open('wallets.json', 'w') as write_file:
            json.dump(data, write_file, indent=4, ensure_ascii=False)
        return f"Wallet {wallet_id} for user {email} created successfully."


    @staticmethod
    def check_balance(email: str, currency: str):
        """
        returns current balance for wallet of *wallet_id* id
        :param wallet_id: int
        :return: wallet balance (float) or None if wallet does not exist
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        for wallet in user_wallets:
            if wallet.get("currency") == currency:
                return wallet.get("balance", 0.0)

        return f"Wallet {currency} not found for user {email}."


    @staticmethod
    def transfer_funds(email: str, currency: str, amount: float):
        """
        Transfers funds to the user's wallet in a given currency.

        :param email: Email of the user
        :param currency: Currency of the target wallet (e.g. 'PLN', 'USD', 'GBP')
        :param amount: Amount to transfer (positive for deposit, negative for withdrawal)
        :return: Success or error message
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        for wallet in user_wallets:
            if wallet['currency'] != currency:
                continue

            #check status after tranfer, dont let make transfer if balance will be less then 0    
            if wallet['balance'] + amount < 0:
                return(f"Insufficient funds. Current balance: {wallet['balance']} {wallet['currency']}, "
                       f"attempted withdrawal: {-amount} {wallet['currency']}.")
            
            wallet['balance'] += amount

            with open('wallets.json', 'w') as f:
                json.dump(data, f, indent=4)

            return (f"Transaction successful. New balance for wallet ({currency}): "
                    f"{wallet['balance']} {wallet['currency']}.")

        return f"No wallet in currency '{currency}' found for user '{email}'."
        
    @staticmethod
    def show_all_wallet(email: str) -> str:

        with open('wallets.json', 'r') as f:
            data = json.load(f)
        
        wallets = data.get("users", {}).get(email)
        if not wallets:
            return f"User '{email}' has no wallets."

        result = f"Wallets for {email}:\n"
        for wallet in wallets:
            result += f"• Wallet ID: {wallet['wallet_id']}, Currency: {wallet['currency']}, Balance: {wallet['balance']}\n"
        return result
    

    def delete_wallet(email: str, currency: str) -> str:
        """
        Deletes the first wallet in the given currency for a specified user.

        :param email: Email of the user
        :param currency: Currency of the wallet to delete
        :return: Success or error message
        """
        with open('wallets.json', 'r') as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."
        
        for i, wallet in enumerate(user_wallets):
            if wallet["currency"] != currency:
                continue

            if wallet["balance"] != 0:
                return (f"Cannot delete wallet {wallet['wallet_id']} in {currency}: "
                        f"balance must be 0, current balance is {wallet['balance']} {currency}.")

            deleted_wallet = user_wallets.pop(i)

            with open('wallets.json', 'w') as f:
                json.dump(data, f, indent=4)

            return (f"Deleted wallet: {deleted_wallet['wallet_id']} "
                    f"({deleted_wallet['currency']}, balance: {deleted_wallet['balance']}).")

        return f"No wallet with currency '{currency}' found for user '{email}'."