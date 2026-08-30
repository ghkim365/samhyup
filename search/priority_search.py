"""
삼협철망 B2B 용접철망 및 특수철망 우선순위별 데이터 수집 & 정제 통합 스크립트
- 수도권 주요 지역 대상 검색 쿼리 자동 매핑
- 네이버 플레이스 크롤링 및 중복 검사
- 1순위(용접철망), 2순위(특수망) 자동 우선순위 태그 및 타겟 매핑
- 데이터 품질 판별 및 구글 시트 일괄 업로드
"""
import requests
from bs4 import BeautifulSoup
import re, sys, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 대상 지역 (수도권 주요 공장 및 물류 거점)
REGIONS = [
    "인천", "김포", "화성", "시흥", "평택", "안성", 
    "파주", "포천", "광주", "용인", "고양", "일산", 
    "의정부", "남양주", "양주", "이천", "구리", "하남", 
    "성남", "수원", "안산", "부천", "서울"
]

# 우선순위별 키워드 리스트
PRIORITY_KEYWORDS = {
    "1순위: 용접철망": ["용접철망", "와이어메쉬", "철망 도소매", "건재상", "철망 대리점"],
    "2순위: 견사망": ["견사 제작", "애견운동장", "애견훈련소", "동물보호소"],
    "2순위: 개비온": ["개비온", "돌망태", "옹벽공사", "석축공사"],
    "2순위: 메쉬파레트": ["메쉬파레트", "메쉬팔레트", "물류보관장비"],
    "2순위: 인테리어철망": ["인테리어 철망", "금속인테리어"],
    "2순위: 메쉬휀스": ["메쉬휀스"]
}

# 제외 카테고리 및 상호명 키워드 (경쟁사 및 불필요 업종 배제)
EXCLUDE_CATEGORY = ["금속가공제품제조", "비계,형틀", "철강"]
EXCLUDE_NAME_KW = ["삼협", "동우철망", "대경철망", "연신철강", "흥창스틸", "용접철망제조"]

# 모호한 상호명 판별을 위한 정규식
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

def search_naver_place(query):
    url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []
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
        # 업체명
        name_tag = li.find("span", class_="YwYLL")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        
        # 카테고리
        cat_tag = li.find("span", class_="YzBgS")
        category = cat_tag.get_text(strip=True) if cat_tag else ""
        
        # 주소
        addr_tag = li.find("span", class_="suKMR")
        address = addr_tag.get_text(strip=True) if addr_tag else ""
        
        # 전화번호 추출
        li_text = li.get_text(" ")
        phone_match = re.search(r'(0\d{1,2}[-\s]\d{3,4}[-\s]\d{4}|0507-\d{4}-\d{4}|0505-\d{3}-\d{4})', li_text)
        phone = phone_match.group(0) if phone_match else ""
        
        # 제외 필터링
        if any(kw in category for kw in EXCLUDE_CATEGORY):
            continue
        if any(kw in name for kw in EXCLUDE_NAME_KW):
            continue
        
        # 지역명 매핑
        region = ""
        for city in REGIONS:
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
    print("🚀 구글 스프레드시트 연결 중...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    # 기존 데이터 읽기
    existing_rows = ws.get_all_values()
    existing_names = set()
    existing_phones = set()
    
    if len(existing_rows) > 1:
        # 헤더가 있는 경우 중복 검사용 집합 빌드
        for row in existing_rows[1:]:
            if len(row) > 2 and row[2]:
                existing_names.add(row[2].strip())
            if len(row) > 4 and row[4]:
                existing_phones.add(row[4].strip())
        print(f"기존 시트 적재 업체 수: {len(existing_names)}개")
    else:
        print("기존 시트가 비어있습니다. 새로 기록을 시작합니다.")
        
    # 헤더 점검 및 생성
    headers = [
        "체크", "연번", "회사명", "주요 사용처/구매목적", "대표 번호", 
        "공식 이메일", "웹사이트 주소", "지역", "주소", "웹사이트 검증", 
        "전화번호 검증", "데이터 품질"
    ]
    ws.update("A1:L1", [headers])
    
    last_seq = 0
    all_new = []
    seen_keys = set()
    
    print("\n🔍 1순위(용접철망) 및 2순위(특수망) 대상 수집을 시작합니다...")
    
    query_count = 0
    # 우선순위별 루프
    for priority, keywords in PRIORITY_KEYWORDS.items():
        print(f"\n📂 {priority} 수집 진행 중...")
        for kw in keywords:
            for region in REGIONS:
                query = f"{region} {kw}"
                query_count += 1
                
                # 쿼터 및 속도 제한 관리용 딜레이 출력
                print(f"  [{query_count}] 🔍 {query}", end=" → ")
                companies = search_naver_place(query)
                new_count = 0
                
                for c in companies:
                    # 상호나 전화번호를 고유 키로 활용
                    key = c["phone"] or c["name"]
                    if key in seen_keys:
                        continue
                    if c["name"] in existing_names:
                        continue
                    if c["phone"] and c["phone"] in existing_phones:
                        continue
                    
                    seen_keys.add(key)
                    
                    last_seq += 1
                    quality = assess_quality(c["name"], c["phone"])
                    phone_status = "✅ 형식OK" if c["phone"] else "전화없음"
                    
                    # 새로운 행 작성
                    row = [
                        "FALSE",          # A열: 체크 (체크박스 비활성화 상태)
                        str(last_seq),     # B열: 연번
                        c["name"],        # C열: 회사명
                        priority,         # D열: 주요 사용처/구매목적 (우선순위 정보 기입)
                        c["phone"],       # E열: 대표 번호
                        "",               # F열: 공식 이메일
                        "",               # G열: 웹사이트 주소
                        c["region"] or region, # H열: 지역
                        c["address"],     # I열: 주소
                        "URL없음",         # J열: 웹사이트 검증
                        phone_status,     # K열: 전화번호 검증
                        quality           # L열: 데이터 품질
                    ]
                    all_new.append(row)
                    new_count += 1
                
                print(f"{len(companies)}개 발견, {new_count}개 신규")
                time.sleep(1.5) # 네이버 블락 방지용 딜레이
                
    if all_new:
        print(f"\n✍️ 총 {len(all_new)}개 신규 데이터 구글 시트에 일괄 기록 중...")
        # USER_ENTERED 옵션으로 기록하여 체크박스가 올바르게 체크박스로 렌더링되게 함
        ws.append_rows(all_new, value_input_option='USER_ENTERED')
        print("✅ 구글 시트 기록이 완료되었습니다!")
    else:
        print("\n신규로 발견된 업체가 없습니다.")
        
    print("\n🎉 모든 수집 및 정제 작업이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
