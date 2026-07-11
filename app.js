// 관심 품목 자동 입력 함수
function selectProduct(productName) {
    const selectEl = document.getElementById('productSelect');
    if (selectEl) {
        selectEl.value = productName;
        // 선택 후 견적 폼으로 부드럽게 스크롤
        document.getElementById('quote-form').scrollIntoView({ behavior: 'smooth' });
    }
}

// 견적 문의 폼 제출 이벤트 핸들러
function handleQuoteSubmit(event) {
    event.preventDefault();
    
    const company = document.getElementById('companyName').value;
    const name = document.getElementById('contactPerson').value;
    const phone = document.getElementById('contactPhone').value;
    const product = document.getElementById('productSelect').value;
    const specs = document.getElementById('specsInput').value;
    
    // 메일 내용 빌드
    const mailSubject = `[간편견적요청] ${company} - ${product} 문의`;
    const mailBody = `안녕하세요 삼협철망 담당자님,

B2B 웹 카탈로그를 통해 견적 상담을 요청합니다.

[신청 정보]
- 회사명/현장명: ${company}
- 담당자: ${name}
- 연락처: ${phone}
- 문의 품목: ${product}

[규격 및 요청사항]
${specs || '별도 기재 없음'}

---
본 요청서는 삼협철망 B2B 간편 견적 시스템을 통해 작성되었습니다.`;

    // 사용자 메일 클라이언트로 전달 (mailto 링크 생성)
    const mailtoUrl = `mailto:samhyupm@naver.com?subject=${encodeURIComponent(mailSubject)}&body=${encodeURIComponent(mailBody)}`;
    
    // 메일 프로그램 열기
    window.location.href = mailtoUrl;
    
    alert('작성하신 내용으로 삼협철망 영업팀(samhyupm@naver.com)으로 메일 보내기 창을 띄웁니다.\n\n이메일 발송 완료 후 담당자가 실시간으로 검토하여 견적 회신을 드리겠습니다.');
}
