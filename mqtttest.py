import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect('192.168.0.230', 1883, 60)
client.subscribe("homeassistant/sensor/smartclock/test")


client.loop_forever()