import unittest
import time
from zmq_object_exchanger.zmq_object_exchanger import zmqObjectExchanger

class testClass():
    
      def method(self):
      
        return "testClass"

class testObjectExchanger(unittest.TestCase):

  def test_shared_key(self):
    """Tests usage of shared key for better security."""
  
    key = "myHyperUltraSecureKey"
    
    r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234, shared_key=key)
    r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321, shared_key=key)
    r1.add_remote("robot2", "127.0.0.1", 4321)
    time.sleep(0.1)
    
    r2.send_msg("secure_topic", "confident message")
    time.sleep(0.1)
    
    r1msgs = r1.get_msgs()
    
    r1.stop_listening()
    r2.stop_listening()
    
    self.assertEqual(len(r1msgs), 1)
    
  def test_shared_key_on_one_side(self):
    """Tests usage of shared key where keys are different."""
  
    key = "myHyperUltraSecureKey"
    mkey = "myWrongHyperUltraSecureKey"
    
    r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234, shared_key=key)
    r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321, shared_key=mkey)
    r1.add_remote("robot2", "127.0.0.1", 4321)
    time.sleep(0.1)
    
    r2.send_msg("secure_topic", "confident message")
    time.sleep(0.1)
    
    r1msgs = r1.get_msgs()
    
    r1.stop_listening()
    r2.stop_listening()
    
    self.assertEqual(len(r1msgs), 0)
  

  def test_object_integrity(self):
    """This tests if sent object is received correctly."""
  
        
    r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234)
    r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321)
    
    r1.add_remote("robot2", "127.0.0.1", 4321)
    
    time.sleep(0.1)
    
    obj = testClass()
    
    r2.send_msg("some_topic", obj)

    time.sleep(0.1)
    
    r1msgs = r1.get_msgs()
    
    r1.stop_listening()
    r2.stop_listening()
    
    (prio, robj) = r1msgs[0]
    
    self.assertEqual(robj["data"].method(), "testClass")
    
  
  def test_topic_filtering(self):
    """Tests if topic filtering works properly using number of received messages."""
  
    r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234)
    r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321)
    
    r1.add_remote("robot2", "127.0.0.1", 4321, ["strings_topic"])
    
    time.sleep(0.1)
      
    for i in range(0,10):
    
      r2.send_msg("strings_topic", str(i))
      r2.send_msg("strings_topic_twofold", str(2*i))
      r2.send_msg("numbers_topic", i)
      r2.send_msg("numbers_topic_twofold", 2*i)
      
    time.sleep(0.1)
    
    r1msgs = r1.get_msgs()
    r2msgs = r2.get_msgs()
    
    r1.stop_listening()
    r2.stop_listening()
    
    self.assertEqual(len(r1msgs), 10)
  
