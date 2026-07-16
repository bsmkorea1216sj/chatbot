/**
 * AI 사용 설문 웹앱
 * 웹앱으로 배포된 이 스크립트는 이 스크립트가 바인딩된 스프레드시트의
 * "Responses" 시트에 설문 응답을 저장합니다.
 */

var SHEET_NAME = 'Responses';
var HEADERS = ['타임스탬프', '사용하는 AI', '기타 AI(직접입력)', '무료/유료'];

function doGet() {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('AI 사용 설문')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function getOrCreateSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

/**
 * 클라이언트(Index.html)에서 google.script.run으로 호출하는 함수.
 * formData = { aiTool: string, aiToolOther: string, pricing: string }
 */
function submitSurvey(formData) {
  if (!formData || !formData.aiTool || !formData.pricing) {
    throw new Error('필수 항목이 누락되었습니다.');
  }
  if (formData.aiTool === '기타' && !formData.aiToolOther) {
    throw new Error('기타를 선택한 경우 내용을 입력해 주세요.');
  }

  var sheet = getOrCreateSheet_();
  sheet.appendRow([
    new Date(),
    formData.aiTool,
    formData.aiToolOther || '',
    formData.pricing
  ]);

  return { status: 'ok' };
}
