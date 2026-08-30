"""
Step 2: 데이터 정제
- 상호명이 불명확한 행 플래그 (예: '휀스설치', '휀스시공' 등 업종명 그대로인 경우)
- 전화번호 없는 행 플래그
- H열(웹사이트 검증), I열(전화 검증) 이미 있으므로 J열에 '데이터 품질' 기록
  - '✅ 정상': 상호명+전화번호 모두 있음
  - '⚠️ 전화없음': 전화번호 없음
  - '⚠️ 상호불명확': 상호명이 업종명 수준
  - '❌ 제거권장': 둘 다 없음
"""
import gspread
from google.oauth2.service_account import Credentials
import sys, re

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 상호명으로 보기 어려운 패턴 (업종명/지역명만 있는 경우)
VAGUE_NAME_PATTERNS = [
    r'^(휀스|울타리|메쉬|철망|시공|설치|조경|인테리어)(시공|설치|제작|공사|업체)?$',
    r'^(인천|서울|경기|김포|부천|수원|고양|안산|파주|수원)(휀스|울타리|메쉬|철망|시공|설치|조경)?$',
    r'^(휀스|울타리)(시공|설치|공사)$',
]

def is_vague_name(name):
    for pat in VAGUE_NAME_PATTERNS:
        if re.match(pat, name.strip()):
            return True
    return False

def assess_quality(name, phone):
    has_phone = bool(phone and phone.strip())
    is_vague = is_vague_name(name)
    
    if not has_phone and is_vague:
        return "❌ 제거권장"
    elif is_vague:
        return "⚠️ 상호불명확"
    elif not has_phone:
        return "⚠️ 전화없음"
    else:
        return "✅ 정상"

def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    all_rows = ws.get_all_values()
    data_rows = all_rows[1:]
    
    # L1 헤더 추가 (A열과 B열 추가로 데이터 품질 열은 J에서 L로 변경됨)
    ws.update(values=[["데이터 품질"]], range_name="L1")
    
    quality_values = []
    stats = {"✅ 정상": 0, "⚠️ 상호불명확": 0, "⚠️ 전화없음": 0, "❌ 제거권장": 0}
    
    print(f"{'Row':<5} {'품질':<12} {'회사명':<25} {'전화'}")
    print("-" * 65)
    
    for i, row in enumerate(data_rows):
        name = row[2].strip() if len(row) > 2 else ""  # Column C (회사명)
        phone = row[4].strip() if len(row) > 4 else "" # Column E (대표 번호)
        
        quality = assess_quality(name, phone)
        quality_values.append([quality])
        stats[quality] += 1
        
        if quality != "✅ 정상":
            print(f"{i+2:<5} {quality:<12} {name:<25} {phone}")
    
    # L2 이하에 품질 기록
    ws.update(values=quality_values, range_name=f"L2:L{1+len(quality_values)}")
    
    print(f"\n📊 품질 통계:")
    for k, v in stats.items():
        print(f"  {k}: {v}개")
    print(f"\n✅ L열 데이터 품질 기록 완료 (총 {len(data_rows)}개)")

if __name__ == "__main__":
    main()
