
#Users rejestration

# To do list:
# change temporary dict to json file (its some idea to add date of creation of account)
# hashing
# change on OOP


import re


#temporary dict for testing 
our_users = {
            'admin@admin.com.pl': {
                'login': 'admin',
                'account_type': 'personal',
                'acc_pass': 'Admin$1234'},
            'admin2@admin.eu': {
                'login': 'admin2',
                'account_type': 'business',
                'acc_pass': 'Admin$2345'}
            }

def is_valid_email(mail):
    # i copy this regex :)
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, mail) is not None

def check_mail():
    while True:
        user_mail = input("""
Enter your email adres:
Press X to back to Rejestration menu.
""")
        if user_mail.lower() == 'x':
            return None
        elif not is_valid_email(user_mail):
            print('This is not correct email adress, try again.')
        elif user_mail in our_users:
            print('Email adres alredy in use, choose other.')
        else:
            return user_mail


def check_login():   
    while True:
        user_name = input("""
Enter your username:
Minimum 5 sign, maximum 20. 
Press X to back to Rejestration menu.
""")
        if user_name.lower() == 'x':
            return None
        elif len(user_name) < 5:
            print('Your username is too short, try again')
        elif len(user_name) > 20:
            print('Your username is too long, try again')
        else:
            print(f'Username {user_name} accepted.')
            return user_name



def check_pass():
    while True:
        acc_pass = input("""
Enter your password:
Minimum 7 sign, maximum 16.
Minimum one uppercase character.
Minimum one number.
Press X to back to Rejestration menu.
""")
        if acc_pass.lower() == 'x':
            return None
        elif len(acc_pass) < 7:
            print('Your password is too short, try again')
        elif len(acc_pass) > 16:
            print('Your password is too long, try again')
        elif not any(sign.isupper() for sign in acc_pass):
            print('Your password does not contain an uppercase character ')
        elif not any(sign.isdigit() for sign in acc_pass):
            print('Your password does not contain a number')
        else:
            print('Password accepted.')
            return acc_pass



def new_user_rejestration():
    while True:
        print("""
Thank you for wanting to join us!
Press X to back to Main Menu.
Press 1 to create a personal account.
Press 2 to create a business account.
Press 3 to login.
""")
        rejestration_option = input('Choose your option:')

        if rejestration_option.lower() == 'x':
            print('Back to Main Menu')
            break                                              #break for now, later back to main menu
        
        elif rejestration_option == '1':
            print('Creating a personal account')
            user_mail = check_mail()
            if user_mail is None:
                break
            user_name = check_login()
            if user_name is None:
                break
            acc_pass = check_pass()
            if acc_pass is None:
                break
            our_users[user_mail] = {'login': user_name,
                                    'account_type': 'personal',
                                    'acc_pass': acc_pass}
            print('Your personal account was succesffuly created')
            continue

                
        elif rejestration_option == '2':
            print('Creating a business account')
            user_mail = check_mail()
            if user_mail is None:
                break
            user_name = check_login()
            if user_name is None:
                break
            acc_pass = check_pass()
            if acc_pass is None:
                break
            our_users[user_mail] = {'login': user_name,
                                    'account_type': 'business',
                                    'acc_pass': acc_pass}
            print('Your business account was succesffuly created')
            continue

        elif rejestration_option == '3':
            print('In preparation')                             #break for now, later back to login menu
            break

        else:
            print("I didn't understand the command. Try again.")



if __name__ == '__main__':
    new_user_rejestration()
    print(our_users)