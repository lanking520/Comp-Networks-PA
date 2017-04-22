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


def prompt():
	sys.stdout.write('node> ')
	sys.stdout.flush()


# Node:
'''
Hashmap:
	1112 : [0.5,hop]
	1123 : [0.2,None]
'''

class dvnode:
	def __init__(self, args):
		self.routetable = {}
		self.port = int(args[0])
		args = args[1:]
		self.host = "localhost"
		self.last = False
		self.neighbour = []
		self.queue = []
		for i in range(len(args)/2):
			self.routetable[int(args[i*2])] = [float(args[i*2+1]), None]
			self.neighbour.append(int(args[i*2]))
		if len(args) % 2 != 0:
			self.last = True
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
		for item in nelist:
			if self.routetable.has_key(item[0]):
				if self.routetable[item[0]][0] > self.routetable[source][0]+item[1]:
					# update routing table
					# print "Compare Update"
					# print item[0],source, self.routetable[source][0]+item[1]
					adder = source
					if self.routetable[source][1]:
						adder = self.routetable[source][1]
					self.routetable[item[0]] = [self.routetable[source][0]+item[1],adder]
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

	def sender(self):
		firsttime = True
		while True:
			if len(self.queue) != 0:
				updateflag = self.update(self.queue.pop())
				self.printer()
				if updateflag or firsttime:
					self.broadcast()
					firsttime = False
			if self.last:
				self.broadcast()
				self.last = False

	def listener(self):
		while True:
			try:
				self.s.settimeout(0.01)
				d = self.s.recvfrom(4096)
				msg = "["+str(time.time())+"] Message received at Node "+str(self.port)+ " from Node "+str(d[1][1])
				print msg
				self.queue.append(json.loads(d[0]))
			except socket.timeout:
				pass

if __name__ == "__main__":
	try:
		# Not passed the basic Req
		if len(sys.argv) < 4:
			print 'Usage : python '+ sys.argv[0] +' <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]'
			sys.exit()

		user = dvnode(sys.argv[1:])
		print "Client Mode Start"
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
