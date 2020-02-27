"""
The fire system has an ID, and takes in a config which maps each unit to
a relay.  The config comes from the Battlefield, and is requested by ID.
"""

from battalion.models.fuse import Fuse
from zmq import REP, POLLIN
from zmq.asyncio import Context, Poller
import hashlib
import urllib3
import time
import asyncio
import json
import os


class FireSystem:
    router = {}

    def __init__(self):
        self.active = True
        self.ping = 0
        self.ping_rate = 4000
        self.router["ping"] = self.c_ping
        self.router["fire"] = self.c_fire
        self.router["auth"] = self.c_auth
        self.last_message = 0
        self.address = "tcp://0.0.0.0:5555"
        self.units = []
        self.load_config()
        self.load_units()

    def load_config(self, path="~/.madcat/config.json"):
        path = os.path.expanduser(path)
        if os.path.isfile(path) is False:
            raise EnvironmentError(-1, "MadCat config missing at {}".format(path))
        with open(path) as fh:
            self.config = json.load(fh)

    def run(self):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._lifecycle())
            loop.run_forever()
        except KeyboardInterrupt:
            self.shutdown()

    async def _lifecycle(self):
        while self.active:
            self.establish_socket()
            await self.listen()
            self.disconnect()
        self.shutdown()

    def shutdown(self):
        self.active = False
        print("Shutting down")
        loop = asyncio.get_event_loop()
        loop.close()
        loop.stop()
        exit()

    def load_units(self):
        units = self.config.get("units")
        if not units:
            raise ValueError("INIT ERROR: No units config!")
        for unit_id, pin_id in units.items():
            self.units.append(Fuse(unit_id, pin_id))

    def establish_socket(self):
        self.context = Context()
        self.socket = self.context.socket(REP)
        self.socket.bind(self.address)

        self.poller = Poller()
        self.poller.register(self.socket, POLLIN)

        self.ping = 0
        while self.auth() is False:
            time.sleep(1)

    def disconnect(self):
        self.socket.disconnect(self.address)

    """
    Authentication
    """

    def auth(self):
        http = urllib3.PoolManager()
        try:
            r = http.request(
                "GET",
                "http://{address}:{port}/register".format(
                    **self.config.get("battlefield")
                ),
            )
        except urllib3.exceptions.MaxRetryError:
            print("Cannot connect to Battlefield")
            return False
        print("Registered to Battlefield")
        return True

    async def listen(self):
        listening = True
        while listening:
            events = await self.poller.poll(self.ping_rate)
            if events:
                for socket, idx in events:
                    msg = await self.socket.recv_json()
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
    def unit_ids(self):
        return [x.id for x in self.units]

    def get_unit(self, unit):
        for t in self.units:
            if t.id == unit:
                return t
        return None

    def c_fire(self, **kwargs):
        unit = self.get_unit(kwargs.get("unit"))
        if unit is None:
            self.respond_error("I dont own unit {}".format(kwargs.get("unit")))
        else:
            if unit.fired:
                self.respond_error("Unit {} is not armed!".format(unit.id))
            else:
                if unit.fire():
                    self.socket.send_json({"fired": unit.id})
                else:
                    self.respond_error("Unit {} failed to fire!".format(unit.id))

    def c_ping(self, **kwargs):
        self.socket.send_json({"pong": self.ping})
        self.ping += 1

    def c_auth(self, challenge):
        response = self.config["PSK"].format(challenge)
        self.socket.send_json(
            {
                "auth": {
                    "response": hashlib.md5(response.encode()).hexdigest(),
                    "units": self.unit_ids,
                }
            }
        )
