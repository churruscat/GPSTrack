#!/usr/bin/python
# Morrastronix (V1.0) Agosto 2017 V.10
# https://github.com/ukyg9e5r6k7gubiekd6/gpsd/blob/master/gps/gps.py
# doc en  https://fossies.org/dox/gpsd-3.16/gps_8py_source.html


import os
import sys

sys.path.append('/home/tracker')
from gps import *
import time
import datetime
import calendar
import threading
import luismqtt

##################  VALORES PERSONALIZADOS  ################
V_MIN = 1.6 # m/s #velocidad minima para enviar datos m/s
tEnviaDatos =2   #cada cuanto envio datos
nEnviosaCero=3   # numero de registros que envio cuando V<VMin
############### FIN DE VALORES PERSONALIZADOS  #############

gpsd = None # variable global de estrutura gps

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
        ahoranofix=time.localtime()
        strhoranofix="dia:"+time.strftime("%d-%m-%y",ahoranofix)+' '\
           "hora:"+time.strftime("%H:%M:%S",ahoranofix)
        print '=> no fix.  ',strhoranofix,' modo= ', gpsd.fix.mode
        time.sleep(5)
    return True    

def preparaJSON(tipo):
    if tipo=="localizacion":
        lafecha,resto=gpsd.utc.split('.')
        ahoraUTC=time.strptime(lafecha,"%Y-%m-%dT%H:%M:%S")
        ahora=time.gmtime(calendar.timegm(ahoraUTC)-time.altzone)
        horareal={"dia":time.strftime("%y-%m-%d",ahora),
           "hora":time.strftime("%H:%M:%S",ahora)}
        posicion={ "lat": gpsd.fix.latitude,
          "lon": gpsd.fix.longitude,
          "h": gpsd.fix.altitude}
        movimiento={"speed": round(3.6*gpsd.fix.speed,1),
          "rumbo": gpsd.fix.track,
          "climb": gpsd.fix.climb}
        precision={"eps": gpsd.fix.eps,   # error estimado de velocidad hay tambien ept,epc,epd
          "epx": gpsd.fix.epx,            # error estimado de longitud
          "epy": gpsd.fix.epy,            # error estimado de latitud
          "epz": gpsd.fix.epv}            # error estimado de altura
        return [{"fecha":horareal,
            "pos":posicion,
            "mov":movimiento,
            "prec":precision},{"deviceId":"GPS:BMW-0600HTH"}]

if __name__ == '__main__':
    i=0

    ultimoEnvio=0   #veces que vel< VMIN m/s y he enviado datos
    gpsp = LeeGPS() # create the thread
    
    try:
        gpsp.start() # start it up
        fijaPosicion()
        
        while True:
            if (gpsd.fix.mode==0 or gpsd.fix.mode==1):
                  fijaPosicion()
            if gpsd.fix.speed < V_MIN:   
                #print ('velocidad =',gpsd.fix.speed)
                if ultimoEnvio < nEnviosaCero:
                    ultimoEnvio +=1
                    aEnviar=preparaJSON("localizacion")
                    print aEnviar
                    luismqtt.publica(json.dumps(aEnviar))
            else: 
                aEnviar=preparaJSON("localizacion")
                print aEnviar
                luismqtt.publica(json.dumps(aEnviar))      
                ultimoEnvio=0

            time.sleep(2) 

            '''
'''
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."
