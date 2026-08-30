# 삼협철망(주) - 구글 애즈(Google Ads) 전환 추적 연동 보고서

본 문서는 삼협철망(주) B2B 모바일 간편 견적 카탈로그 웹사이트에 구글 애즈(Google Ads) 광고 전환 추적(견적 문의 완료) 태그를 수동으로 연동한 내역을 기록한 개발 및 설정 보고서입니다.

---

## 1. 연동 개요
* **광고주 계정 ID:** `480-010-0186` (samhyupm)
* **목표 카테고리:** `견적 요청` (Request Quote)
* **측정 방식:** 코드를 사용한 수동 이벤트 측정 (자바스크립트 성공 콜백 이벤트 연동)
* **전환 ID (Conversion ID):** `AW-750842470`
* **전환 라벨 (Conversion Label):** `hAmFCITOvM4cEObkg-YC`
* **전체 전환 매핑 (Send To):** `AW-750842470/hAmFCITOvM4cEObkg-YC`
* **전환 값 (Value):** 전환 당 1원 (KRW) 고정 가치 할당
* **전환 횟수 (Count):** 1회 (리드 중복 집계 방지)

---

## 2. 웹사이트 코드 수정 내역

### ① 글로벌 사이트 태그(Google Tag) 탑재 (`index.html`)
모든 페이지 뷰 및 이벤트 전송의 기반이 되는 구글 글로벌 태그 스크립트를 `<head>` 영역 가장 하단에 추가했습니다.

```html
<!-- Google tag (gtag.js) - Google Ads: 750842470 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-750842470"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'AW-750842470');
</script>
```

### ② 견적서 성공 콜백 이벤트 연동 (`app.js`)
사용자가 견적 입력란을 채우고 **[견적 문의 전송하기]** 버튼을 눌렀을 때, 실시간 온라인 접수 성공 및 메일함 전송 실패 시의 폴백(mailto) 시도 시점 두 군데 모두 구글 애즈 전환 스니펫 함수를 호출하도록 코드를 삽입했습니다.

#### 1) 온라인 즉시 전송 성공 시 (`fetch().then()`)
```javascript
fetch("https://formsubmit.co/ajax/samhyupm@naver.com", {
    method: "POST",
    body: formData
})
.then(response => {
    if (response.ok) {
        // Google Ads 전환 추적 이벤트 전송
        if (typeof gtag === 'function') {
            gtag('event', 'conversion', {
                'send_to': 'AW-750842470/hAmFCITOvM4cEObkg-YC'
            });
        }
        alert('견적 문의가 온라인으로 성공적으로 접수되었습니다!...');
        event.target.reset();
        // ... 생략 ...
    }
})
```

#### 2) 온라인 전송 실패 후 메일 전송 시도 시 (`catch()`)
```javascript
.catch(error => {
    console.error('AJAX Submit Error:', error);
    
    // Google Ads 전환 추적 이벤트 전송 (폴백 전송 시도 시에도 이벤트 발송)
    if (typeof gtag === 'function') {
        gtag('event', 'conversion', {
            'send_to': 'AW-750842470/hAmFCITOvM4cEObkg-YC'
        });
    }
    
    // AJAX 실패 시 기존 mailto 링크 폴백 방식 작동
    alert('온라인 즉시 전송이 제한되어, 기본 메일 발송 프로그램... 작성합니다.');
    // ... 생략 ...
})
```

---

## 3. 구글 애즈 대시보드 내 설정 절차 요약

1. **전환 메뉴 진입:**
   구글 애즈 좌측 메뉴에서 **`목표` (🎯 아이콘)** ➔ **`전환`** ➔ **`요약`** ➔ **`[+ 전환 액션 만들기]`** 파란색 버튼 클릭
2. **소스 선택:**
   **`웹사이트`** 유형 선택 후 대상 사이트 URL (`https://samhyup.vercel.app`) 입력 및 **`[검사]`** 스캔
3. **태그 및 소스 확인:**
   검색된 데이터 소스 중 **`Google 태그`** 체크박스를 활성화하고 **`[완료]`** 클릭
4. **수동 추가 시작:**
   **`[+ 전환 만들기]`** 클릭 후 데이터 소스를 **`samhyupm` (Google 태그)**로 선택
5. **수동 설정 유형 지정:**
   **`코드를 사용하여 수동으로`** 라디오 버튼 체크 후 완료
6. **상세 설정값 매핑:**
   * **카테고리:** `견적 요청`
   * **전환 이름:** `견적 요청`
   * **값:** `모든 전환에서 동일한 가치 사용` ➔ `1 KRW` 지정
   * **횟수:** `1회` (리드 중복 방지)
   * 기타 설정 기본값 유지 후 **`[완료]`** 클릭
7. **코드 추출 및 동의:**
   이전 화면에서 **`[저장하고 계속하기]`** 클릭 ➔ **`[이벤트 스니펫 보기]`** 클릭 후 영문 태그 코드(`AW-750842470/hAmFCITOvM4cEObkg-YC`) 복사 ➔ 최종 **`[동의 및 완료]`** 버튼을 클릭하여 대시보드 세팅 종료.

---

## 4. 향후 모니터링 및 검증 방법
* **태그 작동 여부 검증:**
  구글 크롬 브라우저의 확장 프로그램인 **Google Tag Assistant** 또는 개발자 도구(F12)의 Network 탭에서 `collect` 요청 중 `tid=AW-750842470`으로 발송되는 요청이 있는지 확인함으로써 전송 상태를 검증할 수 있습니다.
* **구글 애즈 데이터 반영 시간:**
  현장 사용자가 사이트에서 전환 이벤트를 발생시킨 시점으로부터 구글 애즈 대시보드에 리포팅 및 실시간 입찰 데이터로 쌓이기까지는 약 **24시간 ~ 48시간** 가량 소요될 수 있습니다.
