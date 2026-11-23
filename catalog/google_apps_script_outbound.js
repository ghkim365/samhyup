/**
 * 삼협철망 B2B 아웃바운드 이메일 자동 발송 Google Apps Script (GAS) v3
 * 
 * [company 시트 컬럼 기준]
 * A=체크, B=연번, C=회사명, E=대표번호, F=이메일, G=사이트주소, H=지역, I=주소, M=발송대기(회차), N=발송상태, O=최종발송일, P=발송결과
 * [mail_log 시트 컬럼 기준]
 * A=체크, B=연번, C=발송일자, D=회사명, E=이메일 주소, F=발송회차, G=발송상태, H=세부결과, I=비고
 */

var BASE_URL = "https://samhyup.pages.dev/";
var SS_ID = "161bSIprv3S0P8-UyPHnC9fWk4q_KcuANSPL-aZEJo04";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('삼협 아웃바운드')
    .addItem('선택 제안서 발송', 'sendOutboundEmails')
    .addItem('과거 기록 동기화(mail_log → company)', 'syncPastLogsToCompany')
    .addItem('반송 이메일 일괄 실패 처리', 'markBouncedEmails')
    .addToUi();
}

// 트리거 설치 함수 (1회 실행)
function installTrigger() {
  var ss = SpreadsheetApp.openById(SS_ID);
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('onOpen').forSpreadsheet(ss).onOpen().create();
  Browser.msgBox('트리거 설치 완료!');
}

// mail_log 시트에 이메일 발송 결과 자동 기록
function writeMailLog(companyName, email, round, status, detail) {
  try {
    var ss = SpreadsheetApp.openById(SS_ID);
    var log = ss.getSheetByName("mail_log");
    if (!log) {
      log = ss.insertSheet("mail_log");
      log.appendRow(["체크", "연번", "발송일자", "회사명", "이메일 주소", "발송회차", "발송상태", "세부결과", "비고"]);
      log.getRange("A1:I1").setFontWeight("bold").setBackground("#f1f5f9");
    }
    var formattedDate = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
    var lastRow = log.getLastRow();
    var seq = (lastRow <= 1) ? 1 : lastRow;
    log.appendRow(["", seq, formattedDate, companyName, email, round, status, detail, ""]);
  } catch (e) {
    try {
      SpreadsheetApp.getUi().alert("로그 작성 실패 에러: " + e.toString());
    } catch (err) {
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
    var email = values[r][5].toString().trim();     // F열 이메일
    var round = values[r][12] ? values[r][12].toString().trim() : '1일차'; // M열 발송회차
    if (email) {
      targets.push({ row: r + 2, company: company || '대표님', email: email, round: round });
    }
  }

  if (targets.length === 0) {
    SpreadsheetApp.getUi().alert('A열 체크박스에 체크된 대상이 없습니다.');
    return;
  }

  var ui = SpreadsheetApp.getUi();
  var confirm = ui.alert('발송 확인', targets.length + '개 업체에 삼협철망 B2B 제안서를 발송하시겠습니까?', ui.ButtonSet.YES_NO);
  if (confirm !== ui.Button.YES) return;

  // 1. 템플릿 파일 로드
  var htmlTemplate = "";
  try {
    var response = UrlFetchApp.fetch(BASE_URL + "templates/samhyup_proposal.html", { muteHttpExceptions: true });
    if (response.getResponseCode() !== 200) {
      ui.alert('템플릿 로드 실패: HTTP ' + response.getResponseCode());
      return;
    }
    htmlTemplate = response.getContentText("UTF-8");
  } catch (err) {
    ui.alert('템플릿 로드 실패: ' + err.toString());
    return;
  }

  // 2. 인라인 이미지 목록 정의 및 Blob 미리 가져오기
  var imageCids = [
    'logo',
    'assembled_mesh', 'mesh_pallet', 'gabion',
    'assembled_mesh_02', 'assembled_mesh_03', 'assembled_mesh_04', 'assembled_mesh_11',
    'assembled_mesh_06', 'assembled_mesh_07', 'assembled_mesh_12', 'assembled_mesh_09',
    'mesh_pallet_02', 'mesh_pallet_03', 'mesh_pallet_10', 'mesh_pallet_05',
    'mesh_pallet_06', 'mesh_pallet_07', 'mesh_pallet_08', 'mesh_pallet_09',
    'gabion_02', 'gabion_03', 'gabion_04', 'gabion_05',
    'gabion_06', 'gabion_07', 'gabion_08', 'gabion_09'
  ];

  var inlineImages = {};
  for (var i = 0; i < imageCids.length; i++) {
    var cid = imageCids[i];
    var url = "";
    if (cid === 'logo') {
      url = BASE_URL + "images/logo_samhyup.png";
    } else if (cid === 'assembled_mesh') {
      url = BASE_URL + "gallery/assembled_mesh_01.jpg";
    } else if (cid === 'mesh_pallet') {
      url = BASE_URL + "gallery/mesh_pallet_01.jpg";
    } else if (cid === 'gabion') {
      url = BASE_URL + "gallery/gabion_01.jpg";
    } else {
      url = BASE_URL + "gallery/" + cid + ".jpg";
    }

    try {
      var imgBlob = UrlFetchApp.fetch(url).getBlob();
      imgBlob.setName(cid);
      inlineImages[cid] = imgBlob;
    } catch (err) {
      Logger.log("이미지 로드 실패 (CID: " + cid + "): " + url + " - " + err.toString());
    }
  }

  var ok = 0, fail = 0;
  for (var t = 0; t < targets.length; t++) {
    var tgt = targets[t];
    var body = htmlTemplate.replace(/{회사명}/g, tgt.company);
    try {
      GmailApp.sendEmail(
        tgt.email,
        "[삼협철망] " + tgt.company + " 귀사 건설현장 및 자재유통 협력 제안",
        "본 메일은 B2B 협력 제안서 메일입니다. HTML 형식을 지원하는 메일 클라이언트에서 확인해주세요.",
        {
          htmlBody: body,
          inlineImages: inlineImages
        }
      );
      sheet.getRange(tgt.row, 1).setValue(false); // 체크 해제
      var nowStr = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
      sheet.getRange(tgt.row, 14).setValue('성공'); // N열 (발송상태)
      sheet.getRange(tgt.row, 15).setValue(nowStr);  // O열 (발송일)
      sheet.getRange(tgt.row, 16).setValue('Gmail API 발송 완료'); // P열 (발송결과)
      writeMailLog(tgt.company, tgt.email, tgt.round, '성공', 'Gmail API 발송 완료');
      ok++;
    } catch (e) {
      var nowStr = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
      sheet.getRange(tgt.row, 14).setValue('실패'); // N열 (발송상태)
      sheet.getRange(tgt.row, 15).setValue(nowStr);  // O열 (발송일)
      sheet.getRange(tgt.row, 16).setValue(e.toString()); // P열 (발송결과)
      writeMailLog(tgt.company, tgt.email, tgt.round, '실패', e.toString());
      fail++;
    }
  }

  ui.alert('발송 완료\n\n성공: ' + ok + '건\n실패: ' + fail + '건');
}

// 대시보드 및 mail_report.html 용 실시간 JSONP 데이터 제공 API
function doGet(e) {
  var site = e.parameter.site;
  var cb = e.parameter.callback;
  var data = {};

  if (site === 'mailling') {
    var ss = SpreadsheetApp.openById(SS_ID);
    var logSheet = ss.getSheetByName("mail_log");
    var companySheet = ss.getSheetByName("company");
    var logs = [];
    var visits = { success: 0, fail: 0 };

    // ── company 시트에서 회사명 → 상세정보 맵 생성 ──
    var companyMap = {};
    if (companySheet) {
      var cRows = companySheet.getDataRange().getValues();
      for (var c = 1; c < cRows.length; c++) {
        var cName = (cRows[c][2] || '').toString().trim();
        if (cName) {
          companyMap[cName] = {
            phone: (cRows[c][4] || '').toString().trim(),   // E열: 대표번호
            site: (cRows[c][6] || '').toString().trim(),    // G열: 사이트 주소
            region: (cRows[c][7] || '').toString().trim(),  // H열: 지역
            address: (cRows[c][8] || '').toString().trim()   // I열: 주소
          };
        }
      }
    }

    if (logSheet) {
      var rows = logSheet.getDataRange().getValues();
      for (var i = rows.length - 1; i >= 1; i--) {
        var s = rows[i][6];
        if (s === '성공') visits.success++;
        else if (s === '실패') visits.fail++;
        var companyName = rows[i][3];
        var info = companyMap[companyName] || { phone: '', site: '', region: '', address: '' };
        logs.push({
          id: rows[i][1],
          date: rows[i][2],
          company: companyName,
          email: rows[i][4],
          round: rows[i][5],
          status: s,
          detail: rows[i][7],
          note: rows[i][8] || '',
          phone: info.phone,
          site: info.site,
          region: info.region,
          address: info.address
        });
      }
    }
    data = { visits: visits, logs: logs };
  }

  return ContentService
    .createTextOutput(cb + "(" + JSON.stringify(data) + ")")
    .setMimeType(ContentService.MimeType.JAVASCRIPT);
}

// 홈페이지(https://samhyup.pages.dev/) 견적 문의 데이터 수신 및 파일 업로드 처리 API
function doPost(e) {
  try {
    var params = e.parameter;

    if (e.postData && e.postData.contents) {
      try {
        var json = JSON.parse(e.postData.contents);
        params = json;
      } catch (err) { }
    }

    var company = params['회사명_현장명'] || params['companyName'] || '미기입';
    var name = params['담당자명'] || params['contactPerson'] || '미기입';
    var phone = params['연락처'] || params['contactPhone'] || '미기입';
    var email = params['이메일'] || params['contactEmail'] || '미기입';
    var service = params['가공_서비스'] || params['serviceSelect'] || '미선택';
    var specs = params['희망_규격_수량'] || params['specsInput'] || '미기입';

    var fileUrl = "첨부파일 없음";

    if (params.fileData && params.fileName) {
      try {
        var base64Data = params.fileData.split(",")[1] || params.fileData;
        var decoded = Utilities.base64Decode(base64Data);
        var blob = Utilities.newBlob(decoded, params.fileType || 'application/octet-stream', params.fileName);

        var folder;
        var folders = DriveApp.getFoldersByName("삼협철망_견적도면");
        if (folders.hasNext()) {
          folder = folders.next();
        } else {
          folder = DriveApp.createFolder("삼협철망_견적도면");
        }

        var file = folder.createFile(blob);
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
        fileUrl = file.getUrl();
      } catch (fileErr) {
        fileUrl = "파일 저장 실패: " + fileErr.toString();
      }
    }

    var emailBody =
      "🏭 [삼협철망 홈페이지 견적 문의 접수]\n\n" +
      "1. 회사/현장명: " + company + "\n" +
      "2. 담당자명: " + name + "\n" +
      "3. 연락처: " + phone + "\n" +
      "4. 이메일: " + email + "\n" +
      "5. 가공 서비스: " + service + "\n" +
      "6. 희망 규격 및 수량:\n" + specs + "\n\n" +
      "📁 도면 첨부파일 링크:\n" + fileUrl + "\n\n" +
      "---본 메일은 B2B 영업시스템 API에 의해 자동 발송되었습니다.---";

    MailApp.sendEmail({
      to: "samhyupm@naver.com",
      subject: "[삼협철망 견적문의] " + service + " - " + company,
      body: emailBody
    });

    return ContentService
      .createTextOutput(JSON.stringify({ status: "success", fileUrl: fileUrl }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: "error", message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// past log -> company 시트 N, O, P열 동기화
function syncPastLogsToCompany() {
  var ss = SpreadsheetApp.openById(SS_ID);
  var logSheet = ss.getSheetByName("mail_log");
  var companySheet = ss.getSheetByName("company");

  if (!logSheet || !companySheet) {
    SpreadsheetApp.getUi().alert('시트를 찾을 수 없습니다.');
    return;
  }

  var logRows = logSheet.getDataRange().getValues();
  var companyRows = companySheet.getDataRange().getValues();

  var logMap = {};
  for (var i = 1; i < logRows.length; i++) {
    var cName = (logRows[i][3] || '').toString().trim();
    var status = (logRows[i][6] || '').toString().trim();
    var date = logRows[i][2];
    var detail = (logRows[i][7] || '').toString().trim();

    if (cName && status === '성공') {
      logMap[cName] = {
        date: date,
        detail: detail
      };
    }
  }

  var updatedCount = 0;
  for (var r = 1; r < companyRows.length; r++) {
    var companyName = (companyRows[r][2] || '').toString().trim();
    if (companyName && logMap[companyName]) {
      var logData = logMap[companyName];
      var formattedDate = (logData.date instanceof Date)
        ? Utilities.formatDate(logData.date, "Asia/Seoul", "yyyy-MM-dd HH:mm:ss")
        : logData.date.toString();

      companySheet.getRange(r + 1, 14).setValue('성공');
      companySheet.getRange(r + 1, 15).setValue(formattedDate);
      companySheet.getRange(r + 1, 16).setValue(logData.detail);
      updatedCount++;
    }
  }

  SpreadsheetApp.getUi().alert('동기화 완료: 총 ' + updatedCount + '개 업체의 상태를 업데이트했습니다.');
}

// 반송된 이메일 일괄 실패 처리
function markBouncedEmails() {
  var ss = SpreadsheetApp.openById(SS_ID);
  var sheet = ss.getSheetByName("company");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("'company' 시트를 찾을 수 없습니다.");
    return;
  }

  var rows = sheet.getDataRange().getValues();
  var bouncedCompanies = {
    "에이피씨엠": "도메인 주소 오류 (sanner.co 찾을 수 없음)",
    "세광부속": "수신 주소 없음 (sk_autodoor_light 계정 없음)",
    "한일금속": "도메인 주소 오류 (kjc.or 찾을 수 없음)",
    "현성산업": "수신 주소 없음 (hyunsung_industry 계정 없음)"
  };

  var updated = 0;
  var nowStr = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");

  for (var i = 1; i < rows.length; i++) {
    var companyName = (rows[i][2] || "").toString().trim();
    if (bouncedCompanies.hasOwnProperty(companyName)) {
      var reason = bouncedCompanies[companyName];
      sheet.getRange(i + 1, 14).setValue("실패"); // N열
      sheet.getRange(i + 1, 15).setValue(nowStr);   // O열
      sheet.getRange(i + 1, 16).setValue(reason);   // P열
      updated++;
    }
  }

  SpreadsheetApp.getUi().alert("반송 처리 완료: " + updated + "개 업체의 발송상태를 실패로 기록했습니다.");
}
