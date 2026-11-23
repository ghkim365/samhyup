# -*- coding: utf-8 -*-
"""
삼협철망(주) B2B 네이버 블로그 홍보 원고 종합 Word (.docx) 생성 스크립트
표준 맑은 고딕, 본문 10pt, H1 14pt, H2 12pt 지침 엄격 준수
"""
import os
import sys
import docx
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.stdout.reconfigure(encoding='utf-8')

BLOG_DIR = r"d:\Antigravity\builder-samhyup-sales\sales\blog"
OUTPUT_DOCX = os.path.join(BLOG_DIR, "삼협철망_B2B_블로그_홍보원고_종합.docx")
IMAGE_DIR = r"d:\Antigravity\builder-samhyup-sales\catalog\images"
GALLERY_DIR = r"d:\Antigravity\builder-samhyup-sales\catalog\gallery"

os.makedirs(BLOG_DIR, exist_ok=True)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def remove_table_borders(table):
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>')
        tblPr[0].append(borders)

def add_heading_styled(doc, text, level):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    run.font.bold = True
    
    if level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(15, 23, 42)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
    elif level == 2:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(30, 41, 59)
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
    else:
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(51, 65, 85)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
    return p

def add_body_p(doc, text, bold=False, italic=False, color_rgb=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    run.font.size = Pt(10)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb
    return p

def add_bullet_p(doc, title, desc):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    
    r_title = p.add_run(title + ": ")
    r_title.font.name = "맑은 고딕"
    r_title._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    r_title.font.size = Pt(10)
    r_title.font.bold = True
    
    r_desc = p.add_run(desc)
    r_desc.font.name = "맑은 고딕"
    r_desc._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    r_desc.font.size = Pt(10)
    return p

def add_2col_images_with_captions(doc, img_file1, cap1, img_file2, cap2):
    table = doc.add_table(rows=1, cols=2)
    remove_table_borders(table)
    
    cell1, cell2 = table.rows[0].cells
    
    img_path1 = os.path.join(GALLERY_DIR, img_file1)
    img_path2 = os.path.join(GALLERY_DIR, img_file2)
    
    if os.path.exists(img_path1):
        p1 = cell1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.add_run().add_picture(img_path1, width=Inches(2.8))
        cp1 = cell1.add_paragraph()
        cp1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc1 = cp1.add_run(cap1)
        rc1.font.name = "맑은 고딕"
        rc1._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
        rc1.font.size = Pt(9)
        rc1.font.color.rgb = RGBColor(71, 85, 105)
        
    if os.path.exists(img_path2):
        p2 = cell2.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.add_run().add_picture(img_path2, width=Inches(2.8))
        cp2 = cell2.add_paragraph()
        cp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc2 = cp2.add_run(cap2)
        rc2.font.name = "맑은 고딕"
        rc2._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
        rc2.font.size = Pt(9)
        rc2.font.color.rgb = RGBColor(71, 85, 105)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def generate_docx():
    doc = Document()
    
    # 마진 2cm
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # 문서 제목 (H1)
    add_heading_styled(doc, "[공지] 용접철망 전문 제조업체 삼협철망(주) - 맞춤형 철망 솔루션 종합 마스터 원고", 1)
    
    add_body_p(doc, "작성자: 삼협철망(주) 마케팅팀 | 작성일: 2026-10-04", bold=True, color_rgb=RGBColor(100, 116, 139))
    add_body_p(doc, "―" * 50)
    
    add_body_p(doc, "안녕하세요, 40년 전통의 기술력과 자동화 용접 설비로 건설 및 산업용 철망을 전문 생산하는 삼협철망(주) 공식 블로그입니다.")
    add_body_p(doc, "본 문서는 네이버 블로그에 게재되는 삼협철망(주)의 6대 주력 제품군(용접철망, 일체형메쉬, 견사망, 개비온, 메쉬파레트, 동물보호휀스)의 통합 원고입니다.")
    add_body_p(doc, "※ 삼협철망(주)은 용접철망 및 2차가공 전문으로, 능곡망과 크림프망은 취급하지 않습니다.")
    
    # 1. 용접철망
    add_heading_styled(doc, "1. [가장 주력 제품] 용접철망 (Welded Wire Mesh) & 와이어메쉬", 2)
    add_body_p(doc, "용접철망은 삼협철망(주)의 대표 주력 품목입니다. 정밀 전기저항 자동 용접 설비를 사용하여 결합력이 우수하며 격자 구조가 안정적으로 유지됩니다.")
    add_bullet_p(doc, "소재 종류", "흑선(생선), 고내식 아연도금선, SUS304 스테인리스 강선")
    add_bullet_p(doc, "선경 범위", "2.0Ø ~ 8.0Ø (요청 시 맞춤 가공 가능)")
    add_bullet_p(doc, "망목 규격", "20mm x 20mm ~ 75mm x 75mm 이상")
    add_bullet_p(doc, "제작 사이즈", "최대 2,400mm x 6,000mm 판망 제작")
    add_bullet_p(doc, "주요 용도", "건축 기초 슬라브, 미장용, 산업용 안전망, 필터망 프레임")
    
    add_2col_images_with_captions(doc, "assembled_mesh_01.jpg", "▲ [용접철망 01] 고강도 용접철망 완제품", "assembled_mesh_02.jpg", "▲ [용접철망 02] 아연도금 용접철망 출고대기")
    add_2col_images_with_captions(doc, "assembled_mesh_03.jpg", "▲ [용접철망 03] 대형 규격 용접철망", "assembled_mesh_04.jpg", "▲ [용접철망 04] 교차부 자동 용접 상세")

    # 2. 일체형메쉬
    add_heading_styled(doc, "2. 일체형 메쉬 & 인테리어 디자인 용접", 2)
    add_body_p(doc, "철선 교차부를 눌러 플랫 용접(Flat Welding)하여 이음매 단차를 없앤 일체형 메쉬 구조입니다. 손질 시 걸림이 없어 안전하며, 미려한 분체도장이 가능합니다.")
    add_bullet_p(doc, "주요 특징", "단차 없는 매끄러운 단면, 뛰어난 컬러 분체도장 및 아연도금 표면 처리")
    add_bullet_p(doc, "주요 용도", "상업 공간 천정·벽면 인테리어, 전시 매대, 부품 Box, 가구 프레임")
    
    add_2col_images_with_captions(doc, "interior_welding_01.jpg", "▲ [인테리어 01] 분체도장 디자인 메쉬", "integral_mesh_01.jpg", "▲ [일체형 01] 교차부 플랫 용접 일체형메쉬")

    # 3. 메쉬파레트 & 견사망
    add_heading_styled(doc, "3. 메쉬파레트 & 조립식 대형 견사망", 2)
    add_body_p(doc, "고내하중 물류 적재용 접이식 메쉬파레트와 현장 조립이 용이한 대형 견사망입니다.")
    add_bullet_p(doc, "메쉬파레트", "6Ø 선경 / 50x50mm 망목 / 3~4단 다단 적재 가능 / 접이식 공간 절감")
    add_bullet_p(doc, "조립식 견사망", "포인트 정밀 스폿 용접 / 용접 없이 볼트/클립 체결식 / 아연도금 부식 방지")
    
    add_2col_images_with_captions(doc, "mesh_pallet_01.jpg", "▲ [메쉬파레트 01] 접이식 물류 메쉬파레트", "pet_fence_01.jpg", "▲ [견사망 01] 조립식 아연도금 견사망")

    # 4. 개비온 철망 & 동물보호휀스
    add_heading_styled(doc, "4. 개비온 철망 (Gabion) & 동물보호휀스", 2)
    add_body_p(doc, "토목 법면 옹벽 보호용 용접 개비온 철망태와 야생동물 차단 휀스입니다.")
    add_bullet_p(doc, "개비온 철망", "아연도금 강선 전기저항 용접, 현장 돌채움 작업 시 변형 없는 정밀 모듈")
    add_bullet_p(doc, "동물보호휀스", "촘촘한 격자망 구조, 야생동물 침입 차단 및 도로 로드킬 방지")
    
    add_2col_images_with_captions(doc, "gabion_01.jpg", "▲ [개비온 01] 용접 개비온 철망태", "protection_fence_01.jpg", "▲ [동물보호망 01] 로드킬 방지 보호 휀스")

    # 제원표
    add_heading_styled(doc, "5. 삼협철망(주) 주요 생산 품목 제원표", 2)
    
    table = doc.add_table(rows=6, cols=4)
    table.style = 'Table Grid'
    
    headers = ["품목 구분", "선경 범위", "망목 / 가공 규격", "주요 용도"]
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "0F172A")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = "맑은 고딕"
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
            
    data = [
        ["용접철망 (주력)", "2.0Ø ~ 8.0Ø", "20x20mm ~ 75x75mm 이상", "건축 슬라브, 와이어메쉬, 정밀 용접 격자"],
        ["인테리어 / 일체형", "2.0Ø ~ 5.0Ø", "맞춤형 플랫 용접", "단차 없음, 분체도장 컬러 마감, 천장 인테리어"],
        ["메쉬파레트", "6.0Ø", "50mm x 50mm", "접이식 보관, 다단 적재, 물류용"],
        ["견사망", "3.2Ø ~ 5.0Ø", "맞춤 조립 규격", "볼트 체결식 조립, 대형 견사"],
        ["개비온 / 동물보호", "4.0Ø ~ 6.0Ø", "용접형 격자 망태", "친환경 법면 옹벽, 조경, 로드킬 방지"]
    ]
    
    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        if row_idx % 2 == 1:
            bg_color = "F8FAFC"
        else:
            bg_color = "FFFFFF"
            
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = text
            set_cell_background(row_cells[col_idx], bg_color)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = "맑은 고딕"
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')
                run.font.size = Pt(9.5)
                if col_idx == 0:
                    run.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 견적 안내 및 고객센터
    add_heading_styled(doc, "6. 견적/가공 문의 및 고객센터", 2)
    add_bullet_p(doc, "견적/가공 문의 (직통)", "TEL 032-563-4558 / 010-7708-0852")
    add_bullet_p(doc, "팩스 도면 접수", "FAX 032-563-4234")
    add_bullet_p(doc, "이메일 접수", "samhyupm@naver.com")
    add_bullet_p(doc, "공장 주소", "인천광역시 서구 사월로37번길 25 (왕길동)")
    add_bullet_p(doc, "공식 웹사이트", "http://www.samhyup.com/")

    doc.save(OUTPUT_DOCX)
    print(f"Successfully generated {OUTPUT_DOCX}")

if __name__ == "__main__":
    generate_docx()
