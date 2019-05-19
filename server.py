# pip3 install gpiozero

import zmq

from tornado import gen, ioloop, web
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
import hashlib
import uuid

import json
import time

PSK = "md5|{}|<ENTER PRE-SHARED KEY HERE>"

# how many ms to add on to the recv wait in the loop
PING_STEP = 50

class BattleField:

    def __init__(self):
        self.map = set([])
        self.tube_map = {}
        self.fired = set([])

    def fire(self, tube:int):
        battalion = self.tube_map.get(str(tube))
        if battalion is None:
            return {'error': "no such tube"}
        result = battalion.send({"fire":{"tube":tube}})
        if result.get("error"):
            return False, result.get("error")
        self.fired.add(result.get("fired"))
        return True, result.get("fired")
   
    def arm(self, tube:int, battalion):
        self.tube_map[str(tube)] = battalion

    def heartbeat(self):
        dead = []
        for b in self.map:
            if b.ping() is False:
                dead.append(b)
        for battalion in dead:
            battalion.disconnect()
            self.destroy(battalion)

    def destroy(self, battalion):
        self.map.remove(battalion)
        remove = []
        for k, v in self.tube_map.items():
            if v == battalion:
                remove.append(k)
        for dead in remove:
            del self.tube_map[dead] 

battlefield = BattleField()


class Battalion:

    def __init__(self, addr, port, protocol="tcp"):
        self.address = "{}://{}:{}".format(
            protocol,
            addr,
            port
        )
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(self.address)
        self.__pings = []
        self.ping_history = 10

    @property
    def ping_rate(self):
        pings = [x for x in self.__pings if x is not None]
        if len(pings) < 1:
            return 0
        return sum(pings) / len(pings)

    def disconnect(self):
        self.socket.disconnect(self.address)

    def send(self, msg:dict, block=True):
        # send request to worker
        self.socket.send_json(msg)

        ttl = 1
        lt = st = time.time()
        while ttl > (lt - st):
            try:
                # finish web request with worker's reply
                reply = self.socket.recv_json(flags=zmq.NOBLOCK)

                # TODO: check response.  make sure its not an error, etc
                return reply

            except zmq.Again as e:
                lt = time.time()
                ping_seconds = self.ping_rate / 1000
                time.sleep((ping_seconds - ping_seconds / 2))

        return False

    def ping(self):
        if len(self.__pings) > self.ping_history:
            self.__pings = self.__pings[:self.ping_history]
        s = time.time() * 1000
        pong = self.send({"ping":{}})
        if pong is False:
            self.__pings.insert(0, None)
            return False
        else:
            rt = round((time.time() * 1000) - s, 2)
            self.__pings.insert(0, rt)
            return rt


class PingHandler(web.RequestHandler):

    def get(self, tube):
        resp = {}
        for b in battlefield.map:
            resp[b.id] = b.ping_rate
        self.write(resp)

class FireHandler(web.RequestHandler):

    @gen.coroutine
    def post(self):
        try:
            fire_request = json_decode(self.request.body)
            if fire_request.get("tube") is None:
                self.set_status(404)
                self.write({'error': "Unknown tube"})
                return
            fired, message = battlefield.fire(fire_request.get("tube"))
            if fired:
                self.write({'fired': message})
            else:
                self.set_status(400)
                self.write({'error': message})

        except JSONDecodeError:
            self.set_status(400)
            self.write({'error': "Bad JSON format"})
            return

class RegisterHandler(web.RequestHandler):

    @gen.coroutine
    def get(self):
        self.write("ok")

    def on_finish(self):
        b = Battalion(addr=self.request.remote_ip, port=5555)
        challenge = str(uuid.uuid4())
        reply = b.send({"auth":{"challenge":challenge}})
        response = PSK.format(challenge)

        if reply["auth"]["response"] == hashlib.md5(response.encode()).hexdigest():
            for tube in reply["auth"]["tubes"]:
                print("registering {} to ip {}".format(tube, self.request.remote_ip))
                battlefield.arm(tube, b)
            battlefield.map.add(b)
        else:
            print("no good, its full of steam!")

async def heartbeat():
    while True:
        battlefield.heartbeat()
        await gen.sleep(3)


def main():
    urls = [
        (r"/ping/([\d]{1,64})", PingHandler),
        (r"/fire", FireHandler),
        (r"/register", RegisterHandler)        
    ]

    application = web.Application(urls)
    application.listen(8888)
    try:
        ioloop.IOLoop.current().spawn_callback(heartbeat)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print('Interrupted')


if __name__ == "__main__":
    main()
