#!/usr/bin/env python

#one cond var (to notify barber)
#one mutex
#two sems -> chairs and barbers
#hint: try_wait()
import sys
import threading
import time
import random

class Input:
    def __init__(self, num_barbers, num_clients, num_chairs, arrival_t, haircut_t):
        self.num_barbers = num_barbers
        self.num_clients = num_clients
        self.num_chairs  = num_chairs
        self.arrival_t   = arrival_t
        self.haircut_t   = haircut_t

#if input is valid, store in an Input object
def input_arg_handler():
    if len(sys.argv) != 6:
        print "Usage: ./hw2.py num_barbers num_clients num_chairs arrival_t haircut_t"
        exit(1)
    elif (sys.argv[1] < 1 or sys.argv[2] < 1 or sys.argv[3] < 1 or sys.argv[4] < 1 or sys.argv[5] < 1):
        print "Error: all input arguments must be greater than 0"
        exit(1)
    else:
        input = Input(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        return input

#thread function for barbers
def barber(barberID, haircut_t):
    global clientsTally, input, barbersSem, condition

    #loop until day is over
    while (clientsTally < input.num_clients):
        #wait until a client wakes barber up
        print "Barber " + str(barberID) + " waiting"
        barbersSem.release()
        condition.acquire()
        condition.wait()
        condition.release()

        #check to see if its the "end of the day" before continuing to work
        if (clientsTally >= input.num_clients):
            print "Barber " + str(barberID) + " exiting"
            return

        #cut hair
        print "Barber " + str(barberID) + " cutting"
        time.sleep( random.randint(0, haircut_t) )
        #barber done, let the system know is available
        clientsTally += 1
        print "Barber " + str(barberID) + " done || Tally = " + str(clientsTally)
        #barbersSem.release()

#thread functions for clients
def client(clientID):
    global clientsTally, barbersSem, chairsSem, condition

    print "Client " + str(clientID) + " entering"
    barberAvailable = barbersSem.acquire(False)
    #if a barber is not a available, then check if a chair is available
    if not barberAvailable:
        chairAvailable = chairsSem.acquire(False)
        #if a chair is not available, then leave
        if not chairAvailable:
            clientsTally += 1
            print "Client " + str(clientID) + " leaving || Tally = " + str(clientsTally)
            return
        #a is available, wait until a barber is done and then wake barber up and release chair
        else:
            print "Client " + str(clientID) + " got a chair!"
            barbersSem.acquire()
            print "Client " + str(clientID) + " got a barber! (after waiting)"
            condition.acquire()
            condition.notify()
            condition.release()
            chairsSem.release()
    #a barber is available, wake barber up
    else:
        print "Client " + str(clientID) + " got a barber!"
        condition.acquire()
        condition.notify()
        condition.release()


############MAIN##############
input = input_arg_handler();

#synchronization tools
mut = threading.Lock()
condition = threading.Condition()
barbersSem = threading.Semaphore(0)
chairsSem = threading.Semaphore(input.num_chairs)

#tally for finding when "end of day" is
clientsTally = 0

#threads storage
barbers = []
clients = []

#start barbers
for i in range(input.num_barbers):
    b = threading.Thread(target = barber, args = (i,input.haircut_t))
    barbers.append(b)
    b.start()

#start clients at random intervals
for i in range(input.num_clients):
    time.sleep( random.randint(0, input.arrival_t) )
    c = threading.Thread(target = client, args = (i,))
    clients.append(c)
    c.start()

#wait for clients to be done
for c in clients:
    c.join()

#sleep in case barber is mid-cut
time.sleep(input.haircut_t)

#notify barbers that the day is over!
condition.acquire()
condition.notifyAll()
condition.release()
