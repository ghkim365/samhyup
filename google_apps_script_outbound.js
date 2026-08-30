/**
 * 삼협철망 B2B 아웃바운드 이메일 자동 발송 Google Apps Script v3
 *
 * [사용 방법]
 *   1. company 시트에서 발송할 업체의 A열 체크박스 체크
 *   2. 상단 "삼협 아웃바운드" → "선택 제안서 발송" 클릭
 *
 * [컬럼 구조 - company 시트]
 *   A:체크 | B:연번 | C:회사명 | D:주요 사용처/구매목적 | E:공식 이메일
 *   F:공식 이메일 | G:웹사이트 주소 | H:지역 | I:주소 | J:웹사이트 검증
 *   K:전화번호 검증 | L:데이터 품질 | M:발송대기 | N:발송상태 | O:발송일
 *
 * [중복 발송 방지]
 *   N열(발송상태)이 이미 "정상발송"인 행은 A열 체크되어 있어도 자동 스킵
 *
 * [mail_log 시트]
 *   기존 데이터 보존 — 시트가 있으면 그대로 유지하고 행만 추가
 */

var BASE_URL = "https://samhyup.vercel.app/";
var SS_ID    = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04";

// ─────────────────────────────────────────────────────────────────────────────
// 메뉴 생성
// ─────────────────────────────────────────────────────────────────────────────
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('삼협 아웃바운드')
    .addItem('📧 선택 제안서 발송', 'sendOutboundEmails')
    .addSeparator()
    .addItem('📊 발송 현황 확인', 'checkSendStatus')
    .addToUi();
}

// ─────────────────────────────────────────────────────────────────────────────
// 유틸: 헤더 배열에서 키워드 포함 컬럼 인덱스 반환 (0-based)
// ─────────────────────────────────────────────────────────────────────────────
function getColIndex(headers, candidates) {
  for (var i = 0; i < headers.length; i++) {
    var h = headers[i].toString().trim().toLowerCase();
    for (var j = 0; j < candidates.length; j++) {
      if (h.indexOf(candidates[j].toLowerCase()) !== -1) return i;
    }
  }
  return -1;
}

// ─────────────────────────────────────────────────────────────────────────────
// 발송 현황 확인 팝업
// ─────────────────────────────────────────────────────────────────────────────
function checkSendStatus() {
  var ss    = SpreadsheetApp.openById(SS_ID);
  var sheet = ss.getSheetByName('company');
  if (!sheet) { SpreadsheetApp.getUi().alert('[오류] company 시트를 찾을 수 없습니다.'); return; }

  var headers       = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var emailColIdx   = getColIndex(headers, ['이메일', 'email', '메일']);
  var sendStatusIdx = getColIndex(headers, ['발송상태']);
  var lastRow       = sheet.getLastRow();
  var values        = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  var sent = 0, errCount = 0, pending = 0, noEmail = 0;
  for (var r = 0; r < values.length; r++) {
    var email  = emailColIdx >= 0 ? values[r][emailColIdx].toString().trim() : '';
    var status = sendStatusIdx >= 0 ? values[r][sendStatusIdx].toString().trim() : '';
    if (!email || email.indexOf('@') < 0) { noEmail++; }
    else if (status === '정상발송')            { sent++;     }
    else if (status.indexOf('발송오류') === 0) { errCount++; }
    else                                     { pending++;  }
  }

  SpreadsheetApp.getUi().alert(
    '📊 발송 현황\n\n' +
    '  ✅ 정상발송:    ' + sent     + '개\n' +
    '  ❌ 발송오류:    ' + errCount + '개\n' +
    '  📋 미발송 대기: ' + pending  + '개\n' +
    '  ⬜ 이메일 없음: ' + noEmail  + '개\n' +
    '  ──────────────────\n' +
    '  전체 업체:      ' + values.length + '개'
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// mail_log 시트에 발송 이력 기록
// 기존 시트가 있으면 그대로 유지, 없으면 새로 생성 (기존 데이터 보존)
// ─────────────────────────────────────────────────────────────────────────────
function writeMailLog(companyName, email, round, status, detail) {
  try {
    var ss  = SpreadsheetApp.openById(SS_ID);
    var log = ss.getSheetByName('mail_log');
    if (!log) {
      log = ss.insertSheet('mail_log');
      log.appendRow(['체크', '연번', '발송일자', '회사명', '이메일 주소', '발송회차', '발송상태', '세부결과', '비고']);
      log.getRange('A1:I1').setFontWeight('bold').setBackground('#f1f5f9');
    }
    var formattedDate = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss');
    var lastRow = log.getLastRow();
    var seq     = (lastRow <= 1) ? 1 : lastRow;
    log.appendRow(['', seq, formattedDate, companyName, email, round, status, detail, '']);
  } catch (e) {
    try   { SpreadsheetApp.getUi().alert('로그 작성 실패: ' + e.toString()); }
    catch (err) { Logger.log('로그에러: ' + e.toString()); }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 메인: A열 체크된 업체에 제안서 발송
// ─────────────────────────────────────────────────────────────────────────────
function sendOutboundEmails() {
  var ss    = SpreadsheetApp.openById(SS_ID);
  var sheet = ss.getSheetByName('company');
  if (!sheet) { SpreadsheetApp.getUi().alert('[오류] company 시트를 찾을 수 없습니다.'); return; }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) { SpreadsheetApp.getUi().alert('발송할 데이터가 없습니다.'); return; }

  // 헤더 파싱
  var headers       = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var companyColIdx = getColIndex(headers, ['회사명', '업체명', '상호', '수신처']);
  var emailColIdx   = getColIndex(headers, ['이메일', 'email', '메일']);
  var roundColIdx   = getColIndex(headers, ['발송대기', '발송회차', '회차']);
  var sendStatusIdx = getColIndex(headers, ['발송상태']);  // N열
  var sendDateIdx   = getColIndex(headers, ['발송일']);    // O열

  // 기본값 (헤더 감지 실패 시)
  if (companyColIdx < 0) companyColIdx = 2;  // C열
  if (emailColIdx   < 0) emailColIdx   = 5;  // F열
  if (roundColIdx   < 0) roundColIdx   = 12; // M열

  if (sendStatusIdx < 0 || sendDateIdx < 0) {
    SpreadsheetApp.getUi().alert(
      '[오류] N열(발송상태) 또는 O열(발송일) 헤더를 찾을 수 없습니다.\n헤더를 확인해주세요.'
    );
    return;
  }

  var values  = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  var targets = [];
  var skipped = [];

  for (var r = 0; r < values.length; r++) {
    var isChecked = values[r][0];
    if (isChecked !== true && isChecked !== 'TRUE') continue;

    var company = values[r][companyColIdx].toString().trim() || '대표님';
    var email   = values[r][emailColIdx].toString().trim();
    var round   = values[r][roundColIdx].toString().trim() || '1일차';
    var status  = values[r][sendStatusIdx].toString().trim();

    // ★ 중복 발송 방지: 이미 정상발송된 행은 스킵
    if (status === '정상발송') {
      skipped.push(company + ' (이미 발송됨)');
      sheet.getRange(r + 2, 1).setValue(false);
      continue;
    }
    // 유효 이메일 없으면 스킵
    if (!email || email.indexOf('@') < 0) {
      skipped.push(company + ' (이메일 없음)');
      sheet.getRange(r + 2, 1).setValue(false);
      continue;
    }
    targets.push({ rowNum: r + 2, company: company, email: email, round: round });
  }

  if (targets.length === 0) {
    var msg = '발송 대상이 없습니다.';
    if (skipped.length > 0) msg += '\n\n스킵된 업체 (' + skipped.length + '개):\n' + skipped.join('\n');
    SpreadsheetApp.getUi().alert(msg);
    return;
  }

  // 발송 전 확인창
  var previewLines = targets.map(function(t, i) {
    return (i + 1) + '. ' + t.company + '  →  ' + t.email;
  }).join('\n');
  var skipMsg = skipped.length > 0 ? '\n\n⚠️ 이미 발송됨(스킵): ' + skipped.length + '개' : '';

  var confirm = SpreadsheetApp.getUi().alert(
    '📧 발송 대상 확인 (' + targets.length + '개)',
    previewLines + skipMsg + '\n\n위 ' + targets.length + '개 업체에 발송하시겠습니까?',
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  if (confirm !== SpreadsheetApp.getUi().Button.YES) return;

  // 템플릿 로드
  var htmlTemplate = '';
  try {
    var resp = UrlFetchApp.fetch(BASE_URL + 'templates/samhyup_proposal.html', { muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) {
      SpreadsheetApp.getUi().alert('[오류] 템플릿 로드 실패: HTTP ' + resp.getResponseCode());
      return;
    }
    htmlTemplate = resp.getContentText('UTF-8');
  } catch (err) {
    SpreadsheetApp.getUi().alert('[오류] 템플릿 로드 실패: ' + err.toString());
    return;
  }

  // 인라인 이미지 사전 로드 (핵심 이미지 4개만 인라인화, 나머지는 웹 주소 직접 참조)
  var imageCids = [
    'logo',
    'assembled_mesh', 'mesh_pallet', 'gabion'
  ];

  var inlineImages = {};
  for (var i = 0; i < imageCids.length; i++) {
    var cid    = imageCids[i];
    var imgUrl = '';
    if      (cid === 'logo')           { imgUrl = BASE_URL + 'images/logo_samhyup.png';       }
    else if (cid === 'assembled_mesh') { imgUrl = BASE_URL + 'gallery/assembled_mesh_01.jpg'; }
    else if (cid === 'mesh_pallet')    { imgUrl = BASE_URL + 'gallery/mesh_pallet_01.jpg';    }
    else if (cid === 'gabion')         { imgUrl = BASE_URL + 'gallery/gabion_01.jpg';          }
    try {
      var blob = UrlFetchApp.fetch(imgUrl).getBlob();
      blob.setName(cid);
      inlineImages[cid] = blob;
    } catch (e) {
      Logger.log('이미지 로드 실패 (' + cid + '): ' + e.toString());
    }
  }

  // 순차 발송
  var successCount = 0, failCount = 0, failList = [];
  var todayStr = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');

  for (var t = 0; t < targets.length; t++) {
    var target           = targets[t];
    var personalizedHtml = htmlTemplate.replace(/{회사명}/g, target.company);
    try {
      GmailApp.sendEmail(
        target.email,
        '[삼협철망] ' + target.company + ' 귀사 건설현장 및 자재유통 협력 제안',
        '본 메일은 B2B 협력 제안서 메일입니다. HTML 형식을 지원하는 메일 클라이언트에서 확인해주세요.',
        { htmlBody: personalizedHtml, inlineImages: inlineImages }
      );
      sheet.getRange(target.rowNum, sendStatusIdx + 1).setValue('정상발송'); // N열
      sheet.getRange(target.rowNum, sendDateIdx   + 1).setValue(todayStr);  // O열
      sheet.getRange(target.rowNum, 1).setValue(false);                      // A열 체크 해제
      writeMailLog(target.company, target.email, target.round, '성공', 'Gmail API 발송 완료');
      successCount++;
      Utilities.sleep(800);
    } catch (err) {
      Logger.log('발송 오류 (' + target.email + '): ' + err.toString());
      sheet.getRange(target.rowNum, sendStatusIdx + 1).setValue('발송오류: ' + err.message);
      writeMailLog(target.company, target.email, target.round, '실패', err.toString());
      failCount++;
      failList.push(target.company + ' (' + target.email + ')');
    }
  }

  var resultMsg =
    '📧 발송 완료\n\n' +
    '  ✅ 정상발송: ' + successCount    + '건\n' +
    '  ❌ 발송오류: ' + failCount       + '건\n' +
    '  ⏭️ 중복스킵: ' + skipped.length + '건';
  if (failList.length > 0) resultMsg += '\n\n오류 업체:\n' + failList.join('\n');
  SpreadsheetApp.getUi().alert(resultMsg);
}

// ─────────────────────────────────────────────────────────────────────────────
// GAS Web App API (dashboard.html 연동용 JSONP)
// 배포: [배포] → [새 배포] → 유형: 웹앱, 실행: 나, 액세스: 누구나
// ─────────────────────────────────────────────────────────────────────────────
function doGet(e) {
  var site = e.parameter.site;
  var cb   = e.parameter.callback;
  var data = {};

  if (site === 'mailling') {
    var ss           = SpreadsheetApp.openById(SS_ID);
    var logSheet     = ss.getSheetByName('mail_log');
    var companySheet = ss.getSheetByName('company');
    var logs         = [];
    var visits       = { success: 0, fail: 0 };

    // company 시트에서 회사명 → 상세정보 맵 생성
    var companyMap = {};
    if (companySheet) {
      var cRows = companySheet.getDataRange().getValues();
      for (var c = 1; c < cRows.length; c++) {
        var cName = (cRows[c][2] || '').toString().trim(); // C열 회사명
        if (cName) {
          companyMap[cName] = {
            phone:   (cRows[c][4] || '').toString().trim(),  // E열
            site:    (cRows[c][6] || '').toString().trim(),  // G열
            region:  (cRows[c][7] || '').toString().trim(),  // H열
            address: (cRows[c][8] || '').toString().trim()   // I열
          };
        }
      }
    }

    // mail_log 역순 (최신 우선)
    if (logSheet) {
      var rows = logSheet.getDataRange().getValues();
      for (var i = rows.length - 1; i >= 1; i--) {
        var s = rows[i][6]; // G열: 발송상태
        if (s === '성공') visits.success++;
        else if (s === '실패') visits.fail++;
        var companyName = rows[i][3];
        var info = companyMap[companyName] || { phone: '', site: '', region: '', address: '' };
        logs.push({
          id:      rows[i][1],
          date:    rows[i][2],
          company: companyName,
          email:   rows[i][4],
          round:   rows[i][5],
          status:  s,
          detail:  rows[i][7],
          note:    rows[i][8] || '',
          phone:   info.phone,
          site:    info.site,
          region:  info.region,
          address: info.address
        });
      }
    }
    data = { visits: visits, logs: logs };
  }

  return ContentService
    .createTextOutput(cb + '(' + JSON.stringify(data) + ')')
    .setMimeType(ContentService.MimeType.JAVASCRIPT);
}
