# client sends request to bluetooth server MadCat
# asks to connect, and gives Madcat its IP
# Madcat connects to client over zmq, requests config.
# client sends PSK hash with config (tube list)
# server responds OK

"""
client requests request to server web api (sends ip)
server connects to ip and sends  generated random string
server sends random string
client sends sha1 of psk and random string
"""

# client waits for fire instructions


"""
def responder():
    ctx = zmq.Context()
    socket = ctx.socket(zmq.ROUTER)
    socket.bind('tcp://127.0.0.1:5555')
    i = 0
    while True:
        frame, msg = socket.recv_multipart()
        print("\nworker received %r\n" % msg, end='')
        socket.send_multipart([frame, msg + b" to you too, #%i" % i])
        i += 1

responder()
"""
PSK = "md5|{}|bt7f7*f58VFtyuC&^gtFrcFTVGyub^tfrgh76Trdcfr6T7GfRtfG"


import zmq
import json
import hashlib
import urllib3
import time

class Fuse:

    def __init__(self, _id):
        self.id = _id
        self.arm()

    def fire(self):
        print("BOOM MOTHERFUCKER")
        self.fired = True
        return True

    def arm(self):
        self.fired = False

class FireSystem:
    router = {}

    def __init__(self, tubes):
        self.ping = 0
        self.router["ping"] = self.c_ping
        self.router["fire"] = self.c_fire
        self.router["auth"] = self.c_auth
        self.ping_rate = 4000
        self.last_message = 0
        self.address = "tcp://0.0.0.0:5555"
        self.tubes = []
        self.load_tubes(tubes)

    def load_tubes(self, tubes):
        for tube_id in tubes:
            self.tubes.append(Fuse(tube_id))

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
        self.respond_error(f"not a valid command")

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




fs = FireSystem([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
while True:
    fs.establish_socket()
    fs.listen()
    fs.disconnect()