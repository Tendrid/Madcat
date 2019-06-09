# client sends request to bluetooth server MadCat
# asks to connect, and gives Madcat its IP
# Madcat connects to client over zmq, requests config.
# client sends PSK hash with config (tube list)
# server responds OK

# TODO:
"""
Should keep track of start time, when registering, if start time is greater
than the start time registered on the battlefield, the battlefield can return
tube state.  We'll also need a way to force a reload of a list of tubes from
the battlefield.
"""

from battalion.models.firesystem import FireSystem

FireSystem().run()
