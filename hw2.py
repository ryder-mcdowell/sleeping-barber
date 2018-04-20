#!/usr/bin/env python
import sys
import threading
import time
import random

class Input:
    def __init__(self, num_barbers, num_clients, num_chairs, arrival_t, haircut_t):
        self.num_barbers = num_barbers
        self.num_clients = num_clients
        self.num_chairs  = num_chairs
        self.arrival_t   = (arrival_t / 1000000)
        self.haircut_t   = (haircut_t / 1000000)

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

#outputs statistics
def output_stats(input, totalBarberWaitTime, totalClientWaitTime, totalHaircuts, totalClientsWhoLeft):
    print "\nTOTALS:"
    print "Total Haircuts: " + str(totalHaircuts)
    print "Clients That Left: " + str(totalClientsWhoLeft)
    print "Avg Client Wait Time: " + str((totalClientWaitTime / input.num_clients) * 1000000)
    print "Avg Barber Wait Time: " + str((totalBarberWaitTime / input.num_barbers) * 1000000)

#thread function for barbers
def barber(barberID):
    global clientsTally, input, barbersSem, condition, totalBarberWaitTime, totalHaircuts

    #loop until day is over
    while (clientsTally < input.num_clients):
        #wait until a client wakes barber up
        barbersSem.release()
        condition.acquire()
        startTime = time.time()
        condition.wait()
        endTime = time.time()
        condition.release()
        totalBarberWaitTime += (endTime - startTime)

        #check to see if its the "end of the day" before continuing to work
        if (clientsTally >= input.num_clients):
            return

        #cut hair
        time.sleep( random.randint(0, input.haircut_t) )

        #barber done, let the system know is available
        clientsTally += 1
        totalHaircuts += 1

#thread functions for clients
def client(clientID):
    global clientsTally, barbersSem, chairsSem, condition, totalClientWaitTime, totalClientsWhoLeft

    barberAvailable = barbersSem.acquire(False)
    #if a barber is not a available, then check if a chair is available
    if not barberAvailable:
        chairAvailable = chairsSem.acquire(False)
        #if a chair is not available, then leave
        if not chairAvailable:
            clientsTally += 1
            totalClientsWhoLeft += 1
            return
        #a is available, wait until a barber is done and then wake barber up and release chair
        else:
            startTime = time.time()
            barbersSem.acquire()
            endTime = time.time()
            totalClientWaitTime += (endTime - startTime)
            condition.acquire()
            condition.notify()
            condition.release()
            chairsSem.release()
    #a barber is available, wake barber up
    else:
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

#counters
clientsTally = 0
totalBarberWaitTime = 0
totalClientWaitTime = 0
totalHaircuts = 0
totalClientsWhoLeft = 0

#threads storage
barbers = []
clients = []

#start barbers
for i in range(input.num_barbers):
    b = threading.Thread(target = barber, args = (i,))
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

time.sleep(1)

output_stats(input, totalBarberWaitTime, totalClientWaitTime, totalHaircuts, totalClientsWhoLeft)
