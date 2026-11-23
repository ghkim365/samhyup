@echo off
chcp 65001 >nul
echo [삼협철망 디버깅 크롬 브라우저 실행 중...]
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="d:\Antigravity\builder-samhyup-sales\sales\blog\chrome_debug_profile" https://blog.naver.com/samhyupm
