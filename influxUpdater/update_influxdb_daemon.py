#!/usr/bin/python
import ConfigParser, os
import logging.handlers, logging.config
from datetime import datetime
import sys, time, threading, os, glob, logging, ow
import requests
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
import pcd8544.lcd as lcd
import time
import RPi.GPIO as GPIO   #import the GPIO library
import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import MAX6675.MAX6675 as MAX6675

MAX6675_CLK = 6
MAX6675_CS  = 13
MAX6675_DO  = 19
MAX667_VCC = 26 
BUZZER_PIN = 5
DHT11_PIN = 17
DHT11_LAST_T = 0
DHT11_LAST_H = 0
MAX6675_LAST_T = 0
DBNAME = 'temps'

max6675_sensor = MAX6675.MAX6675(MAX6675_CLK, MAX6675_CS, MAX6675_DO)
# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
dht11_sensor = Adafruit_DHT.DHT11

logging.config.fileConfig("updater.cfg")
logging.getLogger(__name__)

config = ConfigParser.ConfigParser()
config.readfp(open('updater.cfg'))
base_dir = config.get('main','base_dir')+"/"
raspiURL = config.get('main','raspiURL')
sleep = config.getint('main','sleep')
cms_url = config.get('main','cms_url')


def buzz(pitch, duration):   #create the function "buzz" and feed it the pitch and duration)
    period = 1.0 / pitch     #in physics, the period (sec/cyc) is the inverse of the frequency (cyc/sec)
    delay = period / 2     #calcuate the time for half of the wave
    cycles = int(duration * pitch)   #the number of waves to produce is the duration times the frequency
    for i in range(cycles):    #start a loop from 0 to the variable "cycles" calculated above
        GPIO.output(BUZZER_PIN, True)   #set pin 5 to high
        time.sleep(delay)    #wait with pin 18 high
        GPIO.output(BUZZER_PIN, False)    #set pin 18 to low
        time.sleep(delay)    #wait with pin 5 low


def startupbeep():
    i=200
    while i<=2000:
        buzz(i, 0.1)  #feed the pitch and duration to the function, "buzz"
        i+=200


def beeper():
    while True:
        buzz(2000,0.1)
        time.sleep(0.1)


def lcd_blink(text):
    i=10
    lcd.cls()
    lcd.locate(0,0)
    lcd.text(text)
    lcd.locate(0,1)
    while i<0:
       lcd.text("after %s sec" % (i))
       if i%2:
           lcd.backlight(1)
       else:
           lcd.backlight(0)
       i-=1
       time.sleep(1)


def value2lcd(date,id,desc,value):
    lcd.cls()
    lcd.locate(0,0)
    lcd.text(date)
    lcd.locate(0,1)
    lcd.text(id)
    lcd.locate(0,2)
    lcd.text(desc)
    lcd.locate(0,3)
    lcd.text("Temp: %s" % (value))
    lcd.locate(0,4)


def lcdstatusupdate(sensor_count,i):
    date = datetime.now()
    lcd.locate(3,0)
    lcd.text(date.strftime('%d/%m/%y'))
    lcd.locate(3,1)
    lcd.text(date.strftime('%H:%M:%S'))
    lcd.locate(3,2)
    lcd.text("sensr: %s" % sensor_count)
    lcd.locate(3,3)
    lcd.text("Next: %s" % i)
    lcd.locate(3,4)

class tmpclass(object):
    pass


def read_dht11():
    h = tmpclass()
    h.address = "DHT11_humidity"
    t = tmpclass()
    t.address = "DHT11_temp"
    humidity, temperature = Adafruit_DHT.read_retry(dht11_sensor, DHT11_PIN)
    if humidity is not None and temperature is not None:
        h.value = humidity
        DHT11_LAST_T = humidity
        t.value = temperature
        DHT11_LAST_H = temperature
    else:
        h.value = DHT11_LAST_H
        t.value = DHT11_LAST_T

    return h,t


def calc_power():
    p = tmpclass()
    pealevool = value = float(ow.Sensor('/28FF461F10140002').temperature11)
    tagasivool = value = float(ow.Sensor('/28FF981E10140071').temperature11)
    delta = abs(pealevool-tagasivool)
    power = delta*4.2*1.1 
    p.value = "%0.2f" % power
    p.address = "Power"
    return p


class EmonCms(object):
    def __init__(self,url):
        self.url = url
        self.json = {}
    def append(self,key,value):
        self.json[key] = value
    def post(self):
       data = str(self.json)
       url = self.url.replace("JSON_DATA",data).strip()
       logging.debug(url)
       r = requests.get(url)
       if r.status_code == requests.codes.ok and r.text == "ok":
           return True
       else:
           return False


def read_max6675():
    t = tmpclass()
    t.address = "boiler_temp"
    temperature = max6675_sensor.readTempC()   
    if temperature:
        t.value = temperature
        MAX6675_LAST_T = temperature
    else:
        t.value = MAX6675_LAST_T

    return t

def setup():
    GPIO.setmode(GPIO.BCM)            # choose BCM or BOARD  
    GPIO.setup(MAX667_VCC, GPIO.OUT) # set a port/pin as an output  MAX6675 VCC
    GPIO.output(MAX667_VCC, 1)       # set port/pin value to 1/GPIO.HIGH/True  
    GPIO.setup(BUZZER_PIN, GPIO.OUT)  #Set pin 18 as an output pin
    GPIO.setwarnings(False)
    startupbeep()


def daemon():
    client = InfluxDBClient('localhost', 8086, 'USER', 'PASSWORD', DBNAME,timeout=30)
    ow.init('localhost:4304')
    lcd.init()
    logging.debug("Daemon starting")
    logging.debug("Create INFLUX database: " + DBNAME)
    errors = 0
    try:
        client.create_database(DBNAME)
    except InfluxDBClientError:
        logging.debug("%s DB already exist" % DBNAME)
        pass
    except:
        logging.exception("Error")
        lcd.text("Exception")
    try:
       client.create_retention_policy('awesome_policy', '3d', 3, default=True)
    except InfluxDBClientError:
       logging.debug("%s policy already exist" % DBNAME)
       pass

    
    for i in range(10):
        try:
            devices = ow.Sensor('/').sensorList()
            date = datetime.now()
            points=[]
            for o in read_dht11():
                devices.append(o)
            devices.append(calc_power())
            devices.append(read_max6675())
            for sensor in devices:
                name = sensor.address
                try:
                    value = float(sensor.value)
                except:
                    value = float(ow.Sensor('/%s' % name).temperature11)
                desc = name
                json_body = {   
                       "time": date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                       "measurement": "rosma_temps",
                       "tags": {
                           "sensor": name,
                       },
                       "fields": {
                           "value": value
                       }
                   }

                points.append(json_body)
                value2lcd(date.strftime('%d/%m/%y %H:%M:%S'),name,desc,value)
                logging.debug(json_body)
                cms = EmonCms(cms_url)
                cms.append(name,value)
                #cms_status = cms.post()
                cms_status = True
                if cms_status:
                    logging.debug("CMS Post ok")
                else:
                    logging.debug("CMS Post failed")
            status=client.write_points(points)
            if status:
                lcd.text("Sent<-OK")
                logging.debug(status)
            else:
                lcd.text("Error!")
                logging.error(status)
            #Show status
            s=0
            lcd.cls()
            while s<sleep:
                lcdstatusupdate(len(devices),s)
                time.sleep(1)
                s+=1
        except:
                logging.exception("Error occurred %s" % sys.exc_info()[1])
                lcd.text("%s Exception!" % errors)
                time.sleep(1)
                if errors == 10:
                     lcd_blink("Rebooting!")
                     d = threading.Thread(name='beeper', target=beeper)
                     d.setDaemon(True)
                     d.start()
                     #os.system("reboot")
                     d.join()
                else:
                    errors += 1
    logging.debug("Daemon exiting")
    return(0)



if __name__ == "__main__":
    setup()
    try:
        d = threading.Thread(name='daemon', target=daemon)
        d.setDaemon(True)
        d.start()
        d.join()
    except:
        logging.exception(error)
