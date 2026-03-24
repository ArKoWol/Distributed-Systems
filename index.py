import time
import sys

import stomp

class MyListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print('received an error "%s"' % frame.body)
    def on_message(self, frame):
        print('received a message "%s"' % frame.body)

conn = stomp.Connection()
conn.set_listener("MyListener", MyListener())
conn.connect("admin", "admin", wait=True)
conn.subscribe(destination='/queue/test', id=1, ack="auto")
conn.send(body="A Test message", destination='/queue/test')
time.sleep(2)
conn.disconnect()

