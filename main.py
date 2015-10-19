# Note: Python does not have an auto commit. Thus, commit at the end of each statement is important.
# File from introduction to cx_oracle

import sys
import cx_Oracle # the package used for accessing Oracle in Python
import getpass # the package for getting password from user without displaying it

#set up some global variables
connection = 0
curs = 0


def mainScreen():
    loginScreen()
    cont = 1
    while(cont):
        print("What would you like to do?") 
        print(" (1) Search for flights \n (2) Make a booking \n (3) List existing "+
              "bookings \n (4) Cancel a booking. \n (5) Logout.")
        action = int(input("Please enter a number: "))
        if action == 1:
            search_flights()
        if action == 2:
            make_booking()
        if action == 3:
            list_bookings()
        if action == 4:
            cancel_booking()
        if action == 5:
            quit_program()
            cont = 0
        
        

def search_flights():
    pass

def make_booking():
    pass

def list_bookings():
    pass
    
def cancel_booking():
    pass
               
def loginScreen():
    print("Login to Oracle database...")
    
    #Because we're modifying global variables
    global connection
    global curs
    
    #I've hardcoded in my username and password temporarily
    #because it's annoying to type out.
    #but definitely change this back before handing it in
    """user = input("Username [%s]: " % getpass.getuser())
    if not user:
        user=getpass.getuser()
	get password
    pw = getpass.getpass()"""

    
    # The URL we are connnecting to
    conString=''+'thunt'+'/' + 'lpoevaece12' +'@gwynne.cs.ualberta.ca:1521/CRS'
    
    try:
        # Establish a connection in Python
        connection = cx_Oracle.connect(conString)
        curs = connection.cursor()
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)
    print("Logged in.")
    
    action = input("Enter l to login as a user/airline, r to register, and q to quit. ")
    if action == "q":
        quit_program()
    if action == "l":
        attempt_login()
    if action == "r":
        register()
    print("Login successful!")
        
def get_useremail():
    user_email = input("Enter your email: ")

    #add white space to the end of email, until it's 20 characters long
    whitespace = 20 - len(user_email)
    for w in range(whitespace):
        user_email = user_email + " "
    return user_email

def get_userpass():
    user_pass = input("Enter your password: ")
    
    #add white space to the end of password, until its 4 characters long    
    whitespace = 4 - len(user_pass)
    for w in range(whitespace):
        user_pass = user_pass + " "
    return user_pass

def attempt_login():
    print("Login as a user:")
    
    failed = 1
    while (failed):
        user_email = get_useremail()
        user_pass = get_userpass()
        failed = login(user_email, user_pass)

def login(user_email, user_pass):    
    #go into Oracle database, check the user exists
    query = "SELECT * FROM users WHERE email = :user_email AND pass = :user_pass" 
    curs.prepare(query)
    curs.execute(None, {'user_email':user_email, 'user_pass':user_pass})
    results = curs.fetchall()
    if (results):
        return 0
    else:
        print("Login unsuccessful! Please try again")    
        return 1

def register():
    print("Register")

    user_email = get_useremail()
    user_pass = get_userpass()
    
    # insert the row into users
    query = "INSERT INTO users VALUES (:user_email, :user_pass, sysdate)" 
    curs.prepare(query)
    curs.execute(None, {'user_email':user_email, 'user_pass':user_pass})
    
    #and then log the user in
    login(user_email, user_pass)
    
def quit_program():
    print("Quit")
    # close the connection
    #cursInsert.close()
    curs.close()
    connection.close()
    sys.exit()

if __name__ == "__main__":
    #createTable()
    mainScreen()
