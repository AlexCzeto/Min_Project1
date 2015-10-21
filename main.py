# Note: Python does not have an auto commit. Thus, commit at the end of each statement is important.
# File from introduction to cx_oracle

import sys
import cx_Oracle # the package used for accessing Oracle in Python
import getpass # the package for getting password from user without displaying it

#set up some global variables
connection = 0
curs = 0

def mainScreen():
    login_info = loginScreen()
    cont = 1
    while(cont):
        print("What would you like to do?") 
        print(" (1) Search for flights \n (2) Make a booking \n (3) List existing "+
              "bookings \n (4) Cancel a booking. \n (5) Logout.")
        action = int(input("Please enter a number: "))
        
        #Action 1: Search for flights and print the results
        if action == 1:
            flights = search_flights()
            print("Your search returned ", len(flights), " flights:")
            for flight in flights:
                print(flights[0])
            
        if action == 2:
            make_booking(login_info)
        if action == 3:
            list_bookings(login_info)
        if action == 4:
            cancel_booking(login_info)
        if action == 5:
            log_out(login_info) 
            quit_program()
            cont = 0
        print("\n")
        
        

def search_flights():
    #delete_existing()
    source = input("Enter source airport: ")
    source = find_port(source)
    dest = input("Enter destination airport: ")
    dest = find_port(dest)    
    date = input("Enter date of flight: ")
    query = "SELECT flightno,src,dst,to_char(dep_time, 'hh24:mi'),to_char(arr_time, 'hh24:mi'),price,seats FROM available_flights WHERE src = :source and dep_date = to_date(:sdate,'DD-Mon-YYYY') and dst = :dest"     curs.prepare(query)
    curs.execute(None,{'sdate':date,'source':source,'dest':dest})
    rows= curs.fetchall()
    return rows
    
def make_booking(login_info):
    """
    Make a booking. A user should be able to select a flight (or flights when 
    there are connections) from those returned for a search and book it. The 
    system should get the name of the passenger and check if the name is listed 
    in the passenger table with the user email. If not, the name and the country 
    of the passenger should be added to the passenger table with the user email. 
    Your system should add rows to tables bookings and tickets to indicate that 
    the booking is done (a unique ticket number should be generated by the system). 
    Your system can be used by multiple users at the same time and overbooking is 
    not allowed. Therefore, before your update statements, you probably want to 
    check if the seat is still available and place this checking and your update 
    statements within a transaction. Finally the system should return the ticket 
    number and a confirmation message if a ticket is issued or a descriptive message 
    if a ticket cannot be issued for any reason.
    """
    flights = search_flights()
    
    # Fetch the flight to be booked
    print("Available flights: ")
    i = 1
    for flight in flights:
        print (i, flight)
    select = input("Please enter your selection: ")
    flight = flights[i-1]
    
    # Book the flight
    
    
    
def list_bookings(login_info):
    pass
    
def cancel_booking(login_info):
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
        login_info = attempt_login()
    if action == "r":
        login_info = register()
    print("Login successful!\n")
    #if the user enters a character other than one of the characters specified, then there will be an error.
    # maybe we should fix this before handing it in?
    # but also it's not a top priority
    return login_info
        
        
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
    return (user_email, user_pass)

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
    registered = 0
    
    while(registered == 0):
        user_email = get_useremail()
        user_pass = get_userpass()
        
        try:
            # insert the row into users
            query = "INSERT INTO users VALUES (:user_email, :user_pass, sysdate)" 
            curs.prepare(query)
            curs.execute(None, {'user_email':user_email, 'user_pass':user_pass})
            registered = 1
    
        except cx_Oracle.IntegrityError as exc:
            print("Ooops! It seems like that email has already been registered!")
            choice = input("Enter 'l' to login with this email or 'r' to register a new one. ")
            if choice == "l":
                attempt_login()
    
    #commit the changes
    connection.commit()
    
    #and then log the user in
    login(user_email, user_pass)
    return (user_email, user_pass)
    
def log_out(user_info):
    #update last_login
    user_email = user_info[0]
    user_pass = user_info[1]

    statement = "UPDATE users SET last_login = sysdate WHERE email = :user_email AND pass =:user_pass"
    curs.prepare(statement)
    curs.execute(None, {'user_email':user_email, 'user_pass':user_pass})
    connection.commit()

def delete_existing():
    try:
        query = "drop view available_flights"
        curs.execute(query)
        create_af()
    except cx_Oracle.DatabaseError as exc:
#        error, = exc.args
#        print( sys.stderr, "Oracle code:", error.code)
#        print( sys.stderr, "Oracle message:", error.message)
        if(error.code == 942):
#            print("caught error")
            create_af()
    
    
def create_af():
    print("Hello")
    query = "create view available_flights(flightno,dep_date, src,dst,dep_time,arr_time,fare,seats,price) as select f.flightno, sf.dep_date, f.src, f.dst, f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time)),f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time))+(f.est_dur/60+a2.tzone-a1.tzone)/24 , fa.fare, fa.limit-count(tno), fa.price from flights f, flight_fares fa, sch_flights sf, bookings b, airports a1, airports a2 where f.flightno=sf.flightno and f.flightno=fa.flightno and f.src=a1.acode and f.dst=a2.acode and fa.flightno=b.flightno(+) and fa.fare=b.fare(+) and sf.dep_date=b.dep_date(+)group by f.flightno, sf.dep_date, f.src, f.dst, f.dep_time, f.est_dur,a2.tzone,a1.tzone, fa.fare, fa.limit, fa.price having fa.limit-count(tno) > 0"
    curs.execute(query)
    connection.commit()


def find_port(port_name):
    port_name = port_name.upper()
    if(len(port_name)== 3): 
        query = "SELECT * FROM airports WHERE acode = :port " 
        curs.prepare(query)
        curs.execute(None,{'port':port_name})
        result = curs.fetchall()

        if(result): 
            return result[0][0]
    
    # There was not an exact match!
    port_name = "%"+port_name+"%"
    query = "SELECT * FROM airports WHERE UPPER(city) LIKE :port OR UPPER(name) LIKE :port"
    curs.prepare(query)
    curs.execute(None,{'port':port_name})

    rows = curs.fetchall()
    print("You did not enter a valid airport code! \n Which of the following did you mean?")
    i = 1
    for row in rows:
        print(i, row[1], row[2], row[3])
        i=i+1
    select = int(input("please enter a number: "))
    return (rows[select-1][0])
    
def quit_program():
    print("Quit")
    # close the connection
    #cursInsert.close()
    curs.close()
    connection.close()
    sys.exit()

if __name__ == "__main__":
    mainScreen()

