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
        # 如果沒有任何事件發生，直接回傳空的 free_time_list
        return jsonify({'free_time': ['08:00 - 09:59', '10:00 - 11:59', '14:00 - 15:59', '16:00 - 17:59', '19:00 - 20:59']})

    # 計算空閒時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    # 計算空閒時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    free_times = []
    # 檢查第一個事件是否從早上 8 點之前開始，如果是，就計算從早上 8 點開始到第一個事件開始之間的空閒時間
    if busy_times[0][0] > start_of_day:
        free_times.append((start_of_day, busy_times[0][0]))

    # 檢查其他事件之間的空閒時間
    for i in range(len(busy_times) - 1):
        if busy_times[i+1][0] > busy_times[i][1]:
            free_times.append((busy_times[i][1], busy_times[i+1][0]))

    # 檢查最後一個事件是否在晚上 10 點之前結束，如果是，就計算從最後一個事件結束到晚上 10 點之間的空閒時間
    if busy_times[-1][1] < end_of_day:
        free_times.append((busy_times[-1][1], end_of_day))

    # 將空閒時間轉換成格式化字串
    free_time_list = [f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}" for start, end in free_times]

    return jsonify({'free_time': free_time_list})

if __name__ == '__main__':
    app.run()
