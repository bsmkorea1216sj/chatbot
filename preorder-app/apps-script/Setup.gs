/**
 * 스프레드시트 초기 세팅 스크립트.
 * Apps Script 편집기에서 setupSpreadsheet 함수를 한 번 실행하면
 * '신청내역' / '상품정보' 시트와 헤더를 자동으로 생성한다.
 */

function setupSpreadsheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  setupApplicationSheet_(ss);
  setupProductSheet_(ss);
  SpreadsheetApp.getUi().alert('시트 세팅이 완료되었습니다.');
}

function setupApplicationSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_NAME_APPLICATIONS);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME_APPLICATIONS);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, APPLICATION_HEADERS.length).setValues([APPLICATION_HEADERS]);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, APPLICATION_HEADERS.length).setFontWeight('bold');
  }
}

function setupProductSheet_(ss) {
  let sheet = ss.getSheetByName(SHEET_NAME_PRODUCTS);
  const isNew = !sheet;
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME_PRODUCTS);

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, PRODUCT_HEADERS.length).setValues([PRODUCT_HEADERS]);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, PRODUCT_HEADERS.length).setFontWeight('bold');
  }

  if (isNew) {
    sheet.getRange(2, 1, 1, PRODUCT_HEADERS.length).setValues([[
      'PRD-001',
      '밸런싱 세럼 30ml',
      'NEW',
      '피부 균형을 맞춰주는 데일리 진정 세럼',
      32000,
      15,
      27200,
      100,
      '',
      '2024-05-20',
      '2024-06-02',
      '2024-06-10',
    ]]);
  }
}
