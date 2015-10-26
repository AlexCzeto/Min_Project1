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
    print("What would you like to do?") 
    print(" (1) Search for flights \n (2) Make a booking \n (3) List existing bookings \n (4) Cancel a booking \n (5) Book a round trip")
    if user_type == "agent": print(" (6) Record flight departure \n (7) Record flight arrival")
    print(" (8) Logout.")
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
        date = input("Enter date of flight : ")
        flights = search_flights(date)
        if not flights:
            print("\nYour search did not return any flights")
        else:
            print("\nYour search returned ", len(flights), " flights:")
            for flight in flights:
                print(flight)
         
    #Action 2: Make a booking    
    if action == 2:
        make_booking(login_info)
    
    #Action 3: List existing bookings
    if action == 3:
        message = ('\nEnter the ticket number of the booking you would like to '
        'know more about,\nor r to return to the main menu : ')
        tno = list_bookings(login_info, message)        
        display_booking_info(tno)
     
    # Action 4: Cancel bookings
    if action == 4:
        message = ("\nEnter the ticket number of the booking you would like to "
        "cancel, \n Or r to return to the main menu : ")
        tno = list_bookings(login_info, message)
        cancel_booking(tno)
        print("\nBooking with ticket number : ",tno,", has been successfully cancelled.\n")

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
      
# This function finds flights that relate to the users input 
# Input: Source airport, destination airport, date 
# Checks for both direct and indirect flights 
def search_flights(date):
# Create view avialable flights
    delete_af()
    delete_gc()
    source = input("Enter source airport: ")
    source = find_port(source)
    dest = input("Enter destination airport: ")
    dest = find_port(dest)    
    sort = input("Enter p to order the flights by price, and n to order the flights by number of connections: ")
    
    if(sort=='p'):
        print("Flights sorted by price")
    
        query = "select flightno1, flightno2,src, dst,to_char(dep_time,'hh24:mi'),to_char(arr_time,'hh24:mi'),stops, layover, price,seats from (select flightno1, flightno2,src,dst,dep_time,arr_time, 1 stops, layover, price, seats from good_connections where to_char(dep_date,'DD-Mon-YYYY')=:sdate and src=:ssrc and dst=:sdst union select flightno flightno1, '' flightno2,src,dst,dep_time,arr_time,0 stops,0 layover, price,seats from available_flights where to_char(dep_date,'DD-Mon-YYYY')=:sdate and src=:ssrc and dst=:sdst) order by price"
        curs.prepare(query)
        curs.execute(None,{'sdate':date,'ssrc':source,'sdst':dest})
        flights=[]
        rows = curs.fetchall()
        return rows
    

    elif(sort=='n'):
        print("Flights sorted by connection number")
    
        query = "select flightno1, flightno2,src, dst,to_char(dep_time,'hh24:mi'),to_char(arr_time,'hh24:mi'),stops, layover, price,seats from (select flightno1, flightno2,src,dst,dep_time,arr_time, 1 stops, layover, price, seats from good_connections where to_char(dep_date,'DD-Mon-YYYY')=:sdate and src=:ssrc and dst=:sdst union select flightno flightno1, '' flightno2,src,dst,dep_time,arr_time,0 stops,0 layover, price,seats from available_flights where to_char(dep_date,'DD-Mon-YYYY')=:sdate and src=:ssrc and dst=:sdst) order by stops"
        curs.prepare(query)
        curs.execute(None,{'sdate':date,'ssrc':source,'sdst':dest})
        rows = curs.fetchall()
        return rows

# Assumed only direct flights now 
# NEED TO ACCOMMODATE Connected flights
def make_booking(login_info):
     # Find passenger
    name = input("Please enter the name of the passenger you wish to make the booking for : ")
    
    name =check_name(name,login_info[0])
    
    # Fetch the flight to be booked
    date = input("Enter date of flight : ")
    flights = search_flights(date)
    if not flights:
        print("\nYour search return no flights.\n")
        display_menu(login_info)
    
    print("Available flights: ")
    i = 1
    for flight in flights:
        print (i, flight)
        i=i+1
    select = int(input("Please enter your selection : "))
    flight = flights[select-1]

    if(flight[1] == None):
        flightno = flight[0]
        p_price = flight[8]

# Find related fare for flight at price 
        query = """
        SELECT fare  
        FROM flight_fares
        WHERE flightno =:sfn and price =:spp """
        curs.prepare(query)
        curs.execute(None,{'sfn':flightno,'spp':p_price})
        result = curs.fetchall()
        fare=result[0][0]

## WHAT IF TICKET IS TAKEN , ERROR HANDLING FOR THIS !!!!!!!!!!!!!

        connection.begin()  
    
        tno = insert_ticket(login_info[0],name,p_price)
        insert_booking(tno,flightno,fare,date)
    else:
        #print("First flight;",flight[0])
        flightno = flight[0]
        fare_info = find_fare(flightno)
        
        connection.begin()  
        tno = insert_ticket(login_info[0],name,fare_info[1])
        insert_booking(tno,flightno,fare_info[0],date)

        #print("Second flight:",flight[1])
        flightno = flight[1]
        fare_info = find_fare(flightno)

        connection.begin()  
        tno = insert_ticket(login_info[0],name,fare_info[1])
        insert_booking(tno,flightno,fare_info[0],date)
    
# ---------------------------------------------------------
# Helper Functions Specifically for Making Bookings
#----------------------------------------------------------
# Helper function that handles the selection of fare type for non-direct flights
# Input: flightno 
# Return : tuple(price and fare type)
def find_fare(flightno):
    query = """
        SELECT fare,price 
        FROM flight_fares
        WHERE flightno=: sfn
        ORDER BY price
    """
    curs.prepare(query)
    curs.execute(None,{'sfn':flightno})
    rows = curs.fetchall()
    print("Available fare types and associated price for flight number : ",flightno)
    i = 1
    for row in rows:
        print(i,row)
        i=i+1
    select = int(input("\nPlease enter your selection : "))
    
    return(rows[select-1][0],rows[select-1][1])

# Helper function that inserts bookings into the booking table
# Handles the selection of a seat and also ensuring that seat is not taken 
# Input : ticket number, flight number, fare, and departure date 
# No return
 
def insert_booking(tno,flightno,fare,date):

    unavl_seats = unavialable_seat(flightno,date)
    if not unavl_seats:
        print("\nAll seats are available")
    else:
        print('Seats that are unavailable : ',unavl_seats)

    seat = input('\nPlease enter an available seat : ')
    seat = add_white(3,seat)

    unavl_seats = unavialable_seat(flightno,date)

    query = " SELECT * FROM tickets WHERE tno =:stno"
    curs.prepare(query)
    curs.execute(None,{'stno':tno})
    
    result = curs.fetchall()
    
    if seat not in unavl_seats:
        try:
            query = "insert into bookings values (:stno,:sfn,:sfare,to_date(:sdate,'DD-Mon-YYYY'),:sseat)"
            curs.prepare(query)
            curs.execute(None,{'stno':tno,'sfn':flightno,'sfare':fare,'sdate':date,'sseat':seat})
            connection.commit()
            print("\nBooking successfully made for flight number : ",flightno,"\nTicket number : ",tno)

# In the case of a non-direct flight the connecting flight could be on the next day, meaning a scheduled flight 
# with that flight number does not exist and will case a "parent does not exist" oracle error 


        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            if error.code == 2291:
                date = increase_date(date)
                #query = "insert into bookings values (:stno,:sfn,:sfare,to_date(:sdate,'DD-Mon-YYYY'),:sseat)"
                #curs.prepare(query)
                curs.execute(None,{'stno':tno,'sfn':flightno,'sfare':fare,'sdate':date,'sseat':seat})
                connection.commit()
                print("\nBooking successfully made for flight number : ",flightno,"\nTicket number : ",tno)
                
    else:
        connection.rollback()
        print("\nBooking not successfully processed for flight number : ",flightno,", seat has already been booked. \n Please try again")
            
# Helper function that finds avialable seats for a given flight on a given day 
# Inputs : Flightno and Dep_date 
# Return : list of seat codes

def insert_ticket(email,name,p_price):
    tno = generate_tno()
    query = "INSERT INTO tickets VALUES (:stno,:sname,:semail,:spp)"
    curs.prepare(query)
    curs.execute(None,{'stno':tno,'sname':name,'semail':email,'spp':p_price})
    return tno

# Helper function that finds all seats already booked for a flight 
def unavialable_seat(flightno,date):
    query = """
    SELECT seat
    FROM bookings
    WHERE flightno =:sfn and dep_date =to_date(:sdate,'DD-Mon-YYYY')""" 
    curs.prepare(query)
    curs.execute(None,{'sfn':flightno,'sdate':date})
    rows = curs.fetchall()
    seats = []
    for row in rows: 
        seats.append(row[0])
    return seats 

# Helper function that increases the date to the next day 
# Inputs : date 
# Return : date + 1
def increase_date(date):
    day = int(date[0]+date[1])
    day = day + 1
    alter = list(date)
    alter[0] = str(day//10)
    alter[1] = str(day%10)
    date = "".join(alter)
    return(date)
    
    
def list_bookings(login_info, message):
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
               
def loginScreen():
    print("Login to Oracle database...")
    
    #Because we're modifying global variables
    global connection
    global curs
    global user_type
    
    
    #I've hardcoded in my username and password temporarily
    #because it's annoying to type out.
    #but definitely change this back before handing it in
    
    # The URL we are connnecting to
    conString=''+'czeto'+'/' + 'smarT_pant5' +'@gwynne.cs.ualberta.ca:1521/CRS'
    
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
#---------------------------------------------
#HELPER FUNCTIONS
#---------------------------------------------

# This functions adds white space to a string to comform to table restrictions 
# Total = total number of char expeceted
# String = string to format
# Return = formated string 
def add_white(total,string):
    whitespace = total - len(string)
    for w in range(whitespace):
        string = string + " "
    return string 

# This function makes sure that the creation of the view "avialable flights" will not cause and error 
def delete_af():

# Drops view if it already exists in database.
    try:
        query = "drop view available_flights"
        curs.execute(query)
        create_af()
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
#        print( sys.stderr, "Oracle code:", error.code)
#        print( sys.stderr, "Oracle message:", error.message)

# If the user did not have an existing view "avialable flights", we will create this view
        if(error.code == 942):
#            print("caught error")
            create_af()
# This function makes sure that the creation of the view "good connections" will not cause and error 
def delete_gc():

# Drops view if it already exists in database.
    try:
        query = "drop view good_connections"
        curs.execute(query)
        create_gc()
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
# If the user did not have an existing view "avialable flights", we will create this view
        if(error.code == 942):
#            print("caught error")
            create_gc()
    
# This function creates the view "available flights"
# The SQL for the creation of this view was taken from the Assigmnet 2 solution    
def create_af():
    try:
        query = "create view available_flights(flightno,dep_date, src,dst,dep_time,arr_time,fare,seats,price) as select f.flightno, sf.dep_date, f.src, f.dst, f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time)),f.dep_time+(trunc(sf.dep_date)-trunc(f.dep_time))+(f.est_dur/60+a2.tzone-a1.tzone)/24 , fa.fare, fa.limit-count(tno), fa.price from flights f, flight_fares fa, sch_flights sf, bookings b, airports a1, airports a2 where f.flightno=sf.flightno and f.flightno=fa.flightno and f.src=a1.acode and f.dst=a2.acode and fa.flightno=b.flightno(+) and fa.fare=b.fare(+) and sf.dep_date=b.dep_date(+)group by f.flightno, sf.dep_date, f.src, f.dst, f.dep_time, f.est_dur,a2.tzone,a1.tzone, fa.fare, fa.limit, fa.price having fa.limit-count(tno) > 0"
        curs.execute(query)
    except cx_Oracle.DatabaseError as exc:
        error, = exc.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)

    connection.commit()
# Creates a modified version of the "good connections" view found in the assigment 2 answers 
# Now groups by seats, departure, and arrival time for the over all flight
# This allows us to access this data
def create_gc():
    query='''
  create view good_connections (src,dst,dep_date,flightno1,flightno2, layover,price,seats,dep_time,arr_time) as
  select a1.src, a2.dst, a1.dep_date, a1.flightno, a2.flightno, a2.dep_time-a1.arr_time,
	min(a1.price+a2.price),LEAST (a1.seats,a2.seats),a1.dep_time,a2.arr_time
  from available_flights a1, available_flights a2
  where a1.dst=a2.src and a1.arr_time +1.5/24 <=a2.dep_time and a1.arr_time +5/24 >=a2.dep_time
  group by a1.src, a2.dst, a1.dep_date, a1.flightno, a2.flightno, a2.dep_time, a1.arr_time,a1.dep_time,a2.arr_time,a1.seats,a2.seats
'''
    curs.execute(query)
    connection.commit()

    

# This function finds a related airport code for the string passed 
# First checks to see if the string is an exact match for an airport code 
# If not, gives user a list of possible airports 
# Returns an airport code form the database in all cases 
def find_port(port_name):
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
    print("\nYou did not enter a valid airport code! \n Which of the following did you mean?\n")
    i = 1
    for row in rows:
        print(i, row[1], row[2], row[3])
        i=i+1
    select = int(input("\nplease enter a number: "))
    return (rows[select-1][0])


# This function checks that a passenger name does not already exist for a user 
def check_name(name,log_email):
    name = add_white(20,name)
    query = """
        SELECT name
        FROM passengers
        WHERE email =: semail 
        """
    curs.prepare(query)
    curs.execute(None,{'semail':log_email})
    rows = curs.fetchall()
    exist_n=[]
    for row in rows:
        exist_n.append(row[0])

    if(name not in exist_n):
        reg_pass(name,log_email)
    return name

def reg_pass(name,log_email):
    con = input("Please enter the country of the passenger : ")
    add_white(10,con)
    query ="INSERT INTO passengers VALUES(:semail,:sname,:scountry)"
    curs.prepare(query)
    curs.execute(None,{'semail':log_email,'sname':name,'scountry':con})

    connection.commit()

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
