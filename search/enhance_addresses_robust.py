# -*- coding: utf-8 -*-
import os, sys, re, time, urllib.parse, logging
import requests
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

CREDS_PATH = r"D:\Antigravity\credentials\ghkim\ghkim_credentials_crawler-hifus_20260221.json"
SPREADSHEET_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

MOBILE_UA = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

log_path = os.path.join(os.path.dirname(__file__), "address_enrichment_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)

def is_short_address(addr):
    if not addr or addr in {"주소없음", "주소"}:
        return True
    tokens = addr.split()
    if len(tokens) <= 3:
        return True
    if re.match(r"^[\w\d]+[동읍면리]$", tokens[-1]):
        return True
    if not any(c.isdigit() for c in addr):
        return True
    return False

def safe_get(url, headers, timeout=10):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.encoding = "utf-8"
        if r.status_code == 200:
            return r
    except Exception as e:
        logging.warning(f"요청 실패: {url} – {e}")
    return None

def get_naver_address(name, region):
    query = urllib.parse.quote(f"{name} {region}")
    r = safe_get(f"https://search.naver.com/search.naver?where=nexearch&query={query}", MOBILE_UA)
    if not r:
        return None
    ids = list(dict.fromkeys(re.findall(r"/place/(\d+)", r.text)))
    for pid in ids[:5]:
        r2 = safe_get(f"https://m.place.naver.com/place/{pid}/home", MOBILE_UA, timeout=12)
        if not r2:
            continue
        # 서비스 제한 감지
        if "서비스 이용이 제한" in r2.text:
            logging.warning(f"Naver 차단 감지 (pid={pid}), 5초 대기...")
            time.sleep(5)
            continue
        m = re.search(r'"roadAddress"\s*:\s*"([^"]+)"', r2.text)
        if not m:
            m = re.search(r'"address"\s*:\s*"([^"]+)"', r2.text)
        if m:
            addr = m.group(1).strip()
            if not is_short_address(addr):
                return addr
    return None

def get_daum_address(name, region):
    query = urllib.parse.quote(f"{name} {region}")
    r = safe_get(
        f"https://search.daum.net/search?w=tot&q={query}",
        {"User-Agent": "Mozilla/5.0", "Accept-Language": "ko-KR,ko;q=0.9"},
        timeout=10
    )
    if not r:
        return None
    # 도로명/지번 주소 패턴 탐색
    for pat in [
        r"((?:서울|경기|인천|부산|대구|광주|대전|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주)[^\"\[\]<>]{5,40}(?:\d{1,5}[-]?\d{0,5}))",
    ]:
        m = re.search(pat, r.text)
        if m:
            addr = m.group(1).strip()
            if not is_short_address(addr):
                return addr
    return None

def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet("company")

    logging.info("📋 시트 읽는 중...")
    rows = ws.get_all_values()
    logging.info(f"전체 {len(rows)-1}행 로드 완료")

    target_rows = []
    for idx in range(2, 502):   # 행 2~501 (헤더=1)
        row = rows[idx - 1] if idx - 1 < len(rows) else []
        if len(row) < 9:
            continue
        cur_addr = row[8]
        if is_short_address(cur_addr):
            target_rows.append((idx, row[2], row[7], cur_addr))

    logging.info(f"보강 대상: {len(target_rows)}개")

    success, fail = 0, 0
    for i, (sheet_row, name, region, old_addr) in enumerate(target_rows, 1):
        logging.info(f"[{i}/{len(target_rows)}] {name} ({region}) – 현재: {old_addr}")

        new_addr = get_naver_address(name, region)
        src = "Naver"
        if not new_addr:
            new_addr = get_daum_address(name, region)
            src = "Daum"

        if new_addr:
            ws.update_cell(sheet_row, 9, new_addr)   # 주소 열 업데이트
            ws.update_cell(sheet_row, 13, old_addr)  # 이전 주소 보존
            logging.info(f"   ✅ {src} 성공 → {new_addr}")
            success += 1
        else:
            logging.info(f"   ⚠️  주소 못 찾음")
            fail += 1

        time.sleep(0.6)

    logging.info(f"=== 완료 === 성공: {success} / 실패: {fail} ===")

if __name__ == "__main__":
    main()
