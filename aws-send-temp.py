from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import os
import time
import datetime
from setenv import AmazonRootCA1, private, certificate, n_remo_token
from remo import NatureRemoAPI

# 初期化
myMQTTClient = AWSIoTMQTTClient("testRule")
topic = "testRule/time"
deviceNo = "3c01b556cb39"

# MQTTクライアントの設定
myMQTTClient.configureEndpoint("a250qcref0helr-ats.iot.ap-northeast-1.amazonaws.com", 8883)
myMQTTClient.configureCredentials(AmazonRootCA1, private, certificate)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(5)

# Connect to AWS IoT endpoint and publish a message
myMQTTClient.connect()
print ("Connected to AWS IoT")

# Reads temperature from sensor and prints to stdout
# id is the id of the sensor
def readSensor(id, count, on):
    power = on
    get_time = time.localtime()
    nowtime = datetime.datetime.now()
    nowsettime = int(time.mktime(nowtime.timetuple()))  # UNIX Time
    #send Command
    message = {}
    message['ID'] = count
    message['power_flag'] = on
    message['time'] = nowtime.strftime('%Y/%m/%d %H:%M:%S')
    message['deviceNo'] = deviceNo
    tfile = open("/sys/bus/w1/devices/"+id+"/w1_slave")
    text = tfile.read()
    tfile.close()
    secondline = text.split("\n")[1]
    temperaturedata = secondline.split(" ")[9]
    temperature = float(temperaturedata[2:])
    temperature = temperature / 1000
    message['temperature']  = temperature
    print ("Sensor: " + id  + " - Current temperature : %0.3f C" % temperature)
    if (power == 0):
        if (temperature >= 30):
            appliances = api.get_appliances()
            api.update_aircon_settings(appliances[0].id, operation_mode='cool', temperature=26)
            on = 1
    if (power == 1):
        if (get_time.tm_hour == 4):
            appliances = api.get_appliances()
            api.update_aircon_settings(appliances[0].id, button='power-off')
            on = 0
    messageJson = json.dumps(message)
    print (messageJson)
    myMQTTClient.publish(topic, messageJson, 1)
    return on
    

# Reads temperature from all sensors found in /sys/bus/w1/devices/
# starting with "28-...
def readSensors(count, on):
    no_sensor = 0
    sensor = ""
    for file in os.listdir("/sys/bus/w1/devices/"):
        if (file.startswith("28-")):
            x = readSensor(file, count, on)
            no_sensor+=1
    if (no_sensor == 0):
        print ("No sensor found! Check connection")
    return x 

# read temperature every 2second for all connected sensors
def loop():
    count = 0
    on = 0
    while True:
        y = readSensors(count, on)
        time.sleep(900)
        on = y
        count+=1

# Nothing to cleanup
def destroy():
    pass

# 対応していない型に対するマッピング後付け指定
def support_datetime_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(repr(o) + " is not JSON serializable")

# Main starts here
if __name__ == "__main__":
    try:
        api = NatureRemoAPI(n_remo_token)
        devices = api.get_devices()
        loop()
    except KeyboardInterrupt:
        myMQTTClient.disconnect()
        destroy()
        