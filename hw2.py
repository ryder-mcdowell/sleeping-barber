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
        input = Input(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
        return input

#outputs statistics
def output_stats(input, totalBarberWaitTime, totalClientWaitTime, totalHaircuts, totalClientsWhoLeft):
    print "\nTOTALS:"
    print "Total Haircuts: " + str(totalHaircuts)
    print "Clients That Left: " + str(totalClientsWhoLeft)
    print "Avg Client Wait Time: " + str((totalClientWaitTime / input.num_clients) * 1000000)
    print "Avg Barber Sleep Time: " + str((totalBarberWaitTime / input.num_barbers) * 1000000)

#thread function for barbers
def barber(barberID):
    global input, barbersSem, condition, mutex, totalBarberWaitTime, done_flag

    #loop until day is over
    while (True):
        condition.acquire()
        barbersSem.release()
        startTime = time.time()
        #wait until a client wakes barber up
        condition.wait()
        endTime = time.time()

        #check to see if its the "end of the day" before continuing to work
        if (done_flag):
            condition.release()
            exit(0)

        mutex.acquire()
        totalBarberWaitTime += (endTime - startTime)       #pushed until after global check for more acurate time (excludes final wait)
        mutex.release()
        #cut hair
        time.sleep( random.uniform(0, input.haircut_t) )
        #barber done
        condition.release()

#thread functions for clients
def client(clientID):
    global barbersSem, chairsSem, condition, mutex, totalClientWaitTime, totalClientsWhoLeft, totalHaircuts

    barberAvailable = barbersSem.acquire(False)
    #if a barber is not a available, then check if a chair is available
    if not barberAvailable:
        chairAvailable = chairsSem.acquire(False)
        #if a chair is not available, then leave
        if not chairAvailable:
            mutex.acquire()
            totalClientsWhoLeft += 1
            mutex.release()
            exit(0)
        #a chair is available, wait until a barber is done and then wake barber up and release chair
        else:
            startTime = time.time()
            barbersSem.acquire()
            endTime = time.time()
            mutex.acquire()
            totalClientWaitTime += (endTime - startTime)
            mutex.release()
            condition.acquire()
            condition.notify()
            condition.release()
            chairsSem.release()
            mutex.acquire()
            totalHaircuts += 1
            mutex.release()
    #a barber is available, wake barber up
    else:
        condition.acquire()
        condition.notify()
        condition.release()
        mutex.acquire()
        totalHaircuts += 1
        mutex.release()


############MAIN##############
input = input_arg_handler();

#synchronization tools
mutex = threading.Lock()
condition = threading.Condition()
barbersSem = threading.Semaphore(0)
chairsSem = threading.Semaphore(input.num_chairs)
done_flag = False

#counters
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
    time.sleep( random.uniform(0, input.arrival_t) )
    c = threading.Thread(target = client, args = (i,))
    clients.append(c)
    c.start()

#wait for clients to be done
for c in clients:
    c.join()
done_flag = True

#sleep in case barber is mid-cut
time.sleep(input.haircut_t * 2)

#notify barbers that the day is over!
condition.acquire()
condition.notifyAll()
condition.release()

output_stats(input, totalBarberWaitTime, totalClientWaitTime, totalHaircuts, totalClientsWhoLeft)
