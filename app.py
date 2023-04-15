import os
import pytz
import datetime
from dateutil import tz
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify
import json
import sys

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']
##CALENDAR_ID = 'chang.yu.chao@gmail.com'
##TIMEZONE = 'Asia/Taipei'

# 設定 Service Account Credentials
creds = None
creds_filename = 'service_credentials.json'

if os.path.exists(creds_filename):
    with open(creds_filename, 'r') as f:
        creds_info = json.load(f)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

if creds is None:
    print('No credentials found. Exiting...')
    exit()

# 設定 Calendar API client
calendar_service = build('calendar', 'v3', credentials=creds)


@app.route('/')
def list_todays_events():
    # 設定目標時區
    TARGET_TIMEZONE = tz.gettz(TIMEZONE)

    # 取得當前時間
    now = datetime.datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(TARGET_TIMEZONE)

    # 設定今天早上 8 點的 TARGET_TIMEZONE 時間
    start_of_day = now.replace(hour=8, minute=0, second=0, microsecond=0)

    # 設定今天晚上 10 點的 TARGET_TIMEZONE 時間
    end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0)

    # 取得今天的事件
    events_result = calendar_service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    

    # 計算忙碌時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    free_time_list = [
        {'time_slot': '08:00 - 09:59', 'free': True},
        {'time_slot': '10:00 - 11:59', 'free': True},
        {'time_slot': '14:00 - 15:59', 'free': True},
        {'time_slot': '16:00 - 17:59', 'free': True},
        {'time_slot': '19:00 - 20:59', 'free': True}
    ]

    cal_time = []
    
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_time = datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE).time()
        end_time = datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE).time()
        for free_time in free_time_list:
            cal_time.append(datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE).time().strftime(("%H:%M:%S")))
            cal_time.append(datetime.datetime.strptime(free_time['time_slot'].split(' - ')[0], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE).strftime(("%H:%M:%S")))
            cal_time.append(datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE).time().strftime(("%H:%M:%S")))
            cal_time.append(datetime.datetime.strptime(free_time['time_slot'].split(' - ')[1], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE).strftime(("%H:%M:%S")))
            if not (start_time < datetime.datetime.strptime(free_time['time_slot'].split(' - ')[0], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE) and end_time < datetime.datetime.strptime(free_time['time_slot'].split(' - ')[1], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE)) and not (start_time > datetime.datetime.strptime(free_time['time_slot'].split(' - ')[0], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE) and end_time > datetime.datetime.strptime(free_time['time_slot'].split(' - ')[1], '%H:%M').time().replace(tzinfo=TARGET_TIMEZONE)):
                free_time['free'] = False
            cal_time.append(free_time['free'])
            cal_time.append("===")

    free_time_list = [free_time['time_slot'] for free_time in free_time_list if free_time['free']]

    # 遍歷free_time_list並將時間顯示方式改為12小時制
    for i in range(len(free_time_list)):
        time_range = free_time_list[i]
        start_time, end_time = time_range.split(" - ")
        start_time_12hr = convert_time_12hr(start_time)
        end_time_12hr = convert_time_12hr(end_time)
        free_time_list[i] = f"{start_time_12hr} - {end_time_12hr}"


##    return jsonify({'free_time': free_time_list,'start_of_day':[start_of_day],'end_of_day':[end_of_day],'events':[events],'busy_times':[busy_times],'now':[now],'cal_time':cal_time})
    return jsonify({'free_time': free_time_list})

# 將24小時制的時間轉換成12小時制
def convert_time_12hr(time_str):
    time_obj = datetime.datetime.strptime(time_str, '%H:%M')
    return time_obj.strftime("%I:%M %p")

##    time_obj = datetime.datetime.strptime(time_str, "%H:%M")
##    time_str_12h = datetime.datetime.strftime(time_obj, "%p %I:%M")
##    time_str_cn = time_str_12h.replace("AM", u"早上").replace("PM", u"下午")
##    return time_str_cn

if __name__ == '__main__':
    app.run(debug=True)
