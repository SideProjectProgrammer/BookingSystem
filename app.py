import os
import pytz
import datetime
from dateutil import tz
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify
import json

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']

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
    TARGET_TIMEZONE = tz.gettz(os.environ['TIMEZONE'])

    # 取得當前時間
    now = datetime.datetime.utcnow()

    # 設定今天早上 8 點的 UTC 時間
    start_of_day = now.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    # 設定今天晚上 10 點的 UTC 時間
    end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)

    # 取得今天的事件
    events_result = calendar_service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        # 如果沒有任何事件發生，直接回傳五個預設時間區間
        return jsonify({'free_time': ['08:00 - 09:59', '10:00 - 11:59', '14:00 - 15:59', '16:00 - 17:59', '19:00 - 20:59']})

    # 計算忙碌時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    free_times = []
    # 檢查五個時間區間是否有事件發生
    time_ranges = [
        (datetime.time(8, 0), datetime.time(10, 0)),
        (datetime.time(10, 0), datetime.time(12, 0)),
        (datetime.time(14, 0), datetime.time(16, 0)),
        (datetime.time(16, 0), datetime.time(18, 0)),
        (datetime.time(19, 0), datetime.time(21, 0))
    ]
    for time_range in time_ranges:
        start_time = datetime.datetime.combine(start_of_day, time_range[0]).astimezone(TARGET_TIMEZONE)
        end_time = datetime.datetime.combine(start_of_day, time_range[1]).astimezone(TARGET_TIMEZONE)
        is_busy = False
        for busy_time in busy_times:
            if busy_time[0] < end_time and start_time < busy_time[1]:
                is_busy = True
                break
        if not is_busy:
            free_times.append((start_time, end_time))
            
    # 將空閒時間轉換成格式化字串
    free_time_list = [f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}" for start, end in free_times]

    return jsonify({'free_time': free_time_list})

if __name__ == '__main__':
    app.run()
