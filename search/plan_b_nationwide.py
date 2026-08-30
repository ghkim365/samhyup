"""
B안: 전국 확대 수집 + 이메일이 발굴된 업체만 선별 저장 (Playwright 버전)
- Playwright를 사용하여 네이버 검색 결과 페이지를 로드해 블록 우회
- 플레이스 ID를 먼저 추출하고, 개별 플레이스 상세 페이지에서 정밀 데이터(상호, 전화, 주소, 홈페이지) 추출
- 공식 홈페이지, 공식 블로그, 또는 검색 스니펫 중 하나라도 이메일이 발굴되면 시트에 추가
- 기존 업체(상호명/전화번호) 중복 제거
"""
import asyncio
from playwright.async_api import async_playwright
import re, sys, time
import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH     = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES         = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]

EMAIL_RE = re.compile(r'([a-zA-Z0-9._%+\-]+@(?:naver\.com|hanmail\.net|daum\.net|nate\.com|gmail\.com|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}))', re.I)
BLOG_RE   = re.compile(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)')

# 전국 확대 지역 (수도권 제외 광역+산업도시)
REGIONS = [
    "부산", "대구", "광주", "대전", "울산",
    "창원", "전주", "청주", "천안", "아산",
    "진주", "포항", "구미", "원주", "춘천",
    "익산", "순천", "여수", "충주", "당진",
]

# 핵심 키워드
KEYWORDS = {
    "1순위: 용접철망": ["철망", "철망제조", "건재상"],
    "2순위: 개비온":   ["개비온", "돌망태"],
    "2순위: 메쉬파레트": ["메쉬파레트"],
    "2순위: 인테리어철망": ["금속인테리어"],
    "2순위: 메쉬휀스": ["휀스", "메쉬휀스"],
}

NOISE = {
    'navercorp.com','naver.com','ncloud.com','naver.me',
    'map.naver.com','place.naver.com','m.place.naver.com',
    'youtube.com','facebook.com','instagram.com','kakao.com','daum.net',
    'saramin.co.kr','jobkorea.co.kr','wanted.co.kr','albamon.com',
    'dart.fss.or.kr','catch.co.kr','bizno.net','ftc.go.kr',
    'google.com','google.co.kr','wikipedia.org','namu.wiki',
    'coupang.com','lotteon.com','gmarket.co.kr','11st.co.kr',
    'daangn.com','findcompany.kr','114.co.kr','kwk114.com','bizwiki.co.kr',
}
NOISE_KW = ['news','tistory.com','egloos.com','sedaily','moneytoday','khan',
            'hankyung','donga','chosun','segye.com','ytn.co.kr','kbs.co.kr',
            'mbc.co.kr','sbs.co.kr','hankookilbo','fintechpost','joynews','newsis']

EXCLUDE_NAME_KW = ["삼협", "동우철망", "대경철망", "연신철강", "흥창스틸"]

def is_noise(url):
    if not url or not url.startswith("http"): return True
    u = url.lower()
    for d in NOISE:
        if d in u: return True
    for k in NOISE_KW:
        if k in u: return True
    return False

def clean_emails(raw):
    bad = ('.png','.jpg','.gif','.js','.css','.svg','.woff','.ico')
    bad_dom = {'example.com','test.com','domain.com','w3.org','sentry.io','schema.org'}
    out = []
    for e in raw:
        e = e.lower().strip('.')
        if any(e.endswith(x) for x in bad): continue
        if e.split('@')[-1] in bad_dom: continue
        out.append(e)
    return out

CONTACT_PATHS = ["", "/contact", "/about", "/company", "/intro",
                 "/contact.html", "/about.html", "/company.html"]

async def get_search_place_ids(page, query):
    url = f"https://search.naver.com/search.naver?query={requests.utils.quote(query)}"
    place_ids = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.0)  # 안정적인 렌더링 대기
        html = await page.content()
        matches = re.findall(r'place/(\d+)', html)
        for pid in matches:
            if pid not in place_ids:
                place_ids.append(pid)
    except Exception as e:
        print(f"[Error] {query} ID 추출 실패: {e}")
    return place_ids

async def get_place_details(page, place_id):
    url = f"https://m.place.naver.com/place/{place_id}/home"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.0)
        html = await page.content()
        
        name_m = re.search(r'"name"\s*:\s*"([^"]+)"', html)
        name = name_m.group(1) if name_m else ""
        if not name:
            name_m = re.search(r'<span class="[^"]*Fc1rA[^"]*">([^<]+)</span>', html)
            if name_m: name = name_m.group(1).strip()
            
        if any(kw in name for kw in EXCLUDE_NAME_KW): return None
        
        phone_m = re.search(r'"phone"\s*:\s*"([^"]+)"', html)
        phone = phone_m.group(1) if phone_m else ""
        
        address_m = re.search(r'"address"\s*:\s*"([^"]+)"', html)
        address = address_m.group(1) if address_m else ""
        
        homepage = ""
        hp_m = re.search(r'"homepage"\s*:\s*"([^"]+)"', html)
        if hp_m:
            homepage = hp_m.group(1).replace("\\/", "/")
            
        category_m = re.search(r'"category"\s*:\s*"([^"]+)"', html)
        category = category_m.group(1) if category_m else ""
            
        return {
            "name": name,
            "phone": phone,
            "address": address,
            "homepage": homepage,
            "category": category
        }
    except Exception as e:
        print(f"[Error] {place_id} 상세 조회 실패: {e}")
        return None

def crawl_email(base_url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.9"}
    for path in CONTACT_PATHS:
        url = base_url.rstrip("/") + path
        try:
            r = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
            if r.status_code >= 400: continue
            found = clean_emails(EMAIL_RE.findall(r.text))
            if found: return found[0]
        except Exception: pass
        time.sleep(0.1)
    return ""

def find_official_blog_email(company_name, region):
    query = f"{company_name} {region} 블로그"
    url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.find_all("a", href=re.compile(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)'))
            for a in links:
                href = a.get("href", "")
                title_text = a.get_text(strip=True)
                if not title_text:
                    parent = a.find_parent()
                    if parent: title_text = parent.get_text(strip=True)
                
                clean_company = re.sub(r'[\s\(\)]', '', company_name)
                clean_title = re.sub(r'[\s\(\)]', '', title_text)
                
                if clean_company in clean_title:
                    match = BLOG_RE.search(href)
                    if match:
                        blog_id = match.group(1)
                        if blog_id not in ["prologue", "postList", "category"]:
                            return f"https://blog.naver.com/{blog_id}", f"{blog_id}@naver.com"
    except Exception: pass
    return "", ""

def snippet_email(name, region):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    for q in [f"{name} 이메일", f"{name} {region} 연락처"]:
        try:
            r = requests.get(f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(q)}", headers=headers, timeout=8)
            if r.status_code == 200:
                found = clean_emails(EMAIL_RE.findall(r.text))
                if found: return found[0]
        except Exception: pass
        time.sleep(0.3)
    return ""

async def async_main():
    print("🚀 구글 시트 연결...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    ws    = gc.open_by_key(SPREADSHEET_ID).worksheet("company")

    # 기존 상호명·전화번호 로드 (중복 방지)
    existing_rows = ws.get_all_values()
    existing_names  = {r[2].strip() for r in existing_rows[1:] if len(r) > 2 and r[2].strip()}
    existing_phones = {r[4].strip() for r in existing_rows[1:] if len(r) > 4 and r[4].strip()}
    last_seq = len(existing_rows) - 1
    print(f"기존 업체: {len(existing_names)}개")

    new_rows  = []
    seen_ids  = set()
    total_q   = 0

    print("\n🔍 B안: Playwright 기반 전국 확대 검색 시작...\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 실제 브라우저와 유사한 환경 세팅
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ko-KR",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        for priority, keywords in KEYWORDS.items():
            for kw in keywords:
                for region in REGIONS:
                    query = f"{region} {kw}"
                    total_q += 1
                    print(f"  [{total_q}] {query}", end=" → ")
                    sys.stdout.flush()

                    place_ids = await get_search_place_ids(page, query)
                    new_cnt   = 0

                    for pid in place_ids:
                        if pid in seen_ids: continue
                        seen_ids.add(pid)
                        
                        c = await get_place_details(page, pid)
                        if not c or not c["name"]: continue
                        
                        if c["name"] in existing_names: continue
                        if c["phone"] and c["phone"] in existing_phones: continue

                        email = ""
                        homepage = c["homepage"]
                        
                        # 1) 홈페이지가 등록된 경우 크롤링
                        if homepage and not is_noise(homepage):
                            email = crawl_email(homepage)
                            
                        # 2) 홈페이지가 없거나 크롤링 실패한 경우 공식 블로그 조회
                        if not email:
                            blog_url, blog_email = find_official_blog_email(c["name"], region)
                            if blog_email:
                                email = blog_email
                                if not homepage: homepage = blog_url
                                
                        # 3) 여전히 없는 경우 검색 스니펫 조회
                        if not email:
                            email = snippet_email(c["name"], region)

                        # 이메일 발굴에 성공한 업체만 B2B 리스트에 추가
                        if not email: continue

                        web_status = "✅ 접속가능" if homepage else "URL없음"
                        quality    = "✅ 정상" if c["phone"] else "⚠️ 전화없음"
                        last_seq  += 1
                        phone_status = "✅ 형식OK" if c["phone"] else "전화없음"

                        row = [
                            "FALSE", str(last_seq), c["name"], priority,
                            c["phone"], email, homepage,
                            region, c["address"],
                            web_status, phone_status, quality
                        ]
                        new_rows.append(row)
                        existing_names.add(c["name"])
                        if c["phone"]: existing_phones.add(c["phone"])
                        new_cnt += 1
                        await asyncio.sleep(0.5)

                    print(f"{len(place_ids)}개 ID 추출 / {new_cnt}개 신규 이메일 가망고객 추가")
                    await asyncio.sleep(1.0)

        await browser.close()

    # 시트에 일괄 기록
    if new_rows:
        print(f"\n✍️ 신규 {len(new_rows)}개 시트 기록 중...")
        ws.append_rows(new_rows, value_input_option='USER_ENTERED')
        print(f"✅ B안 완료! 신규 {len(new_rows)}개 메일 마케팅 타겟 추가 완료!")
    else:
        print("\n신규 가망 고객 없음.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
