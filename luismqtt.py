#! /usr/bin/python
import paho.mqtt.client as paho
import time
import json

ORG = "Casa"
DEVICE_TYPE = "GPS"
LOCATION="BMW-0600HTH"
DEVICE_ID = "GPS"
port = 1883
host = "canmorras.duckdns.org"

username = ""    # metodo e autenticacion, La pass es el token
token = ""   # esta es la password
clientId = DEVICE_TYPE+ ":"+ DEVICE_ID

publishTopic  = "GPS/envia"
updateTopic   = "GPS/update"
 
## Defino el cliente mqtt, y lo asocio a usuario y password 
#mqttc = paho.Client(clientId) 
mqttc = paho.Client(clientId, clean_session=True) 
#mqttc.username_pw_set(username , password=token)
mqttc.reconnect_delay_set(60, 600) 
conectado=False

# Funciones de Callback
def on_connect(cliente, userdata, flags, rc):
	global conectado
	print("Codigo de retorno de connect rc: "+str(rc))
	conectado=True
	if rc==0:
		print("Me suscribo al primero obligatorio  " + host )
		mqttc.subscribe(updateTopic, 1)

def on_message(cliente, userdata, msg):
	print( "Mensaje recibido para topic: " + msg.topic + " payload: "+str(msg.payload) + "\n")
 
def on_subscribe(cliente, userdata, mid, granted_qos):
	print("Suscrito OK; mensaje "+str(mid)+"qos "+ str(granted_qos))
	time.sleep(1)

def on_disconnect(client, userdata, rc):
	print("Se ha desconectado, rc= "+str(rc))    
	reconectate()   


def on_publish(client, userdata, mid):
	print("publicado el mensaje "+ str(mid))   

def reconectate():
	global conectado
	conectado=False
	while (not conectado):
		try:
			print("Me reconecto  " )
			mqttc.reconnect()
			conectado=True
			time.sleep(2)
		except Exception as exErr:
			if hasattr(exErr, 'message'):
				print("Error de conexion1 = "+ exErr.message)
			else:
				print("Error de conexion2 = "+exErr)     
			time.sleep(30)
 
# Asigno los callbacks
mqttc.on_message    = on_message
mqttc.on_connect    = on_connect
mqttc.on_subscribe  = on_subscribe
mqttc.on_disconnect = on_disconnect
mqttc.on_publish    = on_publish

# Connecta, si no hay servicio, espera un poco y vuelve a probar

while (not conectado):
	try:
		mqttc.connect(host, port, 60)
		conectado=True
	except:
		print("Error de conexion")
		time.sleep(5)
		conectado=False 

mqttc.loop_start()  # Asi no me tengo que ocupar de recoger los msgs 

def publica(mensaje):
	result, mid = mqttc.publish(publishTopic, mensaje, 1, True )
