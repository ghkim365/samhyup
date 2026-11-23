# -*- coding: utf-8 -*-
"""
삼협철망 company 시트 팩스 대상 업체들을 9개 회차(팩스1일 ~ 팩스9일)로 14개사씩 분할 지정하는 스크립트
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

SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    print("=== [삼협철망 팩스 9개 회차(팩스1일~9일) 14개사 단위 분할 지정] ===")
    
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    rows = ws.get_all_values()
    if not rows:
        print("❌ 시트 데이터를 로드하지 못했습니다.")
        return

    # T열(19): 팩스번호, U열(20): 영업채널, M열(12): 발송대기
    fax_rows = []
    for idx, r in enumerate(rows[1:], start=2):
        t_fax  = r[19].strip() if len(r) > 19 else ""
        u_chan = r[20].strip() if len(r) > 20 else ""
        m_wait = r[12].strip() if len(r) > 12 else ""

        # 팩스번호가 있고 영업채널이 '팩스'이거나 메일 미성공인 대상
        if t_fax and u_chan == "팩스":
            fax_rows.append(idx)
        elif t_fax and m_wait.startswith("팩스"):
            fax_rows.append(idx)

    print(f"📊 총 팩스 대상 업체 수: {len(fax_rows)}곳")

    if not fax_rows:
        print("⚠️ 팩스 대상 업체를 찾지 못했습니다.")
        return

    updates = []
    batch_size = 14
    for i, row_idx in enumerate(fax_rows):
        batch_num = (i // batch_size) + 1
        if batch_num > 9:
            batch_num = 9  # 남은 물량 9차로 통합
        m_val = f"팩스{batch_num}일"
        updates.append({'range': f'M{row_idx}', 'values': [[m_val]]})
        updates.append({'range': f'U{row_idx}', 'values': [['팩스']]})

    if updates:
        ws.batch_update(updates)
        print(f"✅ {len(fax_rows)}개 업체에 대한 M열 9개 회차(팩스1일~팩스9일) 분할 지정 완료!")

if __name__ == '__main__':
    main()
