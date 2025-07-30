import json
from schwifty import IBAN
import random


class Wallet:
    def __init__(
        self, wallet_id: str, owner_id: str, currency: str, iban: int, balance: float
    ):
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
        with open("wallets.json", "r") as f:
            data = json.load(f)

        # create new user, if not exist
        if "users" not in data:
            data["users"] = {}
        if email not in data["users"]:
            data["users"][email] = []

        # get existing wallet IDs of this user
        existing_wallet_ids = {
            wallet["wallet_id"]
            for wallets in data["users"].values()
            for wallet in wallets
        }

        while True:  # makes sure there are no duplicate wallet ids
            wallet_id = str(random.randint(1, 999999999)).zfill(
                9
            )  # generates random id and adds leading zeros up to 9 digits
            if wallet_id not in existing_wallet_ids:
                break

        iban = IBAN.generate(
            "PL", bank_code="252", account_code=wallet_id
        )  # generates valid IBAN

        # creates new wallet with balance = 0
        new_wallet = {
            "wallet_id": wallet_id,
            "currency": currency,
            "iban": iban,
            "balance": 0,
        }

        data["users"][email].append(new_wallet)

        with open("wallets.json", "w") as write_file:
            json.dump(data, write_file, indent=4, ensure_ascii=False)
        return f"Wallet {wallet_id} for user {email} created successfully."

    @staticmethod
    def check_balance(email: str, currency: str):
        """
        returns current balance for wallet of *wallet_id* id
        :param wallet_id: int
        :return: wallet balance (float) or None if wallet does not exist
        """
        with open("wallets.json", "r") as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        for wallet in user_wallets:
            if wallet.get("currency") == currency:
                return wallet.get("balance", 0.0)

        return f"Wallet {currency} not found for user {email}."

    @staticmethod
    def transfer_funds(email: str, currency: str, amount: float, nbp_client):
        """
        Transfers funds to the user's wallet in a given currency.
        Deposits (amount > 0) are assumed to be made in PLN and converted to the target currency.
        Withdrawals (amount < 0) are made directly in the target currency.

        :param email: Email of the user
        :param currency: Currency of the target wallet (e.g. 'PLN', 'USD', 'GBP')
        :param amount: Amount to transfer (positive for deposit, negative for withdrawal)
        :param nbp_client: instance of NBPClient
        :return: Success or error message
        """
        with open("wallets.json", "r") as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        amount_to_add = amount
        deposit_currency = "PLN"  # Default deposit currency

        # --- Deposit Logic (if amount > 0) ---
        if amount > 0:
            if currency != deposit_currency:
                # Convert PLN to the target currency
                try:
                    # Exchange rate for converting from PLN to Target Currency.
                    # NBPClient.rates relies on 'PLN' being set to 1.0.
                    exchange_rate = (
                        nbp_client.rates[deposit_currency] / nbp_client.rates[currency]
                    )
                    converted_amount = amount * exchange_rate
                    print(
                        f"Amount {amount} PLN has been converted to {converted_amount:.2f} {currency} based on the current exchange rate."
                    )
                    amount_to_add = converted_amount
                except (KeyError, TypeError):
                    return f"Error converting currency. No exchange rate found for {currency}."

        # --- Transaction Application ---

        for wallet in user_wallets:
            if wallet["currency"] != currency:
                continue

            # Check if balance will be sufficient for withdrawal (applies only if amount_to_add is negative)
            if wallet["balance"] + amount_to_add < 0:
                # For withdrawals, we show the original withdrawal amount
                return (
                    f"Insufficient funds. Current balance: {wallet['balance']} {wallet['currency']}, "
                    f"attempted withdrawal: {-amount} {wallet['currency']}."
                )

            wallet["balance"] += round(amount_to_add, 2)

            with open("wallets.json", "w") as f:
                json.dump(data, f, indent=4)

            return (
                f"Transaction successful. New balance for wallet ({currency}): "
                f"{wallet['balance']:.2f} {wallet['currency']}."
            )

        return f"No wallet in currency '{currency}' found for user '{email}'."

    @staticmethod
    def show_all_wallet(email: str) -> str:

        with open("wallets.json", "r") as f:
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
        with open("wallets.json", "r") as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        for i, wallet in enumerate(user_wallets):
            if wallet["currency"] != currency:
                continue

            if wallet["balance"] != 0:
                return (
                    f"Cannot delete wallet {wallet['wallet_id']} in {currency}: "
                    f"balance must be 0, current balance is {wallet['balance']} {currency}."
                )

            deleted_wallet = user_wallets.pop(i)

            with open("wallets.json", "w") as f:
                json.dump(data, f, indent=4)

            return (
                f"Deleted wallet: {deleted_wallet['wallet_id']} "
                f"({deleted_wallet['currency']}, balance: {deleted_wallet['balance']})."
            )

        return f"No wallet with currency '{currency}' found for user '{email}'."

    @staticmethod
    def transfer_between_wallets(
        email: str, from_currency: str, to_currency: str, amount: float, nbp_client
    ):
        """
        Transfers funds from one wallet to another for the same user,
        converting the amount at the current exchange rate.

        :param email: User's email
        :param from_currency: Source wallet currency
        :param to_currency: Destination wallet currency
        :param amount: Amount to transfer
        :param nbp_client: NBP client instance
        :return: Success or error message
        """
        if from_currency == to_currency:
            return "Wallet currencies must be different."

        if amount <= 0:
            return "Transfer amount must be positive."

        with open("wallets.json", "r") as f:
            data = json.load(f)

        user_wallets = data.get("users", {}).get(email)
        if not user_wallets:
            return f"User {email} not found."

        from_wallet = next(
            (w for w in user_wallets if w["currency"] == from_currency), None
        )
        to_wallet = next(
            (w for w in user_wallets if w["currency"] == to_currency), None
        )

        if not from_wallet:
            return f"Source wallet in currency '{from_currency}' not found."
        if not to_wallet:
            return f"Destination wallet in currency '{to_currency}' not found."

        if from_wallet["balance"] < amount:
            return f"Insufficient funds in wallet '{from_currency}'."

        try:
            exchange_rate = (
                nbp_client.rates[from_currency] / nbp_client.rates[to_currency]
            )
            converted_amount = amount * exchange_rate
        except (KeyError, TypeError):
            return f"Error converting currencies. No rate found for {from_currency} or {to_currency}."

        from_wallet["balance"] -= amount
        to_wallet["balance"] += round(converted_amount, 2)

        with open("wallets.json", "w") as f:
            json.dump(data, f, indent=4)

        return (
            f"Transfer successful. {amount:.2f} {from_currency} has been transferred to {to_currency} wallet.\n"
            f"New balances: {from_currency}: {from_wallet['balance']:.2f}, {to_currency}: {to_wallet['balance']:.2f}"
        )
