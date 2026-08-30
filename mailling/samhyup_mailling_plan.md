# 삼협철망 B2B 메일 발송 스케줄 및 이력 관리 구축 계획서

## 💡 제안 배경 및 의견
- **별도의 이력 관리(로그) 시트를 만드는 방안을 적극 권장합니다.**
- 메인 `company` 시트의 발송 관련 열 하나에 날짜를 계속 누적시키면, 나중에 특정 업체가 메일을 **총 몇 번 발송받았는지**, **마지막 발송이 언제였는지** 통계를 내거나 분석하기가 어렵습니다.
- 이에 따라, 메일 발송 시마다 별도의 `mail_log` 시트에 한 행(Row)씩 발송 이력을 생성(로그 적재)하고, 메인 `company` 시트에서는 구글시트 수식(`MAXIFS`, `COUNTIF`, `TODAY()`)을 활용해 최종 발송일과 누적 횟수, 경과일수를 자동으로 실시간 표시하도록 구현하는 설계가 가장 효율적이고 직관적입니다.

---

## 📊 1. 구글 스프레드시트 컬럼 구조 (확정)

### [메인 시트: company] 컬럼 구조
| 열 | 컬럼명 | 입력 형식 및 수식 | 역할 및 설명 |
|:---|:---|:---|:---|
| **A열** | 체크 | 체크박스 | 발송 대상 선택 (GAS 트리거) |
| **B열** | 연번 | 숫자 | 업체 일련번호 (사용자 관리) |
| **C열** | 회사명 | 텍스트 | 업체명 |
| **F열** | 이메일 | 텍스트 | 수신 이메일 주소 |
| **M열** | 발송대기 | 텍스트 (예: `대기` 또는 공란) | 현재 보낼 타겟 대상 기입 |
| **N열** | 발송상태 | 텍스트 | 발송 성공 여부 상태 표기 (GAS 자동 기록) |
| **O열** | 최종 발송일 | `=IFERROR(MAXIFS(mail_log!C:C, mail_log!D:D, C2), "")` | mail_log의 C열(발송일자)에서 D열(회사명)이 일치하는 가장 최신 날짜 자동 조회 |
| **P열** | 발송경과 | `=IF(ISBLANK(O2), "", TODAY() - O2)` | 마지막 발송일로부터 오늘까지 경과 일수 |

> [!TIP]
> **P열 10일 도래 시 조건부 서식 강조 설정**
> - **적용 범위**: `P2:P`
> - **조건**: `보다 크거나 같음` → `10`
> - **서식**: 셀 배경색을 연한 빨간색 또는 주황색으로 설정하여 재발송 대상 시각적 모니터링

### [로그 시트: mail_log] 컬럼 구조 (확정)
발송할 때마다 기록이 누적되는 데이터베이스 테이블 역할의 시트입니다.

| 열 | 컬럼명 | 입력 방식 | 비고 |
|:---|:---|:---|:---|
| **A열** | 체크 | 사용자 직접 관리 | 체크박스 |
| **B열** | 연번 | GAS 자동 부여 | 헤더 제외 행 수 기준 |
| **C열** | 발송일자 | GAS 자동 기록 | `yyyy-MM-dd HH:mm:ss` |
| **D열** | 회사명 | GAS 자동 기록 | company 시트 C열 값 |
| **E열** | 이메일 주소 | GAS 자동 기록 | company 시트 F열 값 |
| **F열** | 발송회차 | GAS 자동 기록 | company 시트 M열 값 (`1일차` 등) |
| **G열** | 발송상태 | GAS 자동 기록 | `성공` / `실패` |
| **H열** | 세부결과 | GAS 자동 기록 | API 성공 메시지 또는 에러 로그 |
| **I열** | 비고 | 사용자 직접 관리 | 수동 메모 |

---

## ⚙️ 2. Google Apps Script (GAS) 수정 및 설정법 (삼협철망 전용)

### 1) GAS Web App URL 및 스프레드시트 설정
삼협철망 전용 구글 스프레드시트의 Apps Script 편집기에 들어간 뒤, 아래 코드를 적용합니다.

```javascript
/**
 * 삼협철망 아웃바운드 메일 발송 스크립트 v3
 * [company 시트 컬럼] A=체크, B=연번, C=회사명, F=이메일, M=발송대기(회차)
 * [mail_log 시트 컬럼] A=체크, B=연번, C=발송일자, D=회사명, E=이메일, F=발송회차, G=발송상태, H=세부결과, I=비고
 */

var BASE_URL = "https://samhyupmesh.vercel.app/"; // 삼협철망 웹 서버 도메인 주소로 교체
var SS_ID = "YOUR_SAMHYUP_SPREADSHEET_ID";       // 삼협철망 스프레드시트 고유 ID 입력

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('삼협 아웃바운드')
    .addItem('선택 제안서 발송', 'sendOutboundEmails')
    .addToUi();
}

function writeMailLog(companyName, email, round, status, detail) {
  try {
    var ss = SpreadsheetApp.openById(SS_ID);
    var log = ss.getSheetByName("mail_log");
    if (!log) {
      log = ss.insertSheet("mail_log");
      log.appendRow(["체크","연번","발송일자","회사명","이메일 주소","발송회차","발송상태","세부결과","비고"]);
      log.getRange("A1:I1").setFontWeight("bold").setBackground("#f1f5f9");
    }
    var formattedDate = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
    var lastRow = log.getLastRow();
    var seq = (lastRow <= 1) ? 1 : lastRow;
    log.appendRow(["", seq, formattedDate, companyName, email, round, status, detail, ""]);
  } catch(e) {
    try {
      SpreadsheetApp.getUi().alert("로그 작성 실패 에러: " + e.toString());
    } catch(err) {
      Logger.log("로그에러: " + e.toString());
    }
  }
}

function sendOutboundEmails() {
  var ss = SpreadsheetApp.openById(SS_ID);
  var sheet = ss.getSheetByName("company");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("'company' 시트를 찾을 수 없습니다.");
    return;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('발송할 데이터가 없습니다.');
    return;
  }

  var values = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  var targets = [];

  for (var r = 0; r < values.length; r++) {
    if (values[r][0] !== true) continue;
    var company = values[r][2].toString().trim();   // C열 회사명
    var email   = values[r][5].toString().trim();   // F열 이메일
    var round   = values[r][12].toString().trim() || '1일차'; // M열 발송회차
    if (email) {
      targets.push({ row: r + 2, company: company || '대표님', email: email, round: round });
    }
  }

  if (targets.length === 0) {
    SpreadsheetApp.getUi().alert('A열 체크박스에 체크된 대상이 없습니다.');
    return;
  }

  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert('발송 확인', targets.length + '개 업체에 발송하시겠습니까?', ui.ButtonSet.YES_NO);
  if (confirm !== ui.Button.YES) return;

  // 템플릿 로드
  var resp = UrlFetchApp.fetch(BASE_URL + "templates/samhyup_proposal.html", { muteHttpExceptions: true });
  if (resp.getResponseCode() !== 200) {
    ui.alert('템플릿 로드 실패: HTTP ' + resp.getResponseCode());
    return;
  }
  var html = resp.getContentText("UTF-8");

  var ok = 0, fail = 0;
  for (var t = 0; t < targets.length; t++) {
    var tgt = targets[t];
    var body = html.replace(/{회사명}/g, tgt.company);
    try {
      GmailApp.sendEmail(
        tgt.email,
        "[삼협철망] " + tgt.company + " 귀사 용접철망/와이어메쉬 협력 제안",
        "본 메일은 HTML 형식입니다.",
        { htmlBody: body }
      );
      sheet.getRange(tgt.row, 1).setValue(false);
      writeMailLog(tgt.company, tgt.email, tgt.round, '성공', 'Gmail API 발송 완료');
      ok++;
    } catch(e) {
      writeMailLog(tgt.company, tgt.email, tgt.round, '실패', e.toString());
      fail++;
    }
  }

  ui.alert('발송 완료\n\n성공: ' + ok + '건\n실패: ' + fail + '건');
}
```

---

## 📅 3. company 시트 수식 적용 방법

O, P, Q열 수식을 아래와 같이 적용합니다.

```
O2: =IFERROR(MAXIFS(mail_log!C:C, mail_log!D:D, C2), "")
P2: =IF(ISBLANK(O2), "", TODAY() - O2)
Q2: =COUNTIF(mail_log!D:D, C2)
```

---

## 📅 4. 다음 작업 진행 예정 사항
1. **스프레드시트 수식 적용**: `company` 시트 O/P/Q열에 위 수식 및 조건부 서식 적용.
2. **GAS 코드 스프레드시트 반영**: 위의 삼협철망 전용 코드로 구글 앱스 스크립트 편집기에 붙여넣고 저장 및 배포.
3. **테스트 발송 확인**: 테스트 발송 후 `mail_log` C~I열 정상 기록 여부 확인.
