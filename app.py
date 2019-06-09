# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
import pymongo as pm
import json
import datetime
import tempfile

from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton
)


app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', 'bf1533b1e90a75d5ce6f497e2ac8e4bc')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN',
                                 'c9zoOD4+h2CR88GJVrwRvPIbzoneoT1AnbOl1gxF9A2sahPGRHDrhWqKT47yuD9vvVhkn4U9qwogytR5+w/Ga2YcCCY+OwpABW9irzXqdeNWsUuNeeLOwScusrA9SOFB2q3eo2gXgzXTzYxWEQocuQdB04t89/1O/w1cDnyilFU=')
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

#connect mongoDB


client = pm.MongoClient() 
db = client['linebot'] 
taxinfocol = db['taxpayerinfo']
useraction = db['printAction']
printOrder = db['printOrder']
products = db['products']

userLineid = ''

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#function call api to get the company name and address

from requests import Session
import zeep
from zeep import Client
from zeep.transports import Transport

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def companyName(result):
    output=''
    title = result['vtitleName'].get('anyType', None)[0]
    companyName = result['vName'].get('anyType', None)[0]
    output = '{} {}'.format(title,companyName)
    return output

def companyAdd(result):
    output=''
    buildingName = ''
    if result['vBuildingName'].get('anyType', None)[0] != '-':
        buildingName = 'ตึก {} '.format(result['vBuildingName'].get('anyType', None)[0])
    floor = ''
    if result['vFloorNumber'].get('anyType', None)[0] != '-':
        floor = 'ชั้น {} '.format(result['vFloorNumber'].get('anyType', None)[0])
    village = ''
    if result['vVillageName'].get('anyType', None)[0] != '-':
        village = 'หมู่บ้าน {} '.format(result['vVillageName'].get('anyType', None)[0])
    room = ''
    if result['vRoomNumber'].get('anyType', None)[0] != '-':
        room = 'ห้องเลขที่ {}'.format(result['vRoomNumber'].get('anyType', None)[0])
    house = ''
    if result['vHouseNumber'].get('anyType', None)[0] != '-':
        house = 'บ้านเลขที่ {} '.format(result['vHouseNumber'].get('anyType', None)[0])
    house = ''
    if result['vHouseNumber'].get('anyType', None)[0] != '-':
        house = 'บ้านเลขที่ {} '.format(result['vHouseNumber'].get('anyType', None)[0])
    moo = ''
    if result['vMooNumber'].get('anyType', None)[0] != '-':
        moo = 'หมู่ {} '.format(result['vMooNumber'].get('anyType', None)[0])
    soi = ''
    if result['vSoiName'].get('anyType', None)[0] != '-':
        soi = 'ซอย {} '.format(result['vSoiName'].get('anyType', None)[0])
    street = ''
    if result['vStreetName'].get('anyType', None)[0] != '-':
        street = 'ถ. {} '.format(result['vStreetName'].get('anyType', None)[0])
    thambol = ''
    amphur = ''
    if result['vProvince'].get('anyType', None)[0] != 'กรุงเทพมหานคร':
        thambol = 'ต. {} '.format(result['vThambol'].get('anyType', None)[0])
        amphur = 'อ. {} '.format(result['vAmphur'].get('anyType', None)[0])
    if result['vProvince'].get('anyType', None)[0] == 'กรุงเทพมหานคร':
        thambol = 'แขวง. {} '.format(result['vThambol'].get('anyType', None)[0])
        amphur = 'เขต. {} '.format(result['vAmphur'].get('anyType', None)[0])
    province = 'จ. {} '.format(result['vProvince'].get('anyType', None)[0])
    postcode = '{}'.format(result['vPostCode'].get('anyType', None)[0])
    output = buildingName+floor+village+room+house+moo+soi+street+thambol+amphur+province+postcode
    return output

def addressformat(result):
    output=''
    branch = 'สำนักงานใหญ่' if result['vBranchNumber'].get('anyType', None)[0] == 0 else 'สาขาย่อย'
    title = result['vtitleName'].get('anyType', None)[0]
    companyName = result['vName'].get('anyType', None)[0]
    output = '{} {}\nสาขา: {}'.format(title,companyName,branch)
    buildingName = ''
    if result['vBuildingName'].get('anyType', None)[0] != '-':
        buildingName = 'ตึก {} '.format(result['vBuildingName'].get('anyType', None)[0])
    floor = ''
    if result['vFloorNumber'].get('anyType', None)[0] != '-':
        floor = 'ชั้น {} '.format(result['vFloorNumber'].get('anyType', None)[0])
    village = ''
    if result['vVillageName'].get('anyType', None)[0] != '-':
        village = 'หมู่บ้าน {} '.format(result['vVillageName'].get('anyType', None)[0])
    room = ''
    if result['vRoomNumber'].get('anyType', None)[0] != '-':
        room = 'ห้องเลขที่ {}'.format(result['vRoomNumber'].get('anyType', None)[0])
    house = ''
    if result['vHouseNumber'].get('anyType', None)[0] != '-':
        house = 'บ้านเลขที่ {} '.format(result['vHouseNumber'].get('anyType', None)[0])
    house = ''
    if result['vHouseNumber'].get('anyType', None)[0] != '-':
        house = 'บ้านเลขที่ {} '.format(result['vHouseNumber'].get('anyType', None)[0])
    moo = ''
    if result['vMooNumber'].get('anyType', None)[0] != '-':
        moo = 'หมู่ {} '.format(result['vMooNumber'].get('anyType', None)[0])
    soi = ''
    if result['vSoiName'].get('anyType', None)[0] != '-':
        soi = 'ซอย {} '.format(result['vSoiName'].get('anyType', None)[0])
    street = ''
    if result['vStreetName'].get('anyType', None)[0] != '-':
        street = 'ถนน {} '.format(result['vStreetName'].get('anyType', None)[0])
    thambol = ''
    amphur = ''
    if result['vProvince'].get('anyType', None)[0] != 'กรุงเทพมหานคร':
        thambol = 'ตำบล {} '.format(result['vThambol'].get('anyType', None)[0])
        amphur = 'อำเภอ {} '.format(result['vAmphur'].get('anyType', None)[0])
    if result['vProvince'].get('anyType', None)[0] == 'กรุงเทพมหานคร':
        thambol = 'แขวง. {} '.format(result['vThambol'].get('anyType', None)[0])
        amphur = 'เขต. {} '.format(result['vAmphur'].get('anyType', None)[0])
    province = 'จังหวัด {} '.format(result['vProvince'].get('anyType', None)[0])
    postcode = '{}'.format(result['vPostCode'].get('anyType', None)[0])

    output = output+'\nที่อยู่: '+buildingName+floor+village+room+house+moo+soi+street+thambol+amphur+province+postcode
    output = output+'\n\n---------------\nทะเบียนรถอะไรคะ'

    return output

#Get Line user id
import json
def getUserId(x):
    y = json.loads(x)
    y = y['events']
    y = y[0]
    y = y['source']
    y = y['userId']
    return y

import multiprocessing
import threading
import time

countloop = 0
def callapi(x,b):
    global countloop
    try:
        session = Session()
        session.verify = False
        transport = Transport(session=session)
        client = Client('https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx?wsdl',
                        transport=transport)
        result = client.service.Service(
            username='anonymous',
            password='anonymous',
            TIN=x,
            ProvinceCode=0,
            BranchNumber=b,
            AmphurCode=9
        )
        # Convert Zeep Response object (in this case Service) to Python dict.
        result = zeep.helpers.serialize_object(result)
        mydict = { 'taxpayerNumber': str(x), 'taxpayerDetail': result, 'branch': b }
        ins = taxinfocol.insert_one(mydict)
        addressformat(result)
        print('save')

        signature = request.headers['X-Line-Signature']
        # get request body as text
        body = request.get_data(as_text=True)
        userLineid = getUserId(body)
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "taxpayerid": str(x) }}
        useraction.update_one(myquery,newvalue)
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '1' }}
        useraction.update_one(myquery,newvalue)
    except:
        output = 'มีบางอย่างผิดพลาด กรุณาลองใหม่อีกครั้ง'
        if countloop > 5:
            countloop = 0
        else:
            time.sleep(3)
            countloop = countloop + 1
            callapi(x,b)
        
    return output
# all gas price
def gesprice():
    diesail = products.find_one({'gasType': 'ดีเซล'})
    output = 'ราคาน้ำมันปัจจุบัน ของ ESSO\n\n'+diesail.get("gasType")+' \nราคา '+str(diesail.get("gasPrice"))+' บาท/ลิตร\n\n'
    diesailPremiem = products.find_one({'gasType': 'ซูพรีม พลัส ดีเซล'})
    output = output+diesailPremiem.get("gasType")+' \nราคา '+str(diesailPremiem.get("gasPrice"))+' บาท/ลิตร\n\n'
    gasSoholE20 = products.find_one({'gasType': 'แก๊สโซฮอล์ ซูพรีม E20'})
    output = output+gasSoholE20.get("gasType")+' \nราคา '+str(gasSoholE20.get("gasPrice"))+' บาท/ลิตร\n\n'
    gasSohol95 = products.find_one({'gasType': 'แก๊สโซฮอล์ ซูพรีม 95'})
    output = output+gasSoholE20.get("gasType")+' \nราคา '+str(gasSoholE20.get("gasPrice"))+' บาท/ลิตร\n\n'
    gasSohol95plus = products.find_one({'gasType': 'ซูพรีม พลัส แก๊สโซฮอล์ 95'})
    output = output+gasSohol95plus.get("gasType")+' \nราคา '+str(gasSohol95plus.get("gasPrice"))+' บาท/ลิตร\n\n'
    return output

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

#add gastype print action
def addgastype(x):
    global gastype
    gastype = ''
    global output
    output = ''
    global gasSohol95
    global gasSoholE20
    global diesail
    global plus
    gasSohol95 = '95'
    gasSoholE20 = 'E20'
    diesail = 'ดีเซล'
    plus = 'พลัส'

    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})

    if x.find(plus) >= 0:
        if x.find(diesail) >= 0:
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '3' }}
            useraction.update_one(myquery,newvalue)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "gastype": 'ซูพรีม พลัส ดีเซล' }}
            useraction.update_one(myquery,newvalue)
            output = 'ราคาทั้งหมดเท่าไหร่คะ'
        elif x.find(gasSohol95) >= 0:
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '3' }}
            useraction.update_one(myquery,newvalue)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "gastype": 'ซูพรีม พลัส แก๊สโซฮอล์ 95' }}
            useraction.update_one(myquery,newvalue)
            output = 'ราคาทั้งหมดเท่าไหร่คะ'
        else:
            output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'
    elif x.find(gasSoholE20) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'แก๊สโซฮอล์ ซูพรีม E20' }}
        myquery = { "lineid": userLineid }
        useraction.update_one(myquery,newvalue)
        output = 'ราคาทั้งหมดเท่าไหร่คะ'
    elif x.find(gasSohol95) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'แก๊สโซฮอล์ ซูพรีม 95' }}
        myquery = { "lineid": userLineid }
        useraction.update_one(myquery,newvalue)
        output = 'ราคาทั้งหมดเท่าไหร่คะ'
    elif x.find(diesail) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'ดีเซล' }}
        useraction.update_one(myquery,newvalue)
        output = 'ราคาทั้งหมดเท่าไหร่คะ'
    else:
        output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'
    return output

#add gastype print action
def fixgastype(x):
    global gastype
    gastype = ''
    global output
    output = ''
    global userLineid
    userLineid = ''
    global gasSohol95
    global gasSoholE20
    global gasSohole20
    global diesail
    global plus
    gasSohol95 = '95'
    gasSoholE20 = 'E20'
    gasSohole20 = 'e20'
    diesail = 'ดีเซล'
    plus = 'พลัส'

    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})

    if x.find(plus) >= 0:
        if x.find(diesail) >= 0:
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '3' }}
            useraction.update_one(myquery,newvalue)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "gastype": 'ซูพรีม พลัส ดีเซล' }}
            useraction.update_one(myquery,newvalue)
            output = ordertaxinvoice(userLineid)
        elif x.find(gasSohol95) >= 0:
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '3' }}
            useraction.update_one(myquery,newvalue)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "gastype": 'ซูพรีม พลัส แก๊สโซฮอล์ 95' }}
            useraction.update_one(myquery,newvalue)
            output = ordertaxinvoice(userLineid)
        else:
            output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'
    elif x.find(gasSoholE20) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'แก๊สโซฮอล์ ซูพรีม E20' }}
        myquery = { "lineid": userLineid }
        useraction.update_one(myquery,newvalue)
        output = ordertaxinvoice(userLineid)
    elif x.find(gasSohole20) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'แก๊สโซฮอล์ ซูพรีม E20' }}
        myquery = { "lineid": userLineid }
        useraction.update_one(myquery,newvalue)
    elif x.find(gasSohol95) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'แก๊สโซฮอล์ ซูพรีม 95' }}
        myquery = { "lineid": userLineid }
        useraction.update_one(myquery,newvalue)
        output = ordertaxinvoice(userLineid)
    elif x.find(diesail) == 0:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '3' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "gastype": 'ดีเซล' }}
        useraction.update_one(myquery,newvalue)
        output = ordertaxinvoice(userLineid)
    else:
        output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'
    return output

def fixgasprice(x):
    global gastype
    gastype = ''
    global output
    output = ''
    global userLineid
    userLineid = ''
    global gasSohol95
    global gasSoholE20
    global gasSohole20
    global diesail
    global plus
    gasSohol95 = '95'
    gasSoholE20 = 'E20'
    gasSohole20 = 'e20'
    diesail = 'ดีเซล'
    plus = 'พลัส'

    if x.find(plus) >= 0:
        if x.find(diesail) >= 0:
            x = x.split(' ')
            x = x[len(x)-1]
            p = 0
            p = float(x)
            myquery = { "gasType": 'ซูพรีม พลัส ดีเซล' }
            newvalue = { "$set": { "gasPrice": p }}
            products.update_one(myquery,newvalue)
            gastype = 'ซูพรีม พลัส ดีเซล'
        elif x.find(gasSohol95) >= 0:
            x = x.split(' ')
            x = x[len(x)-1]
            p = 0
            p = float(x)
            myquery = { "gasType": 'ซูพรีม พลัส แก๊สโซฮอล์ 95' }
            newvalue = { "$set": { "gasPrice": p }}
            products.update_one(myquery,newvalue)
            gastype = 'ซูพรีม พลัส แก๊สโซฮอล์ 95'
        else:
            output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'
    elif x.find(gasSoholE20) == 0:
        x = x.split(' ')
        x = x[len(x)-1]
        p = 0
        p = float(x)
        myquery = { "gasType": 'แก๊สโซฮอล์ ซูพรีม E20' }
        newvalue = { "$set": { "gasPrice": p }}
        products.update_one(myquery,newvalue)
        gastype = 'แก๊สโซฮอล์ ซูพรีม E20'
    elif x.find(gasSohole20) == 0:
        x = x.split(' ')
        x = x[len(x)-1]
        p = 0
        p = float(x)
        myquery = { "gasType": 'แก๊สโซฮอล์ ซูพรีม E20' }
        newvalue = { "$set": { "gasPrice": p }}
        products.update_one(myquery,newvalue)
        gastype = 'แก๊สโซฮอล์ ซูพรีม E20'
    elif x.find(gasSohol95) == 0:
        x = x.split(' ')
        x = x[len(x)-1]
        p = 0
        p = float(x)
        myquery = { "gasType": 'แก๊สโซฮอล์ ซูพรีม 95' }
        newvalue = { "$set": { "gasPrice": p }}
        products.update_one(myquery,newvalue)
        gastype = 'แก๊สโซฮอล์ ซูพรีม 95'
    elif x.find(diesail) == 0:
        x = x.split(' ')
        x = x[len(x)-1]
        p = 0
        p = float(x)
        myquery = { "gasType": 'ดีเซล' }
        newvalue = { "$set": { "gasPrice": p }}
        products.update_one(myquery,newvalue)
        gastype = 'ดีเซล'
    else:
        output = 'ประเภทน้ำมันไม่ถูกต้อง ระบุใหม่คะ'

    updategas = products.find_one({'gasType': gastype})
    x = 'แก้ไขราคา\n'+updategas.get('gasType')+'\nราคา '+str(updategas.get('gasPrice'))+' บาท/ลิตร'
    output = x
    return output

# to print or change price
def changeorprint(x):
    global userLineid
    userLineid = ''
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})
    
    findstr = 'ปรับ'
    i = x.find(findstr)
    global position
    position = ''
    position = data.get('position')
    if i == -1:
        output = replace(x)
    else:
        if position == 'admin':
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '5' }}
            useraction.update_one(myquery,newvalue)
            output = gesprice()
        else:
            output = cancelall()
    return output

# function replace ' ' and '-' from input
def replace(x):
    number = ''
    global a
    global b
    a = ''
    b =0
    x = x.replace('-','')
    x = x.replace(' ','')
    findstr = 'สาขา'
    i = x.find(findstr)
    if i == -1:
        a = x
    else:
        x = x.split('สาขา')
        a = x[0]
        b = int(x[1])
    c = len(a)
    if c != 13:
        output='โปรดใส่เลขผู้เสียภาษีอีกครั้ง(13 หลัก)'
    else:
        data = taxinfocol.find_one({'taxpayerNumber': a, 'branch':b})
        if data == None:
            output = callapi(a,b)
        else:
            info = data.get('taxpayerDetail')
            output = addressformat(info)

            signature = request.headers['X-Line-Signature']
            # get request body as text
            body = request.get_data(as_text=True)
            userLineid = getUserId(body)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "taxpayerid": a }}
            useraction.update_one(myquery,newvalue)
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "actionid": '1' }}
            useraction.update_one(myquery,newvalue)
    return output

#create tax invoice copy
def createtaxinvoicecopy(taxpayerid,car_plate,gastype,total_price):
    global userLineid
    userLineid = ''

    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    useLineid = getUserId(body)
    
    print('1')
    
    taxid = ''
    taxid = str(taxpayerid)
    
    carplate = ''
    carplate = str(car_plate)
    
    gtype = ''
    gtype = str(gastype)
    
    tprice = 0
    tprice = int(total_price)

    gasengname = ''

    priceperunit = 0
    result = products.find_one({'gasType': gtype})
    priceperunit = int(result.get('gasPrice'))
    gasengname = result.get('engName')
    vat = float(tprice/107*7)
    pricewithoutvat = float(tprice-vat)
    totalgasunit = float(tprice/priceperunit)

    data = taxinfocol.find_one({'taxpayerNumber': taxid})
    info = data.get('taxpayerDetail')
            
    companyname = companyName(info)
    companyadd = companyAdd(info)
    branch = 'สำนักงานใหญ่' if info['vBranchNumber'].get('anyType', None)[0] == 0 else 'สาขาย่อย'

    taxinvoicenuber = 0
    num = printOrder.find_one(sort=[("orderid",-1)])
    taxinnum = int(num.get('orderid'))
    taxinvoicenuber = int(taxinnum+1)
    
    now = datetime.datetime.now()
    record_date = now.strftime("%d" + "/" + "%m" + "/" + "%Y")
    thaiprice = ''
    thaiprice = thai_num2text(tprice)
    printtext = ''    
    output = ''
    output = '        ใบเสร็จรับเงิน/ใบกำกับภาษี\n                  สำเนา\nหจก.เดอะวันปิโตเลียม\n9/7 หมู่ 3 ถ.สุขุมวิท ต.ห้วยกะปิ\nอ.เมืองชลบุรี จ.ชลบุรี 20000\nTel. 086-4069062 FAX: 02-9030080 ต่อ 7811\n'
    output = output+'     Tax ID: 0203556007965\n RD NUMBER: E๐๕๒๐๐๐๐๐๒๐๑๐๕๙\nสาขาที่ออกใบกำกับภาษี : สำนักงานใหญ่\nเลขที่: '+str(taxinvoicenuber)+'1\nวันที่: '
    output = output+now.strftime("%d" + "/" + "%m" + "/" + "%Y") + ' ' + now.strftime("%H" + ":" + "%M") + '\nชื่อ: '+companyname+'\nที่อยู่: '+companyadd
    output = output+'\n\nสาขา: '+ branch+'\nเลขประจำตัวผู้เสียภาษีผู้ซื้อ: '+taxid+'\nทะเบียนรถ: '+carplate+'\n\nรายการ ราคา/หน่วย  ปริมาณ  จำนวนเงิน\n=======================\n'
    output = output+ gasengname+'        '+str(round(priceperunit, 2))+'       '+str(round(totalgasunit, 2))+'      '+str(round(pricewithoutvat, 2))+'\n\n                 มูลค่าสินค้า:      '
    output = output+str(round(pricewithoutvat, 2))+'\nภาษีมูลค่าเพิ่ม(VAT 7%):      '+str(round(vat, 2))+'\n                รวมเป็นเงิน:     '+str(round(pricewithoutvat+vat, 0))+'\n           ('
    output = output+thaiprice+'บาทถ้วน)\nได้รับสินค้าตามรายการบนนี้ไว้ถูกต้อง\nและในสภาพเรียบร้อยทุกประการ\n\nลงชื่อผู้รับเงิน__________________\n\n      *****ขอบคุณที่ใช้บริการ*****\n___________________________'
    
    return output

#create tax invoice real
def createtaxinvoice(taxpayerid,car_plate,gastype,total_price):
    global userLineid
    userLineid = ''

    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    useLineid = getUserId(body)
    
    print('1')
    
    taxid = ''
    taxid = str(taxpayerid)
    
    carplate = ''
    carplate = str(car_plate)
    
    gtype = ''
    gtype = str(gastype)
    
    tprice = 0
    tprice = int(total_price)

    gasengname = ''

    priceperunit = 0
    result = products.find_one({'gasType': gtype})
    priceperunit = int(result.get('gasPrice'))
    gasengname = result.get('engName')
    vat = float(tprice/107*7)
    pricewithoutvat = float(tprice-vat)
    totalgasunit = float(tprice/priceperunit)

    data = taxinfocol.find_one({'taxpayerNumber': taxid})
    info = data.get('taxpayerDetail')
            
    companyname = companyName(info)
    companyadd = companyAdd(info)
    branch = 'สำนักงานใหญ่' if info['vBranchNumber'].get('anyType', None)[0] == 0 else 'สาขาย่อย'

    taxinvoicenuber = 0
    num = printOrder.find_one(sort=[("orderid",-1)])
    taxinnum = int(num.get('orderid'))
    taxinvoicenuber = int(taxinnum+1)
    
    now = datetime.datetime.now()
    record_date = now.strftime("%d" + "/" + "%m" + "/" + "%Y")
    thaiprice = ''
    thaiprice = thai_num2text(tprice)
    printtext = ''    
    output = ''
    output = '        ใบเสร็จรับเงิน/ใบกำกับภาษี\n                  ต้นฉบับ\nหจก.เดอะวันปิโตเลียม\n9/7 หมู่ 3 ถ.สุขุมวิท ต.ห้วยกะปิ\nอ.เมืองชลบุรี จ.ชลบุรี 20000\nTel. 086-4069062 FAX: 02-9030080 ต่อ 7811\n'
    output = output+'     Tax ID: 0203556007965\n RD NUMBER: E๐๕๒๐๐๐๐๐๒๐๑๐๕๙\nสาขาที่ออกใบกำกับภาษี : สำนักงานใหญ่\nเลขที่: '+str(taxinvoicenuber)+'1\nวันที่: '
    output = output+now.strftime("%d" + "/" + "%m" + "/" + "%Y") + ' ' + now.strftime("%H" + ":" + "%M") + '\nชื่อ: '+companyname+'\nที่อยู่: '+companyadd
    output = output+'\n\nสาขา: '+ branch+'\nเลขประจำตัวผู้เสียภาษีผู้ซื้อ: '+taxid+'\nทะเบียนรถ: '+carplate+'\n\nรายการ ราคา/หน่วย  ปริมาณ  จำนวนเงิน\n=======================\n'
    output = output+ gasengname+'  '+str(round(priceperunit, 2))+'  '+str(round(totalgasunit, 2))+'  '+str(round(pricewithoutvat, 2))+'\n\nมูลค่าสินค้า:      '
    output = output+str(round(pricewithoutvat, 2))+'\nภาษีมูลค่าเพิ่ม(VAT 7%):   '+str(round(vat, 2))+'\nรวมเป็นเงิน:     '+str(round(pricewithoutvat+vat, 0))+'\n           ('
    output = output+thaiprice+'บาทถ้วน)\nได้รับสินค้าตามรายการบนนี้ไว้ถูกต้อง\nและในสภาพเรียบร้อยทุกประการ\n\nลงชื่อผู้รับเงิน__________________\n\n      *****ขอบคุณที่ใช้บริการ*****\n___________________________'
    
    return output

#order tax invoice
def ordertaxinvoice(inputx):
    global total_price
    global gastype
    global printtext
    total_price = 0
    gastype = ''
    car_plate = ''
    printtext = ''
    
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    
    data = useraction.find_one({'lineid': userLineid})
    taxpayerid = data.get('taxpayerid')
    date = datetime.datetime.now()
    car_plate = data.get('carplate')
    gastype = data.get('gastype')
    total_price = data.get('totalprice')

    taxinvoicenuber = 0
    num = printOrder.find_one(sort=[("orderid",-1)])
    taxinnum = int(num.get('orderid'))
    taxinvoicenuber = int(taxinnum+1)
    
    printtext = createtaxinvoice(taxpayerid,car_plate,gastype,total_price)
    printtextcopy = createtaxinvoicecopy(taxpayerid,car_plate,gastype,total_price)
    
    mydict = { 'orderid': taxinvoicenuber,'lineid': userLineid, 'taxpayerid': taxpayerid, 'carPlate': car_plate, 'productType': gastype, 'total_price': total_price,'date': date, 'status': 'wait','printtext': printtext,'printtextcopy': printtextcopy}
    ins = printOrder.insert_one(mydict)

    output = printtext+'\n\n##ยึนยัน, ย้อนกลับ หรือ ยกเลิก##'

    myquery = { "lineid": userLineid }
    newvalue = { "$set": { "orderid": taxinvoicenuber }}
    useraction.update_one(myquery,newvalue)

    return output

#add totalprice to print action
def addtotalprice(x):
    global output
    output = ''
    x = x.replace(' ','')
    x = x.replace('บาท','')
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})
    if x.isdigit() == True:
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '4' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "totalprice": x }}
        useraction.update_one(myquery,newvalue)

        output = ordertaxinvoice(userLineid)
    else:
        output = 'จำนวนเงินผิดพลาด กรุณากรอกใหม่'
    return output

def printtax():
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)

    orderid = 0
    data = useraction.find_one({'lineid': userLineid})
    orderid = int(data.get('orderid'))

    text = printOrder.find_one({'orderid': orderid})
    mtext = ''
    ctext = ''
    mtext = text.get('printtext')
    ctext = text.get('printtextcopy')

    tempfiles = tempfile.mktemp(".txt")
    receipt = open(tempfiles, "wt", encoding="utf-8")
    receipt.write(mtext)
    os.startfile(tempfiles,'print')

    tempfilesc = tempfile.mktemp(".txt")
    receiptc = open(tempfilesc, "wt", encoding="utf-8")
    receiptc.write(ctext)
    os.startfile(tempfilesc,'print')

#to print or modify tax invoice
def printconfirm(x):
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})
    global output
    global userLineid
    userLineid = ''
    output = ''
    findstr = 'ยืนยัน'
    i = x.find(findstr)
    fixstr = 'แก้ไข'
    f = x.find(fixstr)
    if i == 0:
        body = request.get_data(as_text=True)
        userLineid = getUserId(body)
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '0' }}
        useraction.update_one(myquery,newvalue)
        printtax()
        output = 'ทำการปริ้นเรียบร้อย'
    if f == 0:
        x = x.replace('แก้ไข','')
        carplate = 'ทะเบียน'
        c = x.find(carplate)
        gastype = 'น้ำมัน'
        g = x.find(gastype)
        totalprice = 'ราคา'
        t = x.find(totalprice)
        if c == 0 :
            x = x.replace('ทะเบียน','')
            myquery = { "lineid": userLineid }
            newvalue = { "$set": { "carplate": x }}
            useraction.update_one(myquery,newvalue)
            output = ordertaxinvoice(userLineid)
        if g == 0 :
            x = x.replace(' ','')
            x = x.replace('น้ำมัน','')
            output = fixgastype(x)
        if t == 0 :
            x = x.replace(' ','')
            x = x.replace('ราคา','')
            output = addtotalprice(x)
    return output

# to remember action of user
def userAction(x):
    global output
    output = ''
    global userLineid
    userLineid = ''
    global data
    data = ''
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    data = useraction.find_one({'lineid': userLineid})
    if data == None:
        mydict = { 'lineid': userLineid, 'actionid': '0', 'taxpayerid': '','carplate': '','totalprice': 0,'gastype':'','position':'user', 'orderid': 0 }
        ins = useraction.insert_one(mydict)
        data = useraction.find_one({'lineid': userLineid})
    if data.get('actionid') == '0':
        output = changeorprint(x)
    if data.get('actionid') == '1':
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '2' }}
        useraction.update_one(myquery,newvalue)
        newvalue = { "$set": { "carplate": x }}
        useraction.update_one(myquery,newvalue)
        output = 'เติมน้ำมันอะไรคะ'
    if data.get('actionid') == '2':
        output = addgastype(x)
    if data.get('actionid') == '3':
        output = addtotalprice(x)
    if data.get('actionid') == '4':
        output = printconfirm(x)
    if data.get('actionid') == '5':
        output = fixgasprice(x)
    if output == '':
        output = cancelall()
    return output
    
def rollback():
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)

    data = useraction.find_one({'lineid': userLineid})
    if data.get('actionid') == '0':
        output = 'บอทพร้อมรับคำสั่งใหม่คะ'
    elif data.get('actionid') == '1':
        myquery = { "lineid": userLineid }
        newvalue = { "$set": { "actionid": '0' }}
        useraction.update_one(myquery,newvalue)
        output = 'บอทพร้อมรับคำสั่งใหม่คะ'
    return output

def cancelall():
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    userLineid = getUserId(body)
    myquery = { "lineid": userLineid }
    newvalue = { "$set": { "actionid": '0' }}
    useraction.update_one(myquery,newvalue)
    output = 'บอทพร้อมรับคำสั่งใหม่คะ'
    
    return output

thai_number = ("ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า")
unit = ("", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน")

def unit_process(val):
    length = len(val) > 1
    result = ''

    for index, current in enumerate(map(int, val)):
        if current:
            if index:
                result = unit[index] + result

            if length and current == 1 and index == 0:
                result += 'เอ็ด'
            elif index == 1 and current == 2:
                result = 'ยี่' + result
            elif index != 1 or current != 1:
                result = thai_number[current] + result

    return result

def thai_num2text(number):
    s_number = str(number)[::-1]
    n_list = [s_number[i:i + 6].rstrip("0") for i in range(0, len(s_number), 6)]
    result = unit_process(n_list.pop(0))

    for i in n_list:
        result = unit_process(i) + 'ล้าน' + result

    return result


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    if text == 'profile' :
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='Display name: ' + profile.display_name),
                    TextSendMessage(text='Status message: ' + profile.status_message)
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't use profile API without user ID"))
    elif text == 'bye':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='Leaving group'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='Leaving group'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't leave from 1:1 chat"))
    elif text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageAction(label='Yes', text='Yes!'),
            MessageAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'ยกเลิก':
        result=cancelall()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))
    elif text == 'กลับ':
        result=rollback()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))
    elif text == 'ย้อน':
        result=rollback()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))
    elif text == 'ย้อนกลับ':
        result=rollback()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))
    elif text == 'ราคาน้ำมัน':
        result=gesprice()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))
    else:
        result=userAction(text)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result))


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    print('5')
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '-' + event.message.file_name
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save file.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
    print('8')
    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)
