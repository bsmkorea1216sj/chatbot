/**
 * 설문 응답 시각화 스크립트 (Responses 시트와 동일한 시트에 출력)
 * Responses 시트의 응답 데이터를 집계하여
 * 같은 시트의 오른쪽 영역(F열~)에 요약 표와
 * AI별 원차트, 무료/유료 사용유형 원차트를 생성합니다.
 *
 * 사용법: Apps Script 편집기에서 이 파일 저장 후,
 * 스프레드시트를 새로고침하면 상단 메뉴에 "설문 분석"이 생기고
 * "차트 생성/갱신"을 클릭하면 됩니다. (직접 generateAnalysis 함수를
 * 실행해도 됩니다.)
 */

var RESPONSES_SHEET_NAME = 'Responses';
var SUMMARY_START_COL = 6; // F열부터 요약 영역 시작 (A~D는 응답 데이터: 타임스탬프/AI/기타/무료·유료)
var SUMMARY_AREA_COLS = 6; // 요약 영역으로 비워둘 열 수 (F~K)

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('설문 분석')
    .addItem('차트 생성/갱신', 'generateAnalysis')
    .addToUi();
}

function generateAnalysis() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(RESPONSES_SHEET_NAME);
  if (!sheet || sheet.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('집계할 응답 데이터가 없습니다. (' + RESPONSES_SHEET_NAME + ' 시트 확인)');
    return;
  }

  var dataRange = sheet.getRange(1, 1, sheet.getLastRow(), 4); // A~D: 타임스탬프, 사용하는 AI, 기타 AI, 무료/유료
  var data = dataRange.getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var aiIdx = headers.indexOf('사용하는 AI');
  var otherIdx = headers.indexOf('기타 AI(직접입력)');
  var pricingIdx = headers.indexOf('무료/유료');

  if (aiIdx === -1 || pricingIdx === -1) {
    SpreadsheetApp.getUi().alert('시트 헤더가 예상과 다릅니다. "사용하는 AI", "무료/유료" 열이 필요합니다.');
    return;
  }

  var aiCounts = {};
  var pricingCounts = {};

  rows.forEach(function (row) {
    var ai = row[aiIdx];
    if (ai) {
      var label = (ai === '기타' && otherIdx !== -1 && row[otherIdx]) ? ('기타: ' + row[otherIdx]) : ai;
      aiCounts[label] = (aiCounts[label] || 0) + 1;
    }

    var pricing = row[pricingIdx];
    if (pricing) {
      pricingCounts[pricing] = (pricingCounts[pricing] || 0) + 1;
    }
  });

  // 기존 요약 영역/차트 정리 (이 스크립트가 만든 F열 이후 영역만 초기화)
  sheet.getCharts().forEach(function (chart) { sheet.removeChart(chart); });
  sheet.getRange(1, SUMMARY_START_COL, sheet.getMaxRows(), SUMMARY_AREA_COLS).clearContent();

  var col = SUMMARY_START_COL;

  // AI별 집계 표
  sheet.getRange(1, col).setValue('사용 AI').setFontWeight('bold');
  sheet.getRange(1, col + 1).setValue('응답 수').setFontWeight('bold');
  var aiKeys = Object.keys(aiCounts);
  aiKeys.forEach(function (key, i) {
    sheet.getRange(2 + i, col).setValue(key);
    sheet.getRange(2 + i, col + 1).setValue(aiCounts[key]);
  });

  // 무료/유료 집계 표 (AI 표 아래쪽에 배치)
  var pricingStartRow = aiKeys.length + 4;
  sheet.getRange(pricingStartRow, col).setValue('사용유형').setFontWeight('bold');
  sheet.getRange(pricingStartRow, col + 1).setValue('응답 수').setFontWeight('bold');
  var pricingKeys = Object.keys(pricingCounts);
  pricingKeys.forEach(function (key, i) {
    sheet.getRange(pricingStartRow + 1 + i, col).setValue(key);
    sheet.getRange(pricingStartRow + 1 + i, col + 1).setValue(pricingCounts[key]);
  });

  SpreadsheetApp.flush();

  // AI별 원차트
  if (aiKeys.length > 0) {
    var aiChart = sheet.newChart()
      .asPieChart()
      .addRange(sheet.getRange(1, col, aiKeys.length + 1, 2))
      .setNumHeaders(1)
      .setPosition(2, col + 3, 0, 0)
      .setOption('title', 'AI별 사용 비율')
      .setOption('pieSliceText', 'percentage')
      .setOption('width', 480)
      .setOption('height', 320)
      .build();
    sheet.insertChart(aiChart);
  }

  // 무료/유료 사용유형 원차트
  if (pricingKeys.length > 0) {
    var pricingChart = sheet.newChart()
      .asPieChart()
      .addRange(sheet.getRange(pricingStartRow, col, pricingKeys.length + 1, 2))
      .setNumHeaders(1)
      .setPosition(pricingStartRow + 2, col + 3, 0, 0)
      .setOption('title', '무료/유료 사용유형 비율')
      .setOption('pieSliceText', 'percentage')
      .setOption('width', 480)
      .setOption('height', 320)
      .build();
    sheet.insertChart(pricingChart);
  }

  sheet.autoResizeColumns(col, 2);
}
