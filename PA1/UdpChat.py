#!/usr/bin/env python
'''
Author: Qing Lan
Date: 1/3/2017
Copyright: Free

'''
import socket
import os, sys
import json
import time
import datetime
from threading import Thread

#Server Accept Type ["Reg", "Dereg", "Offline", "ack"]
#Client Client Type["Chat", "Table", "Notification","ack"]

def prompt() :
    sys.stdout.write('>>> ')
    sys.stdout.flush()

class Server:
	def  __init__(self, PORT, HOST = "localhost"):
		try :
			self.addrbook = {}
			self.kill = False
			# 1024-65535
			PORT = int(PORT)
			if PORT < 1024 or PORT > 65535:
				print 'Port Number out of range'
				sys.exit()
			# UDP Configuration
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.bind((HOST, PORT))
			print 'Socket created and binded'
			print 'listening on: %s : %d' % (HOST, PORT)
			# Error Handling
		except socket.error, msg:
			print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
			sys.exit()

	def listen(self):
		try:
			# Timeout for Server
			self.s.settimeout(0.3)
			d = self.s.recvfrom(4096)
			data = d[0]
			addr = d[1]
			if not data: 
				print "Lost Data..."
			# Send ACK
			ACK = json.dumps({"Type": "ack"})
			self.s.sendto(ACK, addr)
			# JSON reading
			data = json.loads(data)
			return data, addr
		except socket.timeout:
			return None, None

	def send(self, data, addr):
		try:
			# JSON Packaging data
			self.s.sendto(json.dumps(data) , addr)
			# 500msec Timeout
			self.s.settimeout(0.5)
			d = self.s.recvfrom(4096)
			recvdata = json.loads(d[0])
			if recvdata["Type"] == "ack":
				return True
			else:
				return False
		except socket.timeout:
			return False

	def broadcast(self, data):
		for key, value in self.addrbook.iteritems():
			# Need to handle offline client
			if value[2] == "Yes":
				self.send(data, (value[0],value[1]))

	def update_table(self, name, addr):
		if self.addrbook.has_key(name) and self.verification((self.addrbook[name][0], self.addrbook[name][1])) and addr != (self.addrbook[name][0], self.addrbook[name][1]):
			# Condition the User exist and he is actual Online
			self.send({"Type":"Notification", "Msg":"["+ name +" is already Online!]", "Offline": "True"},addr)
		else:
			self.send({"Type":"Notification", "Msg":"[Welcome, You are registered.]", "Offline": "False"},addr)
			self.addrbook[name] = [addr[0], addr[1], "Yes"]
			self.broadcast({"Type":"Table", "Msg":json.dumps(self.addrbook)})
			try:
				# File Operation
				file = open(name, 'r')
				lines = file.readlines()
				file.close()
				os.remove(name)
				# Offline Message Handling
				self.send({"Type":"Notification", "Msg":"[You Have Messages]", "Offline": "False"},addr)
				for line in lines:
					data = json.loads(line)
					# Time Conversion
					times = datetime.datetime.fromtimestamp(int(data["Time"])).strftime('%Y-%m-%d %H:%M:%S')
					msg = times +" "+ data["Msg"]
					self.send({"Type": "Chat", "Sender": data["Sender"], "Msg": msg}, addr)
			except IOError:
				print "No Offline Message for " + name

	def dereg_user(self, nickname):
		self.addrbook[nickname][2] = "No"
		addr = (self.addrbook[nickname][0], self.addrbook[nickname][1])
		self.send({"Type":"Notification", "Msg":"[You are Offline. Bye.]", "Offline": "True"}, addr)
		# Update the Table and send to everyone
		self.broadcast({"Type":"Table", "Msg":json.dumps(self.addrbook)})

	def verification(self, addr):
		sent = self.send({"Type":"Verification"}, addr)
		return sent

	def offline_msg(self, data, addr):
		# Check the user exist first
		if not self.verification(addr):
			self.addrbook[data["Receipent"]][2] = "No"

		if data["Status"] == "Offline" and self.addrbook[data["Receipent"]][2] == "Yes":
			# Condition: User Exist
			self.send({"Type":"Notification", "Msg":"[Client"+ data["Receipent"] +"exists!!]", "Offline": "False"}, addr)
			self.send({"Type":"Table", "Msg":json.dumps(self.addrbook)}, addr)
		else:
			currtime = time.time()
			sender = data["Nickname"]
			recipent = data["Receipent"]
			Msg = data["Msg"]
			try:
				# Append
				file = open(recipent, 'a')
			except IOError:
				# Create
				file = open(recipent, 'w+')
			# Write in file
			file.write(json.dumps({"Time": currtime, "Sender": sender, "Msg": Msg})+"\n")
			file.close()
			# Tell the client
			self.send({"Type":"Notification", "Msg":"[Messages received by the server and saved]", "Offline": "False"}, addr)
			if self.addrbook[data["Receipent"]][2] == "Yes":
				self.addrbook[data["Receipent"]][2] = "No"
				self.broadcast({"Type":"Table", "Msg":json.dumps(self.addrbook)})

	def dereg(self):
		self.broadcast({"Type":"Notification", "Msg":"[Server is Down!]", "Offline": "True"})



class Client:
	def  __init__(self, nickname, Serverip, Serverport,PORT, HOST = "localhost"):
		try :
			# 1024-65535
			self.kill = False
			self.acked = False
			self.addrbook = {}
			self.nickname = nickname
			self.Serverport = int(Serverport)
			self.Serverip = Serverip
			self.PORT = int(PORT)
			if self.PORT < 1024 or self.PORT > 65535:
				print '[Port Number out of range]'
				sys.exit()
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.bind((HOST, self.PORT))
			print 'Socket created and binded'
		except socket.error, msg:
			print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
			sys.exit()

	def listen(self):
		try:
			self.s.settimeout(0.1)
			d = self.s.recvfrom(4096)
			data = d[0]
			addr = d[1]
			if not data: 
				print "Lost Data..."
			data = json.loads(data)
			# Avoid Infinite ACK
			if data["Type"] != "ack":
				ACK = json.dumps({"Type": "ack"})
				self.s.sendto(ACK, addr)
				return data, addr
			else:
				# Set ACK Flag
				self.acked = True
				return None, None

		except socket.timeout:
			return None, None

	def send(self, data, addr):
		try:
			self.isend = True
			self.s.sendto(json.dumps(data), addr)
			time.sleep(0.5)
			# Check ACK flag
			if self.acked:
				self.acked = False
				return True
			else:
				return False
		except socket.timeout:
			self.isend = False
			return False

	def updatetable(self, table):
		self.addrbook = json.loads(table)

	def reg(self):
		msg = {"Type": "Reg", "Nickname": self.nickname}
		return self.serversend(msg)

	def serversend(self, msg):
		sent = False
		times = 0
		# 5 times handling condition
		while not sent and times < 5:
			print "["+str(times+1)+" Attempt Connection.]"
			sent = self.send(msg, (self.Serverip, self.Serverport))
			times += 1
		return sent

	def dereg(self):
		msg = {"Type":"Dereg", "Nickname": self.nickname}
		return self.serversend(msg)

	def suicide(self):
		# Condition Server failed
		prompt()
		print "[Server not responding]"
		prompt()
		print "[Exiting]"
		sys.exit()

def server_logic(server):
	while True:
		data, addr = server.listen()
		# Condition Switch
		if data:
			if data["Type"] == "Reg":
				server.update_table(data["Nickname"], addr)
				print "Incoming Registration Request from "+ data["Nickname"]
			elif data["Type"] == "Dereg":
				server.dereg_user(data["Nickname"])
				print "Incoming De-reg Request from "+ data["Nickname"]
			elif data["Type"] == "Offline":
				server.offline_msg(data, addr)
				print "Incoming Offline Message Request from "+ data["Nickname"]
			else:
				print data

def client_listen(client):
	prompt()
	while True:
		if not client.kill:
			data, addr = client.listen()
			# If there is some data
			if data:
				if data["Type"] == "Table":
					client.updatetable(data["Msg"])
					print "[Client table updated.]"

				elif data["Type"] == "Chat":
					print data["Sender"] + ": " + data["Msg"]

				elif data["Type"] == "Notification":
					print data["Msg"]
					if data["Offline"] == "True":
						client.kill = True
						if data["Msg"] == "[Server is Down!]":
							sys.exit()

				elif data["Type"] == "Verification":
					continue	
				# What will here be?	
				else:
					print data
				prompt()

def client_send(client):
	# Two Threads: one for listen to the other client
	# Another for listening to the users typing
	if not client.reg():
		client.suicide()
	while True:
		data = raw_input()
		prompt()
		# Handle Normal Condition	
		if not client.kill:
			result = data.split()
			if not result:
				continue

			elif result[0] == "send":
				if result[1] in client.addrbook:
					info = client.addrbook[result[1]]
					msg = ' '.join(result[2:])
					# Case user online in the addressbook
					if info[2] == "Yes":
						# However sent failed!
						if not client.send({"Type": "Chat", "Msg" : msg, "Sender": client.nickname}, (info[0],info[1])):
							print "[No ACK from " + result[1] +", message sent to server.]"
							if not client.serversend({"Type":"Offline", "Nickname":client.nickname, "Receipent": result[1], "Status":"Online", "Msg":msg}):
								client.suicide()
						else:
							print "[Message received by "+ result[1] +".]"
							prompt()
					else:
						# Case User has shown offline
						if not client.serversend({"Type":"Offline", "Nickname":client.nickname, "Receipent": result[1], "Status":"Offline", "Msg":msg}):
							client.suicide()
				else:
					# User not existed
					print "[Client "+ result[1] + " Not Existed!]"
					prompt()

			elif result[0] == "dereg":
				if not client.dereg():
					client.suicide()
		else:
			# Once the Client is offline
			result = data.split()
			if not result or len(result) != 2:
				continue
			elif result[0] == "reg":
				client.nickname = result[1]
				client.kill = False
				if not client.reg():
					client.suicide()




if __name__ == "__main__":
	try:
		# Not passed the basic Req
		if(len(sys.argv) < 3):
			print 'Server Usage : python '+ sys.argv[0] +' -s <port>'
			print 'Client Usage : python '+ sys.argv[0] +' -c <nick-name> <server-ip> <server-port> <client-port>'
			sys.exit()
		# Client Mode
		if sys.argv[1] == "-c" and len(sys.argv) == 6:
			user = Client(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
			print "Client Mode Start"
			t1=Thread(target=client_send, args=(user,))
			t2=Thread(target=client_listen, args=(user,))
			# Set daemon Linking
			t1.daemon = True
			t2.daemon = True
			t1.start()
			t2.start()
			# Binding all of them together
			while t1.isAlive() and t2.isAlive():
				t1.join(1)
				t2.join(1)
		# Server Mode
		elif sys.argv[1] == "-s":
			user = Server(sys.argv[2])
			print "Server Mode Start"
			server_logic(user)
		else:
			print 'Server Usage : python '+ sys.argv[0] +' -s <port>'
			print 'Client Usage : python '+ sys.argv[0] +' -c <nick-name> <server-ip> <server-port> <client-port>'
			sys.exit()
		# Handle Ctrl + C
	except KeyboardInterrupt:
		if not user.kill:
			user.dereg()
		user.s.close()
