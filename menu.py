def main_menu():
    print("\n**** KANTOR INTERNETOWY - MENU GLÓWNE****")
    print('1. Zarejestruj się.')
    print('2. Zaloguj się.')
    print('3. Kurs walut.')
    print('4. Kurs złota.')
    print('5. Wyjdź z kantoru.')

def account_selection():
    print("\n**** KANTOR INTERNETOWY - WYBÓR KONTA ****")
    print('1. Konto prywatne.')
    print('2. Konto firmowe.')
    print('3. Konto administratora.')
    print('4. Przejdź do menu głównego.')

def account_menu():
    print("\n**** KANTOR INTERNETOWY - MENU KONTA ****")
    print('1. Utwórz nowy portfel.')
    print('2. Wybór portfela.')
    print('3. Historia transakcji.')
    print('4. Alert walutowy.')
    print('5. Kurs walut.')
    print('6. Kurs złota.')
    print('7. Wyloguj się.')
    print('8. Usuń konto.')

def wallet_menu():
    print("\n**** KANTOR INTERNETOWY - PORTFEL - ****")
    print('1. Stan konta.')
    print('2. Aktualny kurs.')
    print('3. Wpłatomat.')
    print('4. Opóźniona wymiana.')
    print('5. Historia portfela.')
    print('6. Wypłata środków.')
    print('7. Wyjdź z portfela.')
    print('8. Usuń portfel.')


def currency_exchange():
    while True:
        main_menu()
        choice = input("\nWybierz numer funkcji której chcesz użyć: ")
        if choice == "1":
            pass
        elif choice == "2":
            while True:
                account_selection()
                choice = input("\nWybierz numer funkcji której chcesz użyć: ")
                if choice == "1":
                    while True:
                        account_menu()
                        choice = input("\nWybierz numer funkcji której chcesz użyć: ")
                        if choice == "1":
                            pass
                        elif choice == "2":
                            while True:
                                wallet_menu()
                                choice = input("\nWybierz numer funkcji której chcesz użyć: ")
                                if choice == "1":
                                    pass
                                elif choice == "2":
                                    pass
                                elif choice == "3":
                                    pass
                                elif choice == "4":
                                    pass
                                elif choice == "5":
                                    pass
                                elif choice == "6":
                                    pass
                                elif choice == "7":
                                    account_menu()
                                    break
                                elif choice == "8":
                                    pass
                                else:
                                    print("\nNieprawidłowy wybór. Spróbuj ponownie.")
                                continue
                        elif choice == "3":
                            pass
                        elif choice == "4":
                            pass
                        elif choice == "5":
                            pass
                        elif choice == "6":
                            pass
                        elif choice == "7":
                            account_selection()
                            break
                        elif choice == "8":
                            pass
                        else:
                            print("\nNieprawidłowy wybór. Spróbuj ponownie.")
                        continue
                elif choice == "2":
                    while True:
                        account_menu()
                        choice = input("\nWybierz numer funkcji której chcesz użyć: ")
                        if choice == "1":
                            pass
                        elif choice == "2":
                            while True:
                                wallet_menu()
                                choice = input("\nWybierz numer funkcji której chcesz użyć: ")
                                if choice == "1":
                                    pass
                                elif choice == "2":
                                    pass
                                elif choice == "3":
                                    pass
                                elif choice == "4":
                                    pass
                                elif choice == "5":
                                    pass
                                elif choice == "6":
                                    pass
                                elif choice == "7":
                                    account_menu()
                                    break
                                elif choice == "8":
                                    pass
                                else:
                                    print("\nNieprawidłowy wybór. Spróbuj ponownie.")
                                continue
                        elif choice == "3":
                            pass
                        elif choice == "4":
                            pass
                        elif choice == "5":
                            pass
                        elif choice == "6":
                            pass
                        elif choice == "7":
                            account_selection()
                            break
                        elif choice == "8":
                            pass
                        else:
                            print("\nNieprawidłowy wybór. Spróbuj ponownie.")
                        continue
                elif choice == "3":
                    pass
                elif choice == "4":
                    main_menu()
                    break
                else:
                    print("\nNieprawidłowy wybór. Spróbuj ponownie.")
                continue
        elif choice == "3":
            pass
        elif choice == "4":
            pass
        elif choice == "5":
            print("\nDo zobaczenia!")
            break
        else:
            print("\nNieprawidłowy wybór. Spróbuj ponownie.")

currency_exchange()