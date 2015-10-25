# Note: Python does not have an auto commit. Thus, commit at the end of each statement is important.
# File from introduction to cx_oracle

import sys
import cx_Oracle # the package used for accessing Oracle in Python
import getpass # the package for getting password from user without displaying it
import random

#set up some global variables
connection = 0
curs = 0
user_type = "customer"

def mainScreen():
    login_info = loginScreen()
    cont = 1
    while(cont):
        display_menu(login_info)

def display_menu(login_info):
    #Print the available actions for the user to choose
    print("What would you like to do?") 
    print(" (1) Search for flights \n (2) Make a booking \n (3) List existing "+
    "bookings \n (4) Cancel a booking \n (5) Book a round trip")
    if user_type == "agent": print(" (6) Record flight departure \n (7) Record flight arrival")      
    print(" (8) Logout.")            
        
    # Get the user's choice of action and execute it
    while True:
        try: 
            action = int(input("Please enter a number: "))
        except ValueError:
            print("That was not a valid option!")
            continue
        else:
           break
    print("\n")
                
    #Action 1: Search for flights and print the results
    if action == 1:
        flights = search_flights()
        print("Your search returned ", len(flights), " flights:")
        for flight in flights:
            print(flight)
        
    #Action 2: Make a booking    
    if action == 2:
        make_booking(login_info)
        
    #Action 3: List existing bookings
    if action == 3:
        message = ('Enter the ticket number of the booking you would like to '
        'know more about,\nor r to return to the main menu: ')
        tno = list_bookings(login_info, message)        
        display_booking_info(tno)
        
    # Action 4: Cancel bookings
    if action == 4:
        message = ("Enter the ticket number of the booking you would like to "
        "cancel, \nor r to return to the main menu: ")
        tno = list_bookings(login_info, message)
        cancel_booking(tno)

    # Action 5: Book a round trip
    if action ==  5:
        round_trip(login_info)
        
    # Action 5: Record flight departure
    if action == 6: 
        record_departure()
        
    #Action 6: Record flight arrival
    if action == 7: 
        record_arrival()

    #Action 7: Log out
    if action == 8:
        log_out(login_info) 
        quit_program()
        cont = 0        
    
    # Print new line to make it look a little cleaner
    print()

def loginScreen():
    print("Login to Oracle database...")
    
    #Because we're modifying global variables
    global connection
    global curs
    global user_type
    
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
    
    #If the user is an airline agent, then update the user type
    email = login_info[0]    
    query = "SELECT name FROM airline_agents, users WHERE airline_agents.email = :email"
    curs.prepare(query)
    curs.execute(None, {'email':email})
    results = curs.fetchall()
    if (results):
        user_type = "agent"
    
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
        i=i+1
    select = input("Please enter your selection: ")
    flight = flights[i-1]
    
    # Find passenger
    name = input("Please enter the name of the passenger you wish to make the booking for :")
    print(login_info,' ',name)

def round_trip(login_info):
    """
    Find, book round trip flights
    """ 
    source = input("Enter source airport: ")
    source = find_port(source)
    dest = input("Enter destination airport: ")
    dest = find_port(dest)    
    dep_date = input("Enter your departure date: ")
    return_date = input("Enter your return date: ")
    
    dep_flights = find_flights(source, dest, dep_date, "p")
    return_flights = find_flights(source, dest, return_date, "p")

    print(dep_flights)
    print(return_flights)
    
    # I'm going to change this
    return (dep_flights, return_flights)
    
    
def list_bookings(login_info, message):
    """
    List exiting bookings. A user should be able to list all his/her existing 
    bookings. The result will be given in a list form and will include for each 
    booking, the ticket number, the passenger name, the departure date and the 
    price. The user should be able to select a row and get more detailed 
    information about the booking.
    """
    email = login_info[0]
    print("List bookings made by: ",email)

    # Select the bookings 
    query = "SELECT bookings.tno, tickets.name, flights.dep_time, tickets.paid_price FROM bookings, tickets, flights WHERE bookings.tno = tickets.tno AND flights.flightno = bookings.flightno AND tickets.email = :email"
    curs.prepare(query)
    curs.execute(None, {'email':email})
    results = curs.fetchall()
    
    # Print the results
    for result in results:
        name = result[1]
        name = name.strip() #remove white space from passenger name
        string = "Ticket number: {0}    Passenger name: {1}    Departure Date: {2}    Price: {3}".format(result[0], name, result[2], result[3])
        print(string)

    # Get user input: Which booking (if any) would they like to know more about
    while True:
        try:
            select = input(message)
            if select == "r": display_menu(login_info)
            tno = int(select)
        except ValueError:
            print("That was not a valid selection. Please enter a ticket number.")
            continue
        else:
            break
    
    return tno   

def display_booking_info(tno):    
    """
    Display flightno, fare type, src, dst, bag_allow, dep_time, arrival_time
    seats available on the flight
    
    Displayed info:
    flightno - flights
    src - flights
    dst - flights
    dep_time - flights
    fare type: descr - fares
    bag_allow - flight_fares

    Left to do:
    arrival_time (with timezone)
    available_seats
    """
    # arrival time (no time zones)
    query = "SELECT flights.dep_time+(trunc(sch_flights.dep_date)-trunc(flights.dep_time))+(flights.est_dur) FROM flights, sch_flights, bookings WHERE bookings.tno = :tno AND bookings.flightno = flights.flightno AND sch_flights.flightno = flights.flightno"
    curs.prepare(query)
    curs.execute(None, {'tno':tno})
    arr_time = curs.fetchall()[0]

    # Find max seats for the flight
    query = "SELECT flight_fares.limit FROM flight_fares, bookings WHERE bookings.tno = :tno AND bookings.flightno = flight_fares.flightno"
    curs.prepare(query)
    curs.execute(None, {'tno':tno})
    limit = curs.fetchall()[0][0]
    
    # Find the flight number for the flight:
    query = "SELECT flightno FROM bookings WHERE tno = :tno"
    curs.prepare(query)
    curs.execute(None, {'tno':tno})
    flightno = curs.fetchall()[0][0] #flightno ends up with an extra space at the end, but that's okay
    
    # Just making sure that this works...
    query = "SELECT flights.flightno FROM flights WHERE flights.flightno = :flightno"
    curs.prepare(query)
    curs.execute(None, {'flightno':flightno})
    test = curs.fetchall()
    #print(test)
    
    # Find number of booked seats on the flight
    query = "SELECT count(tno) FROM bookings WHERE flightno = :flightno"
    curs.prepare(query)
    curs.execute(None, {'flightno':flightno})
    count = curs.fetchall()[0][0]

    seats = limit - count
    
    #Fetch more information about the booking
    query = "SELECT sch_flights.flightno, flights.src, flights.dst, sch_flights.dep_date, fares.descr, flight_fares.bag_allow FROM sch_flights, bookings, flights, fares, flight_fares WHERE flight_fares.fare = bookings.fare AND flight_fares.flightno = flights.flightno AND fares.fare = bookings.fare AND flights.flightno = sch_flights.flightno AND sch_flights.dep_date = bookings.dep_date AND sch_flights.flightno = bookings.flightno AND bookings.tno = :tno"
    curs.prepare(query)
    curs.execute(None, {'tno':tno})
    booking = curs.fetchall()[0]
 
    # Format the output
    string = "Flight number: {0} From: {1}, To: {2}, Departure: {3}, Arrival Time: {4}  Fare Type: {5}, Bag Allow: {6}  Available Seats: {7}".format(booking[0], booking[1], booking[2], booking[3], arr_time[0], booking[4], booking[5], seats )

    
    #arrival time (time zones)
    #flights.dep_time+(trunc(sch_flights.dep_date)-trunc(flights.dep_time))+(flights.est_dur)/60+a2.tzone-a1.tzone)/24
    
    # Display booking info
    print(string)

def cancel_booking(tno):
    """
    Given a tno, cancel a booking
    """
    query = "DELETE FROM bookings WHERE tno = :tno"
    curs.prepare(query)
    curs.execute(None, {'tno':tno})
    connection.commit()
    
def record_departure():
    flightno = input("Enter the flight number of the flight you wish to update: ")
    flightno = add_white(6, flightno)
    dep_date = input("Enter the departure date (DD-Mon-YYYY): ")
    
    #Check that there was a match    
    query = "SELECT * FROM sch_flights WHERE flightno = :flightno AND dep_date = to_date(:dep_date, 'DD-Mon-YYYY')"
    curs.prepare(query)
    curs.execute(None, {'flightno':flightno, 'dep_date':dep_date})
    result = curs.fetchall()
    
    if (result):
        # get the actual departure time from the agent
        act_dep_time = input("Enter the actual departure time for this flight (hh:mm): ")

        # Update the act_dep_time                  
        query = "UPDATE sch_flights SET act_dep_time = to_date(:act_dep_time,'hh24:mi') WHERE flightno = :flightno AND dep_date = to_date(:dep_date, 'DD-Mon-YYYY')"
        curs.prepare(query)
        curs.execute(None, {'act_dep_time':act_dep_time, 'flightno':flightno, 'dep_date':dep_date})
        connection.commit()
        print("Record updated!")
    
    else:
        print("Sorry, that does not match any scheduled flight records.")
    
def record_arrival():
    flightno = input("Enter the flight number of the flight you wish to update: ")
    flightno = add_white(6, flightno)
    dep_date = input("Enter the departure date (DD-Mon-YYYY): ")
    
    #Check that there was a match    
    query = "SELECT * FROM sch_flights WHERE flightno = :flightno AND dep_date = to_date(:dep_date, 'DD-Mon-YYYY')"
    curs.prepare(query)
    curs.execute(None, {'flightno':flightno, 'dep_date':dep_date})
    result = curs.fetchall()
    
    if (result):
        # get the actual arrrival time from the agent
        act_arr_time = input("Enter the actual arrival time for this flight (hh:mm): ")

        # Update the act_arr_time                  
        query = "UPDATE sch_flights SET act_arr_time = to_date(:act_arr_time,'hh24:mi') WHERE flightno = :flightno AND dep_date = to_date(:dep_date, 'DD-Mon-YYYY')"
        curs.prepare(query)
        curs.execute(None, {'act_arr_time':act_arr_time, 'flightno':flightno, 'dep_date':dep_date})
        connection.commit()
        print("Record updated!")
    
    else:
        print("Sorry, that does not match any scheduled flight records.")
        
def delete_af():
    """
    This function makes sure that the creation of the view "avialable flights" 
    will not cause and error 
    """
    
    # Drops view if it already exists in database.
    try:
        query = "drop view available_flights"
        curs.execute(query)
        create_af()
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
        #print( sys.stderr, "Oracle code:", error.code)
        #print( sys.stderr, "Oracle message:", error.message)

        # If the user did not have an existing view "avialable flights", we will create this view
        if(error.code == 942):
            #print("caught error")
            create_af()

def delete_gc():
    """
    This function makes sure that the creation of the view "good connections" 
    will not cause and error 
    """
    
    #Drops view if it already exists in database.
    try:
        query = "drop view good_connections"
        curs.execute(query)
        create_gc()
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args

        #If the user did not have an existing view "avialable flights"
        #we will create this view
        if(error.code == 942):
            #print("caught error")
            create_gc()
       
def create_af():
    """
    This function creates the view "available flights"
    The SQL for the creation of this view was taken from the Assigmnet 2 solution 
    """    
    #print("creating af")
    try:
        query = "create view available_flights(flightno,dep_date, src,dst,dep_time,arr_time,fare,seats,price) as select f.flightno, sf.dep_date, f.src, f.dst, f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time)),f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time))+(f.est_dur/60+a2.tzone-a1.tzone)/24 , fa.fare, fa.limit-count(tno), fa.price from flights f, flight_fares fa, sch_flights sf, bookings b, airports a1, airports a2 where f.flightno=sf.flightno and f.flightno=fa.flightno and f.src=a1.acode and f.dst=a2.acode and fa.flightno=b.flightno(+) and fa.fare=b.fare(+) and sf.dep_date=b.dep_date(+)group by f.flightno, sf.dep_date, f.src, f.dst, f.dep_time, f.est_dur,a2.tzone,a1.tzone, fa.fare, fa.limit, fa.price having fa.limit-count(tno) > 0"
        curs.execute(query)
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)

    connection.commit()

def create_gc():
    """
    Creates a modified version of the "good connections" view found in the assigment 2 answers 
    Now groups by seats, departure, and arrival time for the over all flight
    This allows us to access this data
    """
    print("creating gc")
    query='''
  create view good_connections (src,dst,dep_date,flightno1,flightno2, layover,price,seats,dep_time,arr_time) as
  select a1.src, a2.dst, a1.dep_date, a1.flightno, a2.flightno, a2.dep_time-a1.arr_time,
	min(a1.price+a2.price),LEAST (a1.seats,a2.seats),a1.dep_time,a2.arr_time
  from available_flights a1, available_flights a2
  where a1.dst=a2.src and a1.arr_time +1.5/24 <=a2.dep_time and a1.arr_time +5/24 >=a2.dep_time
  group by a1.src, a2.dst, a1.dep_date, a1.flightno, a2.flightno, a2.dep_time, a1.arr_time,a1.dep_time,a2.arr_time,a1.seats,a2.seats'''
    curs.execute(query)
    connection.commit()

def find_port(port_name):
    """
    This function finds a related airport code for the string passed 
    First checks to see if the string is an exact match for an airport code 
    If not, gives user a list of possible airports 
    Returns an airport code fromm the database in all cases 
    """
    port_name = port_name.upper()

    #If the string is in airport code format, check for an exact match 
    if(len(port_name)== 3): 
        query = "SELECT * FROM airports WHERE acode = :port " 
        curs.prepare(query)
        curs.execute(None,{'port':port_name})
        result = curs.fetchall()
        print(result)
        if(result): 
            return result[0][0]

    # There was not an exact match!
    # Pattern matches string to a city or airport name in the database 
    port_name = "%"+port_name+"%"
    query = "SELECT * FROM airports WHERE UPPER(city) LIKE :port OR UPPER(name) LIKE :port"
    curs.prepare(query)
    curs.execute(None,{'port':port_name})

    rows = curs.fetchall()

    # User must now select one of the airport codes existing in the database 
    print("You did not enter a valid airport code! \n Which of the following did you mean?")
    i = 1
    for row in rows:
        print(i, row[1], row[2], row[3])
        i=i+1
    select = int(input("please enter a number: "))
    return (rows[select-1][0])
    
def add_white(total,string):
    """
    This functions adds white space to a string to comform to table restrictions
    Total = total number of char expeceted
    String = string to format
    Return = formated string
    """
    whitespace = total - len(string)
    for w in range(whitespace):
        string = string + " "
    return string     
    
def generate_tno():
    """
    This function will search for the largest ticket number, and return a 
    ticket number that is larger by 1 
    
    Arguments: None
    Returns: ticketno (int)
    """    
    query = "SELECT MAX(tno) FROM tickets"
    curs.prepare(query)
    curs.execute(None, {})
    result = curs.fetchall()
    tno = result[0][0] + 1
    return tno    

def quit_program():
    print("Quit")
    # close the connection
    #cursInsert.close()
    curs.close()
    connection.close()
    sys.exit()

if __name__ == "__main__":
    mainScreen()




