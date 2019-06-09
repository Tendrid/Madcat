
class BattleField:
    fireworks = {}

    def __init__(self):
        self.map = set([])
        self.tube_map = {}
        self.fired = set([])
        self.tube_defs = {}

    def defs(self, config, fireworks):
        for fw in fireworks:
            self.fireworks[fw.get('phid')] = fw
        for k,v in config.items():
            self.tube_defs[k] = self.fireworks[v]

        total = 0
        for phid, tube in self.tube_defs.items():
            total += tube['duration']
        print(total/60)

    def fire(self, tube:int):
        battalion = self.tube_map.get(str(tube))
        if battalion is None:
            return {'error': "no such tube"}
        result = battalion.send({"fire":{"tube":tube}})
        if result is False:
            return False, "Socket timeout"            
        elif result.get("error"):
            return False, result.get("error")
        self.fired.add(result.get("fired"))
        return True, result.get("fired")
   
    def arm(self, tube:int, battalion):
        battalion.arm(tube)
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
        print("Timeout: destroying battalion {}".format(battalion.address))
        self.map.remove(battalion)
        remove = []
        for k, v in self.tube_map.items():
            if v == battalion:
                remove.append(k)
        for dead in remove:
            del self.tube_map[dead]