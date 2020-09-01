#!/usr/bin/python
# Morrastronix (V1.0) Agosto 2017 V.10
# https://github.com/ukyg9e5r6k7gubiekd6/gpsd/blob/master/gps/gps.py
# doc en  https://fossies.org/dox/gpsd-3.16/gps_8py_source.html
#version 2 Jul 2020 envía por rabittmq en lugar de mqtt
#envío a cola en local, pero esta debe ser una cola federada


import os
import sys

sys.path.append('/home/tracker')
from gps import *
import datetime
import calendar
from time import time, sleep, altzone,strftime
import threading
import luismqtt
choices=['none','debug', 'info', 'warning', 'error' ,'critical']


##################  VALORES PERSONALIZADOS  ################
msglevel= 'info'
LOCATION=Barco
DEVICEID=GPS_Rasp
cola='GPS.envia'
V_MIN = 1.6 # m/s #velocidad minima para enviar datos m/s
tEnviaDatos =2   #cada cuanto envio datos
nEnviosaCero=3   # numero de registros que envio cuando V<VMin
tiempoParado=300 # a los 5 min de estar parado, envio un registro
############### FIN DE VALORES PERSONALIZADOS  #############

gpsd = None # variable global de estrutura gps
ultimoEnvio=0
noEnvia=0

def get_Host_name_IP(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        logging.info("Hostname :  " + host_name) 
        return(host_ip)
    except: 
        return(False)

class LeeGPS(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd # OJO es la globale
        gpsd = gps(mode=WATCH_ENABLE) # arranco la stream del GPS
        self.current_value = None
        self.running = True # y claro, dpongo este thread en modo activo

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next() #Loop permanente y recogemos CADA conjunto de estructura gpsd y limpio el buffer

def fijaPosicion():
    i=0
    while (gpsd.fix.mode==0 or gpsd.fix.mode==1):   # espero a que el GPS fije posicion
        ahoranofix=time()    # si le resto altzone paso a hora local
        print '=> no fix.  ',ahoranofix,' modo= ', gpsd.fix.mode
        sleep(5)
    return True    

def preparaJSON(tipo):
    if tipo=="localizacion":
        secs,usecs=divmod(time(),1)   # si a time() le restara altzone tendría la hora local
        gpsdata={"measurement":"GPS","time":+str(int(secs))+str(int(usecs*1000000000)),
        "fields":{ "hora":str(int(secs))+str(int(usecs*1000000000)),
          "lat": gpsd.fix.latitude,
          "lon": gpsd.fix.longitude,
          "h": gpsd.fix.altitude,
          "speed": round(3.6*gpsd.fix.speed,1),
          "rumbo": gpsd.fix.track,
          "climb": gpsd.fix.climb,
          "eps": gpsd.fix.eps,   # error estimado de velocidad hay tambien ept,epc,epd
          "epx": gpsd.fix.epx,            # error estimado de longitud
          "epy": gpsd.fix.epy,            # error estimado de latitud
          "epz": gpsd.fix.epv},            # error estimado de altura
          "tags":{"location":LOCATION,"deviceId":DEVICEID} }
        return gpsdata
def abreConexion(host):
    global canal
    reintenta=True

    '''credentials = pika.PlainCredentials(usuario, contrasenya')
    parameters = pika.ConnectionParameters(host, 5672, vHost, credentials )'''
    while reintenta:
        try:
            logging.info("abroconexion")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            canal = connection.channel() 
            reintenta=False

        except pika.exceptions.ConnectionClosedByBroker:
            logging.warning("ConnectionClosedByBroker")
            listaColas=[]
            sleep(60)
        # Don't recover on channel errors
        except pika.exceptions.AMQPChannelError:
            logging.warning("AMQPChannelError")
            listaColas=[]
            sleep(60)
        # Recover on all other connection errors
        except pika.exceptions.AMQPConnectionError:
            logging.warning("AMQPConnectionError")
            listaColas=[]
            sleep(60)
        except Exception as elError:
            logging.warning(elError)
            listaColas=[]
            sleep(60)
    return canal

def enviaRabbit(channel,cola,dato):
    global canal
    reintenta=True
    while reintenta:
        try:
            logging.warning("reintento")
            canal.basic_publish(exchange='metricas.iot',
                routing_key=cola,
                body=dato,
                properties=pika.BasicProperties(
                         delivery_mode = 2))
            logging.warning("**********  ENVIADO  ***********")
            reintenta=False
        #channel=abreConexion('localhost')
        except Exception as elError:
            logging.warning("excepcion")
            logging.warning(elError)
            listaColas=[]
            canal=abreConexion('localhost')
    return canal


if __name__ == '__main__':
    i=0
    ultimoEnvio=0   #veces que vel< VMIN m/s y he enviado datos
    gpsp = LeeGPS() # create the thread
    global canal

    msgLevel=tipoLogging.index(msglevel)*10
    logging.basicConfig(stream=sys.stderr, format = '%(asctime)-15s  %(message)s', level=msgLevel)
    hostIPAddr=get_Host_name_IP()
    logging.error("IP addr: "+hostIPAddr)
    clientemqtt = mqtt.Client()
    #Preparo la conexion a Rabbittmq    
    #client.username_pw_set("admin1", password='admin1')
    clientemqtt.connect(hostIPAddr, 1883) 
    canal=abreConexion('localhost')

    canal.queue_declare(queue=clave,durable=True)
    try:
        gpsp.start() # start it up
        fijaPosicion()     
        while True:
            if (gpsd.fix.mode==0 or gpsd.fix.mode==1):
                fijaPosicion()
            if gpsd.fix.speed < V_MIN:   
                if ultimoEnvio < nEnviosaCero:
                    ultimoEnvio +=1
                    noEnvia=0
                    aEnviar=preparaJSON("localizacion")
                    print aEnviar
                    enviaRabbit(canal,cola,aEnviar):
                else:
                    if noEnvia<tiempoParado:  #sumo dos segundos al temporizador
                        noEnvia+=2
                    else:
                        ultimoEnvio=nEnviosaCero-1   #reseteo la anulacion a enviar
            else: 
                aEnviar=preparaJSON("localizacion")
                print aEnviar
                luismqtt.publica(aEnviar)      
                ultimoEnvio=0
                noEnvia=0

            sleep(2) 

            '''
'''
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."
