"""
Step 3: 키워드 및 지역 확대 수집 (수정본)
- 검증된 유효 키워드 ("휀스 시공", "메쉬휀스", "울타리 설치")를 사용
- 경기권 전역 주요 지역으로 타겟 범위 대폭 확대
  ("일산", "파주", "화성", "시흥", "평택", "광주", "용인", "안성", "양주", "포천", "남양주", "의정부", "이천", "구리", "하남", "성남")
- Google Sheets 연동 및 중복 방지
"""
import requests
from bs4 import BeautifulSoup
import re, sys, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EXPAND_REGIONS = [
    "일산", "파주", "화성", "시흥", "평택", "광주", 
    "용인", "안성", "양주", "포천", "남양주", "의정부", 
    "이천", "구리", "하남", "성남"
]
EXPAND_QUERIES = ["휀스 시공", "메쉬휀스", "울타리 설치"]

EXCLUDE_CATEGORY = ["금속가공제품제조", "비계,형틀", "철강"]
EXCLUDE_NAME_KW = ["삼협", "동우철망", "대경철망", "연신철강", "흥창스틸", "용접철망제조"]

def search_naver_place(query):
    url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"  [요청 오류] {e}")
        return []
    
    soup = BeautifulSoup(res.text, "html.parser")
    root = soup.find("div", class_="place-app-root")
    if not root:
        return []
    
    lis = root.find_all("li")
    results = []
    
    for li in lis:
        name_tag = li.find("span", class_="YwYLL")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        
        cat_tag = li.find("span", class_="YzBgS")
        category = cat_tag.get_text(strip=True) if cat_tag else ""
        
        addr_tag = li.find("span", class_="suKMR")
        address = addr_tag.get_text(strip=True) if addr_tag else ""
        
        li_text = li.get_text(" ")
        phone_match = re.search(r'(0\d{1,2}[-\s]\d{3,4}[-\s]\d{4}|0507-\d{4}-\d{4}|0505-\d{3}-\d{4})', li_text)
        phone = phone_match.group(0) if phone_match else ""
        
        if any(kw in category for kw in EXCLUDE_CATEGORY):
            continue
        if any(kw in name for kw in EXCLUDE_NAME_KW):
            continue
        
        region = ""
        for city in ["인천", "서울", "김포", "부천", "수원", "고양", "안산", "안양", "성남", "용인", "파주", "의정부", "화성", "시흥", "평택", "광주", "안성", "양주", "포천", "이천", "남양주", "구리", "하남"]:
            if city in address:
                region = city
                break
        
        results.append({
            "name": name,
            "category": category,
            "phone": phone,
            "address": address,
            "region": region,
        })
    
    return results

def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    existing_rows = ws.get_all_values()
    existing_names = {row[2].strip() for row in existing_rows[1:] if len(row) > 2 and row[2]}
    existing_phones = {row[4].strip() for row in existing_rows[1:] if len(row) > 4 and row[4]}
    
    last_seq = 0
    for row in existing_rows[1:]:
        if len(row) > 1 and row[1].isdigit():
            last_seq = max(last_seq, int(row[1]))
            
    print(f"기존 업체 수: {len(existing_names)}개 (마지막 연번: {last_seq})\n")
    
    all_new = []
    seen_keys = set()
    
    for region in EXPAND_REGIONS:
        for kw in EXPAND_QUERIES:
            query = f"{region} {kw}"
            print(f"🔍 {query}", end=" → ")
            companies = search_naver_place(query)
            new_count = 0
            
            for c in companies:
                key = c["phone"] or c["name"]
                if key in seen_keys:
                    continue
                if c["name"] in existing_names:
                    continue
                if c["phone"] and c["phone"] in existing_phones:
                    continue
                
                seen_keys.add(key)
                
                last_seq += 1
                row = [
                    "FALSE",      # A열: 체크
                    str(last_seq), # B열: 연번
                    c["name"],    # C열: 회사명
                    kw,           # D열: 주요 사용처/구매목적
                    c["phone"],   # E열: 대표 번호
                    "",           # F열: 공식 이메일
                    "",           # G열: 웹사이트 주소
                    c["region"] or region, # H열: 지역
                    c["address"], # I열: 주소
                ]
                all_new.append(row)
                new_count += 1
            
            print(f"{len(companies)}개 발견, {new_count}개 신규")
            time.sleep(1)
            
    if all_new:
        ws.append_rows(all_new, value_input_option='USER_ENTERED')
        print(f"\n✅ {len(all_new)}개 신규 확대 업체 시트 기록 완료!")
        
        # step2_clean_data도 새로운 컬럼 구조에 맞게 수정이 필요할 수 있으니 
        # 품질 평가는 이번 단계에서는 데이터 수동 확인을 하므로 생략하거나,
        # 아래 메인 호출 시 정상 작동하는지 확인
        try:
            import step2_clean_data
            print("\n⚙️ 추가된 신규 업체들에 대해 데이터 품질 판별 재평가를 수행합니다...")
            step2_clean_data.main()
        except Exception as e:
            print(f"품질 판별 업데이트 중 오류 발생 (무시 가능): {e}")
    else:
        print("\n신규 확대 업체 없음.")

if __name__ == "__main__":
    main()
