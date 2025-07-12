import re
import json
import bcrypt
from datetime import datetime
from user import User
from wallet import Wallet
from nbp_client import NBPClient


class UserRegistration:
    def __init__(self, auth_file='users_auth.json', users_file='users_data.json'):
        self.auth_file = auth_file
        self.users_file = users_file
        self.auth = self.load_json(auth_file)
        self.users = self.load_json(users_file)


    @staticmethod
    def load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}


    @staticmethod
    def save_json(data, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)


    @staticmethod
    def is_valid_email(email):
        """Checks if it's an email"""
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None


    def check_mail(self, email):
        """Check email exist in current database"""
        return email not in self.auth


    @staticmethod
    def input_with_limit(text, max_length=25):
        """Limits chars to input"""
        while True:
            value = input(text).strip()
            if len(value) <= max_length:
                return value
            print(f'Too long! Max {max_length} characters')


    @staticmethod
    def validate_age(date_of_birth: str) -> str:
        """Checks if the user is over 18 years old"""
        birth_date = datetime.strptime(date_of_birth, "%d-%m-%Y")
        today = datetime.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1  # in case the user hasn't had birthday this year

        if age < 18:
            raise ValueError("User must be over 18 years old.")
        return date_of_birth

    def get_user_input(self):
        """Input all data requirement in User class"""
        print('Please enter your personal details:')

        first_name = self.input_with_limit('First name:')
        last_name = self.input_with_limit('Last name:')
        phone = input("Phone number (optional): ").strip()
        address = input("Address (optional): ").strip()
                                
        while True:
            account_type = input("Account type (personal/business): ").strip().lower()
            if account_type in ['personal', 'business']:
                break
            print('Please enter "personal" or "business".')

        while True:
            date_of_birth = input("Day of birth (DD-MM-YYYY): ").strip()
            try:
                self.validate_age(date_of_birth)
                break
            except ValueError as e:
                print(e)
                print("Please enter a valid birth date (18+).")

        while True:
            email = input('Email:').strip()
            if not self.is_valid_email(email):
                print('Invalid email format. Try again.')
            elif not self.check_mail(email):
                print('Email address already in use, choose another.')
            else:
                break

        while True:
            password = input('Password (7-20 chars, upper, number):')
            if len(password) < 7:
                print("Your password is too short, try again.")
            elif len(password) > 20:
                print("Your password is too long, try again.")
            elif not any(sign.isupper() for sign in password):
                print("Password must contain an upper case character.")
            elif not any(sign.isdigit() for sign in password):
                print("Password must contain a number.")
            else:
                print("Password accepted.")
                break

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "account_type": account_type,
            "date of birth": date_of_birth,
            "phone_number": phone,
            "address": address,
        }


    def register_user(self):
        user_info = self.get_user_input()

        # Hash password
        hashed = bcrypt.hashpw(user_info['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save auth data (hashed password)
        self.auth[user_info['email']] = {"hashed_pass": hashed}
        self.save_json(self.auth, self.auth_file)

        # Save user personal data (without password)
        user_data = user_info.copy()
        user_data.pop('password')
        self.users[user_info['email']] = user_data
        self.save_json(self.users, self.users_file)

        print(f"Your {user_info['account_type']} account was successfully created.")


    def login(self):
        """Login to account. Password validation. -> Boolean"""
        email = input('Email: ').strip()
        password = input('Password: ').strip()

        if email not in self.auth:
            print('You must register account first.')
            return False

        hashed_pass = self.auth[email]['hashed_pass'].encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), hashed_pass):
            print('Login successful.')
            # We create a User object based on information from the users_file
            user_data = self.users[email]
            user = User(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=email,
                password=None,
                account_type=user_data['account_type'],
                date_of_birth=user_data['date of birth'],
                phone_number=user_data['phone_number'],
                address=user_data['address'])
            self.user_menu(user)
            return user
        else:
            print('Login failed.')
            return None


    def user_menu(self, user: User):
        nbp_client = NBPClient()

        user_menu_mess = """
What would you like to do?
Press 1 to update personal info
Press 2 to create new wallet
Press 3 to show all wallets with them ID 
Press 4 to check balance of choosen wallet
Press 5 to change balance of choosen wallet
Press 6 to delete wallet
Press 7 to transfer funds between your wallets
Press 8 to show current exchange rates
Press X to exit"""

        while True:
            print(user_menu_mess)

            option = input('Choose your option: ').lower().strip()

            if option == 'x':
                print("Goodbye")
                break
            elif option == '1':
                self.update_user_info(user)
            elif option == '2':
                currency = str(input('Choose currecy code, for example PLN, USD ():').strip().upper())
                print(Wallet.create_wallet(user.email, currency))
            elif option == '3':
                print(Wallet.show_all_wallet(user.email))
            elif option == '4':
                currency = str(input('which currency would you like to SEE? (use format like USD, XXX):').strip().upper())
                print(Wallet.check_balance(user.email, currency))
            elif option == '5':
                currency = str(input('Which currency would you like to CHANGE? (use format like USD, XXX):').strip().upper())
                try:
                    amount = float(input('Enter amount of currency: (positive for deposit, negative for withdrawal)'))
                    print(Wallet.transfer_funds(user.email, currency, amount, nbp_client))
                except ValueError:
                    print("Invalid amount. Please enter a number.")
            elif option == '6':
                currency = str(input('Which currency wallet would you like to DELETE? (use format like USD, XXX):').strip().upper())
                print(Wallet.delete_wallet(user.email, currency))
            elif option == '7':
                from_currency = input("Which wallet do you want to transfer funds FROM? (e.g., PLN, USD): ").strip().upper()
                to_currency = input("Which wallet do you want to transfer funds TO? (e.g., PLN, USD): ").strip().upper()
                try:
                    amount = float(input(f"What amount do you want to transfer from {from_currency} to {to_currency}? "))
                    print(Wallet.transfer_between_wallets(user.email, from_currency, to_currency, amount, nbp_client))
                except ValueError:
                    print("Invalid amount. Please enter a number.")
            elif option == '8':
                print(nbp_client.show_current_rates())


            else:
                print("Unrecognized command. Try again.")

    def update_user_info(self, user: User):
        print("Leave blank to keep existing value.")

        first_name = input(f"First name [{user.first_name}]: ").strip() or user.first_name
        last_name = input(f"Last name [{user.last_name}]: ").strip() or user.last_name
        phone = input(f"Phone number [{user.phone_number or ''}]: ").strip() or user.phone_number
        address = input(f"Address [{user.address or ''}]: ").strip() or user.address

        while True:
            account_type_input = input(f"Account type [{user.account_type}] (personal/business): ").strip().lower()
            if account_type_input == '':
                account_type = user.account_type
                break
            elif account_type_input in ['personal', 'business']:
                account_type = account_type_input
                break
            else:
                print('Please enter "personal" or "business", or leave blank to keep current value.')

        user.update_user_info(first_name, last_name, None, phone, address)

        # save changing data
        self.users[user.email]['first_name'] = user.first_name
        self.users[user.email]['last_name'] = user.last_name
        self.users[user.email]['phone_number'] = user.phone_number
        self.users[user.email]['address'] = user.address
        self.users[user.email]['account_type'] = user.account_type

        self.save_json(self.users, self.users_file)
        print("User data updated successfully.")
