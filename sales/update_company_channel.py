# -*- coding: utf-8 -*-
"""
삼협철망 company 시트 영업채널(U열) 및 발송대기(M열) 자동 업데이트 스크립트
N열(발송상태) = '성공' -> U열 '메일', M열 '메일 정기'
N열(발송상태) = '실패'/'반송' -> U열 '팩스', M열 '팩스1일' (T열 팩스번호 존재 시)
"""
import sys
import os
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATHS = [
    r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json",
    r"D:\Antigravity\credentials\ghkim\ghkim_credentials.json"
]
CREDS_PATH = next((p for p in CREDS_PATHS if os.path.exists(p)), CREDS_PATHS[0])

# 삼협철망 데이터 구글 스프레드시트 ID
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    print("=== [삼협철망 company 시트 영업채널(U열) & 발송대기(M열) 동기화] ===")
    
    if not os.path.exists(CREDS_PATH):
        print(f"❌ 인증서 파일이 없습니다: {CREDS_PATH}")
        return

    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")

    rows = ws.get_all_values()
    if not rows:
        print("❌ 시트 데이터를 불러오지 못했습니다.")
        return

    headers = rows[0]
    print(f"헤더 개수: {len(headers)}, 총 행 수: {len(rows)-1}")

    # Column Mapping:
    # M (index 12): 발송대기
    # N (index 13): 발송상태
    # T (index 19): 팩스
    # U (index 20): 영업채널

    updates = []
    mail_success_count = 0
    fax_pivot_count = 0

    for idx, r in enumerate(rows[1:], start=2):
        m_wait   = r[12].strip() if len(r) > 12 else ""
        n_status = r[13].strip() if len(r) > 13 else ""
        t_fax    = r[19].strip() if len(r) > 19 else ""
        u_chan   = r[20].strip() if len(r) > 20 else ""

        if n_status == "성공":
            if u_chan != "메일" or m_wait != "메일 정기":
                updates.append({'range': f'U{idx}', 'values': [['메일']]})
                updates.append({'range': f'M{idx}', 'values': [['메일 정기']]})
                mail_success_count += 1

        elif n_status in ["실패", "반송"] and t_fax:
            if u_chan != "팩스" or not m_wait.startswith("팩스"):
                updates.append({'range': f'U{idx}', 'values': [['팩스']]})
                updates.append({'range': f'M{idx}', 'values': [['팩스1일']]})
                fax_pivot_count += 1

    print(f"📊 메일 성공 업데이트: {mail_success_count}건, 팩스 전환 업데이트: {fax_pivot_count}건")

    if updates:
        ws.batch_update(updates)
        print("✅ 구글 스프레드시트 company 시트 U열/M열 동기화 완료!")
    else:
        print("ℹ️ 이미 최신 상태로 반영되어 있습니다.")

if __name__ == '__main__':
    main()
