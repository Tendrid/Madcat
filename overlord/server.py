# pip3 install gpiozero
"""

from overlord.models.battalion import Battalion
from overlord.models.battlefield import BattleField
from tornado import gen, ioloop, web
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
import hashlib
import uuid

battlefield = BattleField()

PSK = "md5|{}|<ENTER PRE-SHARED KEY HERE>"

# how many ms to add on to the recv wait in the loop
PING_STEP = 50


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


def start():
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
"""