# 사전 구매신청 웹앱

Google Sheets를 DB로 사용하는 "사전 구매신청" 랜딩페이지 + Google Apps Script 백엔드입니다.

## 폴더 구조

```
preorder-app/
  apps-script/          # clasp로 push하는 Apps Script 프로젝트
    appsscript.json      # clasp 매니페스트 (Web App 배포 설정)
    Code.gs               # doGet/doPost 백엔드 API
    Setup.gs              # 시트/헤더 자동 생성 스크립트
    Page.html              # HtmlService 진입 페이지 (index.html 역할)
    Stylesheet.html         # style.css를 <style> 태그로 감싼 include 파일
    JavaScript.html          # script.js를 <script> 태그로 감싼 include 파일
    .clasp.json.example       # clasp 설정 템플릿 (scriptId 채운 뒤 .clasp.json으로 저장)
  static/                # 별도 정적 호스팅용 (Netlify, S3, GitHub Pages 등)
    index.html
    style.css
    script.js
```

Apps Script는 프로젝트 안에 `.css`/`.js` 파일을 독립 에셋으로 둘 수 없어(허용 타입은 `.gs`/`.html`/`.json`뿐),
같은 UI를 두 가지 형태로 제공합니다.

- **`apps-script/`**: Apps Script 프로젝트 자체에서 `doGet`이 페이지까지 서빙하는 방식(HtmlService). `Stylesheet.html`/`JavaScript.html`은 `static/style.css`, `static/script.js`와 내용이 동일하며, `Page.html`에서 `include()`로 불러옵니다.
- **`static/`**: 프론트를 별도 정적 호스팅에 올리고, 배포된 Apps Script Web App URL을 API로만 호출하는 방식(스펙 5번 문서의 "별도 정적 호스팅" 옵션).

두 버전의 UI/로직을 수정할 때는 양쪽을 함께 반영해야 합니다.

---

## 1. 스프레드시트 초기 세팅

1. Google Sheets에서 새 스프레드시트를 만들고 이름을 `사전구매신청_DB`로 지정합니다.
2. 확장 프로그램 → Apps Script로 편집기를 엽니다.
3. 이 저장소의 `apps-script/` 폴더 내용을 붙여넣거나(아래 clasp 가이드 참고), 최소한 `Code.gs`, `Setup.gs`를 추가합니다.
4. Apps Script 편집기에서 함수 선택 드롭다운을 `setupSpreadsheet`로 바꾸고 ▶ 실행합니다.
   - `신청내역`, `상품정보` 시트가 없으면 생성되고, 헤더(1행)가 자동으로 채워집니다.
   - `상품정보` 시트가 새로 만들어진 경우 샘플 상품 1건(`밸런싱 세럼 30ml`)이 2행에 채워집니다.
5. `상품정보` 시트의 `이미지URL` 컬럼에 실제 상품 이미지 링크(Drive 공개 링크 등)를 입력하고, 예약 시작일/종료일/출시예정일을 원하는 날짜로 수정합니다.
6. 최초 실행 시 스크립트 권한 승인 팝업이 뜨면 승인합니다.

### 시트 스키마

`신청내역`(A~M)과 `상품정보`(A~L) 컬럼 구성은 기획 문서 그대로이며, `Code.gs`의 `APPLICATION_HEADERS` / `PRODUCT_HEADERS` 상수에 정의되어 있습니다. 백엔드는 컬럼 위치가 아니라 1행의 헤더명을 기준으로 값을 매핑하므로, 열 순서를 바꾸더라도 헤더 텍스트만 동일하면 동작합니다.

---

## 2. clasp로 로컬 개발 / 배포

```bash
npm install -g @google/clasp
clasp login

cd preorder-app/apps-script
cp .clasp.json.example .clasp.json
# .clasp.json의 scriptId를 1단계에서 만든 Apps Script 프로젝트 ID로 교체
# (Apps Script 편집기 → 프로젝트 설정 → 스크립트 ID에서 확인)

clasp push        # 로컬 파일을 Apps Script 프로젝트로 업로드
clasp deploy      # Web App으로 배포 (버전 생성)
```

배포 시 액세스 권한을 **"익명 사용자도 접근 가능"**(테스트용)으로 설정합니다. `appsscript.json`에 이미
`"access": "ANYONE_ANONYMOUS"`로 설정되어 있으며, 최초 배포는 Apps Script 편집기의 "배포 → 새 배포"에서
한 번 승인 절차를 거쳐야 합니다. 이후에는 `clasp deploy`로 갱신할 수 있습니다.

배포가 끝나면 발급되는 Web App URL(`https://script.google.com/macros/s/xxxx/exec`)을 기록해 둡니다.

> 실서비스로 전환할 때는 `access`를 조직 내부용으로 제한하거나, `doPost`에서 `Origin`/Referer 검증 로직을
> 추가하는 것을 권장합니다(현재는 테스트 목적의 익명 접근 상태입니다).

---

## 3. 프론트엔드 연결

### 옵션 A. Apps Script HtmlService로 같은 프로젝트에서 서빙

별도 설정 없이 Web App URL 자체가 페이지 주소입니다. `doGet`이 `action` 파라미터가 없을 때 `Page.html`을
렌더링하며, `ScriptApp.getService().getUrl()`로 자기 자신의 URL을 `webAppUrl` 변수로 템플릿에 주입하므로
프론트 코드에서 별도 설정이 필요 없습니다.

### 옵션 B. 별도 정적 호스팅 (GitHub Pages, Netlify, S3 등)

`static/index.html` 하단의 아래 값을 배포된 Web App URL로 교체한 뒤 정적 호스팅에 업로드합니다.

```html
<script>
  window.PRE_ORDER_CONFIG = {
    webAppUrl: "https://script.google.com/macros/s/xxxx/exec",
    productId: "",
  };
</script>
```

`productId`를 비워두면 `상품정보` 시트의 첫 번째 상품을 자동으로 불러옵니다. 특정 상품을 지정하려면
`상품ID` 값을 넣습니다.

### CORS 관련 참고

- `GET`(상품 조회)은 단순 요청이라 CORS 제약이 없습니다.
- `POST`(신청 제출)는 `Content-Type: text/plain;charset=utf-8`으로 전송해 프리플라이트(OPTIONS)를
  발생시키지 않습니다(`script.js`에 이미 적용됨). Apps Script Web App은 프리플라이트 요청을 정상적으로
  처리하지 못하므로, 이 방식이 표준 우회법입니다. 본문은 여전히 JSON 문자열이며 서버(`doPost`)에서
  `JSON.parse(e.postData.contents)`로 파싱합니다.

---

## 4. API 명세

### `GET {WebAppURL}?action=getProduct[&productId=PRD-001]`

```json
{
  "success": true,
  "product": {
    "productId": "PRD-001",
    "name": "밸런싱 세럼 30ml",
    "badge": "NEW",
    "description": "피부 균형을 맞춰주는 데일리 진정 세럼",
    "price": 32000,
    "discountRate": 15,
    "preorderPrice": 27200,
    "stock": 100,
    "imageUrl": "...",
    "reservationStart": "2024-05-20",
    "reservationEnd": "2024-06-02",
    "releaseDate": "2024-06-10"
  }
}
```

### `POST {WebAppURL}`

요청 본문:

```json
{
  "action": "submitApplication",
  "name": "홍길동",
  "phone": "01012345678",
  "email": "test@example.com",
  "quantity": 2,
  "productId": "PRD-001",
  "agree": true
}
```

응답(성공):

```json
{ "success": true, "applicationId": "PRE-1719900000000" }
```

응답(실패):

```json
{ "success": false, "message": "개인정보 수집·이용에 동의해 주세요." }
```

서버는 프론트에서 넘어온 가격을 신뢰하지 않고, `상품정보` 시트의 정가/할인율을 기준으로 사전예약가와
결제예정금액을 다시 계산한 뒤 `신청내역` 시트에 append합니다. 동시 제출 시 `LockService.getScriptLock()`으로
행 경쟁을 방지합니다.

---

## 5. 로컬에서 정적 프론트만 미리보기

Apps Script 배포 전에 레이아웃만 확인하려면 `static/` 폴더를 정적 서버로 띄우면 됩니다.

```bash
cd preorder-app/static
python3 -m http.server 8000
```

이 경우 `webAppUrl`이 설정되어 있지 않으면 상품 데이터 fetch가 실패하고 에러 메시지가 표시되는 것이
정상입니다(실제 배포된 Web App URL을 연결해야 상품 데이터/카운트다운이 채워집니다).
