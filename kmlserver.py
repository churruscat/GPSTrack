#! /usr/bin/python3
# kmlserver.py  v1.0 lee de influxdb entre dos fechas y lo muestra 
# en googlemaps
# Morrastronix by churruscat 2019
from flask import Flask
# Hay que instalar flask_restful y flask_cors
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
import requests
import json
import sys 

from influxdb import InfluxDBClient
from googleapiclient import errors
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

app = Flask(__name__)

#@app.route("/")
CORS(app)
api = Api(app)

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'

host="192.168.1.11"
user=""
password=""
#dbnameLocal="materiaoscuradb"
#medidas="siempre.temporal"
hostRemoto="morrasflo.es"
port=8086
MAXREG=1900 #numero max de puntos (orresponde aprox a 10M de fichero, que es el autentico maximo )
nombreFichero= "KMLtrak.KML"
dispositivo='GPS:BMW-0600HTH'
baseDeDatos='maquinas'
laMeasurement='gps'

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
    respuesta={"registros totales":i,
            "registros saltados":j,
            "fichero":fichero}
    return respuesta

def inicia( user, password, dbname, measurement, dispositivo, inicial, final ):
    cliente = InfluxDBClient(host, port, user, password, dbname)
    queryBusca=("select dia,hora,lon,lat,speed from %s where deviceId='%s' and time>='%s' and time<='%s' ")\
                 % (measurement, dispositivo, inicial, final)
    return trazaPuntos(cliente,queryBusca,nombreFichero)

def get_authenticated(SCOPES, credential_file='credentials.json',
                  token_file='token.json', service_name='drive',
                  api_version='v3'):
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage(token_file)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credential_file, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build(service_name, api_version, http=creds.authorize(Http()))
    return service


def retrieve_all_files(service):
    """Retrieve a list of File resources.

    Args:
        service: Drive API service instance.
    Returns:
        List of File resources.
    """

    result = []
    page_token = None
    while True:
        try:
            param = {}
            if page_token:
                param['pageToken'] = page_token
            files = service.files().list(**param).execute()

            result.extend(files['files'])
            page_token = files.get('nextPageToken')
            if not page_token:
                break
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break

    return result


def insert_file(service, name, description, parent_id, mime_type, filename):
    """Insert new file.

    Args:
        service: Drive API service instance.
        name: Name of the file to insert, including the extension.
        description: Description of the file to insert.
        parent_id: Parent folder's ID.
        mime_type: MIME type of the file to insert.
        filename: Filename of the file to insert.
    Returns:
        Inserted file metadata if successful, None otherwise.
    """
    media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
    body = {
        'name': name,
        'description': description,
        'mimeType': mime_type
    }
    # Set the parent folder.
    if parent_id:
        body['parents'] = [{'id': parent_id}]

    try:
        file = service.files().create(
            body=body,
            media_body=media_body).execute()
        return file
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return None

def update_file(service, file_id, new_name, new_description, new_mime_type,
            new_filename):
    """Update an existing file's metadata and content.

    Args:
        service: Drive API service instance.
        file_id: ID of the file to update.
        new_name: New name for the file.
        new_description: New description for the file.
        new_mime_type: New MIME type for the file.
        new_filename: Filename of the new content to upload.
        new_revision: Whether or not to create a new revision for this file.
    Returns:
        Updated file metadata if successful, None otherwise.
    """
    try:
        # First retrieve the file from the API.
        file = service.files().get(fileId=file_id).execute()
        # File's new metadata.
        del file['id']
        file['name'] = new_name
        file['description'] = new_description
        file['mimeType'] = new_mime_type
        # File's new content.
        media_body = MediaFileUpload(
            new_filename, mimetype=new_mime_type, resumable=True)
        # Send the request to the API.
        updated_file = service.files().update(
            fileId=file_id,
            body=file,
            media_body=media_body).execute()
        return updated_file
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return None


class creakml(Resource):

    def get(self, name):
        return "GET no tiene sentido en CREA", 404

    def post(self, name):

        parametros=json.loads(name)
        resultado=inicia("","","maquinas","gps",parametros['deviceId'],
                parametros['fecha_ini'],parametros['fecha_fin'])       
        return resultado,200

class subekml(Resource):

    def get(self, name):
        service = get_authenticated(SCOPES)
        parametros=json.loads(name)
        results = retrieve_all_files(service)
        target_file_descr = 'fichero KML'
        target_file_id = [file['id'] for file in results if file['name'] == parametros['fichero']]
        if target_file_id==[]:
            return "File not found", 404
        else:
            return {"fichero":parametros['fichero'],"id1":target_file_id[0]},200

    def put(self, name):
        post(self,name)

    def post(self, name):
        service = get_authenticated(SCOPES)
        parametros=json.loads(name)
        results = retrieve_all_files(service)
        target_file_descr = 'fichero KML'
        target_file_id = [file['id'] for file in results if file['name'] == parametros['fichero']]
        if len(target_file_id) == 0:
            nuevo=True
            file_uploaded = insert_file(service, parametros['fichero'], target_file_descr, 'Tracks',
                                    'application/vnd.google-earth.kml+xml', parametros['fichero'])
        else:
            nuevo=False
            file_uploaded = update_file(service, target_file_id[0], parametros['fichero'], target_file_descr,
                                    'application/vnd.google-earth.kml+xml', parametros['fichero'])       
        return {"nuevo":nuevo,"fichero":parametros['fichero'],"id":file_uploaded['id']},200
      
api.add_resource(creakml, "/creakml/<string:name>")
api.add_resource(subekml, "/subekml/<string:name>")

app.run(debug=False,host='0.0.0.0', port=5000)
