import gspread
from google.oauth2.service_account import Credentials
import sys

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def main():
    print("🚀 구글 스프레드시트 연결 중...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    # 전체 데이터 읽기
    all_rows = ws.get_all_values()
    if not all_rows:
        print("시트가 완전히 비어 있습니다.")
        return
        
    header = all_rows[0]
    data_rows = []
    
    # 회사명이 채워진 실제 유효 데이터만 필터링
    for row in all_rows[1:]:
        if len(row) > 2 and row[2].strip() != "":
            data_rows.append(row)
            
    print(f"발견된 실제 유효 데이터 행 수: {len(data_rows)}개")
    
    if not data_rows:
        print("재정렬할 유효 데이터가 없습니다.")
        return
        
    # 연번(B열) 재시퀀싱 (1부터 시작)
    for idx, row in enumerate(data_rows, start=1):
        if len(row) > 1:
            row[1] = str(idx)
            
    # 시트 전체 초기화
    print("🧹 시트의 불필요한 빈 행 청소 중...")
    ws.clear()
    
    # 헤더 작성
    ws.update("A1:L1", [header])
    
    # 유효 데이터 일괄 기록
    print(f"✍️ {len(data_rows)}개의 데이터를 2행부터 조밀하게 다시 기록 중...")
    ws.append_rows(data_rows, value_input_option='USER_ENTERED')
    
    print("✅ 시트 재정렬 및 연번 재부여 작업이 완전히 완료되었습니다!")

if __name__ == "__main__":
    main()
