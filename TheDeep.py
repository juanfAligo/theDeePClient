# coding:utf-8
import argparse
import socket
import json
import time
import string
import logging
import re
from base64 import b64encode,b64decode
import random, string

parser = argparse.ArgumentParser(description='Configura los parametros para lanzar escaneos desd SecDevOps')
parser.add_argument('--IP', type=str, nargs='?', help='IP del servidor donde se ejecuta el SecDevOps')
parser.add_argument('--port', type=int, nargs='?', help='puerto donde escucha el SecDevOps')
parser.add_argument('--token', type=str, nargs='?', help='token de autenticacion')
parser.add_argument('--tipo', type=str, nargs='?', help='Tipo de prueba (0,1,2)')
parser.add_argument('--code', type=int, nargs='?', help='Tipo de proyecto')
parser.add_argument('--id', type=str, nargs='?', help='id del proyecto')
parser.add_argument('--url', type=str, nargs='?', help='url objetivo')
parser.add_argument('--shome', type=str, nargs='?', help='scanner home')
parser.add_argument('--ruta', type=str, nargs='?', help='ruta del workspace del proyecto')
parser.add_argument('--login', type=str, nargs='?', help='opciones de login')
error=""

#Variables de control de errores
Network_fail=0
TheDeep_Fail=0
server_ip=0
server_port=0
url=0
project_id=0
tipo=0
lenguaje=''
url=0

args = parser.parse_args()
if args.IP:
        server_ip=args.IP
else:
        error="Es necesario ingresar la IP del servidor (--IP <IP del servidor>)"

if args.port:
        server_port=args.port
else:
        error="Es necesario ingresar la IP del servidor (--port <Puerto en el que escucha el servidor>)"

if args.token:
        token=args.token
else:
        error="Es necesario ingresar el token de autenticacion generado por The DeeP (--token <tipo>)"

if args.tipo != None:
        tipo=args.tipo
else:
        error="Es necesario ingresar el tipo (--tipo <tipo>)"

if args.id:
        project_id=args.id
else:
        error="Es necesario ingresar el id del proyecto"

def conexion(msg):
        respuesta=False
        BUFFER_SIZE=1024
        s = socket.socket()
        try:
                logging.info("Tratando de conectar con %s:%s",server_ip, server_port)
                s.connect((server_ip, server_port))
                logging.info("conexion estrablecida con %s:%s",server_ip, server_port)
        except Exception as error:
                logging.error("Error con la conexion con TheDeep (%s:%s): %s",server_ip, server_port,str(error))
                return respuesta
        else:
                try:
                        s.send(msg.encode())
                        logging.info("Informacion enviada a TheDeep %s:%s -> %s",server_ip, server_port, msg)
                        respuesta=s.recv(BUFFER_SIZE)
                        respuesta=json.loads(respuesta)
                except Exception as err:
                        logging.error("Respuesta invalida: %s", err)
                        respuesta=False

                s.close()
                return respuesta
                

def _get_Scan_ID():
                '''
                0=Java-Maven, 1=Java-Gradle, 2= MSBuild , 3= Otros

                Retorna el ID del task de sonarqube
                :param workspace: ruta donde esta el proyecto, se obtiene con el comando pwd
                :return: ID del task(escaneo) de sonarqube
                '''
                ruta_workspace=''
                if args.ruta:
                        ruta_workspace=args.ruta

                if lenguaje_proyecto == 0:
                        ruta_report_task = '/target/sonar/report-task.txt'

                elif lenguaje_proyecto == 1:
                        ruta_report_task ='/build/sonar/report-task.txt'

                elif lenguaje_proyecto == 2:
                        ruta_report_task = '/.../report-task.txt' # en construcción

                elif lenguaje_proyecto == 3:
                        ruta_report_task = '/.scannerwork/report-task.txt'
                else:
                        logging.error("El lenguaje ingresado no es valido")
                        return None

                try:
                        report_task = open(ruta_workspace+ruta_report_task,'r')
                except Exception as err:
                        logging.error("Error en la lectura del archivo %s: %s",ruta_workspace+ruta_report_task, str(err))
                        return None
                else:
                        for item in report_task:
                                if re.match( 'ceTaskId',item ):
                                        list_items=item.split('=')
                                        if len(list_items)>=2:
                                                Scan_ID = list_items[1].replace('\n', '') #que pasa si la respuesta es incorrecta.
                                                logging.info("Escanner estatico retorna el Scan Id correctamente")
                                                return Scan_ID
                                        else:
                                                logging.error("Respuesta invalidad de escanner estatico")
                                                return None


def _get_sonarscan_command():#<scannerHome>
        #0=Java-Maven, 1=Java-Gradle, 2= MSBuild , 3= Otros

        if lenguaje_proyecto == 0:

                cmd4jenkins = 'mvn sonar:sonar'

        elif lenguaje_proyecto == 1:


                cmd4jenkins = './gradlew sonarqube'

        elif lenguaje_proyecto == 2:

                cmd4jenkins = ''

        elif lenguaje_proyecto == 3:

                #JS,TS,Go,Python,PHP,...
                if args.shome:
                        scannerHome=args.shome
                        #0=Java-Maven, 1=Java-Gradle, 2= MSBuild , 3= Otros
                else:
                        return 0

                file = open("project.properties", "w")

                file.write("sonar.sources=." + "\n")

                file.write("sonar.projectKey="+project_id)

                file.close()

                cmd4jenkins = scannerHome+'/bin/sonar-scanner -Dproject.settings=project.properties'

        else:

                logging.error('Error: no se especifico tipo de proyecto, lenguaje no Valido')

                cmd4jenkins = ''

        return cmd4jenkins


def get_id_request(chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(8))#Retorna un string para identificar la comunicacion

def salting(stringLength=13):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


####################################################### MAIN ####################################################################
logging.basicConfig(filename='TheDeep_client.log',format='%(asctime)s:%(levelname)s: %(message)s', level=logging.DEBUG)

if error:# Si hay un error en la paremetrización del agente
        print('1')
        logging.error(error)
else:
        respuesta=0
        #tipos: 0 estático inicio, 1 estatico fin, 2 dinamico
        if tipo=="0":#escaneo estatico parametrizacion
                if args.code != None:
                        lenguaje_proyecto=args.code
                        #0=Java-Maven, 1=Java-Gradle, 2= MSBuild , 3= Otros
                        sonar_command=_get_sonarscan_command()
                        if sonar_command:
                                print(sonar_command)
                        else:
                                logging.error("No se pudo obtener el comando del escaner estatico")
                                print("1")
                else:
                        logging.error("Es necesario ingresar el lenguaje del proyecto --code ")
                        print("1")

        elif tipo=="1": #Obtener reporte de sonar
                #0=Java-Maven, 1=Java-Gradle, 2= MSBuild , 3= Otros
                #id_scan=_get_Scan_ID()
                id_scan=project_id
                if id_scan: # Si se obtiene un id valido de escaneo
                        in_progress=True # Inicia la consulta constante hasta terminar el escaneo
                        TheDeep_Fail=0
                        while in_progress: #Mientras este en progreso se solicita el estado
                                peticion='{"req":2'+', "tipo": 1, "id":"'+project_id+'", "token":"'+token+'", "id_scan":"'+ id_scan+'"}'
                                respuesta=conexion(msg=peticion) #msg de control para finalizar sonar y obtener reporte se debe enviar el id_scan, el req, token, project_id y request_id
                                if respuesta:
                                        logging.info(str(respuesta))
                                        scan_status=respuesta.get("status")
                                        if scan_status==1: #En progreso
                                                TheDeep_Fail=0
                                                time.sleep(10)
                                        elif scan_status==2: #Terminado con exito
                                                pipeline=respuesta.get('pipeline')
                                                logging.info("Escaneo Terminado con exito")
                                                if pipeline=='1':
                                                        logging.info("El proyecto NO cumple las politicas")
                                                        print (pipeline)
                                                elif pipeline=="0":
                                                        logging.info("El proyecto CUMPLE las politicas")
                                                        print (pipeline)
                                                else:
                                                        logging.error("El campo pipeline de la respuesta es invalido o no existe, Validar las respuestas en The Deep")
                                                in_progress=False
                                        elif scan_status ==0:
                                                error=respuesta.get("msg")
                                                logging.error("Se ha generado un error con el escaneo: "+error)
                                                in_progress=False
                                                print("1")
                                        elif scan_status == 4:
                                                logging.warning(respuesta.get("msg"))
                                                TheDeep_Fail+=1
                                        else:
                                                logging.error("stus %s: scan_status no Valido", str(scan_status))
                                                in_progress=False
                                                print("1")
                                else:#Time out, si no hay respuesta se sale 
                                        print('1')
                                        in_progress=False
                                        break

                                if TheDeep_Fail==2: # si se dan dos errores cierra la conexion
                                        logging.error("Error en TheDeep")
                                        in_progress=False
                                        print ("1")
                else:
                        logging.error("No se encontro un scan id valido")
                        print("1")

        elif tipo=="2":# Escaneo dinamico
                if args.url:
                        url=args.url
                        #Opciones de mapa del sitio
                        peticion='{"req":1, "tipo":2,"token":"'+token+'","url":"'+url+'", "id":"'+project_id+'"}'
                        in_progress=True
                        if args.login:
                                try:
                                        login_str=args.login
                                except Exception as err:
                                        logging.error("El argumento login debe estar codificado en base64")
                                        print("1")
                                else:
                                        try:
                                                #Estructura login con form {"<form_user_id>":"<user>","<form_pass_id>":"<password>","validar":<"patron">, "url":"<url_login>"}
                                                print(b64decode(login_str))
                                                login=json.loads(b64decode(login_str))
                                        except Exception as err:
                                                # login tiene la siguiente estructura {"user":"usario","pass":"password","url":"<url del logging>","form_user_id":"id del input","form_pass_id":"id del input"}
                                                # o {"cookie":"my_cookie=contenido; path=/"}
                                                logging.error("El parametro login debe ser un JSON valido y codificado en base64: "+str(err))
                                                in_progress=False
                                                print("1")

                                        else:
                                                if login.get("validar") and login.get("url"):# para login con formulario
                                                        peticion='{"req":1, "tipo":2,"token":"'+token+'","url":"'+url+'", "id":"'+project_id+'", "login":"'+salting()+login_str+'"}'
                                                elif "cookie" in login: # para login con cookie
                                                        peticion='{"req":1, "tipo":2,"token":"'+token+'","url":"'+url+'", "id":"'+project_id+'", "login":"'+salting()+login_str+'"}'
                                                else:
                                                        in_progress=False
                                                        logging.error("login no cuenta con todos los campos, debe tener la siguiente estructura")
                                                        print("1")
                        if in_progress:
                                respuesta=conexion(msg=peticion)
                                if respuesta:
                                        logging.info(str(respuesta))
                                        status=4
                                        status=respuesta.get('status',-1)
                                        if status==3:
                                                id_scan=respuesta["id_scan"]
                                                time.sleep(5)#tiempo de gracia para iniciar el escaneo
                                                TheDeep_Fail=0
                                                logging.info("Escaneo creado exitosamente")
                                                while in_progress:
                                                        if TheDeep_Fail == 2:
                                                                logging.info("Se han generado varios problemas en The Deep")
                                                                print ("1")
                                                                in_progress=False
                                                                break

                                                        respuesta=conexion(msg='{"req":2, "tipo":2,"token":"'+token+'","id":"'+project_id+'", "id_scan":"'+id_scan+'"}')
                                                        if respuesta:
                                                                scan_status=4
                                                                scan_status=respuesta.get("status",-1)
                                                                if scan_status==1:
                                                                        #Continua a la espera
                                                                        TheDeep_Fail=0
                                                                        logging.info("Escaneando ...")
                                                                        time.sleep(10)#Tiempo hasta la siguiente checkeo
                                                                elif scan_status==0:
                                                                        in_progress=False
                                                                        logging.error("TheDeep: "+respuesta.get("msg"))
                                                                        print("1")
                                                                elif scan_status==2:
                                                                        in_progress=False
                                                                        pipeline=respuesta.get('pipeline',None)
                                                                        if pipeline == None:
                                                                                logging.error("No se ha encontrado el campo pipeline en la respuesta")
                                                                                print("1")
                                                                        elif pipeline=="0" or pipeline=="1":
                                                                                logging.info("Escaneo finalizado correctamente")
                                                                                if pipeline=="1":
                                                                                        logging.info("El proyecto NO cumple las politicas")
                                                                                elif pipeline=="0":
                                                                                        logging.info("El proyecto CUMPLE las politicas")
                                                                                print(pipeline)
                                                                        else:
                                                                                logging.error("El campo pipeline de la respuesta es invalido o no existe, Validar las respuestas en The Deep, pipeline=%s",str(pipeline))
                                                                                print("1")

                                                                elif scan_status==4:
                                                                        TheDeep_Fail+=1
                                                                        logging.warning(respuesta.get("msg"))
                                                                else:
                                                                        logging.error("status %s scan_status no Valido", str(scan_status))
                                                                        in_progress=False
                                                                        print("1")

                                                        else:
                                                                print('1')
                                                                in_progress=False
                                                                break

                                        elif status==4:
                                                TheDeep_Fail+=1
                                                logging.error(respuesta.get('msg', 'Se ha presentado un problema en The Deep'))
                                                print("1")
                                        elif status==0:
                                                logging.error(respuesta["msg"])
                                                print("1")
                                        else:
                                                logging.error("status no Valido")
                                                print("1")
                                else:
                                        logging.error("No hay una respuesta valida de TheDeep %s:%s",server_ip, server_port)
                                        print("1")
                else:
                        logging.error("Error en la parametrizacion del agente: Es necesario ingresar la url a escanear (--url <url>)")
                        print("1")
        elif tipo=="3":# Escaneo estatico AZ
                peticion='{"req":1, "tipo":1,"token":"'+token+'","id":"'+project_id+'"}'
                respuesta=conexion(msg=peticion)
                if respuesta:
                        logging.info(str(respuesta))
                        status=respuesta.get('status',-1)
                        if status==3: #Creado de forma exitosa
                                
                                project_key=respuesta.get("id_scan")
                                print('##vso[task.setvariable variable=project_key;]'+project_key)
                
                                """
                                #Fase de preparacion 

                                task: SonarQubePrepare@4
                                inputs:
                                SonarQube: 'thedeep_statico'
                                scannerMode: 'CLI'
                                configMode: 'manual'
                                cliProjectKey: '$(project_key)'
                                
                                #Fase
                                task: SonarQubeAnalyze@4
                                task: SonarQubePublish@4
                                """
                else:
                        print('1')
        else:
                print('1')
                logging.error("tipo invalido")
