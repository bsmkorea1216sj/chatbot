/**
 * 설문 응답 시각화 스크립트 (Responses 시트와 동일한 시트에 출력)
 * Responses 시트의 응답 데이터를 집계하여
 * 같은 시트의 오른쪽 영역(F열~)에 요약 표와
 * AI별 원차트, 무료/유료 사용유형 원차트를 생성합니다.
 *
 * AI별 표/차트와 사용유형 표/차트를 좌우로 충분히 간격을 두고 배치하여
 * (F~G열 vs Q~R열) 두 차트가 겹쳐서 안 보이는 문제를 방지합니다.
 *
 * 사용법: Apps Script 편집기에서 이 파일 저장 후,
 * 스프레드시트를 새로고침하면 상단 메뉴에 "설문 분석"이 생기고
 * "차트 생성/갱신"을 클릭하면 됩니다. (직접 generateAnalysis 함수를
 * 실행해도 됩니다.)
 */

var RESPONSES_SHEET_NAME = 'Responses';
var AI_TABLE_COL = 6;        // F열: AI별 표
var PRICING_TABLE_COL = 17;  // Q열: 사용유형 표 (원차트 폭 480px가 기본 열너비 기준 약 5~6열을 차지하므로
                              // AI 차트(F열 시작)와 절대 겹치지 않도록 충분히 간격을 둠)
var CLEAR_START_COL = 6;     // F열부터
var CLEAR_NUM_COLS = 20;     // F~Y열까지 요약 영역으로 확보 후 초기화

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('설문 분석')
    .addItem('차트 생성/갱신', 'generateAnalysis')
    .addToUi();
}

function generateAnalysis() {
  var ui = SpreadsheetApp.getUi();
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(RESPONSES_SHEET_NAME);
  if (!sheet || sheet.getLastRow() < 2) {
    ui.alert('집계할 응답 데이터가 없습니다. (' + RESPONSES_SHEET_NAME + ' 시트 확인)');
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
    ui.alert('시트 헤더가 예상과 다릅니다. "사용하는 AI", "무료/유료" 열이 필요합니다.');
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
  sheet.getRange(1, CLEAR_START_COL, sheet.getMaxRows(), CLEAR_NUM_COLS).clearContent();

  // AI별 집계 표 (F~G열)
  sheet.getRange(1, AI_TABLE_COL).setValue('사용 AI').setFontWeight('bold');
  sheet.getRange(1, AI_TABLE_COL + 1).setValue('응답 수').setFontWeight('bold');
  var aiKeys = Object.keys(aiCounts);
  aiKeys.forEach(function (key, i) {
    sheet.getRange(2 + i, AI_TABLE_COL).setValue(key);
    sheet.getRange(2 + i, AI_TABLE_COL + 1).setValue(aiCounts[key]);
  });

  // 무료/유료 집계 표 (Q~R열, AI 표와 같은 줄에서 시작하되 열을 충분히 분리)
  sheet.getRange(1, PRICING_TABLE_COL).setValue('사용유형').setFontWeight('bold');
  sheet.getRange(1, PRICING_TABLE_COL + 1).setValue('응답 수').setFontWeight('bold');
  var pricingKeys = Object.keys(pricingCounts);
  pricingKeys.forEach(function (key, i) {
    sheet.getRange(2 + i, PRICING_TABLE_COL).setValue(key);
    sheet.getRange(2 + i, PRICING_TABLE_COL + 1).setValue(pricingCounts[key]);
  });

  SpreadsheetApp.flush();

  // AI별 원차트: F열 표 아래쪽에 배치 (표 바로 아래, 다른 차트와 열이 겹치지 않음)
  if (aiKeys.length > 0) {
    var aiChart = sheet.newChart()
      .asPieChart()
      .addRange(sheet.getRange(1, AI_TABLE_COL, aiKeys.length + 1, 2))
      .setNumHeaders(1)
      .setPosition(aiKeys.length + 3, AI_TABLE_COL, 0, 0)
      .setOption('title', 'AI별 사용 비율')
      .setOption('pieSliceText', 'percentage')
      .setOption('width', 480)
      .setOption('height', 320)
      .build();
    sheet.insertChart(aiChart);
  }

  // 무료/유료 사용유형 원차트: Q열 표 아래쪽에 배치 (AI 차트와 열이 충분히 분리되어 겹치지 않음)
  if (pricingKeys.length > 0) {
    var pricingChart = sheet.newChart()
      .asPieChart()
      .addRange(sheet.getRange(1, PRICING_TABLE_COL, pricingKeys.length + 1, 2))
      .setNumHeaders(1)
      .setPosition(pricingKeys.length + 3, PRICING_TABLE_COL, 0, 0)
      .setOption('title', '무료/유료 사용유형 비율')
      .setOption('pieSliceText', 'percentage')
      .setOption('width', 480)
      .setOption('height', 320)
      .build();
    sheet.insertChart(pricingChart);
  }

  sheet.autoResizeColumns(AI_TABLE_COL, 2);
  sheet.autoResizeColumns(PRICING_TABLE_COL, 2);

  // 실행 후 자동으로 F1 셀로 화면을 이동시켜, 스크롤 안 해서 못 보는 경우를 방지
  SpreadsheetApp.setActiveSheet(sheet);
  sheet.setActiveRange(sheet.getRange(1, AI_TABLE_COL));

  ui.alert('설문 분석 차트가 생성/갱신되었습니다. (Responses 시트 F열로 화면이 이동합니다. 그래도 안 보이면 시트를 오른쪽으로 스크롤해 F~R열 부근을 확인해 주세요.)');
}
