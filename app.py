import os
from datetime import datetime, time, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from flask import Flask, jsonify

app = Flask(__name__)

# 從環境變數中讀取 Google 相關變數
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_EMAIL = os.environ['SERVICE_ACCOUNT_EMAIL']
SERVICE_ACCOUNT_KEY = os.environ['SERVICE_ACCOUNT_KEY'].replace('\\n', '\n')
CALENDAR_ID = os.environ['CALENDAR_ID']
TIMEZONE = os.environ['TIMEZONE']

print('CALENDAR_ID:', os.environ['CALENDAR_ID'])
print('TIMEZONE:', os.environ['TIMEZONE'])

print('SERVICE_ACCOUNT_EMAIL:', os.environ['SERVICE_ACCOUNT_EMAIL'])
print('SERVICE_ACCOUNT_KEY:', os.environ['SERVICE_ACCOUNT_KEY'])
print('CALENDAR_ID:', os.environ['CALENDAR_ID'])
print('TIMEZONE:', os.environ['TIMEZONE'])
print('PROJECT_ID:', os.environ['PROJECT_ID'])
print('PRIVATE_KEY_ID:', os.environ['PRIVATE_KEY_ID'])
print('CLIENT_ID:', os.environ['CLIENT_ID'])
print('AUTH_URI:', os.environ['AUTH_URI'])
print('TOKEN_URI:', os.environ['TOKEN_URI'])
print('AUTH_PROVIDER_X509_CERT_URL:', os.environ['AUTH_PROVIDER_X509_CERT_URL'])
print('CLIENT_X509_CERT_URL:', os.environ['CLIENT_X509_CERT_URL'])

# 設定 Service Account Credentials
creds = Credentials.from_service_account_info({
    "type": "service_account",
    "project_id": os.environ['PROJECT_ID'],
    "private_key_id": os.environ['PRIVATE_KEY_ID'],
    "private_key": SERVICE_ACCOUNT_KEY,
    "client_email": SERVICE_ACCOUNT_EMAIL,
    "client_id": os.environ['CLIENT_ID'],
    "auth_uri": os.environ['AUTH_URI'],
    "token_uri": os.environ['TOKEN_URI'],
    "auth_provider_x509_cert_url": os.environ['AUTH_PROVIDER_X509_CERT_URL'],
    "client_x509_cert_url": os.environ['CLIENT_X509_CERT_URL']
}, scopes=SCOPES)

# 設定 Calendar API client
calendar_service = build('calendar', 'v3', credentials=creds)


@app.route('/')
def list_todays_events():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run()
