#! /usr/bin/python
import paho.mqtt.client as paho
import time , json ,configparser

''' gpstrack.conf sample:
[log_level]
        log_level = warning
[settings]
        device_id = Main_GPS
        location  = my_car
        destination_host= my.mqtt.server
        user_id=
        password=
        publish_topic=

'''        
configFile= './gpstrack.conf'
parser = configparser.ConfigParser()
parser.read(configFile)
parser.read(configFile)
if parser.has_section("log_level"):
    if parser.has_option("log_level","log_level"):  
        loglevel=parser.get("log_level","log_level")
    else:
        loglevel='warning'
else: 
    loglevel='warning'
logging.basicConfig(stream=sys.stderr, format = '%(asctime)-15s  %(message)s', level=loglevel.upper())  
if parser.has_section("settings"):
    if parser.has_option("settings","device_id"):   
        DEVICE_ID=parser.get("settings","device_type")
    else:
        DEVICE_ID='GPS'
    if parser.has_option("settings","location"):    
        LOCATION=parser.get("settings","location")
    else:
        LOCATION='Nowhere'
    if parser.has_option("settings","destination_host"):    
        host=parser.get("settings","destination_host")
    else:
        LOCATION='127.0.0.1'
    if parser.has_option("settings","user_name"):   
        username=parser.get("settings","user_name")
    else:
        username=''
    if parser.has_option("settings","password"):    
        password=parser.get("settings","password")
    else:
        password=''     
    if parser.has_option("settings","publish_topic"):   
        publish_topic=parser.get("settings","publish_topic")
    else:
        publish_topic='GPS'
port = 1883
clientId=DEVICE_ID
mqttc = paho.Client(clientId, clean_session=True) 
#mqttc.username_pw_set(username , password=token)
mqttc.reconnect_delay_set(60, 600) 
conectado=False
## Defino el cliente mqtt, y lo asocio a usuario y password 

# Funciones de Callback
def on_connect(cliente, userdata, flags, rc):
    global conectado
    print("Codigo de retorno de connect rc: "+str(rc))
    conectado=True

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
    if result!=0
    print("error mqtt.publish:",mqttc.error_string(result))
    if result not in (
        mqttc.MQTT_ERR_AGAIN,
        mqttc.MQTT_ERR_PROTOCOL,
        mqttc.MQTT_ERR_INVAL,
        mqttc.MQTT_ERR_NO_CONN,
        mqttc.MQTT_ERR_CONN_REFUSED,
        mqttc.MQTT_ERR_NOT_FOUND,
        mqttc.MQTT_ERR_TLS,
        mqttc.MQTT_ERR_PAYLOAD_SIZE,
        mqttc.MQTT_ERR_NOT_SUPPORTED,
        mqttc.MQTT_ERR_AUTH,
        mqttc.MQTT_ERR_ERRNO):
        print ("result=",mqttc.error_string(result))
