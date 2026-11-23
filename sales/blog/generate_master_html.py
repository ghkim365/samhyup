# -*- coding: utf-8 -*-
"""
삼협철망(주) B2B 네이버 블로그 포스팅 마스터 HTML 생성 스크립트
삼협철망 공식 네이버 블로그 주요 공지 글 및 주력 제품군(용접철망, 일체형메쉬, 견사망, 개비온철망, 메쉬파레트, 동물보호휀스) 데이터 반영
단 하나의 통합 마스터 HTML 생성: samhyup_blog_master.html
"""
import os
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

BLOG_DIR = r"d:\Antigravity\builder-samhyup-sales\sales\blog"
CATALOG_IMG_DIR = r"d:\Antigravity\builder-samhyup-sales\catalog\images"
CATALOG_GALLERY_DIR = r"d:\Antigravity\builder-samhyup-sales\catalog\gallery"
OUTPUT_HTML = os.path.join(BLOG_DIR, "samhyup_blog_master.html")

os.makedirs(BLOG_DIR, exist_ok=True)

def get_b64(path):
    if not os.path.exists(path):
        print(f"⚠️ 이미지 파일 없음: {path}")
        return ""
    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('utf-8')}"

def build_master_html():
    logo_b64 = get_b64(os.path.join(CATALOG_IMG_DIR, "logo_samhyup.png"))
    banner_b64 = get_b64(os.path.join(CATALOG_IMG_DIR, "banner.png"))
    
    # 1. 용접철망 (가장 주력 - 4장)
    mesh_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "assembled_mesh_01.jpg"))
    mesh_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "assembled_mesh_02.jpg"))
    mesh_03 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "assembled_mesh_03.jpg"))
    mesh_04 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "assembled_mesh_04.jpg"))

    # 2. 인테리어용접 / 일체형메쉬 (4장)
    interior_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "interior_welding_01.jpg"))
    interior_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "interior_welding_02.jpg"))
    integral_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "integral_mesh_01.jpg"))
    integral_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "integral_mesh_02.jpg"))

    # 3. 메쉬파레트 / 견사망 (4장)
    pallet_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "mesh_pallet_01.jpg"))
    pallet_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "mesh_pallet_02.jpg"))
    pet_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "pet_fence_01.jpg"))
    pet_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "pet_fence_02.jpg"))

    # 4. 개비온철망 / 동물보호휀스 (4장)
    gabion_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "gabion_01.jpg"))
    gabion_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "gabion_02.jpg"))
    protect_01 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "protection_fence_01.jpg"))
    protect_02 = get_b64(os.path.join(CATALOG_GALLERY_DIR, "protection_fence_02.jpg"))

    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[삼협철망(주) 네이버 블로그 마스터 원고] 용접철망·일체형메쉬·개비온·견사망 맞춤 제작 가이드</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --naver-green: #03C75A;
      --navy-dark: #0f172a;
      --navy-blue: #1e293b;
      --accent-orange: #ea580c;
      --accent-blue: #0284c7;
      --bg-gray: #f1f5f9;
      --text-main: #334155;
      --text-title: #0f172a;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Noto Sans KR', sans-serif;
      background-color: var(--bg-gray);
      color: var(--text-main);
      line-height: 1.85;
      padding: 30px 15px;
      word-break: keep-all;
    }}
    .blog-container {{
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 16px;
      box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }}
    .blog-top-banner {{
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      padding: 20px 30px;
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 4px solid var(--naver-green);
    }}
    .blog-top-banner .brand-logo {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .blog-top-banner img {{
      max-height: 44px;
      width: auto;
    }}
    .blog-top-banner .brand-name {{
      font-size: 20px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.5px;
    }}
    .btn-rich-copy {{
      background: var(--naver-green);
      color: #ffffff;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 15px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 12px rgba(3, 199, 90, 0.3);
      transition: all 0.2s ease;
    }}
    .btn-rich-copy:hover {{
      background: #02b350;
      transform: translateY(-2px);
    }}
    .post-content {{ padding: 45px 36px; }}
    .post-category {{ color: var(--accent-blue); font-weight: 800; font-size: 15px; margin-bottom: 10px; }}
    .post-title {{ font-size: 27px; font-weight: 900; color: var(--text-title); line-height: 1.38; margin-bottom: 18px; letter-spacing: -0.8px; }}
    .post-meta {{ font-size: 13.5px; color: #94a3b8; border-bottom: 2px solid #f1f5f9; padding-bottom: 22px; margin-bottom: 35px; display: flex; gap: 16px; flex-wrap: wrap; }}
    
    .blog-greeting {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid var(--naver-green); padding: 24px; border-radius: 10px; font-size: 16px; color: #334155; margin-bottom: 35px; line-height: 1.8; }}
    
    h2.section-h2 {{ font-size: 22px; font-weight: 900; color: #0f172a; margin: 45px 0 20px; padding-bottom: 10px; border-bottom: 3px solid #e2e8f0; display: flex; align-items: center; gap: 8px; }}
    p {{ margin-bottom: 18px; font-size: 16px; word-break: keep-all; }}
    ul.bullet-list {{ margin: 0 0 25px 20px; font-size: 15.5px; }}
    ul.bullet-list li {{ margin-bottom: 10px; line-height: 1.7; }}
    
    .spec-table {{ width: 100%; border-collapse: collapse; margin: 25px 0 35px; border-radius: 10px; overflow: hidden; border: 1px solid #cbd5e1; font-size: 14.5px; word-break: keep-all; }}
    .spec-table th {{ background: #0f172a; color: #ffffff; font-weight: 700; padding: 14px 16px; text-align: center; border-right: 1px solid #334155; }}
    .spec-table td {{ padding: 13px 16px; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; text-align: center; color: #334155; }}
    .spec-table tr:nth-child(even) {{ background-color: #f8fafc; }}

    .blog-image-gallery-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 25px 0; }}
    .blog-image-gallery-2col .gallery-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
    .blog-image-gallery-2col .gallery-card img {{ width: 100%; height: 240px; object-fit: cover; display: block; }}
    .blog-image-gallery-2col .gallery-card .caption {{ padding: 11px 14px; font-size: 13.5px; color: #475569; text-align: center; font-weight: 600; background: #f8fafc; border-top: 1px solid #f1f5f9; }}

    .highlight-banner-card {{ background: #ffffff; border: 2px solid #03C75A; border-radius: 14px; padding: 16px; text-align: center; margin: 30px 0; box-shadow: 0 6px 16px rgba(3, 199, 90, 0.1); }}
    .highlight-banner-card img {{ width: 100%; max-width: 740px; height: auto; border-radius: 10px; margin-bottom: 10px; }}

    .cta-banner {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 35px 28px; border-radius: 14px; text-align: center; margin-top: 50px; }}
    .cta-banner h3 {{ font-size: 22px; font-weight: 900; margin-bottom: 10px; color: #ffffff; }}
    .cta-banner p {{ font-size: 15px; color: #94a3b8; margin-bottom: 22px; }}
    .cta-info-grid {{ display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; margin-bottom: 20px; font-size: 15px; text-align: left; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; }}
    
    .clean-text-box {{ background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 25px; margin-top: 50px; font-size: 14.5px; color: #334155; white-space: pre-wrap; word-break: break-all; line-height: 1.8; }}
  </style>
</head>
<body>

<div class="blog-container">
  <div class="blog-top-banner">
    <div class="brand-logo">
      <img src="{logo_b64}" alt="삼협철망 로고">
      <span class="brand-name">삼협철망(주)</span>
    </div>
    <button class="btn-rich-copy" onclick="copyRichText()">
      📋 네이버 블로그 원클릭 복사
    </button>
  </div>

  <div class="post-content" id="blogPostContent">
    <div class="post-category">용접철망 &amp; 철망 2차가공 전문 · 삼협철망(주)</div>
    <h1 class="post-title">[공지] 용접철망·일체형메쉬·견사망·개비온 전문 제조업체 삼협철망(주) - 맞춤형 철망 솔루션의 모든 것</h1>
    <div class="post-meta">
      <span>작성자: 삼협철망(주) 마케팅팀</span>
      <span>작성일: 2026-10-04</span>
      <span>공식 블로그 연동 B2B 통합 마스터 원고</span>
    </div>

    <div class="blog-greeting">
      안녕하세요! 40년 전통의 기술력과 자동화 용접 설비를 바탕으로 고품질 용접철망 및 특수 철망을 생산·가공하는 <strong>삼협철망(주)</strong> 공식 블로그입니다.<br><br>
      저희 삼협철망(주)은 인천 서구 왕길동 본사 공장에서 <strong>용접철망(가장 주력 품목), 와이어메쉬, 일체형 메쉬, 인테리어용접, 메쉬파레트, 견사망, 개비온 철망, 동물보호휀스</strong>를 중간 유통 거품 없는 공장 직판 합리적 단가로 제작·전국 출고하고 있습니다. (※ 능곡망 및 크림프망은 취급하지 않습니다.)
    </div>

    <!-- 공장 배너 사진 -->
    <div class="highlight-banner-card">
      <img src="{banner_b64}" alt="삼협철망 공장 전경 배너">
      <div style="font-weight: 700; color: #0f172a; font-size: 15px;">▲ 인천 왕길동 공장 자동화 생산 라인 &amp; 전국 직송 출고 시스템</div>
    </div>

    <!-- 1. [가장 주력] 용접철망 & 와이어메쉬 -->
    <h2 class="section-h2">🏆 1. [가장 주력 제품] 용접철망 (Welded Mesh) &amp; 와이어메쉬</h2>
    <p>용접철망은 삼협철망(주)의 매출 1위 핵심 생산품입니다. 자동화 전기저항 용접 방식으로 교차점을 정밀 용접하여 격자 구조가 흐트러지지 않으며 뛰어난 인장강도와 결합력을 자랑합니다.</p>
    <ul class="bullet-list">
      <li><strong>주요 소재:</strong> 흑선(생선), 고내식 아연도금선, SUS304 스테인리스 강선</li>
      <li><strong>선경(Wire Dia):</strong> 2.0Ø ~ 8.0Ø (요청 규격 맞춤 가공 가능)</li>
      <li><strong>망목(Grid Mesh):</strong> 20mm × 20mm ~ 75mm × 75mm 이상 (선경별 맞춤)</li>
      <li><strong>제작 가능 규격:</strong> 최대 2,400mm × 6,000mm 판망 제작</li>
      <li><strong>주요 용도:</strong> 건축 기초 슬라브, 미장용, 산업용 안전망, 필터망 프레임</li>
    </ul>

    <div class="blog-image-gallery-2col">
      <div class="gallery-card">
        <img src="{mesh_01}" alt="용접철망 01">
        <div class="caption">▲ [용접철망 01] 정밀 격자 구조 용접철망 완제품</div>
      </div>
      <div class="gallery-card">
        <img src="{mesh_02}" alt="용접철망 02">
        <div class="caption">▲ [용접철망 02] 고강도 아연도금 용접철망 출고 대기</div>
      </div>
    </div>
    <div class="blog-image-gallery-2col">
      <div class="gallery-card">
        <img src="{mesh_03}" alt="용접철망 03">
        <div class="caption">▲ [용접철망 03] 대형 사이즈 수직/수평 격자 용접</div>
      </div>
      <div class="gallery-card">
        <img src="{mesh_04}" alt="용접철망 04">
        <div class="caption">▲ [용접철망 04] 공장 자동화 정밀 용접 스폿 상세</div>
      </div>
    </div>

    <!-- 2. 일체형 메쉬 & 인테리어 용접 -->
    <h2 class="section-h2">🎨 2. 일체형 메쉬 &amp; 인테리어 디자인 용접</h2>
    <p>철선 교차부를 눌러 플랫 용접(Flat Welding)하여 이음매 단차를 해소한 차세대 매끄러운 메쉬 구조물입니다. 손질이 안전하고 미려한 분체도장 처리가 가능합니다.</p>
    <ul class="bullet-list">
      <li><strong>특징:</strong> 단차가 없어 매끄럽고 세련된 디자인 연출, 내부식성 분체도장 코팅</li>
      <li><strong>용도:</strong> 상업 공간 천정·벽면 인테리어, 전시 매대, 부품 Box, 가구 프레임</li>
    </ul>

    <div class="blog-image-gallery-2col">
      <div class="gallery-card">
        <img src="{interior_01}" alt="인테리어용접 01">
        <div class="caption">▲ [인테리어 01] 미려한 컬러 분체도장 인테리어망</div>
      </div>
      <div class="gallery-card">
        <img src="{integral_01}" alt="일체형메쉬 01">
        <div class="caption">▲ [일체형 01] 단차 없는 교차부 플랫 용접 일체형메쉬</div>
      </div>
    </div>

    <!-- 3. 메쉬파레트 & 견사망 -->
    <h2 class="section-h2">📦 3. 메쉬파레트 &amp; 조립식 견사망</h2>
    <p>물류 적재용 접이식 메쉬파레트와 현장 볼트 체결식 대형 견사망 솔루션을 제공합니다.</p>
    <ul class="bullet-list">
      <li><strong>메쉬파레트:</strong> 6Ø 선경 / 50x50mm 망목 / 3~4단 다단 적재 / 접이식 보관</li>
      <li><strong>견사망:</strong> 포인트 스폿 정밀 용접 / 볼트·클립 조립식 / 고내식 아연도금</li>
    </ul>

    <div class="blog-image-gallery-2col">
      <div class="gallery-card">
        <img src="{pallet_01}" alt="메쉬파레트 01">
        <div class="caption">▲ [메쉬파레트 01] 고내하중 접이식 물류 메쉬파레트</div>
      </div>
      <div class="gallery-card">
        <img src="{pet_01}" alt="견사망 01">
        <div class="caption">▲ [견사망 01] 조립식 대형 아연도금 견사망</div>
      </div>
    </div>

    <!-- 4. 개비온 철망 & 동물보호휀스 -->
    <h2 class="section-h2">⛰️ 4. 개비온 철망 (Gabion) &amp; 동물보호휀스</h2>
    <p>토목 친환경 법면 보호 옹벽용 개비온 철망태와 야생동물 로드킬 차단용 고강도 휀스입니다.</p>
    <ul class="bullet-list">
      <li><strong>개비온:</strong> 아연도금 강선 전기저항 용접, 현장 돌채움 시 변형 없는 형상 유지</li>
      <li><strong>동물보호휀스:</strong> 촘촘한 격자망목으로 소형 동물 침입 방지, 내후성 분체도장</li>
    </ul>

    <div class="blog-image-gallery-2col">
      <div class="gallery-card">
        <img src="{gabion_01}" alt="개비온철망 01">
        <div class="caption">▲ [개비온 01] 친환경 토목 옹벽용 용접 개비온 철망태</div>
      </div>
      <div class="gallery-card">
        <img src="{protect_01}" alt="동물보호휀스 01">
        <div class="caption">▲ [동물보호망 01] 야생동물 로드킬 차단 고강도 휀스</div>
      </div>
    </div>

    <!-- 제원표 -->
    <h3 style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 35px; margin-bottom: 12px;">📊 삼협철망(주) 주요 생산 품목 가공 규격 표</h3>
    <table class="spec-table">
      <thead>
        <tr>
          <th>품목 구분</th>
          <th>선경 범위</th>
          <th>망목 / 가공 규격</th>
          <th>주요 특징 및 적용 분야</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>용접철망 (주력)</strong></td>
          <td>2.0Ø ~ 8.0Ø</td>
          <td>20x20mm ~ 75x75mm 이상</td>
          <td>건축 기초, 와이어메쉬, 정밀 용접 격자</td>
        </tr>
        <tr>
          <td><strong>인테리어 / 일체형</strong></td>
          <td>2.0Ø ~ 5.0Ø</td>
          <td>맞춤형 플랫 용접</td>
          <td>단차 없음, 분체도장 컬러 마감, 매장·천장</td>
        </tr>
        <tr>
          <td><strong>메쉬파레트</strong></td>
          <td>6.0Ø</td>
          <td>50mm × 50mm (다단 적재)</td>
          <td>접이식 공간 절감, 지게차 이동 용이</td>
        </tr>
        <tr>
          <td><strong>견사망 / 휀스</strong></td>
          <td>3.2Ø ~ 5.0Ø</td>
          <td>맞춤 조립 규격</td>
          <td>볼트 체결식 조립, 포인트 스폿 용접</td>
        </tr>
        <tr>
          <td><strong>개비온 / 동물보호</strong></td>
          <td>4.0Ø ~ 6.0Ø</td>
          <td>용접형 격자 망태 구조</td>
          <td>법면 옹벽, 조경 벽체, 로드킬 방지망</td>
        </tr>
      </tbody>
    </table>

    <!-- CTA 문의 바너 -->
    <div class="cta-banner">
      <h3>📞 삼협철망(주) 공장 직판 빠른 견적 문의</h3>
      <p>도면이나 희망 규격·수량을 FAX 또는 이메일로 보내주시면 24시간 내 최저 단가 견적서를 제출합니다.</p>
      
      <div class="cta-info-grid">
        <div>
          • <strong>견적/가공 문의 (직통):</strong> TEL 032-563-4558 / 010-7708-0852<br>
          • <strong>팩스 도면 접수:</strong> FAX 032-563-4234
        </div>
        <div>
          • <strong>이메일 접수:</strong> samhyupm@naver.com<br>
          • <strong>공장 주소:</strong> 인천광역시 서구 사월로37번길 25 (왕길동)<br>
          • <strong>공식 웹사이트:</strong> <a href="http://www.samhyup.com/" target="_blank" style="color:#38bdf8;">www.samhyup.com</a>
        </div>
      </div>
    </div>

    <!-- 순수 텍스트 복사용 박스 -->
    <div class="clean-text-box">
■ 네이버 블로그 복사용 텍스트 (Ctrl+C / Ctrl+V)

[공지] 용접철망 전문 제조업체 삼협철망(주) - 맞춤형 철망 솔루션의 모든 것

안녕하세요! 40년 전통의 기술력과 최첨단 자동화 용접 설비를 보유한 용접철망 전문 제조업체 삼협철망(주)입니다.

저희 삼협철망(주)은 중간 유통 단계를 없앤 공장 직판 합리적 단가로 전국 건설 현장 및 산업체에 용접철망을 대량 공급하고 있습니다.

■ 주력 생산 및 가공 품목
1. 용접철망 (가장 주력 제품): 선경 2.0Ø~8.0Ø / 망목 20x20mm~75x75mm이상 / 최대 2.4m x 6.0m
2. 일체형 메쉬 & 인테리어용접: 교차부 플랫 용접으로 단차 없는 매끈한 표면, 분체도장 마감
3. 메쉬파레트 & 견사망: 6.0Ø 고내하중 접이식 메쉬파레트, 조립식 대형 견사망
4. 개비온 철망 & 동물보호휀스: 친환경 법면 보호 옹벽 개비온, 로드킬 방지 고강도 휀스
(※ 능곡망 및 크림프망은 취급하지 않습니다.)

■ 견적 및 도면 접수처
- 견적/가공 문의 (직통): TEL 032-563-4558 / 010-7708-0852
- 팩스 도면 접수: FAX 032-563-4234
- 이메일: samhyupm@naver.com
- 주소: 인천광역시 서구 사월로37번길 25 (왕길동)
- 홈페이지: http://www.samhyup.com/
    </div>
  </div>
</div>

<script>
function copyRichText() {{
  const container = document.getElementById('blogPostContent');
  const range = document.createRange();
  range.selectNode(container);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  try {{
    document.execCommand('copy');
    alert('✅ 네이버 블로그용 스마트에디터 원고(이미지 및 서식 포함)가 클립보드에 복사되었습니다! 네이버 글쓰기 화면에서 Ctrl+V 하시면 완벽히 입력됩니다.');
  }} catch (err) {{
    alert('⚠️ 복사 중 오류가 발생했습니다. 영역을 직접 드래그하여 Ctrl+C 하세요.');
  }}
  selection.removeAllRanges();
}}
</script>

</body>
</html>
'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Successfully generated {OUTPUT_HTML}")

if __name__ == "__main__":
    build_master_html()
