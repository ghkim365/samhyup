// [중요] 구글 스프레드시트 연동용 앱스 스크립트 웹 앱 URL을 배포 후 아래 빈칸에 붙여넣으세요.
// 예: "https://script.google.com/macros/s/AKfycb.../exec"
const GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwdvHIlVa80e-JNZFnF9cqJYrDQfMg2DUxSyF_tIN5yy0SWiGnUMprGaGEDj9rDZ1kJTQ/exec";

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

// LocalStorage에 견적 정보 기록 헬퍼 함수
function saveQuoteToAnalytics(company, name, phone, email, product, specs, attachment) {
    try {
        const currentData = JSON.parse(localStorage.getItem('samhyup_analytics')) || { visits: { google_ads: 0, search: 0, direct: 0 }, quotes: [] };
        const sessionSource = sessionStorage.getItem('samhyup_session_source') || 'direct';
        const attachmentName = attachment || '';
        
        const newQuote = {
            id: currentData.quotes.length > 0 ? Math.max(...currentData.quotes.map(q => q.id)) + 1 : 1,
            date: new Date().toISOString(),
            company: company,
            name: name,
            phone: phone,
            email: email,
            product: product,
            specs: specs || '별도 기재 없음',
            source: sessionSource,
            attachment: attachmentName
        };
        
        currentData.quotes.push(newQuote);
        localStorage.setItem('samhyup_analytics', JSON.stringify(currentData));

        // 구글 스프레드시트 실시간 전송 연동 (sendBeacon / fetch 사용)
        if (GAS_WEB_APP_URL && GAS_WEB_APP_URL.startsWith('http')) {
            const payload = JSON.stringify({
                action: 'submitQuote',
                site: 'catalog',
                source: sessionSource,
                company: company,
                name: name,
                phone: phone,
                email: email,
                product: product,
                specs: specs || '별도 기재 없음',
                attachment: attachmentName
            });

            if (navigator.sendBeacon) {
                const blob = new Blob([payload], { type: 'text/plain;charset=utf-8' });
                navigator.sendBeacon(GAS_WEB_APP_URL, blob);
                console.log('GAS quote submitted via sendBeacon.');
            } else {
                fetch(GAS_WEB_APP_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'text/plain;charset=utf-8'
                    },
                    body: payload
                }).catch(err => console.error('GAS quote submit error:', err));
            }
        }
    } catch (e) {
        console.error('Error saving quote to analytics:', e);
    }
}

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
            // 로컬 스토리지에 저장
            const attachmentName = (fileInput && fileInput.files.length > 0) ? fileInput.files[0].name : '';
            saveQuoteToAnalytics(company, name, phone, email, product, specs, attachmentName);
            
            // Google Ads 전환 추적 이벤트 전송
            if (typeof gtag === 'function') {
                gtag('event', 'conversion', {
                    'send_to': 'AW-750842470/hAmFCITOvM4cEObkg-YC'
                });
            }
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
        
        // 로컬 스토리지에 저장 (실패 시에도 분석 통계 보존을 위해 견적 시도로 기록)
        const attachmentName = (fileInput && fileInput.files.length > 0) ? fileInput.files[0].name : '';
        saveQuoteToAnalytics(company, name, phone, email, product, specs, attachmentName);
        
        // Google Ads 전환 추적 이벤트 전송 (폴백 전송 시도 시에도 이벤트 발송)
        if (typeof gtag === 'function') {
            gtag('event', 'conversion', {
                'send_to': 'AW-750842470/hAmFCITOvM4cEObkg-YC'
            });
        }
        
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

// LocalStorage 분석 데이터 초기화 및 방문 추적
(function() {
    // 순수한 실시간 데이터 초기 상태 (더미 없음)
    const initialData = {
        visits: {
            google_ads: 0,
            search: 0,
            direct: 0
        },
        quotes: []
    };

    // 로컬 스토리지에 데이터가 없으면 초기 데이터 세팅
    if (!localStorage.getItem('samhyup_analytics')) {
        localStorage.setItem('samhyup_analytics', JSON.stringify(initialData));
    }

    // 이번 세션의 유입 소스 판단 및 기록
    if (!sessionStorage.getItem('samhyup_session_recorded')) {
        let source = 'direct';
        const urlParams = new URLSearchParams(window.location.search);
        
        // 1. Google Ads 유입 판정 (gclid 파라미터가 있거나, utm_source가 google이거나, utm_medium이 cpc일 때)
        if (urlParams.has('gclid') || urlParams.get('utm_source') === 'google' || urlParams.get('utm_medium') === 'cpc') {
            source = 'google_ads';
        } 
        // 2. 검색 엔진 유입 판정 (referrer가 네이버, 다음, 구글 등일 때)
        else if (document.referrer) {
            const referrer = document.referrer.toLowerCase();
            if (referrer.includes('naver.com') || referrer.includes('daum.net') || referrer.includes('google.co.kr') || referrer.includes('google.com')) {
                source = 'search';
            }
        }

        // 저장된 통계 업데이트
        try {
            const currentData = JSON.parse(localStorage.getItem('samhyup_analytics')) || initialData;
            currentData.visits[source] = (currentData.visits[source] || 0) + 1;
            localStorage.setItem('samhyup_analytics', JSON.stringify(currentData));
            sessionStorage.setItem('samhyup_session_recorded', 'true');
            sessionStorage.setItem('samhyup_session_source', source);

            // 구글 스프레드시트 실시간 방문 전송
            if (GAS_WEB_APP_URL && GAS_WEB_APP_URL.startsWith('http')) {
                fetch(GAS_WEB_APP_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'text/plain;charset=utf-8'
                    },
                    body: JSON.stringify({
                        action: 'trackVisit',
                        site: 'catalog',
                        source: source
                    })
                }).catch(err => console.error('GAS visit track error:', err));
            }
        } catch (e) {
            console.error('Error updating analytics data:', e);
        }
    }
})();

// 로고 5회 연속 클릭 시 비밀 마케팅 대시보드로 이동하는 히든 포털 기능
let logoClickCount = 0;
let logoClickTimeout = null;

function handleLogoClick(event) {
    event.preventDefault();
    logoClickCount++;
    
    // 3초 동안 추가 클릭이 없으면 카운터 리셋
    clearTimeout(logoClickTimeout);
    logoClickTimeout = setTimeout(() => {
        logoClickCount = 0;
    }, 3000);
    
    // 5번 연속 클릭 시 대시보드 새 탭 열기
    if (logoClickCount >= 5) {
        logoClickCount = 0;
        window.open('dashboard.html', '_blank');
    }
}


// ── GALLERY FILTER & MODAL ──
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.gallery-tab');
    const items = document.querySelectorAll('.gallery-item');
    
    // Tab filtering
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            
            const filter = tab.getAttribute('data-filter');
            
            items.forEach(item => {
                const category = item.getAttribute('data-category');
                if (filter === 'all' || filter === category) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });
        });
    });

    // Modal control
    const modal = document.getElementById('galleryModal');
    const modalImg = document.getElementById('galleryModalImg');
    const modalBadge = document.getElementById('galleryModalBadge');
    const modalTitle = document.getElementById('galleryModalTitle');
    const modalDesc = document.getElementById('galleryModalDesc');
    const modalClose = document.getElementById('galleryModalClose');
    const modalBackdrop = document.getElementById('galleryModalBackdrop');
    const modalQuoteBtn = document.getElementById('galleryModalQuoteBtn');

    if (modal) {
        items.forEach(item => {
            item.addEventListener('click', () => {
                const img = item.querySelector('img').src;
                const title = item.getAttribute('data-title');
                const desc = item.getAttribute('data-desc');
                const catText = item.querySelector('.gallery-cat-badge').textContent;
                const service = item.getAttribute('data-service');
                
                modalImg.src = img;
                modalImg.alt = title;
                modalBadge.textContent = catText;
                modalTitle.textContent = title;
                modalDesc.textContent = desc;
                
                modalQuoteBtn.onclick = () => {
                    selectProduct(service);
                    closeModal();
                };
                
                modal.classList.add('open');
                document.body.style.overflow = 'hidden';
            });
        });

        const closeModal = () => {
            modal.classList.remove('open');
            document.body.style.overflow = '';
        };

        if (modalClose) modalClose.addEventListener('click', closeModal);
        if (modalBackdrop) modalBackdrop.addEventListener('click', closeModal);
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('open')) {
                closeModal();
            }
        });
    }
});
