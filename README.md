# CSEE4119 Super Chatter

Name: Qing Lan						UNI: ql2282

## Description
Super Chatter is a course project to enable 

## Tutorial

## Program Feature

## Algorithms and Data Structure

## Current Known Issue

### Handle Multiple request at the same time
The client and server's listener are designed with 100 msec timeout. Considering a large amount of users using the application at the same time, there maybe some packet timed-out. This issue could be fixed in the future version by adding a Complex threading system. Every Listener itself is a thread with an expire time. The listening process wouldn't delayed by a single thread. 