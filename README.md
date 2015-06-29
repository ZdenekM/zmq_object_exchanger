# zmq_object_exchanger

[![Build Status](https://travis-ci.org/ZdenekM/zmq_object_exchanger.svg?branch=master)](https://travis-ci.org/ZdenekM/zmq_object_exchanger)

This stuff helps you to send and receive arbitrary Python objects over network - it uses pyzmq to do so. Python objects are serialized, compressed and sent over network. There is PriorityQueue on both ends so messages/objects with higher priority (lower integer number) are sent/received first. Moreover usage of PriorityQueue makes methods for sending and getting data thread-safe. Messages are sent on '''topics''' and each receiver can filter incoming data based on topics names.

Sending dictionary over network (well, let's do it on localhost for simplicity) is such easy:

```python
sender = zmqObjectExchanger("sender", "127.0.0.1", 1234)
receiver = zmqObjectExchanger("receiver", "127.0.0.1", 4321)
receiver.add_remote("sender", "127.0.0.1", 1234)
time.sleep(0.1) # some time is usually required here

d = {}
d["foo"] = "bar"
sender.send_msg("dictionary_topic", d) # send message with default priority (topic doesn't matter in this case)
time.sleep(0.1)
received_msgs = receiver.get_msgs() # array of received messages

msg = received_msgs[0] # there is probably only one :)
rd = msg["data"] # returned structure is dictionary, where key 'data' contains actual message
print(rd["foo"]) # will print 'bar'

receiver.stop_listening() # cleanup
sender.stop_listening()
```

Please note that this is not really secure as somebody might send you some malicious code. If you trust the other party and your network it's completely ok. If your network is not completely safe, please use cryptographic signature and verification. You just need to add one more parameter - your shared key.

```python
key = "myHyperUltraSecureKey"
sender = zmqObjectExchanger("sender", "machine1", 1234, shared_key=key) 
receiver = zmqObjectExchanger("receiver", "machine2", 4321, shared_key=key)

```
And that's all - rest is same as in the previous example. The class will check for you if delivered messages are fine (not modified).

## Future plans

* Support for request / response.
* Support for callbacks.
* Secure transfer over SSH.
* Better tests.
* More examples including usage with ROS.
