# CSEE4119 GBN + DV

Author: Qing Lan

## Description
The Programming Assignment for Go-Back-N and Distance-Vector Implementation. The application should run in Python 2.7 Version.

## Tutorial
To provides the full functionalities of the program and avoid unexpected error please run the followings:

```bash
$ sudo apt-get install build-essentials
```
### GBN Module

#### Start up a Sender/Receiver

```bash
$ python gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p>]
```
-d means running as drop packet per n and -p means drop with probability.

#### Startup

If running normally, the console should typically show:
```
node>
```
### Distance-Vector Routing

#### Start up a Node
```bash
python dvnode.py <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]
```

### Combination

#### Start up a Node

```bash
python cnnode.py <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... <neighborM-port> <loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... neighborN-port> [last]
```

## Program Feature

### GBN
This program are implemented in two thread with good tolernace with most of the error. Built with OOD Architecture, the sender and listener of GBN instance would run at the same time to send and receive message. The A Window is maintained in every cycle to send/process messages. Every Element in a window will be in the following format: ["ACK/SD/NS", "PKG_NUM"+'char']. Window itself is implemented in a list(See "sorter" function for more details).

### DV
This Program are implemented in two thread with comprehensive tolerance on Routing Table updates. Built in OOD Flavor, the sender and listener of DV instance would run at the same time to broadcast and receive update. A queue are implemented to ensure not losing any updates. Everytime we pop a update and compare with the original Routing table which would in the following format: port : [distance, Next Hop]. The table would finally converge into a stage where every node would reach to a minimum.

### Combination
This take the advantage of the previous two parts and implemented with two threads. Most of the parts are simplfied with the minimum code. Probes are continously sending and table are sent out with update every 5 second. Most of the Counting paramters are extened with different ports for management. These functions are written in a flexible way with support on multiple nodes.

- Class Architecture: Better Maintainance
- Thread Safe: Set Daemon on Listener and Sender, keep Main thread handle the Interruption
- Clean Architecture: No Hardcoded section, Easy to extend.

The application improves the Ctrl+C interruption handling. It would kill itself automatically if Ctrl+C pressed.

## Current Known Issue

### GBN Corner case:
sometimes the Loss rate are not correct (With small test sets).

### Combination:
Infinity loop may happened (Program goes crazy), could be solved by Poison Reverse.