import zmq
import threading
import zlib
import cPickle as pickle
import Queue
import sys
import hmac
import hashlib
import time

class Thread(threading.Thread):
    """
    Helper class providing stoppable thread.
    """

    def __init__(self, name):

        threading.Thread.__init__(self)
        self.name = name

        self.mailbox = Queue.Queue()

        self.daemon = True

    def stop(self):

        self.mailbox.put("shutdown")

    def is_shutdown(self):
        try:
                data = self.mailbox.get(block=False)
        except Queue.Empty:
                return False
        return data == 'shutdown'

class zmqObjectExchangerException(Exception):
    pass

class zmqObjectInterface(Thread):
    """
    Helper class representing (remote) publisher.
    """

    # TODO request - response (services)

    def __init__(self, parent, name, ip, port, topics, shared_key="", logging=False):

        Thread.__init__(self, name="zmqObjectInterface: " + name)

        self.name = name
        self.topics = topics
        self.parent = parent

        self.shared_key = shared_key
        
        self.logging = logging # add more options (to file, etc.)

        self.context = zmq.Context()
        self.sub_queue = Queue.PriorityQueue()

        self.sub_socket = self.context.socket(zmq.SUB)
        self.socket_str = "tcp://" + ip + ":" + str(port)
        self.log("Subscribing to: " + self.socket_str)
        self.sub_socket.connect(self.socket_str)
        
        # ZMQ does topic filtering on subscriber side so we can do it on our own
        # if len(topics) == 0:
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, u"")
        #     self.log("All topics")
        # else:
        #     for topic in self.topics:
        #         self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, unicode(topic))
        #         self.log("Topic: " + topic)

        self.start()

    def disconnect(self):

        self.sub_socket.disconnect(self.socket_str)

    def log(self, msg):
        
        if self.logging:
        
            print("[" + self.name + "_sub] " + msg)
            sys.stdout.flush()

    def run(self):

        self.log("Listening to messages")

        while not self.is_shutdown():

            [topic, name, z, digest] = self.sub_socket.recv_multipart()  # TODO timeout
            
            if (name != self.name):
            
                continue
                
            if len(self.topics) != 0 and topic not in self.topics:
            
                continue

            p = zlib.decompress(z)

            if self.shared_key != "":

                new_digest = hmac.new(self.shared_key, p, hashlib.sha1).hexdigest()

                if digest != new_digest:

                    self.log("Integrity check failed")
                    continue

            msg = pickle.loads(p)
            self.log("Received message from " + name + " (priority " + str(msg["prio"]) + ")")

            msg["topic"] = topic
            msg["name"] = name
            msg["received"] = time.time()

            self.sub_queue.put((msg["prio"], msg))
            
            if self.parent.callback is not None:
            
                self.parent.callback_queue.put(self.parent.callback)

        self.log("Stopping listening for messages from " + self.name)

    def get_msgs(self):
        """Returns all received messages."""

        msgs = []

        while True:

            msg = self.get_msg()
            if msg is None:
                break
            msgs.append(msg)

        return msgs

    def get_msg(self, block=False, timeout=0):
        """Returns one message."""

        try:

            (prio, msg) = self.sub_queue.get(block, timeout)
            return msg

        except Queue.Empty:

            pass

        return None


class zmqObjectExchanger(Thread):
    """
    This class acts as a publisher and at the same time it can handle incoming data from one or more sources.
    """

    def __init__(self, name, ip, port, shared_key="", callback = None, logging=False):

        Thread.__init__(self, name="zmqObjectExchanger: " + name)

        self.name = name

        self.shared_key = shared_key

        self.context = zmq.Context()
        
        self.callback = callback
        self.callback_queue = Queue.Queue()
        
        self.logging = logging

        self.pub_socket = self.context.socket(zmq.PUB)
        self.socket_str = "tcp://*" + ":" + str(port)
        self.log("Going to publish on: " + self.socket_str)
        
        try:
        
            self.pub_socket.bind(self.socket_str)
            
        except zmq.ZMQError:
        
            raise zmqObjectExchangerException("bind error")

        self.subs = {}

        self.pub_queue = Queue.PriorityQueue()

        self.start()
    
    def spinOnce(self):
    
        try:
            callback = self.callback_queue.get(False)
        except Queue.Empty:
            return
        callback()
        
    def spin(self):
    
        while True:
            
            callback = self.callback_queue.get()
            callback()

    def log(self, msg):
    
        if self.logging:

            print("[" + self.name + "] " + msg)
            sys.stdout.flush()

    def stop_listening(self):

        for key in self.subs:

            self.subs[key].stop()
            self.subs[key].disconnect()

        self.stop()
        self.pub_socket.unbind(self.socket_str)

    def run(self):

        while not self.is_shutdown():

            (prio, topic, msg) = self.pub_queue.get()

            self.log("Publishing msg with priority: " + str(prio))

            msg["prio"] = prio

            p = pickle.dumps(msg)
            z = zlib.compress(p)

            digest = ""

            if self.shared_key != "":

                digest = hmac.new(self.shared_key, p, hashlib.sha1).hexdigest()

            self.pub_socket.send_multipart([topic, self.name, z, digest])

    def add_remote(self, name, ip, port, topics=[]):
        """Add (remote) data source we want to listen to."""

        robot = zmqObjectInterface(self, name, ip, port, topics, self.shared_key, logging = self.logging)
        self.subs[name] = robot

    def get_msgs(self, name=""):
        """Get all received messages from specific source or from all of them."""

        msgs = []

        if name == "":

            for key in self.subs:

                msg = self.subs[key].get_msgs()
                msgs.extend(msg)

        else:

            try:

                msg = self.subs[name].get_msgs()
                msgs.extend(msg)
                
            except KeyError:
            
                raise zmqObjectExchangerException("not known name")

        return msgs

    def send_msg(self, topic, data, prio=10):
        """Send object to specified topic. Messages with lower priority will be send first."""

        # there might be more fileds in future (timestamp?) so let's use dictionary
        tmp = {}
        tmp["data"] = data
        tmp["sent"] = time.time()

        self.pub_queue.put((prio, topic, tmp))

if __name__ == "__main__":

    pass
