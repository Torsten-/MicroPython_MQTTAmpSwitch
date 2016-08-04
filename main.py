from config import *
import network
import machine
import time
from umqtt.simple import MQTTClient
import ubinascii

ledr = machine.Pin(4, machine.Pin.OUT)
ledl = machine.Pin(2, machine.Pin.OUT)
switch = machine.Pin(5, machine.Pin.IN)
amp1r = machine.Pin(14, machine.Pin.OUT)
amp1l = machine.Pin(13, machine.Pin.OUT)
amp2r = machine.Pin(16, machine.Pin.OUT)
amp2l = machine.Pin(12, machine.Pin.OUT)

act_amp = 1
new_amp = 1
wlan_connected = 1

ap_if = network.WLAN(network.AP_IF)
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

CLIENT_ID = ubinascii.hexlify(machine.unique_id())
mqtt = MQTTClient(CLIENT_ID, MQTT_SERVER)

def connect_wifi():
  global sta_if,ap_if
  print('connecting to network...')
  sta_if.connect(SSID,PW)
  time.sleep(2)
  if not sta_if.isconnected():
    print('could not connect!')
    ap_if.active(True)
  else:
    print('connection success: ', sta_if.ifconfig())
    ap_if.active(False)
    connect_mqtt()

def connect_mqtt():
  global mqtt
  mqtt.set_callback(mqtt_input)
  mqtt.connect()
  mqtt.subscribe(MQTT_TOPIC)
  print("MQTT connected to %s, subscribed to %s topic" % (MQTT_SERVER, MQTT_TOPIC))

def set_amp(n):
  global act_amp
  print('Change Amp from ',act_amp,' to ',n)
  if n == 2:
    amp1l.low()
    amp1r.low()
    ledl.low()
    time.sleep_ms(200)
    amp2l.high()
    amp2r.high()
    ledr.high()
    act_amp = 2
    try:
      mqtt.publish(MQTT_TOPIC_STATE, b"2")
    except:
      print('send state to MQTT failed!')
  else:
    amp2l.low()
    amp2r.low()
    ledr.low()
    time.sleep_ms(200)
    amp1l.high()
    amp1r.high()
    ledl.high()
    act_amp = 1
    try:
      mqtt.publish(MQTT_TOPIC_STATE, b"1")
    except:
      print('send state to MQTT failed!')

def switch_pressed(p):
  global new_amp
  if act_amp == 1:
    new_amp = 2
  else:
    new_amp = 1

def mqtt_input(topic, msg):
  global new_amp
  if msg == b"2":
    new_amp = 2
  else:
    new_amp = 1

def run():
  while True:
    if not sta_if.isconnected():
      connect_wifi()
    else:
      mqtt.check_msg()
  
    if new_amp != act_amp:
      set_amp(new_amp)

set_amp(act_amp)
switch.irq(trigger=machine.Pin.IRQ_FALLING, handler=switch_pressed)
run()
