# pip3 install gpiozero

# Legion
# - Battalion
#   - Squadron
#     - Unit

from overlord.models.battalion import Battalion
from overlord.models.legion import Legion
from tornado import gen, ioloop, web, template
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
import json
import hashlib
import uuid
import os


legion = Legion()
with open("overlord/def/fireworks.json") as fw_defs:
    fw_config = json.load(fw_defs)

with open("overlord/def/config.json") as unit_defs:
    unit_config = json.load(unit_defs)

legion.defs(unit_config, fw_config)


PSK = "md5|{}|JoihiuGy7cr58fr76"


class PingHandler(web.RequestHandler):
    def get(self):
        resp = {}
        for b in legion.battalions:
            resp[str(b.id)] = int(b.ping_rate)
        self.write(resp)


class FireHandler(web.RequestHandler):
    def check_xsrf_cookie(self, *args, **kwargs):
        pass

    @gen.coroutine
    def post(self):
        try:
            fire_request = json_decode(self.request.body)
            if fire_request.get("unit") is None:
                self.set_status(404)
                self.write({"error": "Unknown unit"})
                return
            fired, message = legion.fire(fire_request.get("unit"))
            if fired:
                self.write({"fired": message})
            else:
                self.set_status(400)
                self.write({"error": message})

        except JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Bad JSON format"})
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
                self.write({"error": "Unknown cue"})
                return
            legion.cue(fire_request.get("cue"))
            self.write({"started": fire_request.get("cue")})
        except JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Bad JSON format"})
            return


class RegisterHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.write("ok")

    def on_finish(self):
        b = Battalion(addr=self.request.remote_ip, port=5555)
        challenge = str(uuid.uuid4())
        reply = b.send({"auth": {"challenge": challenge}})
        response = PSK.format(challenge)

        if reply["auth"]["response"] == hashlib.md5(response.encode()).hexdigest():
            for unit in reply["auth"]["units"]:
                print("registering {} to ip {}".format(unit, self.request.remote_ip))
                legion.arm(unit, b)
            legion.battalions.add(b)
        else:
            print("no good, its full of steam!")


class WebUI(web.RequestHandler):
    def get(self):
        loader = template.Loader("overlord/templates")
        _t = loader.load("index.html")
        units = {}
        for tid, battalion in legion.unit_map.items():
            units[tid] = {"bid": battalion.id}
            units[tid].update(legion.unit_defs.get(tid, {}))
        self.write(_t.generate(units=units, legion=legion, title="Madcat"))


class LegionJSON(web.RequestHandler):
    def get(self):
        battalions = []
        for battalion in legion.battalions:
            b = {"bid": str(battalion.id), "units": []}
            for tid, unit in battalion.units.items():
                t = {"tid": tid, "fired": unit.fired}
                t.update(legion.unit_defs.get(tid, {}))
                b["units"].append(t)
            battalions.append(b)
        self.write(
            json.dumps(
                {
                    "battalions": battalions,
                    "cues": legion.cue_defs,
                    "squadrons": legion.squadrons,
                }
            )
        )


async def heartbeat():
    while True:
        legion.heartbeat()
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
        (r"/legion", LegionJSON),
        (r"/ping", PingHandler),
        (r"/fire", FireHandler),
        (r"/cue", CueHandler),
        (r"/register", RegisterHandler),
        (r"/(.*)", web.StaticFileHandler, dict(path=settings["static_path"])),
    ]

    # npm run build

    application = web.Application(urls, **settings)
    application.listen(8888)
    try:
        ioloop.IOLoop.current().spawn_callback(heartbeat)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("Interrupted")


if __name__ == "__main__":
    main()
