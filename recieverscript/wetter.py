import sys
import json
import csv
#import pymysql
import time
#import rrdtool
import os
import requests
import subprocess
import mysql.connector
zeitstempel_alt = "2021-06-26 13:12:12"
os.system("clear")


mydb = mysql.connector.connect(
  host="192.168.0.19",
  user="wetter",
  password="TES0deGt2U4j5ADE",
  database="wetter"
)


"""
#Datenbnkverbindung mariaDB herstellen
db = pymysql.connect(host="192.168.2.11", user="WerAuchImmer", passwd="WasAuchImmer", db="SensorenDB")
#db.autocommit(True)
cursor = db.cursor()

    Mein Datensatz: msg_typ ; id ; battery ; temperature_C ; humidity ; wind_dir_deg ; wind_avg_km_h ; wind_max_km_h ; rain_mm
    
{"time" : "2021-08-26 11:35:33", "model" : "Fineoffset-WHx080", "subtype" : 0, "id" : 200, "battery_ok" : 1, "temperature_C" : 18.300, "humidity" : 56, "wind_dir_ deg" : 315, "wind_avg_km_h" : 7.344, "wind_max_km_h" : 11.016, "rain_mm" : 12.900, "mic" : "CRC"}

"""

def getusievert():
    out = subprocess.check_output('python2.7 /home/daniel/gq-gmc-control/gq-gmc-control.py -b 57600 -p /dev/ttyUSB0 --cpm', shell=True).decode('utf-8')
    out = out.split("\n")
    out = (out[1]).strip(' uSv/h')
    #print(out)
    #url6=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/79132940-077c-11ec-b211-e3346ae45cd8.json?operation=add&value={}"'.format(out))
    #cmd6=('curl -X POST '+url6)
    #print(cmd6)
    #os.system(cmd6)

    mycursor = mydb.cursor()

    sql = "INSERT INTO data (timestamp, stationid, battery, temperature, humidity, winddirection, wind_avg, wind_max, rain_mm, radioactivity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = ('{0[time]}'.format(Dateneingang), '{0[id]}'.format(Dateneingang), '{0[battery_ok]}'.format(Dateneingang),'{0[temperature_C]}'.format(Dateneingang),'{0[humidity]}'.format(Dateneingang),'{0[wind_dir_deg]}'.format(Dateneingang),'{0[wind_avg_km_h]}'.format(Dateneingang),'{0[wind_max_km_h]}'.format(Dateneingang),'{0[rain_mm]}'.format(Dateneingang),(out))
    mycursor.execute(sql, val)

    mydb.commit()

    print(mycursor.rowcount, "record inserted.")



for line in sys.stdin:
    Dateneingang = json.loads(line.strip())
    zeitstempel = time.mktime(time.strptime(Dateneingang["time"], '%Y-%m-%d %H:%M:%S'))
    subtype = Dateneingang["subtype"]
    id = Dateneingang["id"]
    battery_ok = Dateneingang["battery_ok"]
    temperatur = Dateneingang ["temperature_C"]
    humidity = Dateneingang ["humidity"]
    wind_direction = Dateneingang ["wind_dir_deg"]
    wind_avg_km_h = Dateneingang ["wind_avg_km_h"]
    wind_max_km_h = Dateneingang ["wind_max_km_h"]
    rain_mm = Dateneingang ["rain_mm"]

    
    """Datenaufbereitung
    Die Senderidentifizierung erfolgt Anhand der id, Bestimmung des Datentyps mit subtype

"""
    #Doppelten Datensatz über Timestamp verwerfen
    if zeitstempel == zeitstempel_alt:
       print("Datensatz bereits empfangen! Verwerfe anderen Datensatz. \n")
    else:
       
#        if Dateneingang["id"] == 200:
        if Dateneingang["id"] == 197:
           print('Temperatur: {0[temperature_C]}°C'.format(Dateneingang))
           print('Luftfeuchtigkeit: {0[humidity]}%'.format(Dateneingang))
           print('Windrichtung: {0[wind_dir_deg]}°'.format(Dateneingang))
           print('Windgeschwindigkeit: {0[wind_avg_km_h]}km/h'.format(Dateneingang))
           print('Maximale Windgeschwindigkeit: {0[wind_max_km_h]}km/h'.format(Dateneingang))
           print('Niederschlag: {0[rain_mm]}mm'.format(Dateneingang))
           if Dateneingang["battery_ok"] == 1:
              print('Batteriestand: Voll')
           else:
              print('Batteriestand: Leer')
           print('Zeitstempel des Senders: {0[time]}'.format(Dateneingang))
           zeitstempel_alt = zeitstempel
           print("\n")

           #Daten an Volkszähler schicken
           #URLS Generieren
           #url1=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/c8b5ea00-0661-11ec-a4b0-39ae3ec93ad9.json?operation=add&value={0[temperature_C]}"'.format(Dateneingang))
           #url2=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/ec861490-0661-11ec-b055-0d13f9d9c621.json?operation=add&value={0[humidity]}"'.format(Dateneingang))
           #url3=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/20c39b70-0662-11ec-bff8-c9f9267dafa5.json?operation=add&value={0[wind_avg_km_h]}"'.format(Dateneingang))
           #url4=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/0a3151f0-0662-11ec-a6cc-873fe0019d0c.json?operation=add&value={0[wind_max_km_h]}"'.format(Dateneingang))
           #url5=('"http://web42216.pfweb.eu/vz/htdocs/middleware.php/data/b7fd61e0-0767-11ec-a275-752c33dc47b2.json?operation=add&value={0[rain_mm]}"'.format(Dateneingang))


           #Systemfreundlich verpacken
           #cmd1=('curl -X POST '+url1)
           #cmd2=('curl -X POST '+url2)
           #cmd3=('curl -X POST '+url3)
           #cmd4=('curl -X POST '+url4)
           #cmd5=('curl -X POST '+url5)

           #Daten Senden
           #os.system(cmd1)
           #os.system(cmd2)
           #os.system(cmd3)
           #os.system(cmd4)
           #os.system(cmd5)

           print("\n")
           getusievert()



"""
    if Dateneingang["rid"] == 228: #Sender 1
        data = '%f:%s:U:U:%s:U:U' % (zeitstempel, temperatur, relH)
        insert1 = "INSERT INTO Sensor1_Prol(SensorID, DateTime, TempC, Humi) VALUES('{0[channel]}', '{0[time]}', '{0[temperature_C]}', '{0[humidity]}');".format(Dateneingang)
    elif Dateneingang["rid"] == 208: #Sender 2
        data = '%f:U:%s:U:U:%s:U' % (zeitstempel, temperatur, relH)
        insert1 = "INSERT INTO Sensor2_Prol(SensorID, DateTime, TempC, Humi) VALUES('{0[channel]}', '{0[time]}', '{0[temperature_C]}', '{0[humidity]}');".format(Dateneingang)
    elif Dateneingang["rid"] == 246: #Sender 3
        data = '%f:U:U:%s:U:U:%s' % (zeitstempel, temperatur, relH)
        insert1 = "INSERT INTO Sensor3_Prol(SensorID, DateTime, TempC, Humi) VALUES('{0[channel]}', '{0[time]}', '{0[temperature_C]}', '{0[humidity]}');".format(Dateneingang)
    #Schreiben rrd
    #data = "N:Temp1:Temp2:Temp3:Hum1:Hum2:Hum3"
    rrdtool.update("/home/pi/sensordaten.rrd", data)
    #Schreiben mySQL
    cursor.execute(insert1)
    db.commit()
"""
