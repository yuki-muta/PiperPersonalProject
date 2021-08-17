import os
import requests
import boto3
from boto3.dynamodb.conditions import Key
import datetime

# Line Notify
ACCESS_TOKEN = os.environ["access_token"]
HEADERS = {"Authorization": "Bearer %s" % ACCESS_TOKEN}
URL = "https://notify-api.line.me/api/notify"

DYNAMO_DB = boto3.resource('dynamodb')
DYNAMO_TABLE = DYNAMO_DB.Table(os.environ["table_name"])

def lambda_handler(event, context):
    itemdata = DYNAMO_TABLE.scan(ConsistentRead=True)
    message = '\n''部屋の温度が30°を超えました。\n冷房を26°に設定しました。'
    count = 0
    for item in itemdata["Items"]:
        if (count == 0):
            latest_time = datetime.datetime.strptime(item['time'], '%Y/%m/%d %H:%M:%S')
        dt = datetime.datetime.strptime(item['time'], '%Y/%m/%d %H:%M:%S')
        if (latest_time <= dt):
            latest_temperature = item['temperature']
            latest_ID = item['ID']
            latest_time = datetime.datetime.strptime(item['time'], '%Y/%m/%d %H:%M:%S')
        count+=1
    latest_time = datetime.datetime.strftime(latest_time, '%Y/%m/%d %H:%M:%S')
    response = DYNAMO_TABLE.query(
        KeyConditionExpression=Key('time').eq(latest_time)
    )
    for items in response["Items"]:
        latest_power = items['power_flag']
    if (latest_power == 0):
        if(latest_temperature > 30):    
            message += '\n' "室温:" + str(latest_temperature)
            print(message)
            data = {'message': message}
            #lineに通知
            requests.post(URL, headers=HEADERS, data=data)