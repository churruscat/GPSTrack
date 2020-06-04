#!/usr/bin/python
# Morrastronix (V1.0) Mayo 2019 V.10
import requests
import json
import sys
import argparse
import csv
import time
import datetime
import subprocess
from pytz import timezone

from influxdb import InfluxDBClient
host="192.168.1.11"
user=""
password=""
#dbnameLocal="materiaoscuradb"
#medidas="siempre.temporal"
hostRemoto="canmorras.duckdns.org"
port=8086
MAXREG=1500 #numero max de puntos (orresponde aprox a 10M de fichero, que es el autentico maximo )
nombreFichero= "track.kml"
dispositivo='GPS'
location='BMW-0600HTH'
baseDeDatos='iotdb'
laMeasurement='GPS'

preIcono='"><IconStyle><scale>0.5</scale>'+\
          '<Icon><href>http://labs.google.com/ridefinder/images/'
postIcono='</href></Icon></IconStyle></Style>\n'         
iconos =[['icon1','mm_20_white.png'],
         ['icon2','mm_20_gray.png'],
         ['icon3','mm_20_blue.png'],
         ['icon4','mm_20_green.png'],
         ['icon5','mm_20_yellow.png'],
         ['icon6','mm_20_orange.png'],
         ['icon7','mm_20_red.png'],
         ['icon8','mm_20_purple.png']]

def pondata(fichero, nombre, valor):
    fichero.write('<Data name="'+nombre +\
        '"><value>'+str(valor)+'</value></Data>\n')

def trazaPuntos(cliente,laQuery,fichero):
    haypunto=0
    resultados=cliente.query(laQuery)
    #Colapsaar en una sola linea, asi te ahorras una variable(numPuntos)
    puntos = list(resultados.get_points())
    numPuntos=len(puntos)
    skipdoc=int(numPuntos/MAXREG)+1
    salida = open(fichero,"w")
    salida.write('<?xml version="1.0" encoding="UTF-8"?>'+\
    '<kml xmlns="http://www.opengis.net/kml/2.2">'+\
    '<Document>'+\
      '<name>Data+BalloonStyle</name>'+\
      '<Style id="stilo-b">'+\
        '<BalloonStyle><text>'+\
            '<![CDATA[Velocidad $[vel]+'\
            ']]></text></BalloonStyle></Style>\n')
    x=0
    for ficheroicono in iconos:
        salida.write('<Style id="'+iconos[x][0]+preIcono+iconos[x][1]+postIcono)
        x+=1      
    i=0
    j=0
    for doc in puntos:
        #print(doc['dia'],doc['hora'],doc['lon'],doc['lat'],doc['speed'])
        sys.stderr.write('\r'+str(i))
        c,r=divmod(i,skipdoc)
        if r < 0.001: 
            salida.write('<Placemark><name>'+\
                doc['dia']+' '+doc['hora']+\
                '</name><styleUrl>#stilo-b</styleUrl>\n')
            indice=int(doc['speed']/20)
            if indice>7:
                indice=7
            salida.write('<styleUrl>#'+iconos[indice][0]+'</styleUrl>\n<ExtendedData>')
            #lo pongo separado por si quiero anyadir en el futuro <name>, <cmt> o <desc>
            pondata(salida,"Vel",doc['speed']) 
            salida.write('</ExtendedData>\n<Point><coordinates>')
            salida.write(str(doc['lon'])+','+str(doc['lat']))
            salida.write('</coordinates></Point>\n</Placemark>\n')
        else:
            j+=1
        i+=1
    salida.write('</Document></kml>')
    salida.close()
    print( "\n\tFIN.\nTotal:\t\t"+str(i)+" registros ")  
    print("Me he saltado\t"+str(j) + " registros")        
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hace una query a un deviceId entre dos fechas')
    parser.add_argument('-u', '--user', nargs='?', default='root',
                        help='User name.')
    parser.add_argument('-p', '--password', nargs='?', default='password',
                        help='password.')
    parser.add_argument('-b', '--dbname', nargs='?', default=baseDeDatos,
                            help='Base de Datos.')
    parser.add_argument('-m', '--measurement', nargs='?', default=laMeasurement,
                            help='nombre de la medida (measurement name).')                                                        
    parser.add_argument('-d', '--dispositivo', nargs='?', default=dispositivo,
                            help='Device ID.') 
    parser.add_argument('-l', '--location', nargs='?', default=location,
                            help='Device ID.')    
    parser.add_argument('-i', '--inicial', nargs='?', required=True,
                            help='fecha inicial. aaaa-mm-dd')                          
    parser.add_argument('-f', '--final', nargs='?', required=True,
                            help='fecha final. aaaa-mm-dd') 
    args = parser.parse_args()
    #llamada por defecto: creakml.py -i 2019-06-11 -f 2019-06-12 -b maquinas -m gps -d GPS:BMW-0600HTH
    cliente = InfluxDBClient(host, port, args.user, args.password, args.dbname)
    queryBusca=("select dia,hora,lon,lat,speed from %s where deviceId= '%s' and location= '%s'and time>= '%s' and time<='%s' ")\
                 % (args.measurement, args.dispositivo,args.location, args.inicial, args.final)
    print("query busqueda = ",queryBusca)
    trazaPuntos(cliente,queryBusca,nombreFichero)


    exit

