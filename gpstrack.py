#!/usr/bin/python
# Morrastronix (V1.0) Agosto 2017 
#by chuRRuscat
#  V1.2  adden gpstrack.conf
# https://github.com/ukyg9e5r6k7gubiekd6/gpsd/blob/master/gps/gps.py
# doc en  https://fossies.org/dox/gpsd-3.16/gps_8py_source.html


import os
import sys

sys.path.append('/home/tracker')
from gps import *
import datetime
import calendar
from time import time, sleep, altzone,strftime
import threading
import luismqtt

##################  VALORES PERSONALIZADOS  ################
V_MIN = 0.5 # m/s #velocidad minima para enviar datos m/s
tEnviaDatos =10   #cada cuanto envio datos
nEnviosaCero=3   # numero de registros que envio cuando V<VMin
tiempoParado=300 # a los 5 min de estar parado, envio un registro
############### FIN DE VALORES PERSONALIZADOS  #############

gpsd = None # variable global de estrutura gps
ultimoEnvio=0
noEnvia=0

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
        gpsdata={ "hora":str(int(secs))+str(int(usecs*1000000000)),
          "lat": gpsd.fix.latitude,
          "lon": gpsd.fix.longitude,
          "h": gpsd.fix.altitude,
          "speed": round(3.6*gpsd.fix.speed,1),
          "rumbo": gpsd.fix.track,
          "climb": gpsd.fix.climb,
          "eps": gpsd.fix.eps,   # error estimado de velocidad hay tambien ept,epc,epd
          "epx": gpsd.fix.epx,            # error estimado de longitud
          "epy": gpsd.fix.epy,            # error estimado de latitud
          "epz": gpsd.fix.epv}            # error estimado de altura
        enviar='['+json.dumps(gpsdata)+',{"location":"'+LOCATION+'","deviceId":"'+DEVICE_ID+'"}]'
        return enviar

if __name__ == '__main__':
    i=0
    LOCATION=luismqtt.LOCATION
    DEVICE_ID=luismqtt.DEVICE_ID
    ultimoEnvio=0   #veces que vel< VMIN m/s y he enviado datos
    gpsp = LeeGPS() # create the thread
    
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
                    luismqtt.publica(aEnviar)
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

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."
