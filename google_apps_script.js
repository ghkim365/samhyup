/**
 * 삼협철망 B2B 마케팅 & 견적 모니터링 연동 Google Apps Script (GAS) - 최종 컬럼 정밀 매핑 버전
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000); 
    
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    var site = data.site || 'catalog';
    var source = data.source || 'direct';
    
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (action === 'trackVisit') {
      var sheet = getOrCreateSheet(ss, 'analytics_visits');
      
      if (sheet.getLastRow() === 0) {
        sheet.appendRow(['날짜', '사이트', 'Google Ads', '검색 (Organic)', '직접 유입 (Direct)']);
        sheet.getRange(1, 1, 1, 5).setFontWeight('bold').setBackground('#f3f4f6');
      }
      
      var today = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');
      var lastRow = sheet.getLastRow();
      var foundRow = -1;
      
      var startRow = Math.max(2, lastRow - 35);
      if (lastRow >= 2) {
        var range = sheet.getRange(startRow, 1, lastRow - startRow + 1, 2);
        var values = range.getValues();
        for (var i = 0; i < values.length; i++) {
          var rowDate = Utilities.formatDate(new Date(values[i][0]), 'Asia/Seoul', 'yyyy-MM-dd');
          var rowSite = values[i][1];
          if (rowDate === today && rowSite === site) {
            foundRow = startRow + i;
            break;
          }
        }
      }
      
      if (foundRow !== -1) {
        var col = 3;
        if (source === 'search') col = 4;
        else if (source === 'direct') col = 5;
        
        var cell = sheet.getRange(foundRow, col);
        cell.setValue(Number(cell.getValue()) + 1);
      } else {
        var adsCount = (source === 'google_ads') ? 1 : 0;
        var searchCount = (source === 'search') ? 1 : 0;
        var directCount = (source === 'direct') ? 1 : 0;
        sheet.appendRow([today, site, adsCount, searchCount, directCount]);
      }
      
      return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: 'Visit tracked' }))
        .setMimeType(ContentService.MimeType.JSON);
        
    } else if (action === 'submitQuote') {
      var sheet = getOrCreateSheet(ss, 'analytics');
      
      // 시트 헤더가 없을 때만 자동 생성 (사용자 헤더 보호)
      if (sheet.getLastRow() === 0) {
        sheet.appendRow([
          '접수 일시',           // A열
          '사이트',             // B열
          '유입 경로',           // C열
          '회사/현장명',         // D열
          '담당자',             // E열
          '연락처',             // F열
          '이메일',             // G열
          '요청 품목',           // H열
          '희망 규격 및 수량',     // I열
          '첨부파일',           // J열
          '구분'                // K열
        ]);
        sheet.getRange(1, 1, 1, 11).setFontWeight('bold').setBackground('#e0f2fe');
      }
      
      var nowStr = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss');
      
      // 시트의 컬럼 순서 (A~K열)에 맞춰 데이터를 정확하게 정렬하여 삽입
      sheet.appendRow([
        nowStr,                                                // A열: 접수 일시
        site === 'main_site' ? '공식홈' : '카탈로그',             // B열: 사이트
        source,                                                // C열: 유입 경로
        data.company || '일반 개인/현장',                       // D열: 회사/현장명
        data.name || '담당자 미기재',                           // E열: 담당자
        data.phone || '연락처 미기재',                           // F열: 연락처
        data.email || '',                                      // G열: 이메일
        data.product || '공식홈 문의',                          // H열: 요청 품목
        data.specs || '',                                      // I열: 희망 규격 및 수량
        data.attachment || '',                                 // J열: 첨부파일
        site === 'main_site' ? '공식홈 문의' : '카탈로그 문의'    // K열: 구분
      ]);
      
      return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: 'Quote submitted' }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'Unknown action' }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function doGet(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    var visitsSheet = ss.getSheetByName('analytics_visits');
    var visitsData = { google_ads: 0, search: 0, direct: 0 };
    var targetSite = e.parameter.site;
    
    if (visitsSheet && visitsSheet.getLastRow() >= 2) {
      var visitsRange = visitsSheet.getRange(2, 1, visitsSheet.getLastRow() - 1, 5);
      var visitsValues = visitsRange.getValues();
      for (var i = 0; i < visitsValues.length; i++) {
        var rowSite = visitsValues[i][1];
        if (!targetSite || rowSite === targetSite) {
          visitsData.google_ads += Number(visitsValues[i][2] || 0);
          visitsData.search += Number(visitsValues[i][3] || 0);
          visitsData.direct += Number(visitsValues[i][4] || 0);
        }
      }
    }
    
    var quotesSheet = ss.getSheetByName('analytics');
    var quotesList = [];
    
    if (quotesSheet && quotesSheet.getLastRow() >= 2) {
      var quotesRange = quotesSheet.getRange(2, 1, quotesSheet.getLastRow() - 1, 11);
      var quotesValues = quotesRange.getValues();
      for (var i = 0; i < quotesValues.length; i++) {
        var rowSite = quotesValues[i][1]; // B열 (사이트)
        var normalizedSite = (rowSite === '공식홈') ? 'main_site' : 'catalog';
        if (!targetSite || normalizedSite === targetSite) {
          quotesList.push({
            id: 201 + i,
            date: quotesValues[i][0],          // A열
            site: normalizedSite,              // B열 기반으로 대시보드 호환 판단
            source: quotesValues[i][2],        // C열 (유입 경로)
            company: quotesValues[i][3],       // D열 (회사/현장명)
            name: quotesValues[i][4],          // E열 (담당자)
            phone: quotesValues[i][5],         // F열 (연락처)
            email: quotesValues[i][6],         // G열 (이메일)
            product: quotesValues[i][7],       // H열 (요청 품목)
            specs: quotesValues[i][8],         // I열 (희망 규격 및 수량)
            attachment: quotesValues[i][9]     // J열 (첨부파일)
          });
        }
      }
    }
    
    var responseData = {
      visits: visitsData,
      quotes: quotesList
    };
    
    var callback = e.parameter.callback;
    if (callback) {
      return ContentService.createTextOutput(callback + '(' + JSON.stringify(responseData) + ')')
        .setMimeType(ContentService.MimeType.JAVASCRIPT);
    }
    
    return ContentService.createTextOutput(JSON.stringify(responseData))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    var errorResult = { error: error.toString() };
    var callback = e.parameter.callback;
    if (callback) {
      return ContentService.createTextOutput(callback + '(' + JSON.stringify(errorResult) + ')')
        .setMimeType(ContentService.MimeType.JAVASCRIPT);
    }
    return ContentService.createTextOutput(JSON.stringify(errorResult))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function getOrCreateSheet(ss, sheetName) {
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  return sheet;
}
