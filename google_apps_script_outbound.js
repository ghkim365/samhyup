/**
 * 삼협철망 B2B 아웃바운드 이메일 자동 발송 Google Apps Script (GAS)
 * 
 * [설치 및 사용 방법]
 * 1. 구글 스프레드시트에서 [확장 프로그램] > [Apps Script]를 클릭합니다.
 * 2. 기존 코드가 있다면 하단에 붙여넣거나 새 스크립트 파일을 만들어 본 코드를 입력합니다.
 * 3. 저장 후 스프레드시트를 새로고침하면 상단에 "삼협 아웃바운드" 메뉴가 나타납니다.
 * 4. "company" 시트의 A열 체크박스를 선택한 후, "삼협 아웃바운드" > "선택 제안서 발송"을 누릅니다.
 */

// Vercel 배포 주소에 맞춰 설정
var BASE_URL = "https://samhyup.vercel.app/";

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('삼협 아웃바운드')
    .addItem('선택 제안서 발송', 'sendOutboundEmails')
    .addToUi();
}

function sendOutboundEmails() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('company');
  if (!sheet) {
    SpreadsheetApp.getUi().alert('오류: "company" 이름의 시트를 찾을 수 없습니다.');
    return;
  }
  
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('발송할 데이터가 없습니다.');
    return;
  }
  
  // 헤더 파싱하여 회사명, 이메일 주소 열 찾기
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var emailColIdx = -1;
  var companyColIdx = -1;
  
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i].toString().trim();
    if (header === '이메일' || header === '메일' || header === 'Email' || header === '이메일주소') {
      emailColIdx = i + 1;
    }
    if (header === '회사명' || header === '업체명' || header === '상호' || header === '회사' || header === '수신처') {
      companyColIdx = i + 1;
    }
  }
  
  // 감지 실패 시 기본값 설정 (A열: 체크, B열: 회사명, C열: 이메일 등으로 가정)
  if (companyColIdx === -1) companyColIdx = 2; // 기본 B열
  if (emailColIdx === -1) emailColIdx = 3;   // 기본 C열
  
  var dataRange = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn());
  var values = dataRange.getValues();
  
  var targets = [];
  for (var r = 0; r < values.length; r++) {
    var rowNum = r + 2;
    var isChecked = values[r][0]; // A열 (체크박스)
    
    if (isChecked === true || isChecked === 'TRUE') {
      var companyName = values[r][companyColIdx - 1].toString().trim();
      var emailAddress = values[r][emailColIdx - 1].toString().trim();
      
      if (emailAddress) {
        targets.push({
          rowNum: rowNum,
          companyName: companyName || '대표님',
          emailAddress: emailAddress
        });
      }
    }
  }
  
  if (targets.length === 0) {
    SpreadsheetApp.getUi().alert('알림: A열 체크박스에 체크된 대상이 없습니다.');
    return;
  }
  
  // 확인 창 표시
  var confirmUi = SpreadsheetApp.getUi().alert(
    '이메일 발송 확인',
    '총 ' + targets.length + '개 업체에 B2B 제안서를 발송하시겠습니까?',
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (confirmUi !== SpreadsheetApp.getUi().Button.YES) {
    return;
  }
  
  // 1. 템플릿 파일 로드
  var htmlTemplate = "";
  try {
    var response = UrlFetchApp.fetch(BASE_URL + "templates/samhyup_proposal.html");
    htmlTemplate = response.getContentText("UTF-8");
  } catch (err) {
    SpreadsheetApp.getUi().alert('템플릿 로드 실패: ' + BASE_URL + 'templates/samhyup_proposal.html 주소를 확인해주세요. (에러: ' + err.toString() + ')');
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
  
  // 3. 순차 발송 진행
  var successCount = 0;
  var failCount = 0;
  
  for (var t = 0; t < targets.length; t++) {
    var target = targets[t];
    
    // 회사명 개인화 치환
    var personalizedHtml = htmlTemplate.replace(/{회사명}/g, target.companyName);
    
    try {
      GmailApp.sendEmail(
        target.emailAddress,
        "[삼협철망] " + target.companyName + " 귀사 건설현장 및 자재유통 협력 제안",
        "본 메일은 B2B 협력 제안서 메일입니다. HTML 형식을 지원하는 메일 클라이언트에서 확인해주세요.",
        {
          htmlBody: personalizedHtml,
          inlineImages: inlineImages
        }
      );
      
      // 발송 완료 후 체크 해제 및 기록 남기기
      sheet.getRange(target.rowNum, 1).setValue(false); // 체크박스 해제
      
      // 발송완료일시 기록용 열 (만약 열이 충분하다면 맨 끝 열 옆에 기록)
      var statusCol = sheet.getLastColumn() + 1;
      var statusColIdx = headers.indexOf('최종 발송일시') + 1;
      if (statusColIdx > 0) {
        statusCol = statusColIdx;
      } else {
        sheet.getRange(1, statusCol).setValue('최종 발송일시').setFontWeight('bold');
        headers.push('최종 발송일시');
      }
      
      var nowStr = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss');
      sheet.getRange(target.rowNum, statusCol).setValue('발송완료 (' + nowStr + ')');
      
      successCount++;
    } catch (err) {
      Logger.log("메일 발송 에러 (" + target.emailAddress + "): " + err.toString());
      failCount++;
    }
  }
  
  SpreadsheetApp.getUi().alert(
    '이메일 발송 완료\n\n' +
    '- 성공: ' + successCount + '건\n' +
    '- 실패: ' + failCount + '건'
  );
}
