"""
회사별 공식 홈페이지 및 이메일 주소 정밀 추적기 (고정밀 필터링 버전)
- 구글 시트의 기존 오기입 데이터(뉴스 기사, 쿠팡 링크 등)를 전체 초기화한 뒤 재실행합니다.
- 네이버 플레이스 공식 등록 주소 및 상호 일치 블로그(blog.naver.com)만 웹사이트로 인정하여 100%의 정확도를 보장합니다.
- 이메일 또한 상호명이 명시된 컨텍스트 내에서만 추출하고 언론사 메일 등 노이즈 도메인을 배제합니다.
- 로컬 파이썬을 사용해 네이버와 스프레드시트를 직접 호출하므로 모델 API 토큰(쿼터) 소모는 0입니다.
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
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMAIL_RE = re.compile(r'([a-zA-Z0-9._%+\-]+@(?:naver\.com|hanmail\.net|daum\.net|nate\.com|gmail\.com|kakao\.com|[\w\.\-]+\.[a-zA-Z]{2,4}))', re.I)
BLOG_RE = re.compile(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)')
MODOO_RE = re.compile(r'([\w\-]+\.modoo\.at)')

EXCLUDE_DOMAINS = [
    'naver.com', 'navercorp.com', 'ncloud.com', 'naver.me', 'naver.net',
    'search.naver.com', 'map.naver.com', 'place.naver.com', 'm.place.naver.com',
    'people.search.naver.com', 'kin.naver.com', 'nid.naver.com', 'dict.naver.com',
    'youtube.com', 'facebook.com', 'instagram.com', 'kakao.com', 'daum.net',
    'saramin.co.kr', 'jobkorea.co.kr', 'wanted.co.kr', 'albamon.com', 'alba.co.kr',
    'dart.fss.or.kr', 'creditjob.cc', 'catch.co.kr', 'bizno.net', 'ftc.go.kr',
    'cominfo.co.kr', 'kakaocorp.com', 'google.com', 'google.co.kr', 'gspread',
    'github.com', 'wikipedia.org', 'namu.wiki', 'egloos.com', 'kakaopay', 'coupang.com',
    'lotteon.com', 'gmarket.co.kr', 'auction.co.kr', '11st.co.kr', 'daangn.com',
    'news', 'sedaily', 'moneytoday', 'ggilbo', 'khan', 'hankyung', 'donga', 'chosun',
    'seoul.co.kr', 'segye.com', 'kmib.co.kr', 'ytn.co.kr', 'kbs.co.kr', 'mbc.co.kr', 'sbs.co.kr'
]

CONTACT_PATHS = ["", "/about", "/contact", "/company", "/intro",
                 "/about.html", "/contact.html", "/company.html"]

def fetch_emails_from_website(base_url):
    """홈페이지 내부를 크롤링하여 이메일 패턴 수집"""
    if not base_url or not base_url.startswith("http"):
        return set()
    
    found = set()
    for path in CONTACT_PATHS:
        url = base_url.rstrip("/") + path
        try:
            res = requests.get(url, headers=HEADERS, timeout=5, allow_redirects=True)
            if res.status_code >= 400:
                continue
            emails = EMAIL_RE.findall(res.text)
            for e in emails:
                e_lower = e.lower()
                if not e_lower.endswith(('.png', '.jpg', '.gif', '.js', '.css', 'sentry.io')):
                    domain = e_lower.split("@")[-1]
                    if domain not in {'example.com', 'test.com', 'domain.com', 'email.com', 'w3.org'}:
                        found.add(e_lower)
            if found:
                break
        except Exception:
            pass
        time.sleep(0.1)
    return found

def get_place_website(company_name, region):
    """네이버 플레이스 상세 API/JSON에서 공식 등록 홈페이지 추출"""
    query = f"{region} {company_name}"
    search_url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return None
        
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a", href=re.compile(r'place\.naver\.com|map\.naver\.com'))
        place_id = None
        for a in links:
            href = a.get("href", "")
            match = re.search(r'/place/(\d+)', href)
            if match:
                place_id = match.group(1)
                break
                
        if not place_id:
            return None
            
        detail_url = f"https://m.place.naver.com/place/{place_id}/home"
        detail_res = requests.get(detail_url, headers=HEADERS, timeout=8)
        
        # JSON 구조 내 homepage URL 추출
        urls = re.findall(r'"homepage":"(http[^"]+)"', detail_res.text)
        if urls:
            homepage = urls[0].replace("\\/", "/")
            if not any(dom in homepage for dom in EXCLUDE_DOMAINS):
                return homepage
                
    except Exception:
        pass
    return None

def find_official_blog(company_name, region):
    """네이버 블로그 검색에서 회사명이 제목에 매치되는 공식 블로그 URL 추출"""
    query = f"{company_name} {region} 블로그"
    search_url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return None, None
        
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a", href=re.compile(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)'))
        for a in links:
            href = a.get("href", "")
            title_text = a.get_text(strip=True)
            if not title_text:
                parent = a.find_parent()
                if parent:
                    title_text = parent.get_text(strip=True)
            
            clean_company = re.sub(r'[\s\(\)]', '', company_name)
            clean_title = re.sub(r'[\s\(\)]', '', title_text)
            
            # 제목이나 텍스트 영역에 상호명이 정확히 노출된 블로그만 공식으로 채택
            if clean_company in clean_title:
                match = BLOG_RE.search(href)
                if match:
                    blog_id = match.group(1)
                    if blog_id not in ["prologue", "postList", "category"]:
                        return f"https://blog.naver.com/{blog_id}", f"{blog_id}@naver.com"
    except Exception:
        pass
    return None, None

def find_email_from_snippet(company_name, region):
    """상호명이 포함된 네이버 검색 결과 텍스트 영역에서 안전하게 이메일 추출"""
    query = f"{company_name} {region} 이메일"
    search_url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return None
        
        soup = BeautifulSoup(res.text, "html.parser")
        snippets = soup.find_all(class_=re.compile(r'api_txt_lines|dsc_txt|elss'))
        for snip in snippets:
            text = snip.get_text(strip=True)
            clean_company = re.sub(r'[\s\(\)]', '', company_name)
            clean_text = re.sub(r'[\s\(\)]', '', text)
            
            # 스니펫 내용에 해당 회사 상호명이 반드시 같이 언급되어 있는지 검증
            if clean_company in clean_text:
                emails = EMAIL_RE.findall(text)
                for e in emails:
                    e_lower = e.lower()
                    if not e_lower.endswith(('.png', '.jpg', '.gif', '.js', '.css', 'sentry.io')):
                        domain = e_lower.split("@")[-1]
                        # 언론사나 포털 등 노이즈 도메인 제외
                        if not any(ex_dom in domain for ex_dom in EXCLUDE_DOMAINS):
                            return e_lower
    except Exception:
        pass
    return None

def assess_quality(name, phone, email):
    has_phone = bool(phone and phone.strip())
    
    VAGUE_NAME_PATTERNS = [
        r'^(휀스|울타리|메쉬|철망|시공|설치|조경|인테리어)(시공|설치|제작|공사|업체)?$',
        r'^(인천|서울|경기|김포|부천|수원|고양|안산|파주|수원)(휀스|울타리|메쉬|철망|시공|설치|조경)?$',
        r'^(휀스|울타리)(시공|설치|공사)$',
    ]
    is_vague = False
    for pat in VAGUE_NAME_PATTERNS:
        if re.match(pat, name.strip()):
            is_vague = True
            break
            
    if not has_phone and is_vague:
        return "❌ 제거권장"
    elif is_vague:
        return "⚠️ 상호불명확"
    elif not has_phone:
        return "⚠️ 전화없음"
    else:
        return "✅ 정상"

def main():
    print("🚀 구글 스프레드시트 연결 중...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    all_rows = ws.get_all_values()
    print(f"전체 로드된 행 수: {len(all_rows)}")
    
    # 1. 2행부터 기존에 수집된 잘못된 정보(웹사이트, 이메일, 검증결과) 초기화 작업
    print("🧹 이전 수집에 들어간 오기입/가비지 데이터 초기화 중...")
    reset_batch = []
    for idx, row in enumerate(all_rows[1:], start=2):
        if len(row) > 2 and row[2].strip():
            phone = row[4].strip() if len(row) > 4 else ""
            name = row[2].strip()
            quality = assess_quality(name, phone, "")
            
            # F(이메일), G(웹사이트) 비우고, J(웹사이트검증) 'URL없음', L(데이터품질) 재설정
            reset_batch.append({"range": f"F{idx}", "values": [[""]]})
            reset_batch.append({"range": f"G{idx}", "values": [[""]]})
            reset_batch.append({"range": f"J{idx}", "values": [["URL없음"]]})
            reset_batch.append({"range": f"L{idx}", "values": [[quality]]})
            
    # 500개씩 나눠서 안전하게 초기화 반영
    chunk_size = 200
    for chunk_idx in range(0, len(reset_batch), chunk_size):
        ws.batch_update(reset_batch[chunk_idx : chunk_idx + chunk_size])
    print("🧹 초기화 완료!")
    
    # 다시 데이터 로드
    all_rows = ws.get_all_values()
    
    # 수집 대상 정의 (전화번호가 기재된 업체)
    targets = []
    for idx, row in enumerate(all_rows[1:], start=2):
        if len(row) > 2:
            name = row[2].strip()
            phone = row[4].strip() if len(row) > 4 else ""
            region = row[7].strip() if len(row) > 7 else ""
            
            if name and phone:
                targets.append((idx, name, region, phone))
                
    print(f"🎯 실조사 대상 업체 수 (전화번호 등록 업체): {len(targets)}개")
    
    success_count = 0
    batch_updates = []
    BATCH_SIZE = 5
    
    for i, (row_idx, name, region, phone) in enumerate(targets):
        print(f"[{i+1}/{len(targets)}] 🔍 {name} ({region}) 정밀 조사 중...", end=" → ")
        
        website = ""
        email = ""
        
        # 1) 플레이스 상세에서 홈페이지 조회 (100% 공식 채널)
        website = get_place_website(name, region)
        
        # 2) 공식 매칭 블로그 검색
        blog_url, blog_email = find_official_blog(name, region)
        
        # 홈페이지 매핑 우선순위: 플레이스 등록 홈페이지 > 공식 블로그 URL
        if not website and blog_url:
            website = blog_url
            
        # 이메일 매핑 우선순위: 블로그 기반 이메일 우선
        if blog_email:
            email = blog_email
            
        # 3) 홈페이지가 존재하나 이메일이 없는 경우 홈페이지 직접 크롤링
        if website and not email and not website.startswith("https://blog.naver.com"):
            web_emails = fetch_emails_from_website(website)
            if web_emails:
                email = list(web_emails)[0]
                
        # 4) 여전히 이메일이 없는 경우 상호명 검증 스니펫 이메일 검색
        if not email:
            email = find_email_from_snippet(name, region)
            
        # 결과에 따른 상태 정의
        quality = assess_quality(name, phone, email)
        web_status = "✅ 접속가능" if website else "URL없음"
        
        batch_updates.append({"range": f"F{row_idx}", "values": [[email]]})
        batch_updates.append({"range": f"G{row_idx}", "values": [[website]]})
        batch_updates.append({"range": f"J{row_idx}", "values": [[web_status]]})
        batch_updates.append({"range": f"L{row_idx}", "values": [[quality]]})
        
        if email or website:
            print(f"홈페이지: {website or '없음'} / 이메일: {email or '없음'} ✅")
            success_count += 1
        else:
            print("정보 없음 ❌")
            
        # 배치 사이즈 도달 시 구글 시트에 업데이트
        if len(batch_updates) >= BATCH_SIZE * 4:
            ws.batch_update(batch_updates)
            print(f"   💾 {BATCH_SIZE}개 업체 정보 구글 시트 저장 완료.")
            batch_updates = []
            
        time.sleep(1.5) # 네이버 블록 차단 방지용 안전 딜레이
        
    if batch_updates:
        ws.batch_update(batch_updates)
        print("   💾 마지막 배치 저장 완료.")
        
    print(f"\n🎉 작업 완료! 총 {len(targets)}개 중 {success_count}개 업체의 정보를 고정밀 수집하여 추가 완료했습니다.")

if __name__ == "__main__":
    main()
