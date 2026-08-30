/**
 * 삼협철망(주) 공식 홈페이지용 마케팅 & 견적 유입 트래킹 스크립트 (samhyup_tracker.js) - 중복 방지, 에디터 본문, 중복 필터링 최종 패치
 */
(function() {
    const GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwdvHIlVa80e-JNZFnF9cqJYrDQfMg2DUxSyF_tIN5yy0SWiGnUMprGaGEDj9rDZ1kJTQ/exec";

    // 디바운스/중복 전송 제어를 위한 메모리 변수
    let lastSubmitTime = 0;
    let lastSubmitPayload = "";

    function trackVisitorSource() {
        if (sessionStorage.getItem('samhyup_main_session_tracked')) {
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const referrer = document.referrer ? document.referrer.toLowerCase() : '';
        let source = 'direct';

        if (urlParams.has('gclid') || urlParams.get('utm_source') === 'google_ads' || urlParams.get('utm_source') === 'google') {
            source = 'google_ads';
        } else if (referrer.includes('naver.com') || referrer.includes('daum.net') || referrer.includes('google.co.kr') || referrer.includes('google.com') || referrer.includes('bing.com')) {
            source = 'search';
        }

        let rawData = localStorage.getItem('samhyup_main_analytics');
        let data = rawData ? JSON.parse(rawData) : { visits: { google_ads: 0, search: 0, direct: 0 }, quotes: [] };

        if (!data.visits) {
            data.visits = { google_ads: 0, search: 0, direct: 0 };
        }
        data.visits[source] = (data.visits[source] || 0) + 1;
        localStorage.setItem('samhyup_main_analytics', JSON.stringify(data));
        
        sessionStorage.setItem('samhyup_main_session_tracked', 'true');
        sessionStorage.setItem('samhyup_main_source', source);
        console.log('[Samhyup Tracker] Visitor source tracked:', source);

        if (GAS_WEB_APP_URL && GAS_WEB_APP_URL.startsWith('http')) {
            fetch(GAS_WEB_APP_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                body: JSON.stringify({ action: 'trackVisit', site: 'main_site', source: source })
            }).catch(err => console.error('[Samhyup Tracker] GAS visit track error:', err));
        }
    }

    // HTML 태그 제거 헬퍼 함수
    function stripHtml(html) {
        if (!html) return "";
        let tmp = document.createElement("DIV");
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || "";
    }

    function submitQuote(quoteDetails) {
        const now = Date.now();
        const payloadString = JSON.stringify(quoteDetails);

        // 동일 데이터 3초 이내 중복 전송 차단 (디바운싱 방어 코드)
        if (now - lastSubmitTime < 3000 && lastSubmitPayload === payloadString) {
            console.log('[Samhyup Tracker] Duplicate submission blocked by debounce.');
            return;
        }
        lastSubmitTime = now;
        lastSubmitPayload = payloadString;

        let rawData = localStorage.getItem('samhyup_main_analytics');
        let data = rawData ? JSON.parse(rawData) : { visits: { google_ads: 0, search: 0, direct: 0 }, quotes: [] };
        if (!data.quotes) data.quotes = [];

        const source = sessionStorage.getItem('samhyup_main_source') || 'direct';
        const nextId = data.quotes.length > 0 ? Math.max(...data.quotes.map(q => q.id)) + 1 : 101;

        const newQuote = {
            id: nextId,
            date: new Date().toISOString(),
            company: quoteDetails.company || '일반 개인/현장',
            name: quoteDetails.name || '담당자 미기재',
            phone: quoteDetails.phone || '연락처 미기재',
            email: quoteDetails.email || '',
            product: quoteDetails.product || '공식홈 문의',
            specs: quoteDetails.specs || '',
            source: source,
            attachment: quoteDetails.attachment || ''
        };

        data.quotes.push(newQuote);
        localStorage.setItem('samhyup_main_analytics', JSON.stringify(data));
        console.log('[Samhyup Tracker] New quote request pushed:', newQuote);

        if (GAS_WEB_APP_URL && GAS_WEB_APP_URL.startsWith('http')) {
            const payload = JSON.stringify({
                action: 'submitQuote',
                site: 'main_site',
                source: source,
                company: quoteDetails.company || '일반 개인/현장',
                name: quoteDetails.name || '담당자 미기재',
                phone: quoteDetails.phone || '연락처 미기재',
                email: quoteDetails.email || '',
                product: quoteDetails.product || '공식홈 문의',
                specs: quoteDetails.specs || '',
                attachment: quoteDetails.attachment || ''
            });

            if (navigator.sendBeacon) {
                const blob = new Blob([payload], { type: 'text/plain;charset=utf-8' });
                navigator.sendBeacon(GAS_WEB_APP_URL, blob);
                console.log('[Samhyup Tracker] GAS quote submitted via sendBeacon.');
            } else {
                fetch(GAS_WEB_APP_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                    body: payload
                }).catch(err => console.error('[Samhyup Tracker] GAS quote submit error:', err));
            }
        }
    }

    // 폼 제출 파싱 핸들러
    function handleFormSubmit(formEl, type) {
        // 워드프레스 내장 에디터(TinyMCE 등)의 내용을 textarea로 동기화
        if (typeof tinyMCE !== 'undefined') {
            try {
                tinyMCE.triggerSave();
            } catch (e) {
                console.log('[Samhyup Tracker] TinyMCE triggerSave error:', e);
            }
        }

        let titleInput, writerInput, contentInput, phoneInput, emailInput, companyInput;

        if (type === 'cafe24') {
            titleInput = formEl.querySelector('input[name="subject"]') || formEl.querySelector('#subject');
            writerInput = formEl.querySelector('input[name="writer"]') || formEl.querySelector('#writer') || formEl.querySelector('input[name="name"]');
            contentInput = formEl.querySelector('textarea[name="content"]') || formEl.querySelector('#content');
            phoneInput = formEl.querySelector('input[name^="phone"]') || formEl.querySelector('input[title*="연락처"]') || formEl.querySelector('input[title*="전화"]');
            emailInput = formEl.querySelector('input[name^="email"]') || formEl.querySelector('input[title*="이메일"]');
            companyInput = null;
        } else {
            // KBoard
            titleInput = formEl.querySelector('input[name="title"]') || formEl.querySelector('input[name="subject"]');
            writerInput = formEl.querySelector('input[name="member_display"]') || 
                          formEl.querySelector('input[name="writer"]') ||
                          formEl.querySelector('input[name*="writer"]') ||
                          formEl.querySelector('input[name*="display"]');
            
            // KBoard의 본문 textarea 이름은 kboard_content 입니다.
            contentInput = formEl.querySelector('textarea[name="kboard_content"]') || 
                           formEl.querySelector('textarea[name="content"]');
            
            // 이메일 필드 매핑
            emailInput = formEl.querySelector('input[name*="email"]') || 
                         formEl.querySelector('input[name*="kboard_option_email"]');
            
            // 연락처 필드 매핑
            phoneInput = formEl.querySelector('input[name*="tel"]') || 
                         formEl.querySelector('input[name*="phone"]') || 
                         formEl.querySelector('input[name*="contact"]') ||
                         formEl.querySelector('input[name*="kboard_option_tel"]') ||
                         formEl.querySelector('input[name*="kboard_option_phone"]');
                         
            // 회사명 필드 매핑
            companyInput = formEl.querySelector('input[name*="company"]') || 
                           formEl.querySelector('input[name*="office"]') ||
                           formEl.querySelector('input[name*="kboard_option_company"]');
        }

        // 회사명 기본값 설정
        let companyVal = '일반 개인/현장';
        if (companyInput && companyInput.value.trim() !== '') {
            companyVal = companyInput.value.trim();
        }

        // 작성자(담당자) 정보 매핑
        let nameVal = '담당자 미기재';
        if (writerInput && writerInput.value.trim() !== '') {
            nameVal = writerInput.value.trim();
        } else {
            // 로그인한 사용자의 경우 일반 텍스트나 hidden 필드로 작성되어 있을 수 있으므로 페이지 전역 탐색
            const textAuthorEl = formEl.querySelector('.kboard-attr-row.kboard-attr-author .attr-value') ||
                                 formEl.querySelector('.kboard-attr-row:nth-child(2) .attr-value') ||
                                 document.querySelector('.kboard-detail-author-name') ||
                                 document.querySelector('.detail-value') ||
                                 document.querySelector('#wp-admin-bar-my-account .display-name') ||
                                 document.querySelector('.ab-item .display-name');
            if (textAuthorEl && textAuthorEl.textContent.trim() !== '') {
                nameVal = textAuthorEl.textContent.trim();
            }
        }

        // 이메일 값 추출
        let emailVal = '';
        if (emailInput && emailInput.value.trim() !== '') {
            emailVal = emailInput.value.trim();
        }

        // 연락처 값 추출 및 방어 코드 (연락처 필드에 이메일이 잘못 들어오는 현상 방지)
        let phoneVal = '연락처 미기재';
        if (phoneInput && phoneInput.value.trim() !== '') {
            const val = phoneInput.value.trim();
            if (val.includes('@')) {
                phoneVal = '연락처 미기재';
                if (!emailVal) emailVal = val;
            } else {
                phoneVal = val;
            }
        }

        // 본문 상세내용 추출 및 HTML 태그 청소
        let specsVal = '상세 내용 없음';
        if (contentInput && contentInput.value.trim() !== '') {
            specsVal = stripHtml(contentInput.value.trim());
        }

        // 첨부파일 이름 추출
        const fileInput = formEl.querySelector('input[type="file"]');
        const attachmentVal = (fileInput && fileInput.files.length > 0) ? fileInput.files[0].name : '';

        const quoteDetails = {
            company: companyVal,
            name: nameVal,
            phone: phoneVal,
            email: emailVal,
            product: titleInput ? titleInput.value.trim() : '공식홈 문의',
            specs: specsVal,
            attachment: attachmentVal
        };

        submitQuote(quoteDetails);
    }

    function bindCafe24BoardForm() {
        const boardForm = document.querySelector('form[id^="boardWriteForm"]') || document.querySelector('#boardWriteForm');
        if (!boardForm || boardForm.samhyupBound) return;

        console.log('[Samhyup Tracker] Cafe24 board form detected.');
        boardForm.samhyupBound = true;
        boardForm.addEventListener('submit', function() {
            handleFormSubmit(boardForm, 'cafe24');
        });
    }

    function bindKBoardForm() {
        // div 래퍼가 아닌 실제 form 태그에만 바인딩하도록 명시적 수정
        const directForm = document.querySelector('form#kboard-editor-form') || 
                           document.querySelector('form.kboard-form') ||
                           document.querySelector('form[action*="kboard_editor_execute"]');
        if (directForm) {
            if (directForm.samhyupBound) return;
            console.log('[Samhyup Tracker] Direct KBoard form detected.');
            directForm.samhyupBound = true;
            directForm.addEventListener('submit', function() {
                handleFormSubmit(directForm, 'kboard');
            });
            return;
        }

        const iframes = document.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            try {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                if (doc) {
                    const iframeForm = doc.querySelector('form#kboard-editor-form') || 
                                       doc.querySelector('form.kboard-form') ||
                                       doc.querySelector('form[action*="kboard_editor_execute"]');
                    if (iframeForm) {
                        if (iframeForm.samhyupBound) return;
                        console.log('[Samhyup Tracker] KBoard form detected inside iframe.');
                        iframeForm.samhyupBound = true;
                        iframeForm.addEventListener('submit', function() {
                            handleFormSubmit(iframeForm, 'kboard');
                        });
                    }
                }
            } catch (e) {}
        });
    }

    // 초기 실행
    window.addEventListener('DOMContentLoaded', () => {
        trackVisitorSource();
        [600, 1500, 3000].forEach(delay => {
            setTimeout(() => {
                bindCafe24BoardForm();
                bindKBoardForm();
            }, delay);
        });
    });

    window.SamhyupTracker = {
        submitQuote: submitQuote,
        getTrackedSource: function() {
            return sessionStorage.getItem('samhyup_main_source') || 'direct';
        }
    };
})();
</script>
