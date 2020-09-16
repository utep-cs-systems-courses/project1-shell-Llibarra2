#! /usr/bin/env python3

import os, sys, re

# save parent pid
pid = os.getpid() 

def get_prompt(): 
    return os.read(0, 1024).decode()[:-1]

def process_user_query(action): 
    if action == '':
        if not os.isatty(sys.stdin.fileno()): 
            sys.exit(0)
        return

    elif 'cd' in action:#changes in directory
            cmd, path = re.split(' ', action)
            if path != '..': 
                path = os.getcwd() + '/' +  path
            os.chdir(path)

    elif '\x03' in action: 
        sys.exit(0)
    elif '\x7C' in action: # pipes
        pipe(action)
    elif '\x3e' in action: #all output in the command is inputed into the specified file
        cmd, file_path = [i.strip() for i in re.split('[\x3e]', action)] # split by > 
        file_path = os.getcwd() + '/' + file_path
        cmd = [i.strip() for i in re.split('[\x20]', cmd)]
        r = os.fork()
        if r < 0: 
            os.write(2, ("fork failed, returning with %d\n").encode())
            sys.exit(1)
        elif r == 0: 
            os.close(1) # close stdout
            sys.stdout = open(file_path, 'w+')
            fd = sys.stdout.fileno()
            os.set_inheritable(fd, True)
            os.dup(fd)
            global_exec(cmd)
            os.write(2, ("Command %s not found\n" % args[0]).encode())
            sys.exit(1) # we return with error beacuse execv overrides our current process memeory
        else: 
            r_child = os.waitpid(r, 0)

    elif 'exit' in action: 
        sys.exit(0)
    else: 
        execute(action)
        
def path(args): 
    try: 
        os.execve(args[0], args, os.environ)
    except FileNotFoundError: 
        pass

def global_exec(args): 
    for dir in re.split('[\x3a]', os.environ['PATH']): # :
        program = "%s/%s" % (dir, args[0])
        try: 
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            pass


def pipe(action): 
    r,w = os.pipe()
    for f in (r,w): 
        os.set_inheritable(f, True)
    
    cmds = [i.strip() for i in re.split('[\x7C]', action)] # split by |
    childs = []
    parent = True
    even = 0
    for cmd in cmds: 
        even += 1
        rc = os.fork()
        if rc: 
            childs.append(rc)
        else: 
            parent = False
            if even % 2 != 0: 
                os.close(1) # close stdout
                write = os.dup(w)
                for i in (r,w):
                    os.close(i)

                sys.stdout = os.fdopen(write, "w")
                fd = sys.stdout.fileno()
                os.set_inheritable(fd, True)
            else: 
                os.close(0) # close stdin
                read = os.dup(r)
                for i in (r,w):
                    os.close(i)

                sys.stdin = os.fdopen(read, "r")
                fd = sys.stdin.fileno()
                os.set_inheritable(fd, True)

            args = [i.strip() for i in re.split('[\x20]', cmd)]
            global_exec(args)
            break
    if parent: 
        for i in (r,w): 
            os.close(i)

        for child in childs: 
            os.waitpid(child, 0)
   
def execute(action): 
    rc = os.fork()
    if rc < 0: 
        os.write(2, ("FAIL, returning with %d\n").encode())
        sys.exit(1)
    elif rc == 0:
        args = [i.strip() for i in re.split('[\x20]', action)] # split by space
        if '\x2f' in args[0]: 
            path(args)
        else:
            global_exec(args)
        os.write(2, ("Action %s not found\n" % args[0]).encode())
        sys.exit(1) # we return with error beacuse execv overrides our current process memeory
    else: 
        r_child = os.waitpid(rc, 0) 
            



#file descriptor 0 is for std input
#file descriptor 1 is for std output
#file descriptor 2 is for std error

try: 
    sys.ps1 = os.environ['PS1']
except KeyError: 
    sys.ps1 = '$ '

if sys.ps1 is None:
    sys.ps1 = '$ '

if __name__ == '__main__':
    while True:
        os.write(1, sys.ps1.encode())
        action = get_prompt()
        process_user_query(action)