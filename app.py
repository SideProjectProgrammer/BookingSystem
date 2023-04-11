import os
import pytz
from dateutil import tz
from datetime import datetime, time, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']

# 設定 Service Account Credentials
creds = None
creds_filename = 'credentials.json'

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
def list_upcoming_events():
    # 設定目標時區
    TARGET_TIMEZONE = tz.gettz(os.environ['TIMEZONE'])

    # 取得當前時間
    now = datetime.now(tz=pytz.utc).astimezone(TARGET_TIMEZONE)

    # 設定查詢時間範圍
    start_date = now.date()
    end_date = start_date + timedelta(days=7)

    # 轉換為 UTC 時間
    start_utc = datetime.combine(start_date, time.min).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_utc = datetime.combine(end_date, time.max).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # 使用 Calendar API 取得未來 7 天的預約
    try:
        events_result = calendar_service.events().list(calendarId=CALENDAR_ID, timeMin=start_utc, timeMax=end_utc, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
    except HttpError as error:
        print('Google Calendar API error:', error)
        print(error.content)
        return jsonify({'error': 'Google Calendar API error: %s' % error}), 500

    # 回傳預約資訊
    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.fromisoformat(start).strftime('%H:%M')
        event_list.append({'title': event['summary'], 'start_time': start_time})

    return jsonify({'events': event_list})


if __name__ == '__main__':
    app.run()
