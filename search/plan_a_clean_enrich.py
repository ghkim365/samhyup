"""
A안 Step1: 시트 정제 — 견사망(애견유치원·훈련소·보호소류) 삭제 + 재정렬
A안 Step2: 남은 499개 중 전화있고 이메일 없는 411개 대상 이메일 수집
  - 네이버 플레이스 공식 홈페이지 추출 → 홈페이지 내부 이메일 크롤링
  - 홈페이지 없으면: 네이버 검색 스니펫에서 이메일 직접 추출
"""
import requests
from bs4 import BeautifulSoup
import re, sys, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH     = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES         = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]

MOBILE_UA  = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1", "Accept-Language": "ko-KR,ko;q=0.9"}
DESKTOP_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.9"}

EMAIL_RE = re.compile(r'([a-zA-Z0-9._%+\-]+@(?:naver\.com|hanmail\.net|daum\.net|nate\.com|gmail\.com|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}))', re.I)

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
NOISE_KW = [
    'news','tistory.com','egloos.com','sedaily','moneytoday','khan',
    'hankyung','donga','chosun','segye.com','ytn.co.kr','kbs.co.kr',
    'mbc.co.kr','sbs.co.kr','hankookilbo','fintechpost','joynews','newsis',
]

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

def get_place_homepage(name, region):
    try:
        q = f"{region} {name}"
        r = requests.get(f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(q)}", headers=MOBILE_UA, timeout=8)
        if r.status_code != 200: return ""
        place_id = None
        for m in re.finditer(r'/place/(\d+)', r.text):
            place_id = m.group(1); break
        if not place_id: return ""
        dr = requests.get(f"https://m.place.naver.com/place/{place_id}/home", headers=MOBILE_UA, timeout=8)
        for m in re.finditer(r'"homepage"\s*:\s*"(http[^"]+)"', dr.text):
            u = m.group(1).replace("\\/", "/")
            if not is_noise(u): return u
    except Exception: pass
    return ""

def crawl_email(base_url):
    for path in CONTACT_PATHS:
        url = base_url.rstrip("/") + path
        try:
            r = requests.get(url, headers=DESKTOP_UA, timeout=6, allow_redirects=True)
            if r.status_code >= 400: continue
            found = clean_emails(EMAIL_RE.findall(r.text))
            if found: return found[0]
        except Exception: pass
        time.sleep(0.1)
    return ""

def snippet_email(name, region):
    """홈페이지가 없을 때: 검색 스니펫에서 이메일 추출"""
    for q in [f"{name} 이메일", f"{name} {region} 연락처"]:
        try:
            r = requests.get(f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(q)}", headers=DESKTOP_UA, timeout=8)
            if r.status_code != 200: continue
            found = clean_emails(EMAIL_RE.findall(r.text))
            if found: return found[0]
        except Exception: pass
        time.sleep(0.5)
    return ""

# ─── 메인 ───────────────────────────────────────────────────
def main():
    print("🚀 구글 시트 연결...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    ws    = gc.open_by_key(SPREADSHEET_ID).worksheet("company")

    # ── STEP 1: 시트 정제 ────────────────────────────────────
    print("\n🧹 STEP 1: 견사망(애견유치원·훈련소·보호소) 제거 중...")
    all_rows = ws.get_all_values()
    header   = all_rows[0]

    keep_rows = []
    removed   = 0
    for row in all_rows[1:]:
        if len(row) < 3 or not row[2].strip():
            continue  # 빈 행 무시
        pri = row[3].strip() if len(row) > 3 else ""
        if "견사망" in pri:
            removed += 1
        else:
            keep_rows.append(row)

    # 연번 재부여
    for i, row in enumerate(keep_rows, start=1):
        if len(row) > 1: row[1] = str(i)

    print(f"  삭제: {removed}개  유지: {len(keep_rows)}개")
    ws.clear()
    ws.update("A1:L1", [header])
    if keep_rows:
        ws.append_rows(keep_rows, value_input_option='USER_ENTERED')
    print("  ✅ 시트 정제 완료!")

    # ── STEP 2: 이메일 수집 ──────────────────────────────────
    print("\n📧 STEP 2: 이메일 정밀 수집 시작...")
    all_rows = ws.get_all_values()

    targets = []
    for idx, row in enumerate(all_rows[1:], start=2):
        name   = row[2].strip() if len(row) > 2 else ""
        phone  = row[4].strip() if len(row) > 4 else ""
        email  = row[5].strip() if len(row) > 5 else ""
        region = row[7].strip() if len(row) > 7 else ""
        if name and phone and not email:
            targets.append((idx, name, region))

    print(f"  대상: {len(targets)}개\n")

    batch   = []
    ok_web  = 0
    ok_mail = 0
    BATCH_N = 5

    for i, (row_idx, name, region) in enumerate(targets, start=1):
        print(f"[{i:>3}/{len(targets)}] {name} ({region})", end="  ")
        sys.stdout.flush()

        homepage = get_place_homepage(name, region)
        email    = ""

        if homepage:
            email   = crawl_email(homepage)
            ok_web += 1
            if email: ok_mail += 1
        
        # 홈페이지 없거나 이메일 못 찾은 경우 스니펫 시도
        if not email:
            email = snippet_email(name, region)
            if email: ok_mail += 1

        web_status = "✅ 접속가능" if homepage else "URL없음"
        print(f"→ 메일:{email or '없음':<35}  홈:{homepage[:40] if homepage else '없음'}")

        batch.append({"range": f"F{row_idx}", "values": [[email]]})
        batch.append({"range": f"G{row_idx}", "values": [[homepage]]})
        batch.append({"range": f"J{row_idx}", "values": [[web_status]]})

        if len(batch) >= BATCH_N * 3:
            ws.batch_update(batch)
            print(f"   💾 저장 (홈:{ok_web} / 메일:{ok_mail})")
            batch = []

        time.sleep(1.2)

    if batch:
        ws.batch_update(batch)

    print(f"\n✅ A안 완료! 대상 {len(targets)}개 → 홈페이지:{ok_web} / 이메일:{ok_mail}개 발굴")

if __name__ == "__main__":
    main()
