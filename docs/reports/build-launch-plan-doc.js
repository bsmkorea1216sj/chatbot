const D = require("docx");
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,
  AlignmentType,HeadingLevel,BorderStyle,LevelFormat,convertInchesToTwip} = D;

const KR="Malgun Gothic";
const INK="171A1C", MUTED="63676B", ACC="8C2F39", SIG="1E6A5B";
const CW=9026;                    // A4 - 1" margins
const HDRFILL="EFE7E7", ZEBRA="F5F4F1";

const NB={top:{style:BorderStyle.NIL},bottom:{style:BorderStyle.NIL},left:{style:BorderStyle.NIL},right:{style:BorderStyle.NIL}};
const TB={style:BorderStyle.SINGLE,size:3,color:"D6D3C8"};
const CB={top:TB,bottom:TB,left:TB,right:TB};

const t=(s,o={})=>new TextRun({text:s,font:KR,size:o.size||20,bold:!!o.bold,color:o.color||INK,italics:!!o.i});

function P(s,o={}){return new Paragraph({
  children:Array.isArray(s)?s:[t(s,o)],
  alignment:o.align, spacing:{before:o.before??0,after:o.after??140,line:o.line||280},
  indent:o.indent, border:o.border});}

function H(num,title){return new Paragraph({
  children:[t(num+"  ",{bold:true,size:24,color:ACC}),t(title,{bold:true,size:24,color:INK})],
  heading:HeadingLevel.HEADING_1,
  spacing:{before:360,after:160},
  border:{bottom:{style:BorderStyle.SINGLE,size:6,color:ACC,space:6}}});}

function H2(title){return new Paragraph({
  children:[t(title,{bold:true,size:21,color:INK})],
  heading:HeadingLevel.HEADING_2, spacing:{before:260,after:110}});}

function BUL(s,o={}){return new Paragraph({
  children:Array.isArray(s)?s:[t(s)],
  bullet:{level:o.level||0}, spacing:{after:80,line:280}});}

function CALL(label,body){
  return new Table({columnWidths:[CW],width:{size:CW,type:WidthType.DXA},borders:{
      top:{style:BorderStyle.NIL},bottom:{style:BorderStyle.NIL},right:{style:BorderStyle.NIL},
      left:{style:BorderStyle.SINGLE,size:18,color:ACC},
      insideHorizontal:{style:BorderStyle.NIL},insideVertical:{style:BorderStyle.NIL}},
    rows:[new TableRow({children:[new TableCell({
      width:{size:CW,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill:"F7F5F2"},
      margins:{top:140,bottom:140,left:200,right:200},
      children:[new Paragraph({children:[t(label,{bold:true,size:19,color:ACC})],spacing:{after:60}}),
                new Paragraph({children:[t(body,{size:19,color:INK})],spacing:{after:0,line:280}})]})]})]});}

function TBL(head,rows,widths,opt={}){
  const cell=(txt,i,isHead,rowIdx)=>new TableCell({
    width:{size:widths[i],type:WidthType.DXA},
    shading:{type:ShadingType.CLEAR,fill:isHead?HDRFILL:(opt.zebra&&rowIdx%2===1?ZEBRA:"FFFFFF")},
    margins:{top:80,bottom:80,left:120,right:120},
    children:[new Paragraph({
      children:[t(String(txt).replace(/^\*/,""),{bold:isHead||String(txt).startsWith("*"),size:18,
        color:isHead?MUTED:INK})],
      alignment:(opt.right||[]).includes(i)?AlignmentType.RIGHT:AlignmentType.LEFT,
      spacing:{after:0,line:260}})]});
  return new Table({
    columnWidths:widths, width:{size:widths.reduce((a,b)=>a+b,0),type:WidthType.DXA},
    borders:{top:TB,bottom:TB,left:TB,right:TB,insideHorizontal:TB,insideVertical:TB},
    rows:[new TableRow({tableHeader:true,children:head.map((h,i)=>cell(h,i,true,0))}),
      ...rows.map((r,ri)=>new TableRow({children:r.map((c,i)=>cell(c,i,false,ri))}))]});}

const SP=(h)=>new Paragraph({children:[t("")],spacing:{after:h||100}});

/* ─────────────────────────────────────────── */
const body=[];

// 표제
body.push(new Paragraph({children:[t("BSM  ·  최소비용 런칭 계획",{bold:true,size:18,color:ACC})],spacing:{after:80}}));
body.push(new Paragraph({children:[t("AI 챗봇 임대 서비스",{bold:true,size:44,color:INK})],spacing:{after:40}}));
body.push(new Paragraph({children:[t("12주 안에 첫 유료 고객 10곳까지",{size:26,color:MUTED})],
  spacing:{after:180},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:INK,space:10}}}));
body.push(P([t("작성일 2026-09-07   ·   버전 1.0   ·   대상: 내부 실행 계획",{size:18,color:MUTED})],{after:220}));

body.push(TBL(["구분","내용"],[
  ["*총 현금 투입","약 120만 원 (12주간, 대표 인건비 제외)"],
  ["*기간","12주 (3개월)"],
  ["*목표","무료 체험 누적 50건 → 유료 고객 10곳"],
  ["*원가 손익분기","유료 2곳 (월 19.8만 원)"],
  ["*광고비","0원 — 보유 채널(유튜브·블로그·자사몰)만 사용"],
], [1900,7126]));
body.push(SP(240));

// 1
body.push(H("1","요약"));
body.push(P("AI 챗봇을 월 구독으로 임대하는 사업을 최소 비용으로 시작한다. 핵심은 제품을 크게 만들지 않는 것이다. 업종 하나, 채널 하나, 요금제 하나로 좁히고, 이미 보유한 유튜브·블로그·자사몰을 유일한 유입 경로로 쓴다. 광고비는 쓰지 않는다."));
body.push(P("12주간 현금 지출은 약 120만 원이며 대부분 클라우드·API 사용료다. 유료 고객 2곳만 확보해도 운영 원가를 넘어서므로, 이 사업의 위험은 돈이 아니라 시간이다. 따라서 8주차와 12주차에 중단·전환 기준을 미리 정해 두고, 기준에 미달하면 타깃이나 제품 범위를 바꾼다."));
body.push(CALL("이 계획의 한 문장",
  "제품을 만들기 전에 수요를 먼저 확인하고, 보유 콘텐츠를 유입·데모·학습데이터로 세 번 쓰며, 유료 고객 10곳으로 시장 반응을 검증한다."));
body.push(SP(160));

// 2
body.push(H("2","다섯 가지 원칙"));
body.push(TBL(["원칙","실행 방법"],[
  ["*① 팔리는지 먼저 확인한다","1주차에 랜딩페이지와 무료 체험 신청 폼만 공개한다. 제품은 없다. 신청이 들어오는지로 수요를 판정한다."],
  ["*② 하나씩만 한다","업종 1개(IT·네트워크 또는 쇼핑몰), 채널 1개(웹 위젯), 요금제 1개(월 9.9만 원). 선택지를 늘리는 순간 개발과 영업이 동시에 무거워진다."],
  ["*③ 광고비 0원","유튜브·블로그·자사몰이 이미 있다. 유료 광고는 전환율이 검증된 뒤에 쓴다. 검증 전 광고는 돈으로 답을 사는 것이 아니라 답을 흐린다."],
  ["*④ 무료 한도 안에서 돌린다","GCP 무료 등급과 경량 모델로 초기 트래픽을 흡수한다. 예산 알림을 프로젝트 생성 즉시 설정한다."],
  ["*⑤ 중단 기준을 미리 정한다","8주·12주 두 지점의 판정 기준을 지금 문서에 적는다(9항). 나중에 정하면 반드시 자기합리화가 들어간다."],
], [1900,7126], {zebra:true}));
body.push(SP(160));

// 3
body.push(H("3","MVP 경계 — 무엇을 만들고 무엇을 미루는가"));
body.push(P("아래 오른쪽 항목은 기술적으로 어려워서 빼는 것이 아니라, 유료 고객 10곳을 확인하기 전에는 필요 없기 때문에 뺀다."));
body.push(TBL(["12주 안에 만든다","나중으로 미룬다"],[
  ["문서·URL 업로드와 자동 색인","카카오톡 채널·인스타 DM 연동"],
  ["웹 위젯 1종 (스크립트 한 줄 설치)","음성 상담(AICC) 연동"],
  ["답변 근거 인용 표시","파트너 분양 포털"],
  ["“모름 → 상담 연결” 폴백","SSO·권한 관리·다국어"],
  ["대화 로그 조회 화면","주문 변경·예약 같은 액션 에이전트"],
  ["카드 결제·구독 청구","모바일 앱, 온프레미스 설치"],
], [4513,4513]));
body.push(SP(160));

// 4
body.push(H("4","최소 기술 구성"));
body.push(TBL(["구성","선택","월 비용","이유"],[
  ["프론트·호스팅","Firebase Hosting","0원","무료 SSL·CDN 포함. 정적 페이지는 서버 비용이 발생하지 않는다"],
  ["백엔드 API","Cloud Run (서울)","0~2만 원","요청이 없으면 인스턴스 0. 유휴 비용이 없다"],
  ["문서 저장·검색","BigQuery + 임베딩","1~2만 원","쿼리 단위 과금. 초기 데이터량에서는 사실상 무료 구간"],
  ["생성 모델","경량 모델 우선","3~5만 원","고성능 모델은 어려운 질문에만 라우팅한다"],
  ["세션·설정 저장","Firestore","0원","무료 한도 내"],
  ["결제","국내 PG 연동","0원","가입비 없음. 결제 수수료만 발생"],
  ["코드·배포","GitHub + Cloud Build","0원","무료 빌드 한도 내"],
  ["*합계","*—","*약 5만 원","*파일럿 10곳 · 월 3,000세션 기준"],
], [1500,1900,1100,4526]));
body.push(CALL("주의 — “무료”의 함정",
  "Always Free의 가상머신·스토리지는 미국 리전 전용이다. 서울 리전에 만들면 첫 달부터 과금된다. 또한 로그 보존기간을 기본값으로 두면 로깅 비용이 조용히 커진다. 보존 30일로 제한하고 예산 알림을 반드시 건다."));
body.push(SP(160));

// 5
body.push(H("5","비용"));
body.push(H2("12주 초기 투입 (현금)"));
body.push(TBL(["항목","금액","비고"],[
  ["도메인 (1년)","3만 원",".com 또는 .kr"],
  ["GCP 인프라 (3개월)","15만 원","무료 한도 활용, 월 5만 원"],
  ["LLM·임베딩 API (3개월)","30만 원","파일럿 10곳 기준"],
  ["약관·개인정보처리방침","20만 원","표준 템플릿 + 전문가 검토"],
  ["통신판매업 신고","4.5만 원","등록면허세, 연 1회"],
  ["상표 출원 (1개 류)","12만 원","선택 사항이나 초기 출원 권장"],
  ["디자인·스톡 이미지","10만 원","템플릿 구매"],
  ["결제(PG) 연동","0원","가입비 없음"],
  ["예비비","25.5만 원","약 21%"],
  ["*합계","*120만 원","*대표 인건비 제외"],
], [3000,1500,4526], {right:[1]}));

body.push(H2("런칭 후 월 손익 (유료 10곳 기준)"));
body.push(TBL(["항목","금액"],[
  ["매출 (10곳 × 99,000원)","990,000원"],
  ["클라우드·모델 원가","130,000원"],
  ["*총이익","*860,000원 (87%)"],
  ["원가 손익분기점","유료 2곳 (198,000원)"],
], [5500,3526], {right:[1]}));
body.push(P([t("고정비가 사실상 없으므로 유료 2곳이면 서비스는 스스로 굴러간다. 이 구조 덕분에 ",{}),
  t("실패해도 잃는 금액이 120만 원을 넘지 않는다",{bold:true}),
  t(". 다만 대표의 12주는 회수되지 않으므로, 시간을 비용으로 계산해 중단 기준을 지켜야 한다.",{})]));
body.push(CALL("비용을 더 줄이는 방법",
  "AI 바우처·소상공인 AI 지원사업의 공급기업으로 등록하면 고객의 실부담이 낮아져 영업이 쉬워지고, 초기 레퍼런스를 정부 과제로 확보할 수 있다. 신청 자체는 무료이므로 1주차 과업에 포함한다."));
body.push(SP(160));

// 6
body.push(H("6","요금제 — 하나만 둔다"));
body.push(TBL(["구분","내용"],[
  ["*무료 체험","14일, 카드 등록 없이 시작. 문서 100페이지·200세션 한도"],
  ["*정식 플랜","월 99,000원 (VAT 별도) — 문서 500페이지, 월 1,000세션, 웹 위젯 1채널"],
  ["*초과 사용","세션당 80원"],
  ["*개통 지원","초기 20곳 무료. 조건은 도입 후기와 사례 공개 동의"],
  ["*연납","2개월 할인 (연 990,000원)"],
], [1900,7126], {zebra:true}));
body.push(P("플랜을 셋으로 쪼개는 것은 유료 고객 30곳을 넘긴 뒤에 한다. 그 전에는 어떤 기능에 돈을 더 낼지 알 수 없고, 선택지가 늘면 상담 시간만 길어진다."));
body.push(SP(160));

// 7
body.push(H("7","사용자 유입 계획"));
body.push(P("광고를 쓰지 않으므로 유입은 전적으로 보유 자산과 직접 접촉에서 나온다. 아래 순서대로 착수한다."));
body.push(TBL(["#","채널","방법","3개월 목표"],[
  ["1","유튜브 (보유)","‘챗봇 직접 만들기’ 실전 시리즈 주 1편. 영상 설명란 첫 줄에 무료 체험 링크","영상 12편 · 신청 20건"],
  ["2","블로그 (보유)","기존 글 하단에 체험 배너. 신규 글은 롱테일 검색어 공략","신규 24편 · 신청 15건"],
  ["3","자사몰 (보유)","자사몰에 챗봇을 먼저 붙여 1호 사례로 공개. ‘우리가 직접 쓴다’는 증명","사례 콘텐츠 3건"],
  ["4","커뮤니티","쇼핑몰·소상공인 카페와 오픈채팅에서 무료 진단 제공 (홍보 아님, 도움 먼저)","신청 10건"],
  ["5","직접 접촉","블로그 독자·구독자 중 사업자 50곳에 개별 메일 발송","신청 5건"],
  ["6","정부 바우처","공급기업 등록 후 수요기업 매칭","리드 확보"],
], [500,1500,4526,2500]));

body.push(H2("콘텐츠 운영 규칙"));
body.push(BUL([t("사이트의 챗봇은 광고가 아니라 데모다. ",{}),t("블로그 전편과 영상 자막을 학습시켜",{bold:true}),t(" 방문자가 직접 질문해 성능을 확인하게 한다.",{})]));
body.push(BUL([t("챗봇이 답하지 못한 질문 목록이 다음 달 콘텐츠 주제다. ",{}),t("실제 수요가 확인된 키워드",{bold:true}),t("이므로 검색어 도구보다 정확하다.",{})]));
body.push(BUL("블로그 글을 사이트에 통째로 복사하지 않는다. 중복 콘텐츠로 양쪽 검색 순위가 함께 떨어진다. 요약과 원문 링크만 둔다."));
body.push(BUL([t("모든 링크에 UTM을 붙인다. 규칙은 ",{}),
  t("utm_source=youtube · utm_medium=video_desc · utm_campaign=202610_launch · utm_content=영상ID",{bold:true}),
  t(" 형식으로 고정한다. 이 규칙이 없으면 어느 영상이 고객을 데려왔는지 끝내 알 수 없다.",{})]));
body.push(SP(160));

// 8
body.push(H("8","12주 실행 일정"));
body.push(TBL(["주차","과업","완료 판정"],[
  ["1–2주","랜딩페이지 + 무료 체험 신청 폼 공개. 도메인·법적 표기·결제사 가입. 정부 바우처 공급기업 등록. 자사몰에 챗봇 수동 구축","신청 폼 가동 · 신청 5건"],
  ["3–5주","MVP 개발 — 문서 업로드, 자동 색인, 웹 위젯, 근거 인용, 상담 연결 폴백","외부 사이트에 위젯 설치 성공"],
  ["6–7주","파일럿 5곳 무료 운영. 골든셋 100문항으로 정확도 측정 후 개선","정답률 85% 이상"],
  ["8주","결제 연동 후 유료 전환 시작. 파일럿 고객에게 첫 청구","1차 판정 (9항)"],
  ["9–10주","콘텐츠 엔진 가동 — 주 1영상 + 주 2글. 사례 콘텐츠 3건 제작","누적 신청 30건"],
  ["11–12주","커뮤니티·직접 접촉 집중. 이탈 원인 인터뷰","유료 10곳 · 2차 판정"],
], [1080,4946,3000]));
body.push(SP(160));

// 9
body.push(H("9","성공 · 중단 기준"));
body.push(P("두 지점에서 판정한다. 기준 미달 시 “조금만 더”가 아니라 정해진 행동을 실행한다."));
body.push(TBL(["시점","계속 조건","미달 시 행동"],[
  ["*8주차","무료 체험 신청 누적 20건 이상","제품이 아니라 메시지·타깃 문제다. 업종을 바꾸거나 랜딩 문구를 전면 교체한다"],
  ["*8주차","체험 고객의 자동 완결률 50% 이상","영업을 멈추고 품질 개선에만 집중한다. 이 상태로 파는 것은 평판을 태우는 일이다"],
  ["*12주차","유료 고객 3곳 이상","가격이 아니라 가치 문제다. 업종을 좁히거나 개통 지원 방식을 바꾼다"],
  ["*12주차","체험 → 유료 전환율 15% 이상","온보딩 과정을 재설계한다. 대개 고객의 문서 정리를 도와주지 않아서 생긴다"],
], [900,2700,5426]));
body.push(CALL("판정의 원칙",
  "네 기준 중 둘 이상 미달이면 사업 방향을 바꾼다. 하나만 미달이면 그 하나만 고친다. 전부 고치려 들면 원인을 분리할 수 없다."));
body.push(SP(160));

// 10
body.push(H("10","리스크"));
body.push(TBL(["리스크","대응"],[
  ["*챗봇이 틀린 답을 한다","사이트 챗봇은 곧 제품 시연이다. 근거를 찾지 못하면 답하지 않고 상담으로 넘기도록 기본값을 설정한다. 데모에서의 오답 한 건이 계약을 날린다"],
  ["*블로그 플랫폼 종속","티스토리 Open API는 이미 종료됐다. RSS로 전체 글을 자체 저장소에 백업해 두고, 콘텐츠 자산을 플랫폼 밖에 확보한다"],
  ["*클라우드 비용 폭주","예산 알림, 결제 한도, Cloud Run 최대 인스턴스 상한을 프로젝트 생성 즉시 설정한다"],
  ["*대표 시간 소진","개발과 영업을 같은 주에 병행하지 않는다. 3–7주는 개발, 9–12주는 영업으로 블록을 나눈다"],
], [2000,7026]));
body.push(SP(160));

// 11
body.push(H("11","확정이 필요한 항목"));
body.push(BUL("타깃 업종 — IT·네트워크(블로그 강점) 또는 쇼핑몰(자사몰 강점) 중 하나. 1주차에 결정해야 랜딩 문구가 나온다."));
body.push(BUL("유튜브 구독자·월 조회수, 블로그 누적 글 수·월 방문자 — 유입 목표를 가설이 아닌 실제 기저값으로 교체한다."));
body.push(BUL("티스토리 RSS가 전문 발행인지 요약 발행인지 — 챗봇 학습 데이터 확보 방법이 달라진다."));
body.push(BUL("도메인 보유 여부와 자사몰(카페24)과의 통합 방식."));
body.push(BUL("사업자등록·통신판매업 신고 상태."));
body.push(SP(200));

body.push(new Paragraph({
  children:[t("본 계획은 최소 자본으로 시장 반응을 확인하기 위한 12주 실행안이며, 금액은 공개 단가에 기반한 추정치다. 실제 집행 전 클라우드 요금 계산기와 세무·법무 확인이 필요하다.",{size:16,color:MUTED})],
  spacing:{before:240},
  border:{top:{style:BorderStyle.SINGLE,size:6,color:"D6D3C8",space:8}}}));
body.push(new Paragraph({children:[t("BSM · AI 챗봇 임대 서비스 최소비용 런칭 계획 v1.0 · 2026.09.07",{size:16,color:MUTED})]}));

const spaced=[];
body.forEach(el=>{spaced.push(el); if(el instanceof Table) spaced.push(SP(70));});

const doc=new Document({
  creator:"BSM", title:"AI 챗봇 임대 서비스 최소비용 런칭 계획",
  styles:{default:{document:{run:{font:KR,size:20,color:INK}}}},
  sections:[{properties:{page:{margin:{top:1440,right:1440,bottom:1440,left:1440}}},children:spaced}]});

Packer.toBuffer(doc).then(b=>{
  require("fs").writeFileSync("/tmp/claude-0/-home-user-chatbot/7a62990a-0f4b-57ec-af6f-77c2ddc99b78/scratchpad/BSM_AI챗봇_임대사업_런칭계획.docx",b);
  console.log("WROTE", b.length, "bytes");});
