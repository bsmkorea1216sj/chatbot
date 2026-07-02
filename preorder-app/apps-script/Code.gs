/**
 * 사전 구매신청 웹앱 백엔드
 * Google Sheets(신청내역 / 상품정보)를 DB로 사용하는 Apps Script Web App API.
 */

const SHEET_NAME_APPLICATIONS = '신청내역';
const SHEET_NAME_PRODUCTS = '상품정보';

const APPLICATION_HEADERS = [
  '신청ID', '신청일시', '이름', '연락처', '이메일', '상품명',
  '신청수량', '정가', '할인율', '사전예약가', '결제예정금액', '개인정보동의', '신청상태',
];

const PRODUCT_HEADERS = [
  '상품ID', '상품명', '배지', '서브설명', '정가', '할인율', '사전예약가',
  '재고/한정수량', '이미지URL', '사전예약시작일', '사전예약종료일', '출시예정일',
];

function doGet(e) {
  const params = (e && e.parameter) || {};

  if (params.action === 'getProduct') {
    return jsonResponse(getProduct(params.productId));
  }

  // action 파라미터가 없으면 같은 프로젝트 내 HtmlService 페이지를 서빙한다.
  const template = HtmlService.createTemplateFromFile('Page');
  template.webAppUrl = ScriptApp.getService().getUrl();
  return template
    .evaluate()
    .setTitle('사전 구매신청')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.action !== 'submitApplication') {
      return jsonResponse({ success: false, message: '지원하지 않는 요청입니다.' });
    }
    return jsonResponse(submitApplication(body));
  } catch (err) {
    return jsonResponse({ success: false, message: '요청 처리 중 오류가 발생했습니다: ' + err.message });
  }
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function getSheet_(name) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sheet) throw new Error('시트를 찾을 수 없습니다: ' + name);
  return sheet;
}

function sheetToObjects_(sheet) {
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return [];
  const headers = values[0];
  return values
    .slice(1)
    .filter((row) => row.some((cell) => cell !== ''))
    .map((row) => {
      const obj = {};
      headers.forEach((h, i) => (obj[h] = row[i]));
      return obj;
    });
}

function getProduct(productId) {
  const sheet = getSheet_(SHEET_NAME_PRODUCTS);
  const products = sheetToObjects_(sheet);
  if (!products.length) {
    return { success: false, message: '등록된 상품이 없습니다.' };
  }
  const product = productId
    ? products.find((p) => String(p['상품ID']) === String(productId))
    : products[0];
  if (!product) {
    return { success: false, message: '상품을 찾을 수 없습니다.' };
  }
  return { success: true, product: formatProduct_(product) };
}

function formatProduct_(row) {
  const price = Number(row['정가']) || 0;
  const discountRate = Number(row['할인율']) || 0;
  const preorderPrice = row['사전예약가']
    ? Number(row['사전예약가'])
    : Math.round(price * (1 - discountRate / 100));

  return {
    productId: row['상품ID'],
    name: row['상품명'],
    badge: row['배지'],
    description: row['서브설명'],
    price: price,
    discountRate: discountRate,
    preorderPrice: preorderPrice,
    stock: Number(row['재고/한정수량']) || 0,
    imageUrl: row['이미지URL'],
    reservationStart: formatDate_(row['사전예약시작일']),
    reservationEnd: formatDate_(row['사전예약종료일']),
    releaseDate: formatDate_(row['출시예정일']),
  };
}

function formatDate_(value) {
  if (!value) return '';
  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) return String(value);
  return Utilities.formatDate(date, Session.getScriptTimeZone() || 'Asia/Seoul', 'yyyy-MM-dd');
}

function submitApplication(body) {
  const name = body.name;
  const phone = body.phone;
  const email = body.email;
  const quantity = body.quantity;
  const productId = body.productId;
  const agree = body.agree;

  if (!agree) {
    return { success: false, message: '개인정보 수집·이용에 동의해 주세요.' };
  }
  if (!name || !String(name).trim()) {
    return { success: false, message: '이름을 입력해 주세요.' };
  }
  const phoneDigits = String(phone || '').replace(/[^0-9]/g, '');
  if (!/^0\d{8,10}$/.test(phoneDigits)) {
    return { success: false, message: '연락처 형식이 올바르지 않습니다.' };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || ''))) {
    return { success: false, message: '이메일 형식이 올바르지 않습니다.' };
  }

  const qty = Math.max(1, parseInt(quantity, 10) || 1);

  const productResult = getProduct(productId);
  if (!productResult.success) {
    return productResult;
  }
  const product = productResult.product;
  const paymentAmount = product.preorderPrice * qty;

  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const sheet = getSheet_(SHEET_NAME_APPLICATIONS);
    const applicationId = 'PRE-' + new Date().getTime();
    sheet.appendRow([
      applicationId,
      new Date(),
      name,
      phoneDigits,
      email,
      product.name,
      qty,
      product.price,
      product.discountRate,
      product.preorderPrice,
      paymentAmount,
      true,
      '접수완료',
    ]);
    return { success: true, applicationId: applicationId };
  } finally {
    lock.releaseLock();
  }
}
