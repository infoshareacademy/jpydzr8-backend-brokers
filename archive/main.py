from user_registration import UserRegistration


def main():
    app = UserRegistration()

    main_menu_mess = """
Welcome to us cantor! 
We are here for you!

Press 1 to create an account.
Press 2 to login.
Press X to exit.
"""

    while True:
        print(main_menu_mess)
        option = input("Choose your option: ").lower().strip()

        if option == "x":
            print("Goodbye")
            break
        elif option == "1":
            print("Let's create your account.")
            app.register_user()
        elif option == "2":
            print("Let's login.")
            current_user = app.login()
            if current_user:
                print(f"User {current_user.first_name} {current_user.last_name}")
                break
        else:
            print("Unrecognized command. Try again.")


if __name__ == "__main__":
    main()
