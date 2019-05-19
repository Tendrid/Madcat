import zmq
import time

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
                # finish request with worker's reply
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
