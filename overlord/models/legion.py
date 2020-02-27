"""
Cues:

should store firework configs
should have total duration (greatest stat offset + duration)

"""

from tornado import gen


class Legion:
    fireworks = {}

    def __init__(self):
        self.battalions = set([])
        self.unit_map = {}
        self.unit_defs = {}
        self.cue_defs = {}
        self.squadrons = {}

    def defs(self, config, fireworks):
        for fw in fireworks:
            self.fireworks[fw.get("phid")] = fw

        for unit_id, firework in config.get("units", {}).items():
            self.unit_defs[unit_id] = self.fireworks[firework]

        self.squadrons = config.get("squadrons", {})

        for cue_name, config in config.get("cues", {}).items():
            self.cue_defs[cue_name] = {"duration": 0, "cue": []}
            for tid, offset in config.items():
                firework = self.unit_defs.get(tid)
                if firework:
                    self.cue_defs[cue_name]["cue"].append(
                        {"unit_id": tid, "firework": firework, "offset": offset}
                    )
            self.cue_defs[cue_name]["cue"] = sorted(
                self.cue_defs[cue_name]["cue"], key=lambda k: k["offset"]
            )

            # XXX this will only calculate the last firework and its duration as the longest portion of the cue
            # however, if the second to last is 2 minutes duration, the cue will actually last much longer than reported
            d = (
                self.cue_defs[cue_name]["cue"][-1]["firework"]["duration"]
                + self.cue_defs[cue_name]["cue"][-1]["offset"]
            )
            self.cue_defs[cue_name]["duration"] = d

        total = 0
        for phid, unit in self.unit_defs.items():
            total += unit["duration"]
        print("Loaded config is a total duration of {} minutes".format(total / 60))

    @gen.coroutine
    def cue(self, cue):
        if self.cue_defs.get(cue) is None:
            return False, "Invalid cue name"
        print(
            "Starting cue {} which will last for {} seconds".format(
                cue, self.cue_defs.get(cue)["duration"]
            )
        )
        current_cue_time = 0
        for firework in self.cue_defs.get(cue)["cue"]:
            offset = firework["offset"] - current_cue_time
            print("Waiting {} seconds to fire {}".format(offset, firework["unit_id"]))
            yield gen.sleep(offset)
            self.fire(firework["unit_id"])
            current_cue_time += offset

    def fire(self, unit):
        battalion = self.unit_map.get(str(unit))
        if battalion is None:
            return {"error": "no such unit"}

        result = battalion.fire(unit)

        if result is False:
            return False, "Socket timeout"
        elif result.get("error"):
            return False, result.get("error")
        return True, result.get("fired")

    def arm(self, unit, battalion):
        battalion.arm(unit)

        self.unit_map[str(unit)] = battalion

    def heartbeat(self):
        dead = []
        for b in self.battalions:
            if b.ping() is False:
                dead.append(b)
        for battalion in dead:
            battalion.disconnect()
            self.destroy(battalion)

    def destroy(self, battalion):
        print("Timeout: destroying battalion {}".format(battalion.address))
        self.battalions.remove(battalion)
        remove = []
        for k, v in self.unit_map.items():
            if v == battalion:
                remove.append(k)
        for dead in remove:
            del self.unit_map[dead]
