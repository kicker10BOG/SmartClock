import json
import paho.mqtt.client as mqtt
import cherrypy
from cherrypy.process import wspbus, plugins

class MqttClient(plugins.SimplePlugin):
    def __init__(self, bus, app):
        plugins.SimplePlugin.__init__(self, bus)
        self.app = app

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(self.app.config['/']['smartclock.mqtt.address'], self.app.config['/']['smartclock.mqtt.port'], 60)
        self.client.subscribe("homeassistant/sensor/smartclock/#")

    def start(self):
        self.bus.log('Starting up MQTT access')
        cherrypy.engine.subscribe("mqtt", self.read_bus)
        cherrypy.engine.subscribe("websocket-broadcast", self.read_bus)
        cherrypy.engine.subscribe("main", self.loop)

    def stop(self):
        self.bus.log('Stopping down MQTT access')
        cherrypy.engine.unsubscribe("mqtt", self.read_bus)
        cherrypy.engine.unsubscribe("websocket-broadcast", self.read_bus)
        cherrypy.engine.unsubscribe("main", self.loop)

    def on_connect(self, client, userdata, flags, rc):
        self.bus.log("Connected with result code "+str(rc))

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    # insert into mainloop
    def loop(self):
        self.client.loop(1)

    # The callback for when a PUBLISH message is received from the server.
    def read_bus(self, m):
        print("Message received on bus: ", m)
        # try:
        #     mj = json.loads(m)
        #     if mj['type'] == 'alarmTriggered':
        #         self.client.publish("homeassistant/sensor/smartclock/event", m)
        # except Exception as e: 
        #     pass
