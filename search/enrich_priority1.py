"""
1순위 용접철망 업체 대상 고강도 이메일/웹사이트 수집기
전략 (4단계):
  1) 네이버 플레이스 공식 홈페이지 JSON 추출 → 홈페이지 내부 이메일 크롤링
  2) "{회사명} 홈페이지" 검색 → 공식 사이트/modoo/blog 매칭 (부분 상호명 허용)
  3) "{회사명} 이메일" 검색 스니펫에서 이메일 패턴 직접 추출
  4) 발굴된 사이트 내 /about /contact /intro 등 여러 경로 순차 방문하여 이메일 채굴
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

DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
MOBILE_UA = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMAIL_RE = re.compile(
    r'([a-zA-Z0-9._%+\-]+@'
    r'(?:naver\.com|hanmail\.net|daum\.net|nate\.com|gmail\.com|kakao\.com'
    r'|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}))',
    re.I
)
BLOG_RE   = re.compile(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)')
MODOO_RE  = re.compile(r'([\w\-]+\.modoo\.at)')

# ── 완전 제외 도메인 ──────────────────────────────────────────
NOISE_DOMAINS = {
    'navercorp.com','naver.com','ncloud.com','naver.me','naver.net',
    'search.naver.com','map.naver.com','place.naver.com','m.place.naver.com',
    'youtube.com','facebook.com','instagram.com','twitter.com','tiktok.com',
    'kakao.com','kakaocorp.com','daum.net',
    'saramin.co.kr','jobkorea.co.kr','wanted.co.kr','albamon.com','alba.co.kr',
    'dart.fss.or.kr','creditjob.cc','catch.co.kr','bizno.net','ftc.go.kr',
    'cominfo.co.kr','google.com','google.co.kr','github.com','wikipedia.org',
    'namu.wiki','egloos.com','coupang.com','lotteon.com','gmarket.co.kr',
    'auction.co.kr','11st.co.kr','daangn.com','findcompany.kr','114.co.kr',
    'kwk114.com',
}
# 도메인에 이 문자열이 포함되면 제외 (언론사)
NOISE_KEYWORDS = [
    'news','sedaily','moneytoday','ggilbo','khan','hankyung','donga','chosun',
    'seoul.co.kr','segye.com','kmib.co.kr','ytn.co.kr','kbs.co.kr','mbc.co.kr',
    'sbs.co.kr','hankookilbo','fintechpost','joynews','newsis','seohae.go.kr',
    'incheoneum','todayenergy','hkbs.co.kr','reviewro.tistory','assunas.tistory',
    'ilovebusiness.tistory','richcat.tistory','geia.tistory','jungshjoa.tistory',
    'heathtalkmenta','check.kkuda','intn.co.kr','tvchosun','ohmynews',
]

def is_noise(url: str) -> bool:
    if not url:
        return True
    u = url.lower()
    for d in NOISE_DOMAINS:
        if d in u:
            return True
    for k in NOISE_KEYWORDS:
        if k in u:
            return True
    return False

def clean_emails(raw_list):
    """이미지/스크립트 오탐 제거"""
    bad_ext = ('.png','.jpg','.gif','.js','.css','.svg','.woff')
    bad_domain = {'example.com','test.com','domain.com','email.com','w3.org','sentry.io'}
    out = []
    for e in raw_list:
        e = e.lower()
        if any(e.endswith(x) for x in bad_ext):
            continue
        dom = e.split('@')[-1]
        if dom in bad_domain:
            continue
        out.append(e)
    return out

CONTACT_PATHS = [
    "", "/contact", "/about", "/company", "/intro",
    "/contact.html", "/about.html", "/company.html",
    "/bbs/contact.php", "/page/contact",
]

def crawl_website_for_email(base_url: str) -> str:
    """홈페이지 주요 경로를 순차적으로 방문해 이메일 탐색"""
    if not base_url or not base_url.startswith("http"):
        return ""
    for path in CONTACT_PATHS:
        url = base_url.rstrip("/") + path
        try:
            r = requests.get(url, headers=DESKTOP_UA, timeout=6, allow_redirects=True)
            if r.status_code >= 400:
                continue
            found = clean_emails(EMAIL_RE.findall(r.text))
            if found:
                return found[0]
        except Exception:
            pass
        time.sleep(0.15)
    return ""

# ── 단계별 수집 함수 ──────────────────────────────────────────

def step1_place_homepage(name, region):
    """네이버 플레이스 JSON에서 공식 등록 홈페이지 추출"""
    query = f"{region} {name}"
    try:
        r = requests.get(
            f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}",
            headers=MOBILE_UA, timeout=8
        )
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        place_id = None
        for a in soup.find_all("a", href=re.compile(r'/place/(\d+)')):
            m = re.search(r'/place/(\d+)', a.get("href",""))
            if m:
                place_id = m.group(1)
                break
        if not place_id:
            return None
        dr = requests.get(
            f"https://m.place.naver.com/place/{place_id}/home",
            headers=MOBILE_UA, timeout=8
        )
        urls = re.findall(r'"homepage":"(http[^"]+)"', dr.text)
        for u in urls:
            u = u.replace("\\/", "/")
            if not is_noise(u):
                return u
    except Exception:
        pass
    return None

def step2_homepage_search(name, region):
    """'{회사명} 홈페이지' 검색으로 공식 웹사이트/modoo/blog 탐색 (부분 일치 허용)"""
    website  = ""
    blog_url = ""
    modoo_url= ""
    query = f"{name} 홈페이지"
    try:
        r = requests.get(
            f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}",
            headers=DESKTOP_UA, timeout=8
        )
        if r.status_code != 200:
            return "", ""
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 상호명 핵심어 추출 (2글자 이상 단어)
        name_core = re.sub(r'[()\s]','', name)
        
        for a in soup.find_all("a", href=True):
            href = a.get("href","")
            text = (a.get_text(" ", strip=True) + " " +
                    (a.get("title","") or ""))
            
            # 블로그
            bm = BLOG_RE.search(href)
            if bm:
                bid = bm.group(1)
                if bid not in ("prologue","postList","category"):
                    if not blog_url:
                        blog_url = f"https://blog.naver.com/{bid}"
            
            # Modoo
            mm = MODOO_RE.search(href)
            if mm and not modoo_url:
                modoo_url = f"https://{mm.group(0)}"
            
            # 일반 외부 사이트 — 상호명 핵심어가 텍스트 or 도메인에 포함된 경우
            if href.startswith("http") and not is_noise(href):
                dom = re.match(r'https?://([^/]+)', href)
                dom_str = dom.group(1).lower() if dom else ""
                text_match = name_core.lower() in re.sub(r'\s','', text).lower()
                dom_match  = name_core.lower() in dom_str
                if (text_match or dom_match) and not website:
                    website = re.match(r'(https?://[^/]+)', href).group(1)
    except Exception:
        pass
    
    # 우선순위: 공식 사이트 > modoo > blog
    final_web = website or modoo_url or blog_url
    blog_email = ""
    if blog_url and not website:
        bid = blog_url.split("/")[-1]
        blog_email = f"{bid}@naver.com"
    return final_web, blog_email

def step3_snippet_email(name, region):
    """'{회사명} 이메일' 또는 '{회사명} 연락처' 검색 스니펫에서 이메일 직접 추출"""
    for query in [f"{name} 이메일", f"{name} {region} 연락처"]:
        try:
            r = requests.get(
                f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}",
                headers=DESKTOP_UA, timeout=8
            )
            if r.status_code != 200:
                continue
            found = clean_emails(EMAIL_RE.findall(r.text))
            if found:
                return found[0]
        except Exception:
            pass
        time.sleep(0.5)
    return ""

def process(name, region):
    website = ""
    email   = ""
    
    # Step 1: 플레이스 공식 홈페이지
    hp = step1_place_homepage(name, region)
    if hp:
        website = hp

    # Step 2: 홈페이지 검색
    web2, blog_email = step2_homepage_search(name, region)
    if not website and web2:
        website = web2
    if blog_email and not email:
        email = blog_email

    # Step 3: 홈페이지 내부 이메일 크롤링
    if website and not email:
        email = crawl_website_for_email(website)

    # Step 4: 검색 스니펫 이메일 추출
    if not email:
        email = step3_snippet_email(name, region)

    return website, email

# ── 메인 ──────────────────────────────────────────────────────
def main():
    print("🚀 구글 시트 연결 중...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet("company")

    rows = ws.get_all_values()
    print(f"전체 행: {len(rows)}")

    targets = []
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) < 4:
            continue
        name   = row[2].strip()
        priority = row[3].strip()
        phone  = row[4].strip() if len(row) > 4 else ""
        email  = row[5].strip() if len(row) > 5 else ""
        region = row[7].strip() if len(row) > 7 else ""

        # 1순위만, 전화번호 있고, 이메일 아직 없는 행
        if "1순위" in priority and name and phone and not email:
            targets.append((idx, name, region, phone))

    print(f"🎯 1순위 이메일 미수집 대상: {len(targets)}개\n")

    batch  = []
    ok_cnt = 0
    BATCH_SIZE = 5

    for i, (row_idx, name, region, phone) in enumerate(targets, start=1):
        print(f"[{i:>3}/{len(targets)}] {name} ({region}) ...", end=" ")
        sys.stdout.flush()

        website, email = process(name, region)

        web_status = "✅ 접속가능" if website else "URL없음"
        quality    = "✅ 정상" if (phone and email) else ("✅ 정상" if phone else "⚠️ 전화없음")

        batch.append({"range": f"F{row_idx}", "values": [[email]]})
        batch.append({"range": f"G{row_idx}", "values": [[website]]})
        batch.append({"range": f"J{row_idx}", "values": [[web_status]]})
        batch.append({"range": f"L{row_idx}", "values": [[quality]]})

        if email or website:
            print(f"이메일: {email or '없음'} / 홈페이지: {website or '없음'} ✅")
            ok_cnt += 1
        else:
            print("정보 없음 ❌")

        if len(batch) >= BATCH_SIZE * 4:
            ws.batch_update(batch)
            print(f"   💾 {BATCH_SIZE}개 시트 저장.")
            batch = []

        time.sleep(1.5)

    if batch:
        ws.batch_update(batch)
        print("   💾 마지막 배치 저장 완료.")

    print(f"\n🎉 완료! 82개 중 {ok_cnt}개 발굴 성공 ({ok_cnt/len(targets)*100:.1f}%)")

if __name__ == "__main__":
    main()
