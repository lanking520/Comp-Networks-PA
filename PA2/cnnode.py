#!/usr/bin/env python
'''
Author: Qing Lan
Date: 15/4/2017
Copyright: Free

'''
import socket
import os, sys
import time
import random
import json
from threading import Thread

class cnnode:
	def __init__(self, port, recvlist, sendlist):
		self.routetable = {}
		self.port = int(port)
		self.host = "localhost"
		self.last = False
		self.windowsize = 5
		self.neighbour = []
		self.window = {}
		self.droprate = {}
		self.recver = {}
		self.total = {}
		self.lastnum = {}
		self.GBNtimer = {}
		self.queue = []

		for item in recvlist:
			self.neighbour.append(int(item[0]))
			self.droprate[int(item[0])] = float(item[1])
			self.routetable[int(item[0])] = [1,None]
		if sendlist[-1] == 'last':
			self.last = True
			sendlist = sendlist[:-1]
		for item in sendlist:
			self.recver[int(item)] = 0
			self.total[int(item)] = 0
			self.GBNtimer[int(item)] = time.time()
			self.neighbour.append(int(item))
			self.routetable[int(item)] = [1,None]
			# { port :[["ACK/NS/SD","pkgn'p']]}
			self.window[int(item)] = []
			for i in range(self.windowsize):
				self.window[int(item)].append(["NS",str(i)+"p"])
			self.lastnum[int(item)] = 4

		try :
			if self.port < 1024 or self.port > 65535:
				print 'Port Number out of range'
				sys.exit()
			# UDP Configuration
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.bind((self.host, self.port))
			print 'Socket created and binded'
			print 'listening on: %s : %d' % (self.host, self.port)
			# Error Handling
		except socket.error, msg:
			print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
			sys.exit()

	def update(self, data):
		# Pass in a Dict {source :[[dest,dist], [dest,dist] ...]}
		updateflag = False
		source = data.keys()[0]
		nelist = data[source]
		source = int(source)
		if source == self.port:
			# Super User Access
			for item in nelist:
				if (not self.routetable[item[0]][1] and self.routetable[item[0]][0] != item[1]) or self.routetable[item[0]][0] > item[1]:
					self.routetable[item[0]] = [item[1], None]
					updateflag = True

		else:
			# Case Routing Table from elsewhere
			for item in nelist:
				if self.routetable.has_key(item[0]):
					# Case Shorter path found
					if self.routetable[item[0]][0] > self.routetable[source][0]+item[1]:
						# update routing table
						# print "Compare Update"
						# print item[0],source, self.routetable[source][0]+item[1]
						adder = source
						if self.routetable[source][1]:
							adder = self.routetable[source][1]
						self.routetable[item[0]] = [self.routetable[source][0]+item[1],adder]
						updateflag = True
					# Case If the Original Hop change
					elif self.routetable[item[0]][1] == source and self.routetable[source][0]+item[1] != self.routetable[item[0]][0]:
						self.routetable[item[0]] = [self.routetable[source][0]+item[1], source]
						updateflag = True

				elif item[0] != self.port:
					# case destination Not Exist
					# print "Add update"
					# print item[0], source, self.routetable[source][0]+item[1]
					self.routetable[item[0]] = [self.routetable[source][0]+item[1],source]
					updateflag = True
		return updateflag

	def package(self):
		table = {self.port:[]}
		for key in self.routetable:
			table[self.port].append([key,self.routetable[key][0]])
		return table

	def broadcast(self):
		data = json.dumps(self.package())
		for port in self.neighbour:
			addr = (self.host,port)
			self.s.sendto(data, addr)
			msg = "["+str(time.time())+"] Message sent from Node "+str(self.port)+ " to Node "+str(port)
			print msg

	def printer(self):
		print "["+str(time.time())+"] Node "+str(self.port)+" Routing Table"
		for key in self.routetable:
			msg = "("+str(self.routetable[key][0])+") -> Node "+str(key)
			if self.routetable[key][1]:
				msg += "; Next hop -> Node "+str(self.routetable[key][1])
			print msg

	def suicide(self):
		self.s.close()

	def send(self,data, port):
		self.s.sendto(data[1], ("localhost",port))
		#msg = "["+str(time.time())+"] packet"+data[1][:-1]+" "+data[1][-1]+" sent"
		#print msg
		self.total[port] += 1
		data[0] = "SD"
		#time.sleep(0.01)

	def sorter(self, port):
		# { port :[["ACK/NS/SD","pkgn'b']]}
		# NS: Not send, ACK: acked, SD: Send
		ACK_flag = [False,0]
		for i in range(len(self.window[port])):
			if self.window[port][i][0] == "ACK":
				ACK_flag = [True,i]
				break
			if self.window[port][i][0] == "NS":
				self.send(self.window[port][i],port)
				if i == 0:
					self.GBNtimer[port] = time.time() + 0.5

		# Move the Window
		if ACK_flag[0]:
			self.window[port] = self.window[port][ACK_flag[1]+1:]
			# Count received Packet
			for i in range(ACK_flag[1]+1):
				self.lastnum[port] += 1
				self.window[port].append(["NS",str(self.lastnum[port])+'p'])
			self.GBNtimer[port] = time.time() + 0.5

		# Timeout			
		if self.GBNtimer[port] <= time.time():
			# msg = "["+str(time.time())+"] packet"+self.window[port][0][1][:-1]+" timeout"
			# print msg
			self.GBNtimer[port] = time.time() + 0.5
			for i in range(len(self.window[port])):
				self.send(self.window[port][i],port)

	def drop(self, port):
		num = random.uniform(0,1)
		if num <= self.droprate[port]:
			return True
		else:
			return False

	def routeupdator(self):
		table = {self.port:[]}
		for key in self.recver:
			if self.total[key]== 0:
				dist = 1
			else:
				dist = round((self.total[key]-self.recver[key])*1.0/self.total[key],2)
			table[self.port].append([key, dist])
			temptable = {key:[[self.port, dist]]}
			# Single update to the other side
			self.s.sendto(json.dumps(temptable), ("localhost", key))
		self.queue.append(table)


# Main Stuff We are running in thread....

	def sender(self):
		firsttime = True
		while True:
			if not self.last:
				# Section ProbeSender
				if not firsttime:
					for key in self.window:
						self.sorter(key)
					if self.updatetimer < time.time():
						self.updatetimer = time.time() + 5
						self.routeupdator()

					if self.pkt_timer < time.time():
						self.pkt_timer = time.time() + 1
						for key in self.recver:
							if self.total[key] == 0:
								dist = 1
							else:
								dist = round((self.total[key]-self.recver[key])*1.0/self.total[key],2)
							msg = "["+str(time.time())+"] Link to "+str(key)+": "+str(self.total[key])+" packets sent, "+str(self.total[key]-self.recver[key])+" packets lost, loss rate "+str(dist)
							print msg
				else:
					self.updatetimer = time.time()+5
					self.pkt_timer = time.time() + 1
				# Section Table Sender
				if len(self.queue) != 0:
					updateflag = self.update(self.queue.pop())
					self.printer()
					if updateflag or firsttime:
						self.broadcast()
						firsttime = False
						self.last = False
			else:
				self.broadcast()
				self.last = False

	def listener(self):
		while True:
			try:
				self.s.settimeout(0.01)
				d = self.s.recvfrom(4096)
				port = d[1][1]

				if d[0][-1] == 'r':
					#Case Probe
					self.recver[port] += 1
					num = int(d[0][:-1]) - int(self.window[port][0][1][:-1])
					# Avoid Duplicates ACK
					if num >= 0:
						self.window[port][num][0] = "ACK"

				elif d[0][-1] == 'p':
					# Recipent
					if not self.drop(port):
						msg = d[0][:-1]+'r'
						self.s.sendto(msg, d[1])
				else:
					# Table update
					msg = "["+str(time.time())+"] Message received at Node "+str(self.port)+ " from Node "+str(port)
					print msg
					self.queue.append(json.loads(d[0]))
			except socket.timeout:
				pass

if __name__ == "__main__":
	try:
		# Not passed the basic Req
		if len(sys.argv) < 4:
			print 'Usage : python '+ sys.argv[0] +' <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... <neighborM-port> <loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... <neighborN-port> [last]'
			sys.exit()

		args = sys.argv[1:]
		port = args[0]
		args = args[2:]
		i = 0
		recvlist = []
		while args[i] != 'send':
			recvlist.append([args[i],args[i+1]])
			i += 2
		sendlist = args[i+1:]

		user = cnnode(port, recvlist, sendlist)
		print "Cnnode Start"
		t1=Thread(target=user.listener)
		t2=Thread(target=user.sender)
		# Set daemon Linking
		t1.daemon = True
		t2.daemon = True
		t1.start()
		t2.start()
		# Binding all of them together
		while t1.isAlive() and t2.isAlive():
			t1.join(1)
			t2.join(1)
		# Handle Ctrl + C
	except KeyboardInterrupt:
		user.suicide()
