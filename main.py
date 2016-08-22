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
  while not sta_if.isconnected():
    pass
  print('connection success: ', sta_if.ifconfig())
  ap_if.active(False)

def connect_mqtt():
  global mqtt
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
  fail = False
  while True:
    if new_amp != act_amp:
      set_amp(new_amp)

    try:
      mqtt.check_msg()
    except OSError:
      print('MQTT check msg failed')
      fail = True
  
    if fail: # Wifi was down - https://forum.micropython.org/viewtopic.php?f=16&t=2163
      try:
        connect_mqtt()
        fail = False
      except OSError: # Wifi is still down
        print('MQTT reconnect failed')
        time.sleep(2)


set_amp(act_amp)
switch.irq(trigger=machine.Pin.IRQ_FALLING, handler=switch_pressed)
mqtt.set_callback(mqtt_input)
connect_wifi()
connect_mqtt()
run()
