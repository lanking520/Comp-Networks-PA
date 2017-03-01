# CSEE4119 Super Chatter

Name: Qing Lan						UNI: ql2282

## Description
Super Chatter is a Chatting application built in python what enable several users chatting together. It used the UDP protocol + multi-threading to achieve the full functionalities for clients and server.

## Tutorial
To provides the full functionalities of the program and avoid unexpected error please run the followings:
```bash
$ sudo apt-get install build-essentials
```
To run the application, please move to the folder of the Python file. If client has been set-up before server, the client would automatically quit.

### Run as a server

```bash
$ python UdpChat.py -s <port>
```
### Run as a client
```bash

$ python UdpChat.py -c <nick-name> <server-ip> <server-port> <client-port>
```

### Startup

An Operating Server will tipically show:
```
dyn-160-39-140-44:chatter lanking$ python UdpChat.py -s 5000
Socket created and binded
listening on: localhost : 5000
Server Mode Start
```
For Client Side:
```
dyn-160-39-140-44:chatter lanking$ python UdpChat.py -c sonic localhost 5000 1211
Socket created and binded
Client Mode Start
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> 
```

### Chatting

Send a Chat Message (From Lanking to sonic)

#### Lanking
```
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> send sonic hi
>>> [Message received by sonic.]
>>> 
```
#### Sonic
```
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> lanking: hi
>>> 
```
### Offline Chatting
#### Case: sonic shutdown (No Dereg)
Message shown on Lanking's Terminal
```
>>> send sonic hi
>>> [No ACK from sonic, message sent to server.]
[Messages received by the server and saved]
>>> [Client table updated.]
>>> 
```
And a File namely "sonic" will be generated with the following content
```
{"Msg": "hi", "Sender": "lanking", "Time": 1488400115.368341}
```
If sonic Log-back, the file will be loaded properly and removed.
```
>>> reg sonic
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> [You Have Messages]
>>> lanking: 2017-03-01 15:28:35 hi
>>> 
```
### Login and Logoff

#### Logoff

```
>>> dereg
>>> [You are Offline. Bye.]
```
#### Login

```
>>> reg lanking
>>> [Welcome, You are registered.]
>>> [Client table updated.]
```

## Program Feature
This application is designed for Online/Offline communication with complete login/logoff architecture. The protocol this App use is the UDP connection. It contains the a comprehensive error handling features for the know issues:
- Accident Offline handling: Client notify Server -> Server store offline message and update table
- Conflict Login: Username should be unique while the server operating
- Dead Online Client: Server has a Verification function used to check the online status of the client


## Data Structure and Internal Logic

The whole application were built based the two classes, Server and client. All messages are parsed and loaded in JSON.

### Server

#### Variable
- addrbook: Used to store updated Database
- kill: A flag used to shut down the listener of the Server
- s: Socket used to listen and send message

#### Function
- __init__ : Used to create new socket and bind to the IP and port
- listen : Listening logic for server contains functionality to send ACK in response
- send: Send the message to the client (Contains ACK fetcher to fetch ACK)
- broadcast: Send information to all available user
- Update_table: Major function to update the registration table, dealing with registration request
- dereg_user: Process Deregistration request from Client
- verification: Check the user is online or not
- offline_msg: Dealing with offline request and store messages

#### Accepted Request
- Reg: Registration Request
- Dereg: Dereg Request
- Offline: Offline Storage Request
- ack: For acknoledgement

### Client



## Current Known Issue

### Wrong ACK Flag

### Handle Multiple request at the same time
The client and server's listener are designed with 100 msec timeout. Considering a large amount of users using the application at the same time, there maybe some packet timed-out. This issue could be fixed in the future version by adding a Complex threading system. Every Listener itself is a thread with an expire time. The listening process wouldn't delayed by a single thread. If is possible to use a queue to process the incoming requests.

### Ctrl + C Triggering
The handling of Ctrl + C will work all the time. However, sometimes you need to Ctrl + C + Enter to Get it proceed.