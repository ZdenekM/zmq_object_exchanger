import unittest
import time
from zmq_object_exchanger.zmq_object_exchanger import zmqObjectExchanger


class testClass():

    def method(self):

        return "testClass"


class testObjectExchanger(unittest.TestCase):

    def setUp(self):
    
        self.callback_called = False

    def callback(self):
    
        self.callback_called = True

    def test_callback(self):
        """Tests if callback is called properly."""
    
        r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234, callback=self.callback)
        r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321)
        r1.add_remote("robot2", "127.0.0.1", 4321)
        time.sleep(0.1)
        
        r2.send_msg("some_topic", "some message")
        time.sleep(0.1)
        
        r1.spinOnce()
        
        r1.stop_listening()
        r2.stop_listening()
        
        self.assertEqual(self.callback_called, True)
        

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
        
        self.assertEqual(len(r1msgs), 1)

        self.assertEqual(r1msgs[0]["data"].method(), "testClass")
        
    def test_getmsgs_filter(self):
        """This tests if we can read messages from only one source correctly."""

        r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234)
        r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321)
        r3 = zmqObjectExchanger("robot3", "127.0.0.1", 4356)

        r1.add_remote("robot2", "127.0.0.1", 4321)
        r1.add_remote("robot3", "127.0.0.1", 4356)

        time.sleep(0.1)

        data = [1, 2, 3, "Lorem Ipsum"]

        r2.send_msg("some_topic", data)
        r3.send_msg("another_topic", data)

        time.sleep(0.1)

        r1msgs = r1.get_msgs("robot3")

        r1.stop_listening()
        r2.stop_listening()
        r3.stop_listening()
        
        self.assertEqual(len(r1msgs), 1)

        self.assertEqual(r1msgs[0]["name"], "robot3")

    def test_topic_filtering(self):
        """Tests if topic filtering works properly using number of received messages."""

        r1 = zmqObjectExchanger("robot1", "127.0.0.1", 1234)
        r2 = zmqObjectExchanger("robot2", "127.0.0.1", 4321)

        r1.add_remote("robot2", "127.0.0.1", 4321, ["strings_topic"])

        time.sleep(0.1)

        for i in range(0, 10):

            r2.send_msg("strings_topic", str(i))
            r2.send_msg("strings_topic_twofold", str(2*i))
            r2.send_msg("numbers_topic", i)
            r2.send_msg("numbers_topic_twofold", 2*i)

        time.sleep(0.1)

        r1msgs = r1.get_msgs()

        r1.stop_listening()
        r2.stop_listening()

        self.assertEqual(len(r1msgs), 10)
