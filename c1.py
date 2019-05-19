# client sends request to bluetooth server MadCat
# asks to connect, and gives Madcat its IP
# Madcat connects to client over zmq, requests config.
# client sends PSK hash with config (tube list)
# server responds OK

PSK = "md5|{}|<ENTER PRE-SHARED KEY HERE>"

import zmq
import json
import hashlib
import urllib3
import time
from gpiozero import OutputDevice


# TODO:
"""
Should keep track of start time, when registering, if start time is greater
than the start time registered on the battlefield, the battlefield can return
tube state.  We'll also need a way to force a reload of a list of tubes from
the battlefield.
"""

"""
Fuse is a single ignition point in the launch system.  it does not know
how many other fuses there are, or their states.
"""
class Fuse:
    def __init__(self, tube_id, pin_id, active_high=True):
        self.id = tube_id
        self.relay = OutputDevice(
            pin_id,
            active_high=active_high,
            initial_value= not active_high)
        self.arm()

    def fire(self):
        print("BOOM MOTHERFUCKER")
        self.relay.on()
        time.sleep(0.5)
        self.relay.off()
        self.fired = True
        return True

    def arm(self):
        self.fired = False



CONFIG = {
    "active_high": False,
    "tubes":{
        0: 4,
        1: 17,
        2: 27,
        3: 22,
        4: 5,
        5: 6,
        6: 13,
        7: 19,
        8: 26,
        9: 23,
        10: 24,
        11: 25,
        12: 12,
        13: 16,
        14: 20,
        15: 21
    }
}

"""
The fire system has an ID, and takes in a config which maps each tube to
a relay.  The config comes from the Battlefield, and is requested by ID.
"""
class FireSystem:
    router = {}

    def __init__(self, config):
        self.ping = 0
        self.ping_rate = 4000
        self.router["ping"] = self.c_ping
        self.router["fire"] = self.c_fire
        self.router["auth"] = self.c_auth
        self.last_message = 0
        self.address = "tcp://0.0.0.0:5555"
        self.tubes = []
        self.load_tubes(config.get("tubes"))

    def load_tubes(self, tubes):
        if not tubes:
            raise ValueError("INIT ERROR: No tube config!")
        for tube_id, pin_id in tubes.items():
            self.tubes.append(Fuse(tube_id, pin_id))

    def establish_socket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.address)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN) # POLLIN for recv, POLLOUT for send

        self.ping = 0
        while self.auth() is False:
            time.sleep(1)

    def disconnect(self):
        self.socket.disconnect(self.address)

    def auth(self):
        http = urllib3.PoolManager()
        try:
            r = http.request("GET", "http://192.168.86.48:8888/register")
        except urllib3.exceptions.MaxRetryError:
            print("Cannot connect to Battlefield")
            return False
        print("Registered to Battlefield")
        return True

    def listen(self):
        listening = True
        while listening:
            events = self.poller.poll(self.ping_rate)
            if events:
                socket = events[0]
                msg = self.socket.recv_json()
                self.last_message = time.time()
                if type(msg) is not dict:
                    self.respond_error("Message not a dict!")
                if len(msg.keys()) != 1:
                    self.respond_error("Only one request at a time! (for now)")

                for command, request in msg.items():
                    if type(request) is not dict:
                        self.respond_error("Request not a dict!")
                    else:
                        self.router.get(command, self.invalid_command)(**request)
            else:
                print("Missed ping!")
                if (time.time() - self.last_message) > (self.ping_rate / 1000) * 3:
                    print("Connection failed!  Attempting reconnect")
                    listening = False

    def respond_error(self, msg):
        self.socket.send_json({"error": msg})

    def invalid_command(self, **kwargs):
        self.respond_error("not a valid command")

    @property
    def tube_ids(self):
        return [x.id for x in self.tubes]

    def get_tube(self, tube):
        for t in self.tubes:
            if t.id == tube:
                return t
        return None

    def c_fire(self, **kwargs):
        tube = self.get_tube(kwargs.get("tube"))
        if tube is None:
            self.respond_error("I dont own tube {}".format(kwargs.get("tube")))
        else:
            if tube.fired:
                self.respond_error("Tube {} is not armed!".format(tube.id))
            else:
                if tube.fire():
                    self.socket.send_json({"fired": tube.id})
                else:
                    self.respond_error("Tube {} failed to fire!".format(tube.id))

    def c_ping(self, **kwargs):
        self.socket.send_json({"pong": self.ping})
        self.ping += 1

    def c_auth(self, challenge):
        response = PSK.format(challenge)
        self.socket.send_json({
            "auth": {
                "response": hashlib.md5(response.encode()).hexdigest(),
                "tubes": self.tube_ids
            }
        })




fs = FireSystem(CONFIG)
while True:
    fs.establish_socket()
    fs.listen()
    fs.disconnect()