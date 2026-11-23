# -*- coding: utf-8 -*-
"""
삼협철망 company 워크시트 M열(발송대기) '팩스1일' ~ '팩스9일' 데이터를 추출하여
샌드랩스(SendLabs) 대량 팩스 접수용 9개 회차 엑셀(.xlsx) 및 CSV(.csv) 파일 일괄 생성 스크립트
저장 위치: D:\Antigravity\builder-samhyup-sales\sales\fax\
"""
import sys
import os
import csv
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

OUTPUT_DIR = r"D:\Antigravity\builder-samhyup-sales\sales\fax"

BATCH_CONFIG = [
    (1, "팩스1일", "20261006", "10/06(화) 1차"),
    (2, "팩스2일", "20261012", "10/12(월) 2차"),
    (3, "팩스3일", "20261019", "10/19(월) 3차"),
    (4, "팩스4일", "20261026", "10/26(월) 4차"),
    (5, "팩스5일", "20261102", "11/02(월) 5차"),
    (6, "팩스6일", "20261109", "11/09(월) 6차"),
    (7, "팩스7일", "20261116", "11/16(월) 7차"),
    (8, "팩스8일", "20261123", "11/23(월) 8차"),
    (9, "팩스9일", "20261130", "11/30(월) 9차 완결"),
]

def main():
    print("=== [삼협철망 샌드랩스 대량 팩스 접수용 1~9차 전 회차 파일 일괄 추출] ===")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    rows = ws.get_all_values()
    if not rows:
        print("❌ 시트 데이터를 로드하지 못했습니다.")
        return

    # B열(인덱스 1): 연번
    # C열(인덱스 2): 회사명
    # I열(인덱스 8): 주소
    # M열(인덱스 12): 발송대기
    # T열(인덱스 19): 팩스번호
    # U열(인덱스 20): 영업채널

    header = ["연번", "회사명", "팩스번호", "주소", "발송대기", "영업채널"]
    
    has_openpyxl = False
    try:
        import openpyxl
        has_openpyxl = True
    except ImportError:
        pass

    total_created_files = 0

    for b_num, m_target, date_str, label in BATCH_CONFIG:
        batch_data = []
        
        for idx, r in enumerate(rows[1:], start=2):
            m_round   = r[12].strip() if len(r) > 12 else ""
            t_fax     = r[19].strip() if len(r) > 19 else ""
            
            if m_round == m_target and t_fax:
                seq_num   = r[1].strip() if len(r) > 1 else str(idx)
                c_name    = r[2].strip() if len(r) > 2 else ""
                address   = r[8].strip() if len(r) > 8 else ""
                u_channel = r[20].strip() if len(r) > 20 else ""
                
                batch_data.append([seq_num, c_name, t_fax, address, m_round, u_channel])

        print(f"📊 [{m_target} ({label})] 추출된 대상 업체 수: {len(batch_data)}곳")

        if not batch_data:
            print(f"⚠️ [{m_target}] 업체를 찾지 못해 건너뜁니다.")
            continue

        base_filename = f"samhyup_sendlabs_fax_batch{b_num}_{date_str}"

        # 1. CSV 저장
        csv_path = os.path.join(OUTPUT_DIR, f"{base_filename}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(batch_data)
        total_created_files += 1

        # 2. XLSX 엑셀 저장
        if has_openpyxl:
            wb = openpyxl.Workbook()
            ws_out = wb.active
            ws_out.title = f"{m_target}_{len(batch_data)}개사"
            ws_out.append(header)
            for row in batch_data:
                ws_out.append(row)
            
            xlsx_path = os.path.join(OUTPUT_DIR, f"{base_filename}.xlsx")
            wb.save(xlsx_path)
            total_created_files += 1

    print(f"\n✅ 전 회차(1~9차) 샌드랩스 접수 전용 파일 총 {total_created_files}개 생성 완료!")
    print(f"📁 저장 폴더: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
