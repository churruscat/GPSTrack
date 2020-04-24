#! /usr/bin/python
print("voy por globales")
ORG = "MateriaOscura"
DEVICE_TYPE = "GPS"
LOCATION="Barco"
DEVICE_ID = "GPS_Barco"
port = 1883
host = "192.168.1.20"
username = ""    # metodo e autenticacion, La pass es el token
token = ""   # esta es la password
clientId = DEVICE_TYPE+ ":"+ DEVICE_ID

publishTopic  = "GPS/envia"
updateTopic   = "GPS/update"

