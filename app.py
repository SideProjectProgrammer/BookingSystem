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
        return jsonify({'free_time': []})

    # 計算空閒時間
    busy_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        busy_times.append((datetime.datetime.fromisoformat(start).astimezone(TARGET_TIMEZONE), datetime.datetime.fromisoformat(end).astimezone(TARGET_TIMEZONE)))

    # 排序busy_times以方便計算空閒時間
    busy_times.sort()

    # 計算空閒時間
    free_times = []
    start_time = start_of_day

    # 設定新的時間段
    time_periods = [('08:00', '09:59'), ('10:00', '11:59'), ('14:00', '15:59'), ('16:00', '17:59'), ('19:00', '20:59')]

    # 将时间段转换为 datetime 对象
    time_periods = [(datetime.datetime.strptime(start, '%H:%M'), datetime.datetime.strptime(end, '%H:%M')) for start, end in time_periods]

    for busy_start, busy_end in busy_times:
        # 遍历每个时间段
        for period_start, period_end in time_periods:
            # 將 period_start 和 period_end 轉換為帶有時區資訊的 datetime 物件
            period_start = pytz.timezone(TIMEZONE).localize(period_start)
            period_end = pytz.timezone(TIMEZONE).localize(period_end)

            # 如果該時間段與忙碌時間有重疊，則將該時間段添加到 busy_times 中
            if (busy_start <= period_start <= busy_end) or (busy_start <= period_end <= busy_end):
                busy_times.append((period_start, period_end))

        # 对busy_times进行排序
        busy_times.sort()

        # 计算空闲时间
        for i in range(len(busy_times)-1):
            free_start = busy_times[i][1]
            free_end = busy_times[i+1][0]
            if free_end - free_start >= datetime.timedelta(hours=2):
                free_times.append((free_start, free_end))

    # 回傳空閒時間
    free_time_list = []
    for free_time in free_times:
        free_time_str = '{} - {}'.format(free_time[0].strftime('%H:%M'), free_time[1].strftime('%H:%M'))
        free_time_list.append(free_time_str)

    return jsonify({'free_time': free_time_list})

if __name__ == '__main__':
    app.run()
