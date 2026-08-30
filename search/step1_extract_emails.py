"""
Step 1: 홈페이지 보유 업체 이메일 자동 추출
- 웹사이트 E열이 있는 업체만 대상
- 메인/소개/문의 페이지에서 이메일 패턴 추출
- D열 이메일이 비어있는 행에만 기록
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

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
NOISE_DOMAINS = {'example.com', 'test.com', 'domain.com', 'email.com', 'naver.com', 'sentry.io', 'w3.org'}

CONTACT_PATHS = ["", "/about", "/contact", "/company", "/intro",
                 "/about.html", "/contact.html", "/company.html"]

def fetch_emails_from_url(base_url):
    """주어진 URL 및 하위 페이지에서 이메일 수집"""
    found = set()
    for path in CONTACT_PATHS:
        url = base_url.rstrip("/") + path
        try:
            res = requests.get(url, headers=HEADERS, timeout=7, allow_redirects=True)
            if res.status_code >= 400:
                continue
            text = res.text
            emails = EMAIL_RE.findall(text)
            for e in emails:
                domain = e.split("@")[-1].lower()
                if domain not in NOISE_DOMAINS and not domain.endswith(('.js', '.css', '.png', '.jpg')):
                    found.add(e.lower())
            if found:
                break  # 이메일 찾으면 더 탐색 불필요
        except Exception:
            pass
        time.sleep(0.3)
    return found

def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("company")
    
    all_rows = ws.get_all_values()
    print(f"총 {len(all_rows)-1}개 업체 확인 중...\n")
    
    updates = []  # (row_index, email)
    
    for i, row in enumerate(all_rows[1:], start=2):
        name = row[0] if len(row) > 0 else ""
        existing_email = row[3].strip() if len(row) > 3 else ""
        website = row[4].strip() if len(row) > 4 else ""
        
        if not website or existing_email:
            continue  # URL 없거나 이메일 이미 있으면 스킵
        
        print(f"Row {i}: {name} → {website}")
        emails = fetch_emails_from_url(website)
        
        if emails:
            best = sorted(emails)[0]  # 알파벳 첫번째
            print(f"  ✅ {best}")
            updates.append((i, best))
        else:
            print(f"  ❌ 이메일 없음")
        
        time.sleep(0.5)
    
    # 배치 업데이트
    if updates:
        batch = [{"range": f"D{row_i}", "values": [[email]]} for row_i, email in updates]
        ws.batch_update(batch)
        print(f"\n✅ {len(updates)}개 이메일 업데이트 완료")
    else:
        print("\n추출된 이메일 없음")

if __name__ == "__main__":
    main()
