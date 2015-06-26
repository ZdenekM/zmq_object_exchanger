import zmq
import threading
import zlib
import cPickle as pickle
import Queue
import time
import sys
import hmac
import hashlib

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

class zmqObjectInterface(Thread):
  """
  Helper class representing (remote) publisher.
  """

  # TODO request - response (services)

  def __init__(self, name, ip, port, topics, shared_key = ""):
  
    Thread.__init__(self, name="zmqObjectInterface: " + name)
  
    self.name = name
    self.topics = topics
    
    self.shared_key = shared_key
  
    self.context = zmq.Context()
    self.sub_queue = Queue.PriorityQueue()
    
    self.sub_socket = self.context.socket(zmq.SUB)
    self.socket_str = "tcp://" + ip + ":" + str(port)
    self.log("Subscribing to: " + self.socket_str)
    self.sub_socket.connect(self.socket_str)
    if len(topics) == 0:
      self.sub_socket.setsockopt(zmq.SUBSCRIBE, "")
      self.log("All topics")
    else:
      for topic in self.topics:
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, topic)
        self.log("Topic: " + topic)
    
    self.start()
  
  def disconnect(self):
  
    self.sub_socket.disconnect(self.socket_str)
  
  def log(self, msg):
  
    print("[" + self.name + "_sub] " + msg)
    sys.stdout.flush()
    
  def run(self):
  
    self.log("Listening for messages")
  
    while not self.is_shutdown():
    
      [topic, z, digest] = self.sub_socket.recv_multipart() # TODO timeout

      p = zlib.decompress(z)

      if self.shared_key != "":
          
        new_digest = hmac.new(self.shared_key, p, hashlib.sha1).hexdigest()
        
        if digest != new_digest:
        
          self.log("Integrity check failed")
          continue
      
      msg = pickle.loads(p)
      
      try:
      
        # TODO filtering topics using zmq setsockopt doesn't work (so we need to filter here) - why???
        if (msg["name"] == self.name and (topic in self.topics or len(self.topics) == 0)):
      
          self.log("Received message from " + msg["name"] + " (priority " + str(msg["priority"]) + ")")
      
          # callback?
          
          self.sub_queue.put((msg["priority"], msg))
          
      except KeyError:
      
        self.log("Malformed message.")
        
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
      
  def get_msg(self, block = False, timeout = 0):
    """Returns one message."""
  
    try:
  
      return self.sub_queue.get(block, timeout)
      
    except Queue.Empty:
    
      pass
      
    return None
  
    
class zmqObjectExchanger(Thread):
  """
  This class acts as a publisher and at the same time it can handle incoming data from one or more sources.
  """

  def __init__(self, name, ip, port, shared_key = ""):
  
    Thread.__init__(self, name="zmqObjectExchanger: " + name) 
  
    self.name = name
    
    self.shared_key = shared_key
  
    self.context = zmq.Context()

    self.pub_socket = self.context.socket(zmq.PUB)
    self.socket_str = "tcp://*" + ":" + str(port)
    self.log("Going to publish on: " + self.socket_str)
    self.pub_socket.bind(self.socket_str)
    
    self.subs = {}
    
    self.pub_queue = Queue.PriorityQueue()
    
    self.start()
    
  def log(self, msg):
  
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
    
      (prio, msg) = self.pub_queue.get()
      
      self.log("Publishing msg with priority: " + str(prio))
      
      p = pickle.dumps(msg)
      z = zlib.compress(p)
      
      digest = ""
      
      if self.shared_key != "":
      
        digest = hmac.new(self.shared_key, p, hashlib.sha1).hexdigest()
      
      self.pub_socket.send_multipart([msg["topic"], z, digest])
      
  
  def add_remote(self, name, ip, port, topics=[]):
    """Add (remote) data source we want to listen to."""
  
    robot = zmqObjectInterface(name, ip, port, topics, self.shared_key)
    self.subs["name"] = robot
  
  def get_msgs(self, name=""):
    """Get all received messages from specific source or from all of them."""
  
    msgs = []
  
    # TODO test if name exists - raise exception
  
    if name=="":
    
      for key in self.subs:
      
        msg = self.subs[key].get_msgs()
        msgs.extend(msg)
          
    else:
    
      msg = self.subs[name].get_msgs()
      msgs.extend(msg)
        
    return msgs
  
  def send_msg(self, topic, data, prio = 10):
    """Send object to specified topic. Messages with lower priority will be send first."""
  
    tmp = {}
    
    tmp["topic"] = topic
    tmp["name"] = self.name
    tmp["data"] = data
    tmp["priority"] = prio
  
    self.pub_queue.put((prio, tmp))
    
if __name__ == "__main__":

  pass
  

