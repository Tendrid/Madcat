# pip3 install gpiozero


from overlord.models.battalion import Battalion
from overlord.models.battlefield import BattleField
from tornado import gen, ioloop, web, template
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
import json
import hashlib
import uuid
import os


battlefield = BattleField()
with open("overlord/def/fireworks.json") as fw_defs:
    fw_config = json.load(fw_defs)

with open("overlord/def/config.json") as tube_defs:
    tube_config = json.load(tube_defs)

battlefield.defs(tube_config, fw_config)


PSK = "md5|{}|<ENTER PRE-SHARED KEY HERE>"

class PingHandler(web.RequestHandler):

    def get(self):
        resp = {}
        for b in battlefield.battalions:
            resp[str(b.id)] = int(b.ping_rate)
        self.write(resp)

class FireHandler(web.RequestHandler):

    def check_xsrf_cookie(self, *args, **kwargs):
        pass

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

class CueHandler(web.RequestHandler):

    def check_xsrf_cookie(self, *args, **kwargs):
        pass

    @gen.coroutine
    def post(self):
        try:
            fire_request = json_decode(self.request.body)
            if fire_request.get("cue") is None:
                self.set_status(404)
                self.write({'error': "Unknown cue"})
                return
            battlefield.cue(fire_request.get("cue"))
            self.write({'started': fire_request.get("cue")})
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
            battlefield.battalions.add(b)
        else:
            print("no good, its full of steam!")


class WebUI(web.RequestHandler):

    def get(self):
        loader = template.Loader("overlord/templates")
        _t = loader.load("index.html")
        tubes = {}
        for tid, battalion in battlefield.tube_map.items():
            tubes[tid] = {"bid": battalion.id}
            tubes[tid].update(battlefield.tube_defs.get(tid, {}))
        self.write(_t.generate(
            tubes=tubes,
            battlefield=battlefield,
            title="foo"
        ))

class BattlefieldJSON(web.RequestHandler):
    def get(self):
        battalions = []
        for battalion in battlefield.battalions:
            b = {
                "bid": str(battalion.id),
                "tubes": []
            }
            for tid, tube in battalion.tubes.items():
                t = {
                    "tid":tid,
                    "fired":tube.fired
                }
                t.update(battlefield.tube_defs.get(tid, {}))
                b["tubes"].append(t)
            battalions.append(b)

        self.write(json.dumps({
            "battalions": battalions
        }))

async def heartbeat():
    while True:
        battlefield.heartbeat()
        await gen.sleep(3)


def main():

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "dist"),
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "login_url": "/login",
        "xsrf_cookies": True,
    }

    urls = [
        (r"/", WebUI),
        (r"/battlefield", BattlefieldJSON),
        (r"/ping", PingHandler),
        (r"/fire", FireHandler),
        (r"/cue", CueHandler),
        (r"/register", RegisterHandler),
        (r"/(.*)", web.StaticFileHandler, dict(path=settings['static_path'])),
    ]

    #npm run build

    application = web.Application(urls, **settings)
    application.listen(8888)
    try:
        ioloop.IOLoop.current().spawn_callback(heartbeat)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print('Interrupted')


if __name__ == "__main__":
    main()
