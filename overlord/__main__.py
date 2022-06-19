# pip3 install gpiozero

# Legion
# - Battalion
#   - Squadron
#     - Unit

from overlord.models.battalion import Battalion
from overlord.models.legion import Legion
from tornado import gen, ioloop, web, websocket, template
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
import json
import hashlib
import uuid
import os

import logging

logging.basicConfig(format="%(asctime)s %(message)s")

EVENT_CONNECTIONS = set([])

legion = Legion()
with open("overlord/def/fireworks.json") as fw_defs:
    fw_config = json.load(fw_defs)

with open("overlord/def/config.json") as unit_defs:
    unit_config = json.load(unit_defs)

phantom_config = {}
with open("overlord/def/phantom.json") as phantom_defs:
    for firework in json.load(phantom_defs):
        phantom_config[firework["sku"]] = firework


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
                tid = fire_request.get("unit")
                unit = legion.unit_defs.get(tid, {})
                logging.warning(f"<{unit['name']}> was fired from <{tid}>")

                destroy = []
                for client in EVENT_CONNECTIONS:
                    try:
                        client.write_message({"fired": message})
                    except websocket.WebSocketClosedError:
                        destroy.append(client)

                for d in destroy:
                    EVENT_CONNECTIONS.remove(client)

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
        units = {}

        out = {}
        for bid, squadron_ids in legion.config["battalions"].items():
            out[bid] = {}
            for sid in squadron_ids:
                out[bid][sid] = []
                for uid in legion.config["squadrons"][sid]:
                    unit = {"tid": uid, "error": ""}
                    if legion.unit_map.get(uid):
                        unit["fired"] = legion.unit_map.get(uid).units[uid].fired
                        unit["armed"] = legion.unit_map.get(uid).units[uid].armed
                    else:
                        unit["fired"] = 0
                        unit["armed"] = False
                    unit.update(legion.unit_defs.get(uid, {}))
                    if not phantom_config.get(unit["phid"]):
                        print(f"Failed match for phid {unit['phid']}")
                        unit["phantom_def"] = None
                    else:
                        unit["phantom_def"] = phantom_config.get(unit["phid"])
                    out[bid][sid].append(uid)
                    units[uid] = unit

        self.write(
            json.dumps(
                {
                    "battalions": out,
                    "units": units,
                    "cues": legion.cue_defs,
                    # "squadrons": legion.squadrons,
                }
            )
        )


class FireEvents(websocket.WebSocketHandler):
    def open(self):
        EVENT_CONNECTIONS.add(self)
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message("You said: " + message)

    def on_close(self):
        EVENT_CONNECTIONS.remove(self)
        print("WebSocket closed")


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
        (r"/events", FireEvents),
        (r"/(.*)", web.StaticFileHandler, dict(path=settings["static_path"])),
    ]

    # npm run build

    application = web.Application(urls, **settings)
    application.listen(8889, "0.0.0.0")
    try:
        ioloop.IOLoop.current().spawn_callback(heartbeat)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("Interrupted")


if __name__ == "__main__":
    main()
