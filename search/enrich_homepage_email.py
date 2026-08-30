"""
홈페이지 등록 업체 대상 이메일 정밀 추출기
- 전체 830개 업체를 대상으로 네이버 플레이스 JSON에서 공식 홈페이지 추출
- 홈페이지가 있는 업체만 직접 방문하여 이메일 크롤링
- 구글 시트 F(이메일), G(홈페이지), J(웹검증) 배치 업데이트
"""
import requests
from bs4 import BeautifulSoup
import re, sys, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH       = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID   = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES           = ["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]

MOBILE_UA = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMAIL_RE = re.compile(
    r'([a-zA-Z0-9._%+\-]+@'
    r'(?:naver\.com|hanmail\.net|daum\.net|nate\.com|gmail\.com|kakao\.com'
    r'|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}))',
    re.I
)

# ── 노이즈 도메인 ──────────────────────────────────────────────
NOISE = {
    'navercorp.com','naver.com','ncloud.com','naver.me','naver.net',
    'map.naver.com','place.naver.com','m.place.naver.com',
    'youtube.com','facebook.com','instagram.com','twitter.com','tiktok.com',
    'kakao.com','kakaocorp.com','daum.net',
    'saramin.co.kr','jobkorea.co.kr','wanted.co.kr','albamon.com',
    'dart.fss.or.kr','catch.co.kr','bizno.net','ftc.go.kr',
    'google.com','google.co.kr','github.com','wikipedia.org','namu.wiki',
    'coupang.com','lotteon.com','gmarket.co.kr','auction.co.kr','11st.co.kr',
    'daangn.com','findcompany.kr','114.co.kr','kwk114.com','bizwiki.co.kr',
    'comwel.or.kr','hira.or.kr','nhis.go.kr',
}
NOISE_KW = [
    'news','sedaily','moneytoday','ggilbo','khan','hankyung','donga','chosun',
    'seoul.co.kr','segye.com','kmib.co.kr','ytn.co.kr','kbs.co.kr',
    'mbc.co.kr','sbs.co.kr','hankookilbo','fintechpost','joynews','newsis',
    'tistory.com','egloos.com',
]

def is_noise(url: str) -> bool:
    if not url or not url.startswith("http"):
        return True
    u = url.lower()
    for d in NOISE:
        if d in u:
            return True
    for k in NOISE_KW:
        if k in u:
            return True
    return False

def clean_emails(raw):
    bad_ext = ('.png','.jpg','.gif','.js','.css','.svg','.woff','.ico')
    bad_dom = {'example.com','test.com','domain.com','email.com',
               'w3.org','sentry.io','schema.org','openid.net'}
    out = []
    for e in raw:
        e = e.lower().strip('.')
        if any(e.endswith(x) for x in bad_ext):
            continue
        dom = e.split('@')[-1]
        if dom in bad_dom:
            continue
        out.append(e)
    return out

# ── 플레이스 홈페이지 추출 ─────────────────────────────────────
def get_place_homepage(name: str, region: str) -> str:
    query = f"{region} {name}"
    try:
        r = requests.get(
            f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(query)}",
            headers=MOBILE_UA, timeout=8
        )
        if r.status_code != 200:
            return ""
        # Place ID 추출
        place_id = None
        for m in re.finditer(r'/place/(\d+)', r.text):
            place_id = m.group(1)
            break
        if not place_id:
            return ""
        # 모바일 플레이스 홈 JSON
        dr = requests.get(
            f"https://m.place.naver.com/place/{place_id}/home",
            headers=MOBILE_UA, timeout=8
        )
        for m in re.finditer(r'"homepage"\s*:\s*"(http[^"]+)"', dr.text):
            url = m.group(1).replace("\\/", "/")
            if not is_noise(url):
                return url
        # fallback: hd-fence 류 외부 링크가 상세 HTML에 있는 경우
        soup = BeautifulSoup(dr.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a.get("href","")
            if href.startswith("http") and not is_noise(href):
                return href
    except Exception:
        pass
    return ""

# ── 홈페이지 내부 이메일 크롤링 ───────────────────────────────
CONTACT_PATHS = [
    "", "/contact", "/about", "/company", "/intro",
    "/contact.html", "/about.html", "/company.html",
    "/bbs/board.php?bo_table=contact", "/page/contact",
]

def crawl_email(base_url: str) -> str:
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

# ── 메인 ──────────────────────────────────────────────────────
def main():
    print("🚀 구글 시트 연결 중...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    ws    = gc.open_by_key(SPREADSHEET_ID).worksheet("company")

    rows = ws.get_all_values()
    print(f"전체 행 수: {len(rows)-1}개")

    # 대상: 전화번호 있고, 이메일 아직 없는 전체 업체
    targets = []
    for idx, row in enumerate(rows[1:], start=2):
        name   = row[2].strip() if len(row) > 2 else ""
        phone  = row[4].strip() if len(row) > 4 else ""
        email  = row[5].strip() if len(row) > 5 else ""
        region = row[7].strip() if len(row) > 7 else ""
        if name and phone and not email:
            targets.append((idx, name, region))

    print(f"🎯 이메일 미수집 + 전화 있는 업체: {len(targets)}개\n")

    batch    = []
    ok_web   = 0
    ok_email = 0
    BATCH_N  = 5

    for i, (row_idx, name, region) in enumerate(targets, start=1):
        print(f"[{i:>3}/{len(targets)}] {name} ({region})", end="  ")
        sys.stdout.flush()

        # Step 1: 플레이스 공식 홈페이지
        homepage = get_place_homepage(name, region)

        # Step 2: 홈페이지 있으면 이메일 크롤링
        email = ""
        if homepage:
            email = crawl_email(homepage)
            ok_web += 1
            if email:
                ok_email += 1

        web_status = "✅ 접속가능" if homepage else "URL없음"
        print(f"→ 홈:{homepage[:50] if homepage else '없음':<50}  메일:{email or '없음'}")

        batch.append({"range": f"F{row_idx}", "values": [[email]]})
        batch.append({"range": f"G{row_idx}", "values": [[homepage]]})
        batch.append({"range": f"J{row_idx}", "values": [[web_status]]})

        if len(batch) >= BATCH_N * 3:
            ws.batch_update(batch)
            print(f"   💾 저장 완료 (누적 홈:{ok_web} / 이메일:{ok_email})")
            batch = []

        time.sleep(1.2)   # 네이버 딜레이

    if batch:
        ws.batch_update(batch)
        print("   💾 마지막 배치 저장.")

    print(f"\n🎉 완료! 대상 {len(targets)}개 중")
    print(f"   홈페이지 발굴: {ok_web}개")
    print(f"   이메일 발굴  : {ok_email}개")

if __name__ == "__main__":
    main()
