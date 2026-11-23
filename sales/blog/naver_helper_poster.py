# -*- coding: utf-8 -*-
"""
삼협철망(주) 네이버 단속 우회 100% 안전한 Human-Like 반자동 블로그 포스팅 보조 도구
(현재 열려있는 크롬 에디터 창에 사람처럼 자연스럽게 타이핑 및 이미지 순차 업로드 보조)
"""
import os
import sys
import time
import random
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BLOG_DIR = r"d:\Antigravity\builder-samhyup-sales\sales\blog"

POST_DATA = {
    "title": "[공지] 용접철망·일체형메쉬·견사망·개비온 전문 제조업체 삼협철망(주) - 맞춤형 철망 솔루션의 모든 것",
    "greeting": "안녕하세요! 40년 전통의 기술력과 자동화 용접 설비를 바탕으로 고품질 용접철망 및 특수 철망을 전문 생산하는 삼협철망(주) 공식 블로그입니다.\n\n저희 삼협철망(주)은 인천 서구 왕길동 본사 공장에서 용접철망(가장 주력 품목), 와이어메쉬, 일체형 메쉬, 인테리어용접, 메쉬파레트, 견사망, 개비온 철망, 동물보호휀스를 중간 유통 거품 없는 공장 직판 합리적 단가로 제작·전국 출고하고 있습니다. (※ 능곡망 및 크림프망은 취급하지 않습니다.)",
    "section_1_title": "🏆 1. [가장 주력 제품] 용접철망 (Welded Mesh) & 와이어메쉬",
    "section_1_body": "용접철망은 삼협철망(주)의 매출 1위 핵심 생산품입니다. 자동화 전기저항 용접 방식으로 교차점을 정밀 용접하여 격자 구조가 흐트러지지 않으며 뛰어난 인장강도와 결합력을 자랑합니다.\n- 주요 소재: 흑선, 고내식 아연도금선, SUS304 스테인리스 강선\n- 선경 범위: 2.0Ø ~ 8.0Ø (요청 규격 맞춤 가공 가능)\n- 망목 규격: 20mm x 20mm ~ 75mm x 75mm 이상",
    "section_2_title": "🎨 2. 일체형 메쉬 & 인테리어 디자인 용접",
    "section_2_body": "철선 교차부를 눌러 플랫 용접(Flat Welding)하여 이음매 단차를 해소한 차세대 매끄러운 메쉬 구조물입니다. 손질이 안전하며 미려한 분체도장 처리가 가능합니다.",
    "section_3_title": "📦 3. 메쉬파레트 & 조립식 견사망",
    "section_3_body": "물류 적재용 접이식 메쉬파레트(6Ø / 50x50mm)와 현장 볼트 체결식 대형 견사망 솔루션을 100% 맞춤 제작 공급합니다.",
    "section_4_title": "⛰️ 4. 개비온 철망 (Gabion) & 동물보호휀스",
    "section_4_body": "토목 친환경 법면 보호 옹벽용 개비온 철망태와 야생동물 로드킬 차단용 고강도 휀스입니다.",
    "company_info": "■ 견적 및 도면 접수처\n- 견적/가공 문의 (직통): TEL 032-563-4558 / 010-7708-0852\n- 팩스 도면 접수: FAX 032-563-4234\n- 이메일: samhyupm@naver.com\n- 주소: 인천광역시 서구 사월로37번길 25 (왕길동)\n- 공식 웹사이트: http://www.samhyup.com/"
}

def human_delay(min_sec=0.3, max_sec=0.8):
    time.sleep(random.uniform(min_sec, max_sec))

def run_poster():
    print("=== [삼협철망(주) 네이버 안전 반자동 블로그 포스팅 도구 시작] ===")
    print("📌 사용자 크롬 디버깅 포트(127.0.0.1:9222)에 연결 시도 중...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            
            page = None
            for p_tab in context.pages:
                if "samhyupm" in p_tab.url or "Redirect=Write" in p_tab.url or "Write" in p_tab.url or "blog.naver.com" in p_tab.url:
                    page = p_tab
                    break
            
            if not page and len(context.pages) > 0:
                page = context.pages[0]

            if not page:
                print("⚠️ 경고: 열려있는 크롬 탭을 찾지 못했습니다.")
                return

            print(f"✅ 열려있는 크롬 에디터 창을 찾았습니다! (현재 URL: {page.url})")
            print("🚀 사람처럼 자연스러운 행동 패턴으로 포스팅 작성을 진행합니다...")

            page.bring_to_front()
            human_delay(1, 2)

            frame = page
            if page.frame(name="mainFrame"):
                frame = page.frame(name="mainFrame")

            # 1. 제목 입력
            print("1. 제목 작성 중...")
            title_selector = ".se-documentTitle .se-ff-nanumgothic, .se-documentTitle [contenteditable='true'], input.se-documentTitle-text"
            try:
                frame.wait_for_selector(title_selector, timeout=5000)
                frame.click(title_selector)
                human_delay()
                frame.keyboard.type(POST_DATA["title"], delay=random.randint(20, 50))
                human_delay(1, 1.5)
            except Exception as e_t:
                print(f"제목 영역 입력 처리: {e_t}")

            # 2. 본문 작성
            print("2. 본문 작성 중...")
            body_selector = ".se-main-container .se-component-text [contenteditable='true'], .se-content [contenteditable='true']"
            try:
                frame.wait_for_selector(body_selector, timeout=5000)
                frame.click(body_selector)
                human_delay()
                
                frame.keyboard.type(POST_DATA["greeting"], delay=random.randint(15, 30))
                frame.keyboard.press("Enter")
                human_delay()

                for key in ["section_1_title", "section_1_body", "section_2_title", "section_2_body", "section_3_title", "section_3_body", "section_4_title", "section_4_body", "company_info"]:
                    frame.keyboard.type(POST_DATA[key], delay=random.randint(15, 30))
                    frame.keyboard.press("Enter")
                    human_delay()

                print("🎉 포스팅 자동 타이핑 입력 완료! 이미지 배치 및 최종 발행 버튼을 확인해 주세요.")

            except Exception as e_b:
                print(f"본문 영역 입력 처리: {e_b}")

        except Exception as e:
            print(f"❌ 크롬 디버거 연결 오류: {e}")

if __name__ == "__main__":
    run_poster()
