import os
import json
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 👇 [수정 완료] 사용자 정보 적용됨
SPREADSHEET_ID = "1qZ7SXlqDY7wkQmJgk93Scr6sV-hXNbV3LA9ETuIgOLI"
WORKSHEET_NAME = "2025 Adobe"
# ==========================================

flask_app = Flask(__name__)

# 환경변수 로드
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = SlackRequestHandler(app)

def get_sheet_data(keyword):
    # 구글 인증 (Render 환경변수에서 가져옴)
    google_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    # 로컬 테스트용 안전장치
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
        
        # [수정된 부분]
        # 1. 검색: 입력한 이름(keyword)이 있는 셀을 찾습니다.
        cell = worksheet.find(keyword)
        
        # 2. 데이터 가져오기: 찾은 행(row)의 C열(3번)과 D열(4번) 값을 읽습니다.
        email = worksheet.cell(cell.row, 3).value    # C열: 계정
        password = worksheet.cell(cell.row, 4).value # D열: 비밀번호
        
        # 3. 결과 합치기: 보기 좋게 줄바꿈(\n)을 넣어 만듭니다.
        answer = f"🆔 계정: {email}\n🔑 비밀번호: {password}"
        return answer

    except gspread.exceptions.WorksheetNotFound:
        return f"오류: '{WORKSHEET_NAME}' 탭을 찾을 수 없습니다. 시트 아래쪽 탭 이름을 확인해주세요."
    except gspread.exceptions.CellNotFound:
        return f"'{keyword}'님에 대한 계정 정보를 찾을 수 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"

# 명령어 설정: /adobe
@app.command("/adobe")
def handle_search_command(ack, respond, command):
    ack()
    keyword = command['text']
    respond(f"🔍 '{keyword}' 검색 중...")
    result = get_sheet_data(keyword)
    respond(f"📢 결과: {result}")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/")
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)