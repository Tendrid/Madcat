from gpiozero import OutputDevice
from gpiozero.exc import BadPinFactory
from os import environ
import asyncio

if environ.get("DEBUG"):
    import time

    print("----- DEBUG MODE ENABLED -----")

    class OutputDevice:
        def __init__(self, *args, **kwargs):
            self.pin = args[0]
            print(
                "PIN: {} created with active_high: {}".format(
                    self.pin, kwargs.get("active_high")
                )
            )

        def on(self):
            print("[{}] PIN: {} set to on".format(time.time(), self.pin))

        def off(self):
            print("[{}] PIN: {} set to off".format(time.time(), self.pin))


"""
Fuse is a single ignition point in the launch system.  it does not know
how many other fuses there are, or their states.
"""


class Fuse:
    def __init__(self, unit_id, pin_id, active_high=False):
        self.id = unit_id
        self.relay = OutputDevice(pin_id, active_high=active_high)
        self.arm()

    async def _toggle(self):
        self.relay.on()
        print("RELAY {} ON".format(self.id))
        await asyncio.sleep(0.5)
        self.relay.off()
        print("RELAY {} OFF".format(self.id))

    def fire(self):
        loop = asyncio.get_event_loop()
        self.fired = True
        loop.create_task(self._toggle())
        return True

    def arm(self):
        self.fired = False
