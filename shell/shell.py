#! /usr/bin/env python3

import os, sys, re

# save parent pid
pid = os.getpid() 

def get_input(): 
    return os.read(0, 1024).decode()[:-1]

def exec_path(args): 
    try: 
        os.execve(args[0], args, os.environ)
    except FileNotFoundError: 
        pass
    
if __name__ == '__main__':
    while True:
        