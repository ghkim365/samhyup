"""
네이버 플레이스 수요처 크롤러 (최종)
- 스팬 class 기반으로 업체명/카테고리/주소/전화 추출
- Google Sheets company 탭에 중복 제거 후 기록
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

# 수도권 + 키워드 조합
SEARCH_QUERIES = [
    "인천 휀스 시공",
    "인천 메쉬휀스",
    "인천 울타리 설치",
    "인천 견사 제작",
    "인천 개비온",
    "인천 인테리어 철망",
    "김포 휀스 시공",
    "김포 메쉬휀스",
    "김포 울타리 설치",
    "경기 휀스 시공",
    "경기 메쉬휀스",
    "부천 휀스 시공",
    "서울 메쉬휀스",
    "서울 휀스 시공",
    "고양 휀스 시공",
    "수원 휀스 시공",
    "안산 휀스 시공",
]

# 제조사 제외 카테고리/이름 키워드
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
        # 업체명: class="YwYLL"
        name_tag = li.find("span", class_="YwYLL")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        
        # 카테고리: class="YzBgS"
        cat_tag = li.find("span", class_="YzBgS")
        category = cat_tag.get_text(strip=True) if cat_tag else ""
        
        # 주소: class="suKMR"
        addr_tag = li.find("span", class_="suKMR")
        address = addr_tag.get_text(strip=True) if addr_tag else ""
        
        # 전화번호: 텍스트에서 패턴 추출
        li_text = li.get_text(" ")
        phone_match = re.search(r'(0\d{1,2}[-\s]\d{3,4}[-\s]\d{4}|0507-\d{4}-\d{4}|0505-\d{3}-\d{4})', li_text)
        phone = phone_match.group(0) if phone_match else ""
        
        # 필터링
        if any(kw in category for kw in EXCLUDE_CATEGORY):
            continue
        if any(kw in name for kw in EXCLUDE_NAME_KW):
            continue
        
        # 지역 추출
        region = ""
        for city in ["인천", "서울", "김포", "부천", "수원", "고양", "안산", "안양", "성남", "용인", "파주", "의정부"]:
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
    # Google Sheets 연결
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    # 기존 데이터 읽기
    existing_rows = ws.get_all_values()
    # A열(체크): idx 0, B열(연번): idx 1, C열(회사명): idx 2, E열(대표 번호): idx 4
    existing_names = {row[2].strip() for row in existing_rows[1:] if len(row) > 2 and row[2]}
    existing_phones = {row[4].strip() for row in existing_rows[1:] if len(row) > 4 and row[4]}
    
    # 마지막 연번 가져오기
    last_seq = 0
    for row in existing_rows[1:]:
        if len(row) > 1 and row[1].isdigit():
            last_seq = max(last_seq, int(row[1]))
            
    print(f"기존 업체 수: {len(existing_names)}개 (마지막 연번: {last_seq})\n")
    
    all_new = []
    seen_keys = set()
    
    for query in SEARCH_QUERIES:
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
            
            # 새 행 조립 (A열: FALSE, B열: 연번, C열부터 데이터)
            last_seq += 1
            row = [
                "FALSE",      # A열: 체크 (체크박스 비활성화 상태)
                str(last_seq), # B열: 연번
                c["name"],    # C열: 회사명
                query.split(" ", 1)[1] if " " in query else query,  # D열: 주요 사용처/구매목적
                c["phone"],   # E열: 대표 번호
                "",           # F열: 공식 이메일
                "",           # G열: 웹사이트 주소
                c["region"],  # H열: 지역
                c["address"], # I열: 주소
            ]
            all_new.append(row)
            new_count += 1
        
        print(f"{len(companies)}개 발견, {new_count}개 신규")
        time.sleep(1)
    
    if all_new:
        # 데이터가 입력될 때 구글 스프레드시트가 체크박스로 렌더링하도록 
        # append_rows 시 value_input_option='USER_ENTERED' 지정
        ws.append_rows(all_new, value_input_option='USER_ENTERED')
        print(f"\n✅ {len(all_new)}개 신규 업체 시트 기록 완료!")
    else:
        print("\n신규 업체 없음.")
    
    print("\n--- 추가된 업체 목록 ---")
    for r in all_new:
        print(f"  {r[2]} / {r[4]} / {r[8]}")


if __name__ == "__main__":
    main()
