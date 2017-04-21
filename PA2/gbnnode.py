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
from threading import Thread


def prompt():
    sys.stdout.write('node> ')
    sys.stdout.flush()

class GBN:
	def __init__(self, sp, pp, ws, mod, val, HOST = "localhost"):
		self.port = int(sp)
		self.addr = (HOST,int(pp))
		self.windowsize = int(ws)
		self.mode = mod
		self.value = float(val)
		self.sending = False
		self.recvmsg = ""
		self.discarder = 0
		self.recver = 0
		try :
			if self.port < 1024 or self.port > 65535:
				print 'Port Number out of range'
				sys.exit()
			# UDP Configuration
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.bind((HOST, self.port))
			print 'Socket created and binded'
			print 'listening on: %s : %d' % (HOST, self.port)
			# Error Handling
		except socket.error, msg:
			print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
			sys.exit()

	def drop(self):
		total = self.discarder + self.recver+1
		if self.mode == '-d':
			if total != 0 and total % self.value == 0.0:
				return True
			else:
				return False
		else:
			num = random.uniform(0,1)
			if num <= self.value:
				return True
			else:
				return False

	def send(self,data):
		self.s.sendto(data[1], self.addr)
		msg = "["+str(time.time())+"] packet"+data[1][:-1]+" "+data[1][-1]+" sent"
		print msg
		data[0] = "SD"
		#time.sleep(0.01)

	def sorter(self):
		# ["ACK/NS/SD","pkgn'b']
		# NS: Not send, ACK: acked, SD: Send
		ACK_flag = [False,0]
		for i in range(len(self.window)):
			if self.window[i][0] == "ACK":
				ACK_flag = [True,i]
				break
			if self.window[i][0] == "NS":
				self.send(self.window[i])
				if i == 0:
					self.timer = time.time() + 0.5

		# Move the Window
		if ACK_flag[0]:
			self.window = self.window[ACK_flag[1]+1:]
			if len(self.window) != 0:
				lastnum = int(self.window[-1][1][:-1])
				for i in range(ACK_flag[1]+1):
					lastnum += 1
					if len(self.message) > 0:
						self.window.append(["NS",str(lastnum)+self.message[0]])
						self.message = self.message[1:]
			elif len(self.message) != 0:
				# Case ACK to the End
				i  = self.msglen - len(self.message)
				while len(self.window) < self.windowsize and len(self.message) != 0:
					self.window.append(["NS",str(i)+self.message[0]])
					self.message = self.message[1:]
					i += 1
			self.timer = time.time() + 0.5

		# Timeout			
		if self.timer <= time.time():
			msg = "["+str(time.time())+"] packet"+self.window[0][1][:-1]+" timeout"
			print msg
			self.timer = time.time() + 0.5
			for i in range(len(self.window)):
				self.send(self.window[i])


	def listener(self):
		while True:
			while self.sending:
				try:
					self.s.settimeout(0.1)
					d = self.s.recvfrom(4096)
					if d[0] == 'done':
						print "[Summary] "+str(self.discarder)+"/"+str(self.discarder+self.recver)+" packets discarded, loss rate = "+str(self.discarder*1.0/(self.recver+self.discarder))
						#print self.msglen
						self.discarder = 0
						self.recver = 0
					else:
						if self.drop():
							msg = "["+str(time.time())+"] ACK"+d[0]+" discarded"
							print msg
							self.discarder += 1
						else:
							num = int(d[0]) - int(self.window[0][1][:-1])
							# Avoid Duplicates ACK
							if num >= 0:
								self.window[num][0] = "ACK"
								msg = "["+str(time.time())+"] ACK"+d[0]+" received, window moves to "+str(int(d[0])+1)
								print msg
								self.recver += 1
				except socket.timeout:
					pass
			while not self.sending:
				try:
					self.s.settimeout(0.1)
					d = self.s.recvfrom(4096)
					message = d[0]
					if message != 'done':
						if not self.drop():
							msg = "["+str(time.time())+"] packet"+message[:-1]+" "+message[-1]+" received"
							print msg

							result = len(self.recvmsg)-1
							if int(message[:-1]) == len(self.recvmsg):
								# Avoid Duplicated Packets
								result += 1
								self.recvmsg += message[-1]

							self.s.sendto(str(result), self.addr)
							msg = "["+str(time.time())+"] ACK"+str(result)+" sent, expecting packet"+str(result+1)
							self.recver += 1
							print msg
						else:
							msg = "["+str(time.time())+"] packet"+message[:-1]+" discarded"
							self.discarder += 1
							print msg

					else:
						self.s.sendto(message, self.addr)
						print "[Summary] "+str(self.discarder)+"/"+str(self.discarder+self.recver)+" packets dropped, loss rate = "+str(self.discarder*1.0/(self.recver+self.discarder))
						self.discarder = 0
						self.recver = 0
						#print len(self.recvmsg)
						self.recvmsg = ""
						prompt()
				except socket.timeout:
					pass

	def sender(self):
		while True:
			prompt()
			data = raw_input()
			result = data.split()
			if not result:
				continue
			elif result[0] == "send":
				self.window = []
				self.sending = True
				self.message = ' '.join(result[1:])
				self.msglen = len(self.message)
				#print self.message
				time.sleep(0.5)
				# Start Sending message
				i  = 0
				while len(self.window) < self.windowsize and len(self.message) != 0:
					self.window.append(["NS",str(i)+self.message[0]])
					self.message = self.message[1:]
					i += 1
				while len(self.window) > 0:
					self.sorter()
				self.s.sendto("done",self.addr)
				self.sending = False
				time.sleep(0.5)


	def suicide(self):
		self.s.close()


if __name__ == "__main__":
	try:
		# Not passed the basic Req
		if len(sys.argv) != 6:
			print 'Usage : python '+ sys.argv[0] +' <self-port> <peer-port> <window-size> [-d <value-of-n> | -p <value-of-p>]'
			sys.exit()

		user = GBN(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
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
