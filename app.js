// 관심 품목 자동 입력 함수
function selectProduct(productName) {
    const selectEl = document.getElementById('productSelect');
    if (selectEl) {
        selectEl.value = productName;
        // 선택 후 견적 폼으로 부드럽게 스크롤
        document.getElementById('quote-form').scrollIntoView({ behavior: 'smooth' });
    }
}

// 첨부파일 선택 시 파일명 표시 기능
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileAttachment');
    const fileNameDisplay = document.getElementById('fileName');
    
    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                const sizeInMB = file.size / (1024 * 1024);
                if (sizeInMB > 10) {
                    alert('파일 용량이 10MB를 초과합니다. 10MB 이하의 파일만 첨부 가능합니다.');
                    fileInput.value = '';
                    fileNameDisplay.textContent = '선택된 파일 없음 (최대 10MB)';
                } else {
                    fileNameDisplay.textContent = file.name;
                }
            } else {
                fileNameDisplay.textContent = '선택된 파일 없음 (최대 10MB)';
            }
        });
    }
});

// 견적 문의 폼 제출 이벤트 핸들러
function handleQuoteSubmit(event) {
    event.preventDefault();
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;
    
    // 전송 중 UI 상태 표시
    submitBtn.disabled = true;
    submitBtn.textContent = '견적 전송 중...';
    
    const company = document.getElementById('companyName').value;
    const name = document.getElementById('contactPerson').value;
    const phone = document.getElementById('contactPhone').value;
    const email = document.getElementById('contactEmail').value;
    const product = document.getElementById('productSelect').value;
    const specs = document.getElementById('specsInput').value;
    const fileInput = document.getElementById('fileAttachment');

    // FormSubmit AJAX를 위한 FormData 객체 빌드
    const formData = new FormData();
    formData.append("회사명_현장명", company);
    formData.append("담당자명", name);
    formData.append("연락처", phone);
    formData.append("이메일_주소", email);
    formData.append("요청_품목", product);
    formData.append("희망_규격_및_수량", specs || '별도 기재 없음');
    formData.append("_subject", `[B2B간편견적] ${company} - ${product} 문의`);
    
    // 첨부파일이 있는 경우 추가
    if (fileInput && fileInput.files.length > 0) {
        formData.append("첨부파일", fileInput.files[0]);
    }

    // FormSubmit AJAX 전송
    fetch("https://formsubmit.co/ajax/samhyupm@naver.com", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (response.ok) {
            alert('견적 문의가 온라인으로 성공적으로 접수되었습니다!\n\n※ 처음 전송하시는 경우, 삼협철망 메일(samhyupm@naver.com)로 FormSubmit 발송 활성화 링크가 전송됩니다. 해당 메일에서 "Confirm Email" 버튼을 최초 1회만 클릭해주시면 최종 수신이 시작됩니다.');
            event.target.reset();
            const fileNameDisplay = document.getElementById('fileName');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = '선택된 파일 없음 (최대 10MB)';
            }
        } else {
            throw new Error('FormSubmit 전송 실패');
        }
    })
    .catch(error => {
        console.error('AJAX Submit Error:', error);
        
        // AJAX 실패 시 기존 mailto 링크 폴백 방식 작동
        alert('온라인 즉시 전송이 제한되어, 기본 메일 발송 프로그램(Outlook/Mail 등)을 통해 견적 요청 메일을 작성합니다.\n\n※ 첨부파일이 선택된 경우 메일 프로그램 창이 열린 후 직접 수동으로 첨부해서 발송해 주시기 바랍니다.');
        
        const mailSubject = `[간편견적요청] ${company} - ${product} 문의`;
        const mailBody = `안녕하세요 삼협철망 담당자님,

B2B 웹 카탈로그를 통해 견적 상담을 요청합니다.

[신청 정보]
- 회사명/현장명: ${company}
- 담당자: ${name}
- 연락처: ${phone}
- 이메일: ${email}
- 문의 품목: ${product}

[규격 및 요청사항]
${specs || '별도 기재 없음'}

---
※ 첨부파일이 있으신 경우, 메일 프로그램 실행 후 해당 파일을 첨부하여 발송해 주세요.`;

        const mailtoUrl = `mailto:samhyupm@naver.com?subject=${encodeURIComponent(mailSubject)}&body=${encodeURIComponent(mailBody)}`;
        window.location.href = mailtoUrl;
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    });
}
