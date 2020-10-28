#! /usr/bin/env python3

import os, sys, time, re

curr = os.getcwd()
spl = curr.split("/")
short = spl[-1]
#execute = ["wc", "shell2.py"] #default args for using execve()

dir_list = spl #probably don't need this

#maybe continuously update dir list and only allow redirects if in current list

def ls():
	directory_list = os.listdir(curr)
	for i in directory_list:
		print(i, end = "   ")
#	print("")
	return

def lsdir(directory):
	change = False
	original = curr
	directory_list = os.listdir(curr)
	if directory.startswith("/"):
		change = True
		split = directory.split("/")
		directory = split[-1]
		index = 0
		while(index != len(split)-1): #change directory based on usr input
			if split[index] == '':
				index +=1
			os.chdir(split[index]) 
			index = index + 1
	
	if directory.endswith(".txt"):
		fdOut = os.open(directory + ".txt", os.O_CREAT | os.O_WRONLY)
		
	else:
		fdOut = os.open(directory + ".txt", os.O_CREAT | os.O_WRONLY)
						
	
	for a in directory_list:
		a = a + "\n"
		os.write(fdOut, a.encode()) # write to output file
	i = 0
	if (change): 
		while(i < len(split)-1): #return to current dir
			os.chdir("..")
			i = i +1
	return

def update_curr_dir(): 
	curr = os.getcwd()
	spl = curr.split("/")
	short = spl[-1]

def get_current():
	global curr
	curr = os.getcwd()
	os.write(1, (curr + "\n").encode())
	return

def get_short():
	global curr
	global short
	curr = os.getcwd()
	spl = curr.split("/")
	short = "\033[1;35;40m %s\x1b[0m" % spl[-1]
	os.write(1, (short + "$ ").encode())
	return

def loop_shell():
	global short
	
	while True:
		if 'PS1' in os.environ:
			os.write(1,(os.environ['PS1']).encode())
			try:
#				inp = os.read(0,256)
#				user_input = inp.decode().split()
				user_input = [str(n) for n in input().split()]
			except EOFError: 
				sys.exit(1)
		else:
			get_short()
			try:
#				inp = os.read(0,256)
#				user_input = inp.decode().split()
				user_input = [str(n) for n in input().split()]
			except EOFError: 
				sys.exit(1)
		w = True
		
		if user_input == '\n':
			loop_shell()
			return
		
		if not user_input:
			loop_shell()
			return
		
		if user_input[0] == 'exit':
			sys.exit(1)
			
		if "cd" in user_input:
			try:
				os.chdir(user_input[1])
			except FileNotFoundError:
				os.write(1, ("-bash: cd: %s: No such file or directory\n" % directory).encode())
			
			continue
			
		else:
			rc = os.fork()  
		
			if '&' in user_input:
				user_input.remove("&")
				w = False
				
			if user_input[0] == 'exit':
				quit(1)
				
			if rc < 0:
				os.write(2, ("fork failed, returning %d\n" % rc).encode())
				sys.exit(1)

			elif rc == 0:              #son or daughter (#not assuming)
				if user_input[0].startswith("/"):
					try:
						os.execve(user_input[0], user_input, os.environ) # try to exec program
					except FileNotFoundError:
						pass 
				redirect(user_input)
				simple_pipe(user_input)
				execChild(user_input)
				
			else:                           # parent (forked ok)
				if w: #wait
					code = os.wait() 
					if code[1] != 0 and code[1] != 256:
						os.write(2, ("Program terminated with exit code: %d\n" % code[1]).encode())
					

def parse2(cmdString):
	outFile = None
	inFile = None
	cmdString = ' '.join([str(elem) for elem in cmdString])
	cmd = ''
	cmdString = re.sub(' +', ' ', cmdString)
	
	if '>' in cmdString:
		[cmd, outFile] = cmdString.split('>',1)
		outFile = outFile.strip()
		
	if '<' in cmd:
		[cmd, inFile] = cmd.split('<', 1)
		inFile = inFile.strip()
    
	elif outFile != None and '<' in outFile:
		[outFile, inFile] = outFile.split('<', 1)
		
		outFile = outFile.strip()
		inFile = inFile.strip()
	return cmd.split(), outFile, inFile


def simple_pipe(args): #args is a list so I can't split
	
	if '|' in args:
		
		write = args[0:args.index("|")]
		read = args[args.index("|") + 1:]
		
		pr,pw = os.pipe()

		for f in (pr, pw):
			os.set_inheritable(f, True)

		fork = os.fork()
		if fork < 0:
				os.write(2, ("fork failed, returning %d\n" % rc).encode())
				sys.exit(1)

		elif fork == 0: #son or daughter (#not assuming)
			os.close(1)
			os.dup2(pw,1) #redirect inp to child
			for fd in (pr, pw):
				os.close(fd)
			execChild(write)
			
		else:  #parent
			os.close(0)
			os.dup2(pr,0) #redirect outp to parent
			for fd in (pr, pw):
				os.close(fd)
			execChild(read)
			if "|" in read:
				pipe(read)
			execChild(read)
			
def redirect(args):
	if '>' in args or '<' in args:
		cmd,outFile,inFile = parse2(args)
		if '>' in args:
			cmd = cmd[0]
		
	if '>' in args:
		os.close(1)
		os.open(outFile, os.O_CREAT | os.O_WRONLY)
		os.set_inheritable(1,True)
		
		execute = [cmd,outFile]

		execChild(execute) #FIXME: output file only one line  #maybe I should just call lsdir
		
	if '<' in args:
		os.close(0) 
		os.open(args[-1], os.O_RDONLY)
		os.set_inheritable(0,True)
		
		execute = args[0:args.index("<")]
		execChild(execute)
	

def execChild(execute):
	for dir in re.split(":", os.environ['PATH']): # try each directory in the path
		program = "%s/%s" % (dir, execute[0])
		try:
			os.execve(program, execute, os.environ) # try to exec program
		except FileNotFoundError:
			pass 
	time.sleep(1) 
	os.write(2, ("-bash: %s: command not found\n" % execute[0]).encode())
	quit(1)
	
	
if __name__ == "__main__":
	loop_shell()