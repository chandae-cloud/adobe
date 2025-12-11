import os
import json
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- [설정] ---
SPREADSHEET_ID = "1qZ7SXlqDY7wkQmJgk93Scr6sV-hXNbV3LA9ETuIgOLI"
WORKSHEET_NAME = "2025 Adobe"
# -------------

flask_app = Flask(__name__)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = SlackRequestHandler(app)

def get_sheet_data(keyword):
    # 구글 인증 로드
    google_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not google_json and os.path.exists('credentials.json'):
        with open('credentials.json', 'r', encoding='utf-8') as f:
            creds_dict = json.load(f)
    else:
        creds_dict = json.loads(google_json)
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        
        # 1. G열 등 시트 전체에서 '이름' 검색
        cell = worksheet.find(keyword)
        
        # 2. 찾은 행의 C열(3번째), D열(4번째) 가져오기
        email = worksheet.cell(cell.row, 3).value    # C열
        password = worksheet.cell(cell.row, 4).value # D열
        
        return f"👤 이름: {keyword}\n🆔 계정: {email}\n🔑 비밀번호: {password}"

    except gspread.exceptions.WorksheetNotFound:
        return "오류: 시트 탭 이름을 찾을 수 없습니다."
    except gspread.exceptions.CellNotFound:
        return f"😢 '{keyword}'님을 명단에서 찾을 수 없습니다."
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"

# 명령어: /adobe
@app.command("/adobe")
def handle_search_command(ack, respond, command):
    ack()
    keyword = command['text']
    if not keyword:
        respond("이름을 입력해주세요. (예: /adobe 김영규)")
        return
    respond(f"🔍 '{keyword}' 검색 중...")
    result = get_sheet_data(keyword)
    respond(f"📢 결과:\n{result}")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/")
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)