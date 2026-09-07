const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // 13.333 x 7.5
pres.author = "BSM";
pres.company = "BSM";
pres.title = "BSM 챗봇 ISP 투자 유치 계획서";

/* ── 팔레트 ─────────────────────────────── */
const INK="16181B", INK2="3B4044", MUTED="6B6E72", LINE="D9D8D4";
const CARD="F2F2F0", WHITE="FFFFFF";
const ACC="8C2F39", ACC_LT="EFE0E1", ACC_DK="D9848D";
const SIG="1E6A5B", SIG_LT="DEE9E5";
const GOLD="A8823C";
const KR="Malgun Gothic", NUM="Cambria";
const M=0.7, CW=11.93;

/* ── 헬퍼 ───────────────────────────────── */
function footer(s, n){
  s.addText("BSM · 하이브리드 RAG 챗봇 ISP · 투자 유치 계획서",
    {x:M,y:6.94,w:7,h:0.26,fontSize:8.5,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
  s.addText(String(n).padStart(2,"0"),
    {x:12.0,y:6.94,w:0.63,h:0.26,fontSize:9,color:MUTED,fontFace:NUM,align:"right",isTextBox:true,margin:0});
}
function hdr(s, kicker, title, sub){
  s.addShape(pres.ShapeType.rect,{x:M,y:0.47,w:0.1,h:0.1,fill:{color:ACC},line:{color:ACC}});
  s.addText(kicker,{x:M+0.21,y:0.37,w:9,h:0.28,fontSize:10.5,bold:true,color:ACC,
    charSpacing:1.6,fontFace:KR,isTextBox:true,margin:0});
  s.addText(title,{x:M,y:0.70,w:CW,h:0.60,fontSize:31,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:M,y:1.32,w:11.2,h:0.34,fontSize:12.5,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
}
function card(s,x,y,w,h,fill){
  s.addShape(pres.ShapeType.rect,{x,y,w,h,fill:{color:fill||CARD},line:{color:fill===WHITE?LINE:(fill||CARD)}});
}
const hasKR=t=>/[\uAC00-\uD7A3]/.test(String(t));
const vf=t=>hasKR(t)?KR:NUM;
function tile(s,x,y,w,h,k,v,sub,vc,fill,vsize){
  card(s,x,y,w,h,fill||CARD);
  s.addText(k,{x:x+0.2,y:y+0.13,w:w-0.4,h:0.24,fontSize:9.5,bold:true,color:MUTED,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(v,{x:x+0.2,y:y+0.37,w:w-0.4,h:0.44,fontSize:vsize||25,bold:true,color:vc||INK,fontFace:vf(v),isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:x+0.2,y:y+0.83,w:w-0.4,h:Math.max(h-0.93,0.24),fontSize:10,color:MUTED,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
}

/* ══ 01 표지 ═══════════════════════════════ */
{
const s=pres.addSlide(); s.background={color:INK};
s.addShape(pres.ShapeType.rect,{x:M,y:1.05,w:0.13,h:0.13,fill:{color:ACC_DK},line:{color:ACC_DK}});
s.addText("투자 유치 계획서   ·   PRE-SERIES A   ·   2026.09",
  {x:M+0.26,y:0.94,w:9,h:0.3,fontSize:11,bold:true,color:ACC_DK,charSpacing:1.8,fontFace:KR,isTextBox:true,margin:0});
s.addText("챗봇을 회선처럼,\n앱을 분양처럼",
  {x:M,y:1.55,w:9.6,h:1.95,fontSize:52,bold:true,color:WHITE,lineSpacing:60,fontFace:KR,isTextBox:true,margin:0});
s.addText("BSM은 GCP 위에서 동작하는 하이브리드 RAG 챗봇 엔진을 멀티테넌트 인프라로 운영하고,\n업종·지역 단위 파트너에게 챗봇 앱을 분양하여 유통하는 B2B2B AI 서비스 기업입니다.",
  {x:M,y:3.68,w:10.4,h:0.8,fontSize:14.5,color:"C9C7C2",lineSpacing:24,fontFace:KR,isTextBox:true,margin:0});
const f=[["조달 목표","30억 원","1차 18억 / 2차 12억"],["기업가치","Post 150억","Pre-money 120억"],
         ["5년차 매출","260억 원","영업이익 62억 (24%)"],["BEP","3차년도","2029년 · 매출 78억"],
         ["LTV / CAC","10.5배","회수기간 3.8개월"]];
s.addShape(pres.ShapeType.line,{x:M,y:4.86,w:CW,h:0,line:{color:"3A3D41",width:1}});
f.forEach((c,i)=>{
  const x=M+i*(CW/5);
  if(i>0) s.addShape(pres.ShapeType.line,{x:x-0.12,y:5.02,w:0,h:1.08,line:{color:"3A3D41",width:1}});
  s.addText(c[0],{x,y:5.06,w:2.2,h:0.24,fontSize:9.5,bold:true,color:"8E8B86",charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[1],{x,y:5.33,w:2.3,h:0.42,fontSize:21,bold:true,color:WHITE,fontFace:vf(c[1]),isTextBox:true,margin:0});
  s.addText(c[2],{x,y:5.79,w:2.3,h:0.3,fontSize:9.5,color:"8E8B86",fontFace:KR,isTextBox:true,margin:0});
});
s.addText("BSM  ·  netk.tistory.com  ·  bsmshop.cafe24.com",
  {x:M,y:6.68,w:8,h:0.3,fontSize:10,color:"6E6B66",fontFace:KR,isTextBox:true,margin:0});
s.addNotes("표지. 핵심 메시지: 챗봇을 인프라(ISP)로 공급하고 앱을 파트너에게 분양하는 B2B2B 구조. 조달 30억, Post 150억.");
}

/* ══ 02 왜 지금인가 ════════════════════════ */
{
const s=pres.addSlide(); const n=2; footer(s,n);
hdr(s,"MARKET TIMING","왜 지금인가","수요는 폭발했고 공급은 한 구간에서 비어 있습니다. 그 구간의 이름은 “월 10만 원, 2주 개통”입니다.");
const items=[
 ["수요 폭발","2026년 국내 기업용 AI 시장 6조 4,190억 원(전년비 +25%). 국내 AI 시장은 14조 원을 돌파해 2032년 41조 원으로 3배 성장 전망."],
 ["공급 공백","통신사 AICC는 수억 원대 구축형에, 글로벌 SaaS는 영어권 엔터프라이즈에 집중. 771만 중소기업·소상공인 구간은 사실상 무주공산."],
 ["정책 순풍","AX 원스톱 바우처 294억 원, AI 바우처 수요기업당 최대 2억 원. 공급기업 등록 사업자에게 직접 매출로 연결."],
 ["원가 구조 반전","경량 모델·서버리스 벡터 검색으로 테넌트당 월 클라우드 원가 2~4만 원. 월 10만 원대 요금제에서도 총이익률 74~80%."]];
items.forEach((it,i)=>{
  const y=1.86+i*1.12;
  card(s,M,y,7.55,1.0,i%2===0?CARD:WHITE);
  s.addText(String(i+1),{x:M+0.22,y:y+0.2,w:0.4,h:0.4,fontSize:19,bold:true,color:ACC,fontFace:NUM,isTextBox:true,margin:0});
  s.addText(it[0],{x:M+0.72,y:y+0.13,w:2.4,h:0.28,fontSize:14,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(it[1],{x:M+0.72,y:y+0.42,w:6.6,h:0.42,fontSize:10.5,color:INK2,lineSpacing:14,fontFace:KR,isTextBox:true,margin:0});
});
const st=[["국내 AI 시장 (2026)","14조 원","2032년 41조 원"],["기업용 AI 예산 (2026)","6.42조 원","전년 대비 +25%"],
          ["생성형 AI 활용 기업","85%","2026년까지 전망"]];
st.forEach((t,i)=>tile(s,8.7,1.86+i*1.48,3.93,1.36,t[0],t[1],t[2],i===0?ACC:INK,WHITE));
s.addNotes("수요·공급·정책·원가 네 축으로 타이밍을 설명. 오른쪽 스탯 3개는 심사역이 기억할 숫자.");
}

/* ══ 03 포지셔닝 ═══════════════════════════ */
{
const s=pres.addSlide(); const n=3; footer(s,n);
hdr(s,"POSITIONING","시장은 비어 있는 사분면을 가지고 있습니다","정확도와 접근성을 동시에 만족하는 공급자가 국내에 없습니다.");
const X0=1.75,X1=12.35,Y0=2.35,Y1=6.25;
s.addShape(pres.ShapeType.rect,{x:X0,y:Y0,w:X1-X0,h:Y1-Y0,fill:{color:"FAFAF9"},line:{color:LINE}});
s.addShape(pres.ShapeType.line,{x:X0,y:(Y0+Y1)/2,w:X1-X0,h:0,line:{color:LINE,width:1,dashType:"dash"}});
s.addShape(pres.ShapeType.line,{x:(X0+X1)/2,y:Y0,w:0,h:Y1-Y0,line:{color:LINE,width:1,dashType:"dash"}});
s.addText("데이터 정확도 · 거버넌스  ↑",{x:0.7,y:2.35,w:1.0,h:1.4,fontSize:9.5,bold:true,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
s.addText("가격 접근성 · 개통 속도  →",{x:9.6,y:6.32,w:2.75,h:0.3,fontSize:9.5,bold:true,color:MUTED,align:"right",fontFace:KR,isTextBox:true,margin:0});
const pts=[["통신사 AICC",3.22,3.10,MUTED],["AI 전문기업 (SI)",4.90,3.62,MUTED],["글로벌 상담 SaaS",6.30,4.20,MUTED],
           ["플랫폼 범용 봇",9.16,5.30,MUTED],["국내 상담 SaaS",10.90,4.60,MUTED],["DIY 커스텀 GPT",11.35,5.62,MUTED]];
pts.forEach(p=>{
  s.addShape(pres.ShapeType.ellipse,{x:p[1]-0.15,y:p[2]-0.15,w:0.30,h:0.30,fill:{color:"C9C7C2"},line:{color:"ADAAA5"}});
  s.addText(p[0],{x:p[1]-1.05,y:p[2]+0.19,w:2.1,h:0.28,fontSize:10,color:INK2,align:"center",fontFace:KR,isTextBox:true,margin:0});
});
s.addShape(pres.ShapeType.ellipse,{x:10.20,y:2.84,w:0.52,h:0.52,fill:{color:ACC},line:{color:ACC}});
s.addText("BSM",{x:10.20,y:2.96,w:0.52,h:0.28,fontSize:11,bold:true,color:WHITE,align:"center",fontFace:KR,isTextBox:true,margin:0});
s.addText("정확도는 지키고 가격은 내린다",{x:9.06,y:3.42,w:2.8,h:0.28,fontSize:10.5,bold:true,color:ACC,align:"center",fontFace:KR,isTextBox:true,margin:0});
card(s,7.55,2.5,2.5,0.62,ACC_LT);
s.addText("공급 공백 구간\n월 10만 원 · 2주 개통",{x:7.65,y:2.58,w:2.3,h:0.46,fontSize:10,bold:true,color:ACC,align:"center",lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("빈 사분면(우상단)이 BSM의 진입 지점. 정확도를 포기하지 않으면서 가격·개통 속도를 확보하는 것이 제품 요구사항.");
}

/* ══ 04 회사 개요 ══════════════════════════ */
{
const s=pres.addSlide(); const n=4; footer(s,n);
hdr(s,"COMPANY","이미 콘텐츠·커머스·CS를 직접 운영해 온 조직","챗봇 회사에 필요한 실데이터와 유통 자산을 이미 보유하고 있습니다.");
const a=[["기술 블로그","netk.tistory.com","네트워크·IT 실무 콘텐츠 축적","도메인 지식 코퍼스 + 오가닉 유입 채널"],
         ["유튜브 채널","BSM 채널","영상 기반 교육·데모 운영","파트너 모집 및 온보딩 교육 인프라"],
         ["자사몰","bsmshop.cafe24.com","실제 상거래·CS 운영 경험","1호 레퍼런스 테넌트 · 커머스 도메인 팩 원천"]];
a.forEach((c,i)=>{
  const x=M+i*4.05;
  card(s,x,1.84,3.8,1.95,WHITE);
  s.addShape(pres.ShapeType.rect,{x:x+0.22,y:2.06,w:0.09,h:0.09,fill:{color:ACC},line:{color:ACC}});
  s.addText(c[0],{x:x+0.42,y:1.97,w:3.2,h:0.28,fontSize:13.5,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[1],{x:x+0.22,y:2.32,w:3.4,h:0.26,fontSize:10,color:ACC,fontFace:NUM,isTextBox:true,margin:0});
  s.addText(c[2],{x:x+0.22,y:2.66,w:3.4,h:0.3,fontSize:10.5,color:INK2,fontFace:KR,isTextBox:true,margin:0});
  s.addShape(pres.ShapeType.line,{x:x+0.22,y:3.02,w:3.36,h:0,line:{color:LINE,width:1}});
  s.addText(c[3],{x:x+0.22,y:3.10,w:3.4,h:0.55,fontSize:10,color:MUTED,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
});
s.addText("리뉴얼 후 3단 구조",{x:M,y:4.02,w:6,h:0.3,fontSize:14,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
const st=[["BSM 본사","엔진·인프라·모델 운영, 파트너 교육, 품질 보증. SLA 책임 주체.",ACC],
          ["분양 파트너","업종/지역 구좌를 분양받아 최종 고객 모집 · 온보딩 · 1차 CS.",INK],
          ["테넌트 (최종 고객)","자사 데이터로 학습된 챗봇 앱을 월 구독으로 사용.",INK]];
st.forEach((c,i)=>{
  const x=M+i*4.05;
  card(s,x,4.42,3.8,1.12,i===0?ACC_LT:CARD);
  s.addText(c[0],{x:x+0.22,y:4.58,w:3.4,h:0.3,fontSize:12.5,bold:true,color:c[2],fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[1],{x:x+0.22,y:4.90,w:3.4,h:0.52,fontSize:10,color:INK2,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
  if(i<2) s.addText("▶",{x:x+3.83,y:4.86,w:0.2,h:0.24,fontSize:10,color:MUTED,align:"center",isTextBox:true,margin:0});
});
card(s,M,5.72,CW,0.78,CARD);
s.addText([{text:"두 가지 희소 자산  ",options:{bold:true,color:INK}},
  {text:"① 실제 CS 로그와 상품 데이터라는 RAG 평가용 실데이터   ② 온라인 판매 운영 노하우라는 파트너 이전 가능 교육 자산",options:{color:INK2}}],
  {x:M+0.24,y:5.98,w:CW-0.5,h:0.3,fontSize:11.5,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("BSM의 기존 3개 채널이 왜 챗봇 사업의 자산인지 설명. 실측 수치(방문자·구독자·매출)는 IR 제출 전 반영 필요.");
}

/* ══ 05 시장 규모 ══════════════════════════ */
{
const s=pres.addSlide(); const n=5; footer(s,n);
hdr(s,"MARKET SIZE","국내 AI 챗봇 시장 규모","AICC 통계는 콜센터 대체 시장만 집계합니다. 웹·카카오톡 상담봇과 사내 지식봇을 합산한 실질 시장은 그보다 큽니다.");
s.addChart(pres.ChartType.line,
  [{name:"국내 AICC 시장",labels:["2020","2022","2024","2026","2028","2030"],values:[560,857,1311,2006,3069,4697]}],
  {x:M,y:1.92,w:7.5,h:4.15,
   showTitle:true,title:"국내 AICC 시장 규모 (억 원) · CAGR 23.7%",titleFontSize:12,titleColor:INK,titleFontFace:KR,
   chartColors:[ACC],lineDataSymbol:"circle",lineDataSymbolSize:7,lineSize:3,
   showValue:true,dataLabelPosition:"t",dataLabelFontSize:10,dataLabelColor:INK2,dataLabelFontFace:NUM,
   catAxisLabelColor:MUTED,catAxisLabelFontSize:10,catAxisLabelFontFace:NUM,
   valAxisLabelColor:MUTED,valAxisLabelFontSize:10,valAxisLabelFontFace:NUM,valAxisMaxVal:5600,
   valGridLine:{color:"E6E5E2",size:1},catGridLine:{style:"none"},showLegend:false,
   plotArea:{fill:{color:WHITE}}});
s.addText("출처: Allied Market Research (2020 · 2030 실측), 중간 연도는 CAGR 23.7% 적용 보간",
  {x:M,y:6.14,w:7.5,h:0.26,fontSize:8.5,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
const st=[["국내 AI 시장 전체","14조 원","2026년 · 2032년 41조 원 전망",ACC],
          ["국내 생성형 AI","1.14조 원","2025년 · 2032년 5.26조 원",INK],
          ["기업용 AI (ICT 예산)","6.42조 원","2026년 · 전년 대비 +25%",INK],
          ["글로벌 챗봇 시장","$11.45B","2026년 · CAGR 약 23%",INK]];
st.forEach((t,i)=>tile(s,8.55,1.92+i*1.22,4.08,1.12,t[0],t[1],t[2],t[3],WHITE,22));
s.addNotes("AICC는 콜센터 대체 시장만 잡은 보수적 지표. 전체 AI/생성형 AI 시장 성장률이 실제 확장 여력을 보여준다.");
}

/* ══ 06 TAM/SAM/SOM ════════════════════════ */
{
const s=pres.addSlide(); const n=6; footer(s,n);
hdr(s,"TAM / SAM / SOM","도달 가능한 시장과 목표 점유율","771만 사업체 모수에서 bottom-up으로 산출했습니다.");
const f=[["TAM","국내 대화형 AI · AICC · 상담 SaaS 총합 (2030)","1조 2,000억",CARD,INK,0],
         ["SAM","중소·중견 대상 RAG 챗봇 구독 시장","3,000억","E4E3DF",INK,0.55],
         ["SOM","BSM 5차년도 목표 · SAM 침투율 8.7%","260억",ACC_LT,ACC,1.1]];
f.forEach((r,i)=>{
  const y=1.92+i*1.06, x=M+r[5], w=7.7-r[5];
  card(s,x,y,w,0.9,r[3]);
  s.addText(r[0],{x:x+0.22,y:y+0.14,w:1.2,h:0.26,fontSize:10.5,bold:true,color:r[4],charSpacing:1.4,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[1],{x:x+0.22,y:y+0.44,w:w-2.6,h:0.3,fontSize:11,color:INK2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[2],{x:x+w-2.35,y:y+0.26,w:2.13,h:0.42,fontSize:22,bold:true,color:r[4],align:"right",fontFace:NUM,isTextBox:true,margin:0});
});
card(s,M,5.28,7.7,1.22,WHITE);
s.addText("SAM 산출 근거 (Bottom-up)",{x:M+0.24,y:5.42,w:5,h:0.26,fontSize:11.5,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
s.addText("중소기업·소상공인 771만 4천 개(전체 기업의 99.9%) → 온라인 채널 운영·상시 문의 발생 약 60만 개(7.8%)\n→ 3년 내 유료 전환 5% = 3만 테넌트 × 연 ARPU 100만 원 = 3,000억 원",
  {x:M+0.24,y:5.72,w:7.25,h:0.6,fontSize:10.5,color:INK2,lineSpacing:15,fontFace:KR,isTextBox:true,margin:0});
tile(s,8.7,1.92,3.93,1.3,"5년차 목표 매출","260억 원","SAM 침투율 8.7%",ACC,WHITE);
tile(s,8.7,3.34,3.93,1.3,"필요 파트너 구좌","220개좌","구좌당 테넌트 39개",INK,WHITE);
tile(s,8.7,4.76,3.93,1.3,"파트너 1곳 부담","월 3~4건","신규 계약 기준",INK,WHITE);
s.addText("SOM은 영업 난이도로 환산했을 때 파트너 1곳이 월 3~4건을 계약하면 도달하는 수준입니다.",
  {x:8.7,y:6.16,w:3.93,h:0.5,fontSize:9.5,color:MUTED,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("SOM을 매출이 아니라 '파트너 1곳이 월 몇 건 파는가'로 환산해 실현 가능성을 보여주는 것이 핵심.");
}

/* ══ 07 경쟁 구도 ══════════════════════════ */
{
const s=pres.addSlide(); const n=7; footer(s,n);
hdr(s,"COMPETITION","6개 진영, 그리고 아무도 없는 구간","경쟁의 축을 제품 성능이 아니라 유통 구조로 옮깁니다.");
const c=[["통신사 AICC","KT · SKT · LG유플러스","대형 콜센터 레퍼런스, 회선 번들","최소 계약 규모 큼 · 구축 3~6개월 · 소상공인 접근 불가"],
         ["AI 전문기업","솔트룩스 · 와이즈넛 · 스켈터랩스","한국어 NLP 기술력, 공공 레퍼런스","프로젝트형(SI) 매출 → 확장성 낮음 · 셀프서비스 부재"],
         ["플랫폼","네이버 클로바 · 카카오","채널 장악력, 자체 모델 보유","범용 제품 · 테넌트별 데이터 커스터마이징 한계"],
         ["국내 상담 SaaS","채널톡(ALF) · 해피톡","중소·이커머스 최적화, 낮은 진입장벽","상담 UI 중심 · 문서 기반 심층 RAG 대응 약함"],
         ["글로벌 SaaS","Intercom Fin · Zendesk AI","제품 완성도, 브랜드","한국어·국내 규제·세금계산서 대응 미흡 · 고가"],
         ["DIY","커스텀 GPT류","무료~저가, 즉시 사용","거버넌스·감사로그·SLA 부재 · 업무 시스템 연동 불가"]];
c.forEach((r,i)=>{
  const x=M+(i%3)*4.05, y=1.92+Math.floor(i/3)*2.06;
  card(s,x,y,3.8,1.9,WHITE);
  s.addText(r[0],{x:x+0.22,y:y+0.16,w:3.4,h:0.28,fontSize:13,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[1],{x:x+0.22,y:y+0.48,w:3.4,h:0.26,fontSize:9.5,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
  s.addText([{text:"강점  ",options:{bold:true,color:SIG}},{text:r[2],options:{color:INK2}}],
    {x:x+0.22,y:y+0.80,w:3.4,h:0.42,fontSize:9.5,lineSpacing:12,fontFace:KR,isTextBox:true,margin:0});
  s.addText([{text:"약점 = 기회  ",options:{bold:true,color:ACC}},{text:r[3],options:{color:INK2}}],
    {x:x+0.22,y:y+1.26,w:3.4,h:0.52,fontSize:9.5,lineSpacing:12,fontFace:KR,isTextBox:true,margin:0});
});
card(s,M,6.12,CW,0.62,INK);
s.addText("채널톡의 가격과 접근성  +  와이즈넛의 검색 정확도  +  통신사의 유통 구조",
  {x:M,y:6.26,w:CW,h:0.34,fontSize:15,bold:true,color:WHITE,align:"center",fontFace:KR,isTextBox:true,margin:0});
s.addNotes("동급 챗봇을 만드는 회사는 많지만 전국 파트너가 분양받아 파는 챗봇은 없다 — 이것이 경쟁 우위의 본질.");
}

/* ══ 08 정책 환경 ══════════════════════════ */
{
const s=pres.addSlide(); const n=8; footer(s,n);
hdr(s,"POLICY","규제는 비용이 아니라 해자입니다","정부 바우처는 초기 매출로, 규제 대응은 진입장벽으로 전환합니다.");
const p=[["AX 원스톱 바우처 (2026)","예산 294억 원 · 약 20개 과제\nAI + 클라우드 + 데이터 통합 지원","공급기업 등록 후 컨소시엄 참여\n→ 초기 레퍼런스 확보"],
         ["AI 바우처","수요기업당 최대 2억 원\n솔루션 도입 비용 지원","파트너 영업 시 고객 실부담 20%까지\n→ CAC 절감 및 계약 성사율 상승"],
         ["혁신 소상공인 AI 활용지원","소상공인 대상 AI 도입 지원","Starter 플랜(월 9.9만 원) 타깃과\n정확히 일치하는 수요 풀"]];
p.forEach((r,i)=>{
  const x=M+i*4.05;
  card(s,x,1.92,3.8,2.3,WHITE);
  s.addShape(pres.ShapeType.rect,{x:x+0.22,y:2.14,w:0.09,h:0.09,fill:{color:ACC},line:{color:ACC}});
  s.addText(r[0],{x:x+0.42,y:2.05,w:3.2,h:0.3,fontSize:12.5,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[1],{x:x+0.22,y:2.48,w:3.4,h:0.62,fontSize:10.5,color:INK2,lineSpacing:14,fontFace:KR,isTextBox:true,margin:0});
  s.addShape(pres.ShapeType.line,{x:x+0.22,y:3.18,w:3.36,h:0,line:{color:LINE,width:1}});
  s.addText("BSM 활용",{x:x+0.22,y:3.26,w:3.4,h:0.24,fontSize:9,bold:true,color:ACC,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[2],{x:x+0.22,y:3.52,w:3.4,h:0.6,fontSize:10,color:INK2,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
});
s.addText("규제 대응 = 제품 기본 기능",{x:M,y:4.46,w:6,h:0.3,fontSize:14,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
const r=[["AI 기본법","생성형 AI 표시 의무, 투명성·안전성 확보 의무","근거 인용 · AI 고지 배너 · 전 구간 감사로그를 기본 탑재"],
         ["개인정보보호법","상담 데이터 내 개인정보 처리 규율","국내 리전 고정 · PII 마스킹 · 테넌트별 IAM·CMEK · ISMS-P"]];
r.forEach((x2,i)=>{
  const y=4.86+i*0.82;
  card(s,M,y,CW,0.72,i%2===0?CARD:WHITE);
  s.addText(x2[0],{x:M+0.24,y:y+0.22,w:2.0,h:0.28,fontSize:12,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(x2[1],{x:M+2.3,y:y+0.24,w:4.3,h:0.28,fontSize:10.5,color:INK2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(x2[2],{x:M+6.8,y:y+0.24,w:4.8,h:0.28,fontSize:10.5,color:ACC,fontFace:KR,isTextBox:true,margin:0});
});
s.addNotes("감사로그·근거인용·국내 리전은 글로벌 SaaS와 DIY가 단기간에 맞추기 어려운 요건 — 공공·금융·의료 진입의 전제조건.");
}

/* ══ 09 아키텍처 ═══════════════════════════ */
{
const s=pres.addSlide(); const n=9; footer(s,n);
hdr(s,"ARCHITECTURE","하이브리드 RAG 파이프라인 (GCP)","순수 벡터 검색은 “환불 규정”과 “교환 규정”을 유사하다고 판단해 틀린 조항을 인용합니다.");
const LX=M, LW=1.30, BX=2.10, BW=10.53;
let y=1.82;
function row(label, h, draw){
  s.addText(label,{x:LX,y:y+0.13,w:LW,h:0.28,fontSize:9.5,bold:true,color:MUTED,align:"right",charSpacing:1,fontFace:KR,isTextBox:true,margin:0});
  draw(y,h); y+=h;
  if(y<6.2){ s.addShape(pres.ShapeType.downArrow,{x:7.30,y:y+0.005,w:0.12,h:0.12,fill:{color:"C4C2BE"},line:{color:"C4C2BE"}}); }
  y+=0.13;
}
function plain(txt,sub){return (yy,h)=>{
  card(s,BX,yy,BW,h,WHITE);
  s.addText(txt,{x:BX+0.22,y:yy+0.10,w:BW-0.44,h:0.26,fontSize:11.5,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  if(sub) s.addText(sub,{x:BX+0.22,y:yy+0.34,w:BW-0.44,h:0.24,fontSize:10,color:INK2,fontFace:KR,isTextBox:true,margin:0});
};}
row("수집",0.62,plain("웹 · PDF · 엑셀 · 상품DB · CS로그 · 유튜브 자막","Document AI 파싱 → 시맨틱 청킹 → 메타데이터 태깅"));
row("임베딩",0.62,plain("Vertex AI Embeddings","한국어 다국어 모델 · 테넌트별 네임스페이스 분리"));
row("저장 · 이원화",1.08,(yy,h)=>{
  const hw=(BW-0.2)/2;
  card(s,BX,yy,hw,h,ACC_LT);
  s.addText("HOT 티어",{x:BX+0.22,y:yy+0.12,w:hw-0.44,h:0.24,fontSize:9.5,bold:true,color:ACC,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText("Vertex AI Vector Search",{x:BX+0.22,y:yy+0.38,w:hw-0.44,h:0.28,fontSize:12,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText("저지연 ANN, p95 < 50ms · 실시간 상담 경로 전용\n전 테넌트 tenant_id 필터 공유 인덱스",{x:BX+0.22,y:yy+0.64,w:hw-0.44,h:0.40,fontSize:10,color:INK2,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
  const x2=BX+hw+0.2;
  card(s,x2,yy,hw,h,SIG_LT);
  s.addText("COLD 티어",{x:x2+0.22,y:yy+0.12,w:hw-0.44,h:0.24,fontSize:9.5,bold:true,color:SIG,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText("BigQuery VECTOR_SEARCH",{x:x2+0.22,y:yy+0.38,w:hw-0.44,h:0.28,fontSize:12,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText("원문·메타 정본(SSOT) · SEARCH INDEX 키워드(BM25)\n배치 재인덱싱 · 분석 및 리포팅",{x:x2+0.22,y:yy+0.64,w:hw-0.44,h:0.40,fontSize:10,color:INK2,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
});
row("검색 융합",0.62,plain("Dense(의미) ⊕ Sparse(키워드) → RRF 융합 → 메타 필터","품번 · 약품명 · 법령 조항처럼 정확 문자열이 정답인 질의의 실패 모드를 제거"));
row("재순위 · 생성",0.62,plain("Vertex AI Ranking API → Gemini (Flash 기본 / Pro 에스컬레이션)","근거 인용 강제 · 미근거 시 “모름 + 상담사 이관”이 기본값"));
row("서빙 · 운영",0.62,plain("Cloud Run + API Gateway + Cloud Armor + Firestore(세션)","골든셋 자동 회귀 평가 · 프롬프트 버저닝 · 토큰 상한 · 전 구간 감사로그"));
s.addNotes("이원화가 핵심. Hot은 지연, Cold는 원가와 정본. 하이브리드 검색은 한국어 실무 문서의 정확 매칭 실패를 제거한다.");
}

/* ══ 10 원가 경쟁력 ════════════════════════ */
{
const s=pres.addSlide(); const n=10; footer(s,n);
hdr(s,"UNIT COST","이원화가 곧 원가 경쟁력입니다","Vertex 인덱스는 상주 노드 시간당 과금입니다. 테넌트마다 전용 인덱스를 두면 원가가 매출을 넘어섭니다.");
card(s,M,1.92,5.85,2.55,CARD);
s.addText("일반적 구성",{x:M+0.26,y:2.10,w:3,h:0.28,fontSize:10.5,bold:true,color:MUTED,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
s.addText("테넌트별 전용 벡터 인덱스",{x:M+0.26,y:2.42,w:5.3,h:0.32,fontSize:16,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
s.addText("중간 규모 인덱스 3-replica 상주 시\n테넌트당 월 700~800달러 고정 발생",{x:M+0.26,y:2.84,w:5.3,h:0.5,fontSize:11,color:INK2,lineSpacing:15,fontFace:KR,isTextBox:true,margin:0});
s.addText("월 9.9만 원 요금제에서 원가가 매출의 9배",{x:M+0.26,y:3.48,w:5.3,h:0.3,fontSize:12,bold:true,color:ACC,fontFace:KR,isTextBox:true,margin:0});
s.addText("→ 소상공인 시장 진입 자체가 불가능",{x:M+0.26,y:3.84,w:5.3,h:0.3,fontSize:11,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
card(s,6.78,1.92,5.85,2.55,WHITE);
s.addShape(pres.ShapeType.rect,{x:7.04,y:2.14,w:0.09,h:0.09,fill:{color:ACC},line:{color:ACC}});
s.addText("BSM 구성",{x:7.24,y:2.05,w:3,h:0.28,fontSize:10.5,bold:true,color:ACC,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
s.addText("공유 Hot 인덱스 + 쿼리 과금형 Cold",{x:7.04,y:2.42,w:5.3,h:0.32,fontSize:16,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
s.addText("실시간 경로만 공유 인덱스로 처리하고 나머지는\nBigQuery로 이관 — 고정비를 수천 테넌트가 분담",{x:7.04,y:2.84,w:5.3,h:0.5,fontSize:11,color:INK2,lineSpacing:15,fontFace:KR,isTextBox:true,margin:0});
s.addText("테넌트당 월 클라우드 원가 1.2만 ~ 3.5만 원",{x:7.04,y:3.48,w:5.3,h:0.3,fontSize:12,bold:true,color:SIG,fontFace:KR,isTextBox:true,margin:0});
s.addText("→ 월 9.9만 원 요금제에서도 흑자",{x:7.04,y:3.84,w:5.3,h:0.3,fontSize:11,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
const t=[["Starter 원가","약 1.2만 원","월 · 요금 9.9만 원",SIG],["Pro 원가","약 3.5만 원","월 · 요금 29만 원",SIG],
         ["매출총이익률","74 → 80%","Y1 → Y5 개선",ACC],["매출원가율","26 → 20%","규모의 경제 반영",INK]];
t.forEach((x2,i)=>tile(s,M+i*3.06,4.72,2.81,1.42,x2[0],x2[1],x2[2],x2[3],WHITE));
s.addText("모델 라우팅(경량↔고성능), 응답 캐시, 요금제 내 세션 상한으로 LLM 단가 변동 위험을 흡수합니다.",
  {x:M,y:6.30,w:CW,h:0.3,fontSize:10,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("이 슬라이드가 투자 논리의 심장. 왜 남들이 못 하는 가격이 우리에게 가능한가에 대한 구조적 답.");
}

/* ══ 11 품질 SLA ═══════════════════════════ */
{
const s=pres.addSlide(); const n=11; footer(s,n);
hdr(s,"QUALITY","계약서에 쓸 수 있는 품질 지표","정확도를 마케팅 문구가 아니라 측정 가능한 SLA로 정의합니다.");
const q=[["근거 기반 정답률","≥ 90%","테넌트별 골든셋 200문항\n자동 회귀 평가",ACC],
         ["상담 자동 완결률","≥ 65%","상담사 이관 없이\n종료된 세션 비율",INK],
         ["응답 지연 p95","≤ 2.5초","첫 토큰 기준",INK],
         ["할루시네이션","≤ 2%","근거 미포함 답변\n자동 탐지 + 샘플 검수",INK],
         ["가용성","99.9%","월간 기준",INK]];
q.forEach((t,i)=>{
  const x=M+i*2.425;
  card(s,x,1.92,2.2,2.15,WHITE);
  s.addText(t[0],{x:x+0.2,y:2.10,w:1.8,h:0.44,fontSize:10.5,bold:true,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
  s.addText(t[1],{x:x+0.2,y:2.58,w:1.85,h:0.5,fontSize:25,bold:true,color:t[3],fontFace:vf(t[1]),isTextBox:true,margin:0});
  s.addText(t[2],{x:x+0.2,y:3.14,w:1.85,h:0.8,fontSize:9.5,color:INK2,lineSpacing:12,fontFace:KR,isTextBox:true,margin:0});
});
card(s,M,4.34,CW,1.05,ACC_LT);
s.addText("설계 원칙 — 오답보다 이관이 안전하다",{x:M+0.28,y:4.52,w:6,h:0.3,fontSize:14,bold:true,color:ACC,fontFace:KR,isTextBox:true,margin:0});
s.addText("근거를 확보하지 못한 질의에는 답을 만들지 않고 “모름 + 상담사 이관”을 반환합니다. 정확도 미달 리스크를 제품 기본 동작으로 흡수하는 구조입니다.",
  {x:M+0.28,y:4.86,w:11.3,h:0.32,fontSize:11,color:INK2,fontFace:KR,isTextBox:true,margin:0});
const g=[["골든셋 회귀 평가","테넌트별 200문항을 배포 파이프라인에 CI로 연결 — 정확도 하락 시 배포 차단"],
         ["프롬프트 버저닝","프롬프트·인덱스·모델 버전을 함께 기록해 품질 변화의 원인을 추적"],
         ["전 구간 감사로그","질의 · 검색 근거 · 생성 답변을 테넌트별로 보존 — 규제 대응 및 분쟁 시 증빙"]];
g.forEach((r,i)=>{
  const y=5.58+i*0.42;
  s.addShape(pres.ShapeType.rect,{x:M+0.02,y:y+0.11,w:0.08,h:0.08,fill:{color:ACC},line:{color:ACC}});
  s.addText([{text:r[0]+"  ",options:{bold:true,color:INK}},{text:r[1],options:{color:INK2}}],
    {x:M+0.24,y:y,w:11.6,h:0.3,fontSize:10.5,fontFace:KR,isTextBox:true,margin:0});
});
s.addNotes("정확도를 SLA로 계약화할 수 있다는 점이 DIY·범용 챗봇과의 결정적 차이.");
}

/* ══ 12 요금 체계 ══════════════════════════ */
{
const s=pres.addSlide(); const n=12; footer(s,n);
hdr(s,"PRICING","ISP형 요금 체계","가입 → 개통 → 월 이용료 → 사용량 초과 과금. 고객은 회선을 개통하듯 챗봇을 개통합니다.");
const p=[["Starter","99,000","문서 500p\n월 1,000세션\n채널 1개","세션당 80원","소상공인 · 쇼핑몰",false],
         ["Pro","290,000","문서 3,000p\n월 5,000세션\n채널 3개 · API","세션당 55원","중소기업 · 학원 · 병의원",true],
         ["Business","690,000","문서 20,000p\n월 20,000세션\n무제한 채널 · SSO","세션당 35원","중견기업 · 프랜차이즈",false],
         ["Enterprise","별도 견적","전용 프로젝트 / VPC\n온프렘 연동\n커스텀 SLA","사용량 협의","공공 · 금융 · 대기업",false]];
p.forEach((c,i)=>{
  const x=M+i*3.05, hl=c[5];
  card(s,x,1.92,2.75,3.5,hl?ACC_LT:WHITE);
  s.addText(c[0],{x:x+0.22,y:2.10,w:2.3,h:0.3,fontSize:14,bold:true,color:hl?ACC:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[1]==="별도 견적"?c[1]:c[1],{x:x+0.22,y:2.46,w:2.35,h:0.42,fontSize:c[1]==="별도 견적"?17:21,bold:true,color:INK,fontFace:NUM,isTextBox:true,margin:0});
  s.addText(c[1]==="별도 견적"?"연 3,000만 ~ 1억":"원 / 월 (VAT 별도)",{x:x+0.22,y:2.92,w:2.35,h:0.26,fontSize:9.5,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
  s.addShape(pres.ShapeType.line,{x:x+0.22,y:3.26,w:2.31,h:0,line:{color:hl?"D8BFC1":LINE,width:1}});
  s.addText(c[2],{x:x+0.22,y:3.36,w:2.35,h:0.9,fontSize:10.5,color:INK2,lineSpacing:15,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[0]==="Enterprise"?c[3]:"초과 "+c[3],{x:x+0.22,y:4.36,w:2.35,h:0.26,fontSize:10,bold:true,color:hl?ACC:SIG,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[4],{x:x+0.22,y:4.76,w:2.35,h:0.5,fontSize:9.5,color:MUTED,lineSpacing:12,fontFace:KR,isTextBox:true,margin:0});
});
card(s,M,5.62,CW,0.86,CARD);
s.addText([{text:"개통비 30만 ~ 300만 원 (1회)   ",options:{bold:true,color:INK}},
  {text:"데이터 정제 · 초기 학습 · 검수 — 전 플랜 공통.  파트너가 수행하고 개통비의 70%를 가져갑니다.",options:{color:INK2}}],
  {x:M+0.26,y:5.92,w:11.4,h:0.3,fontSize:11.5,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("Pro가 주력 플랜. 개통비는 파트너 수익의 큰 축이며 온보딩 품질을 담보하는 장치이기도 하다.");
}

/* ══ 13 분양 구조 ══════════════════════════ */
{
const s=pres.addSlide(); const n=13; footer(s,n);
hdr(s,"DISTRIBUTION","분양 — CAC를 파트너가 흡수하는 구조","소상공인 시장은 온라인 획득 CAC가 높습니다. 지역 파트너의 대면 영업이 압도적으로 효율적입니다.");
const f=[["BSM 본사","엔진 · 인프라 · 품질 보증","구독 매출 60% + 초과 사용량 100% + 분양비",ACC],
         ["분양 파트너","모집 · 온보딩 · 1차 CS","구독 매출 40% (20개 초과분 45%) + 개통비 70%",INK],
         ["테넌트","월 구독 사용","월 9.9만 ~ 69만 원 + 개통비",INK]];
f.forEach((c,i)=>{
  const x=M+i*4.24;
  card(s,x,1.92,3.9,1.42,i===0?ACC_LT:WHITE);
  s.addText(c[0],{x:x+0.22,y:2.08,w:3.5,h:0.3,fontSize:13.5,bold:true,color:c[3],fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[1],{x:x+0.22,y:2.42,w:3.5,h:0.26,fontSize:10.5,color:INK2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(c[2],{x:x+0.22,y:2.74,w:3.5,h:0.46,fontSize:10,color:MUTED,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
  if(i<2) s.addShape(pres.ShapeType.rightArrow,{x:x+3.98,y:2.5,w:0.24,h:0.2,fill:{color:"C4C2BE"},line:{color:"C4C2BE"}});
});
s.addText("분양 조건",{x:M,y:3.56,w:4,h:0.3,fontSize:14,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
const d=[["분양 단위","업종 팩 × 권역 1구좌 · 권역당 1구좌 상한"],
         ["초기 분양비","1,500만 원 (4주 교육 + 파트너 포털 + 마케팅 키트 + 독점권 12개월)"],
         ["월 플랫폼 사용료","30만 원 · 테넌트 5개 이상 확보 시 면제"],
         ["파트너 손익","테넌트 25개 확보 시 월 순수익 약 200만 원 → 투자금 회수 12~14개월"]];
d.forEach((r,i)=>{
  const y=3.94+i*0.55;
  card(s,M,y,7.55,0.47,i%2===0?CARD:WHITE);
  s.addText(r[0],{x:M+0.22,y:y+0.10,w:1.9,h:0.28,fontSize:10.5,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[1],{x:M+2.16,y:y+0.10,w:5.2,h:0.28,fontSize:10.5,color:INK2,fontFace:KR,isTextBox:true,margin:0});
});
card(s,8.55,3.56,4.08,2.62,INK);
s.addText("분양 모델 리스크 통제",{x:8.79,y:3.76,w:3.6,h:0.3,fontSize:12.5,bold:true,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
s.addText("품질 편차와 “분양비 장사” 오해가 최대 위험입니다.",{x:8.79,y:4.08,w:3.6,h:0.3,fontSize:9.5,color:"A8A6A1",fontFace:KR,isTextBox:true,margin:0});
const g=["파트너 자격 심사 — IT 유통·SI 경력 필수",
         "조건부 환불 — 12개월 내 테넌트 10개 미달 시 50% 환급",
         "테넌트 만족도 기반 파트너 등급제",
         "권역 과밀 방지 상한 · 본사 QA 샘플 검수",
         "표준 계약서 공정거래 사전 검토"];
g.forEach((t,i)=>{
  const y=4.46+i*0.34;
  s.addShape(pres.ShapeType.rect,{x:8.79,y:y+0.10,w:0.07,h:0.07,fill:{color:ACC_DK},line:{color:ACC_DK}});
  s.addText(t,{x:8.98,y:y,w:3.45,h:0.3,fontSize:9.5,color:"D8D6D1",fontFace:KR,isTextBox:true,margin:0});
});
s.addNotes("분양은 자금 조달(선수금)과 유통(CAC 이전), 온보딩 노동 분산을 동시에 해결. 리스크 통제 장치를 먼저 말할 것.");
}

/* ══ 14 유닛 이코노믹스 ════════════════════ */
{
const s=pres.addSlide(); const n=14; footer(s,n);
hdr(s,"UNIT ECONOMICS","한 명의 고객이 만드는 돈","이탈률 월 2.5%를 반영한 보수적 기준입니다.");
const u=[["블렌디드 ARPU","21만 원","월 · 플랜 믹스 6:3:1",INK],
         ["매출총이익률","75%","클라우드·모델 원가 25%",INK],
         ["월 이탈률","2.5%","연 26% · 파트너 CS 개입 반영",INK],
         ["LTV","630만 원","ARPU × 총이익률 ÷ 이탈률",INK],
         ["CAC","60만 원","파트너 마진 선지급 + 본사 지원",INK],
         ["CAC 회수기간","3.8개월","NDR 목표 105%",INK]];
u.forEach((t,i)=>{
  const x=M+(i%3)*4.05, y=1.92+Math.floor(i/3)*1.52;
  tile(s,x,y,3.8,1.4,t[0],t[1],t[2],t[3],WHITE);
});
card(s,M,5.08,CW,1.42,ACC_LT);
s.addText("LTV / CAC",{x:M+0.34,y:5.32,w:2.4,h:0.3,fontSize:11,bold:true,color:ACC,charSpacing:1.4,fontFace:KR,isTextBox:true,margin:0});
s.addText("10.5배",{x:M+0.34,y:5.62,w:2.6,h:0.6,fontSize:40,bold:true,color:ACC,fontFace:NUM,isTextBox:true,margin:0});
s.addShape(pres.ShapeType.line,{x:M+3.3,y:5.34,w:0,h:0.92,line:{color:"D8BFC1",width:1}});
s.addText("SaaS 업계에서 통상 3배 이상이면 건전한 구조로 평가합니다. BSM은 파트너가 획득 비용을 흡수하고 온보딩까지 수행하는 구조라\n동일 ARPU 대비 CAC가 낮고, 파트너의 1차 CS가 이탈률을 억제해 LTV가 함께 올라갑니다.",
  {x:M+3.62,y:5.48,w:8.3,h:0.7,fontSize:11.5,color:INK2,lineSpacing:17,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("LTV/CAC 10.5배의 원인은 파트너 구조 그 자체 — 제품이 아니라 유통 설계에서 나온 숫자임을 강조.");
}

/* ══ 15 로드맵 ═════════════════════════════ */
{
const s=pres.addSlide(); const n=15; footer(s,n);
hdr(s,"ROADMAP","36개월 실행 계획","각 단계의 종료 조건을 정량 지표로 고정했습니다.");
const ph=[["PHASE 0","0–3개월","검증","자사몰을 1호 테넌트로 전환해 상담 자동화율·매출 기여 실측. 블로그·유튜브 콘텐츠로 네트워크·IT 도메인 팩 1차 완성. 무료 파일럿 10개사 유치. AX 바우처 공급기업 등록.","파일럿 10사 · 골든셋 2,000문항",true],
          ["PHASE 1","4–9개월","상품화","셀프서비스 가입·결제·무인 개통 오픈. 카카오톡 채널·웹위젯·인스타그램 DM 연동 완성. 파트너 포털 v1과 4주 교육 커리큘럼 출시.","유료 테넌트 100 · 파트너 8개좌 · MRR 2,000만",false],
          ["PHASE 2","10–18개월","확장","도메인 팩 3종 추가(커머스·교육·의료). AICC 음성 연동. 정부 바우처 컨소시엄 5건 이상 수주. ISMS-P 인증 착수.","유료 테넌트 900 · 파트너 45개좌",false],
          ["PHASE 3","19–36개월","지배","액션 에이전트 출시 — 조회를 넘어 주문 변경·예약·CRM 기록까지 수행. 파트너 도메인 팩 마켓플레이스 개설. 일본·동남아 시범 분양.","유료 테넌트 2,400 · BEP 달성",false]];
ph.forEach((p,i)=>{
  const x=M+i*3.05;
  card(s,x,1.98,2.75,4.15,p[5]?ACC_LT:WHITE);
  s.addShape(pres.ShapeType.ellipse,{x:x+0.22,y:2.16,w:0.2,h:0.2,fill:{color:p[5]?ACC:"C4C2BE"},line:{color:p[5]?ACC:"C4C2BE"}});
  s.addText(p[0],{x:x+0.52,y:2.12,w:2.1,h:0.26,fontSize:9.5,bold:true,color:p[5]?ACC:MUTED,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
  s.addText(p[1],{x:x+0.22,y:2.44,w:2.35,h:0.26,fontSize:10,color:MUTED,fontFace:NUM,isTextBox:true,margin:0});
  s.addText(p[2],{x:x+0.22,y:2.72,w:2.35,h:0.36,fontSize:17,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  s.addText(p[3],{x:x+0.22,y:3.10,w:2.35,h:1.9,fontSize:10,color:INK2,lineSpacing:14,fontFace:KR,isTextBox:true,margin:0});
  card(s,x+0.22,5.12,2.31,0.82,p[5]?"E4CFD1":CARD);
  s.addText("목표",{x:x+0.36,y:5.20,w:2,h:0.22,fontSize:8.5,bold:true,color:MUTED,charSpacing:1,fontFace:KR,isTextBox:true,margin:0});
  s.addText(p[4],{x:x+0.36,y:5.42,w:2.05,h:0.46,fontSize:9.5,bold:true,color:p[5]?ACC:INK,lineSpacing:12,fontFace:KR,isTextBox:true,margin:0});
});
s.addNotes("Phase 1 KPI가 2차 투자금 집행 조건과 동일 — 투자자 입장에서 검증 지점이 명확하다.");
}

/* ══ 16 재무 ═══════════════════════════════ */
{
const s=pres.addSlide(); const n=16; footer(s,n);
hdr(s,"FINANCIALS","5개년 재무 추정","테넌트 증가는 파트너 구좌 수 × 구좌당 평균 테넌트로 구동됩니다. (단위: 억 원)");
const labels=["Y1 ’27","Y2 ’28","Y3 ’29","Y4 ’30","Y5 ’31"];
s.addChart([
  {type:pres.ChartType.bar, data:[{name:"총매출",labels,values:[9.5,32,78,152,260]}],
   options:{chartColors:[ACC],barGapWidthPct:60,showValue:true,dataLabelPosition:"outEnd",
     dataLabelFormatCode:"#,##0.#",dataLabelFontSize:10,dataLabelColor:INK,dataLabelFontFace:NUM}},
  {type:pres.ChartType.line, data:[{name:"영업이익",labels,values:[-8,-6,4,28,62]}],
   options:{chartColors:[SIG],lineSize:3,lineDataSymbol:"circle",lineDataSymbolSize:7,showValue:false}}
],{x:M,y:1.92,w:7.35,h:4.15,
   catAxisLabelColor:MUTED,catAxisLabelFontSize:10,catAxisLabelFontFace:NUM,
   valAxisLabelColor:MUTED,valAxisLabelFontSize:10,valAxisLabelFontFace:NUM,
   valAxisMinVal:-40,valAxisMaxVal:300,
   valGridLine:{color:"E6E5E2",size:1},catGridLine:{style:"none"},
   showLegend:true,legendPos:"t",legendFontSize:10,legendColor:INK2,legendFontFace:KR,
   plotArea:{fill:{color:WHITE}}});
s.addText("막대 = 총매출 · 선 = 영업이익.  영업이익은 3차년도에 +4억 원으로 흑자 전환합니다. (정확한 값은 우측 표 참조)",
  {x:M,y:6.16,w:7.35,h:0.3,fontSize:9,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
const rows=[["파트너 구좌 (누적)","15","45","90","150","220"],
            ["유료 테넌트 (기말)","250","900","2,400","5,000","8,500"],
            ["총매출","9.5","32.0","78.0","152.0","260.0"],
            ["매출총이익","7.0","24.6","60.8","120.0","208.0"],
            ["영업이익","-8.0","-6.0","+4.0","+28.0","+62.0"],
            ["영업이익률","-84%","-19%","5%","18%","24%"],
            ["인원 (기말)","14","22","32","42","55"]];
s.addTable([[{text:"구분",options:{bold:true,color:MUTED,fontSize:9.5}},
   ...labels.map(l=>({text:l,options:{bold:true,color:MUTED,fontSize:9.5,align:"right"}}))],
  ...rows.map((r,i)=>[
    {text:r[0],options:{bold:i>=2&&i<=4,color:INK,fontSize:9.5}},
    ...r.slice(1).map(v=>({text:v,options:{align:"right",fontSize:9.5,fontFace:NUM,
      bold:i===4,color:i===4?(v.startsWith("-")?ACC:SIG):INK2}}))])],
  {x:8.28,y:2.28,w:4.35,h:3.3,colW:[1.45,0.58,0.58,0.58,0.58,0.58],
   border:{type:"solid",color:LINE,pt:0.5},fontFace:KR,valign:"middle",
   fill:{color:WHITE},margin:[4,5,4,5]});
card(s,8.28,5.74,4.35,0.72,CARD);
s.addText("Y1~Y2 누적 손실 14억 · 조달 30억 기준 런웨이 30개월",
  {x:8.48,y:5.86,w:4.0,h:0.48,fontSize:10.5,bold:true,color:INK,lineSpacing:14,fontFace:KR,isTextBox:true,margin:0});
s.addNotes("3차년도 흑자 전환. BEP 시점에 6개월 버퍼가 남는 조달 규모이며 이후 자체 현금흐름으로 성장.");
}

/* ══ 17 투자 제안 ══════════════════════════ */
{
const s=pres.addSlide(); const n=17; s.background={color:INK};
s.addShape(pres.ShapeType.rect,{x:M,y:0.47,w:0.1,h:0.1,fill:{color:ACC_DK},line:{color:ACC_DK}});
s.addText("THE ASK",{x:M+0.21,y:0.37,w:9,h:0.28,fontSize:10.5,bold:true,color:ACC_DK,charSpacing:1.6,fontFace:KR,isTextBox:true,margin:0});
s.addText("30억 원, 마일스톤 연동 2단계 집행",{x:M,y:0.70,w:CW,h:0.6,fontSize:31,bold:true,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
const a=[["라운드","Pre-Series A"],["조달액","30억 원"],["기업가치","Pre 120억 / Post 150억 · 지분 20%"],
         ["증권 형태","상환전환우선주(RCPS) 또는 전환사채(CB) — 협의"],
         ["집행 구조","1차 18억 (계약 즉시) / 2차 12억 (Phase 1 KPI 달성 시)"],
         ["2차 집행 KPI","유료 테넌트 100 · 파트너 8개좌 · MRR 2,000만 · 정답률 90%"]];
a.forEach((r,i)=>{
  const y=1.72+i*0.56;
  s.addShape(pres.ShapeType.line,{x:M,y:y+0.48,w:6.9,h:0,line:{color:"32353A",width:1}});
  s.addText(r[0],{x:M,y:y+0.06,w:1.8,h:0.3,fontSize:10.5,bold:true,color:"8E8B86",fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[1],{x:M+1.86,y:y+0.05,w:5.04,h:0.32,fontSize:i===5?10.5:12,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
});
s.addText("자금 사용 계획",{x:8.0,y:1.72,w:4,h:0.3,fontSize:13,bold:true,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
s.addChart(pres.ChartType.doughnut,
  [{name:"자금 사용",labels:["제품·R&D","영업·마케팅","클라우드 인프라","파트너 네트워크","인증·법무·예비"],
    values:[45,25,12,10,8]}],
  {x:8.35,y:2.02,w:3.9,h:2.85,chartColors:[ACC,"B05A62","C98A90","8E9AA0","5C6166"],
   holeSize:52,showLegend:false,
   showValue:true,showPercent:false,dataLabelFontSize:9.5,dataLabelColor:WHITE,dataLabelFontFace:NUM,
   dataLabelFormatCode:'0"%"',
   plotArea:{fill:{color:INK}},chartArea:{fill:{color:INK}}});
const swatch=[ACC,"B05A62","C98A90","8E9AA0","5C6166"];
const u=[["제품 · R&D","13.5억","45%"],["영업 · 마케팅","7.5억","25%"],["클라우드 인프라","3.6억","12%"],
         ["파트너 네트워크","3.0억","10%"],["인증 · 법무 · 예비","2.4억","8%"]];
u.forEach((r,i)=>{
  const y=4.98+i*0.36;
  s.addShape(pres.ShapeType.rect,{x:8.0,y:y+0.10,w:0.11,h:0.11,fill:{color:swatch[i]},line:{color:swatch[i]}});
  s.addText(r[0],{x:8.24,y,w:2.6,h:0.3,fontSize:10.5,color:"D8D6D1",fontFace:KR,isTextBox:true,margin:0});
  s.addText(r[2],{x:10.8,y,w:0.8,h:0.3,fontSize:10,color:"8E8B86",align:"right",fontFace:NUM,isTextBox:true,margin:0});
  s.addText(r[1],{x:11.65,y,w:0.98,h:0.3,fontSize:10.5,bold:true,color:WHITE,align:"right",fontFace:KR,isTextBox:true,margin:0});
});
card(s,M,5.28,6.9,1.2,"1E2124");
s.addText("밸류에이션 근거",{x:M+0.26,y:5.42,w:4,h:0.28,fontSize:10.5,bold:true,color:ACC_DK,charSpacing:1.2,fontFace:KR,isTextBox:true,margin:0});
s.addText("Y3 예상 매출 78억 기준 Post 150억은 EV/Revenue 1.9배. 국내 B2B SaaS 통상 5~8배, 2026년 시드~시리즈A 100억 이상 빅딜 31건(전년비 +41%)을 감안하면 보수적 수준.",
  {x:M+0.26,y:5.72,w:6.4,h:0.62,fontSize:10.5,color:"C9C7C2",lineSpacing:14,fontFace:KR,isTextBox:true,margin:0});
s.addText("BSM · 하이브리드 RAG 챗봇 ISP · 투자 유치 계획서",{x:M,y:6.94,w:7,h:0.26,fontSize:8.5,color:"6E6B66",fontFace:KR,isTextBox:true,margin:0});
s.addText("17",{x:12.0,y:6.94,w:0.63,h:0.26,fontSize:9,color:"6E6B66",fontFace:NUM,align:"right",isTextBox:true,margin:0});
s.addNotes("2단계 집행으로 투자자 리스크를 낮춘다. 2차 집행 KPI가 Phase 1 종료 조건과 동일.");
}

/* ══ 18 리스크 ═════════════════════════════ */
{
const s=pres.addSlide(); const n=18; footer(s,n);
hdr(s,"RISK","리스크와 대응","영향도 상(上) 항목을 먼저 배치했습니다.");
const r=[["빅테크 번들링","상","플랫폼의 챗봇 무료 끼워팔기","범용이 못 하는 테넌트 전용 데이터 거버넌스·감사로그·업무 시스템 연동으로 회피. 가격이 아니라 책임 소재로 경쟁"],
         ["RAG 정확도 미달","상","오답 1건이 민원으로 직결","골든셋 회귀 평가 CI화. 근거 미확보 시 “모름 + 상담사 이관”이 기본값 — 오답보다 이관이 안전"],
         ["파트너 품질 편차","상","분양 모델의 최대 위험","자격 심사 · 등급제 · 조건부 환불 · 본사 QA 샘플 검수 · 권역당 1구좌 상한"],
         ["개인정보 유출","상","상담 데이터 내 개인정보","국내 리전 고정 · PII 마스킹 · 테넌트별 IAM·CMEK · ISMS-P · 침해 대응 보험"],
         ["LLM 원가 변동","중","모델 단가 및 정책 변경","모델 라우팅(경량↔고성능) · 응답 캐시 · 자체 임베딩 전환 옵션 · 요금제 내 세션 상한"],
         ["규제 강화 · 경기 침체","중","AI 기본법 / IT 예산 축소","표시·투명성 요구를 제품 기본 기능으로 선제 내장. 정부 바우처 연계로 고객 실부담 20%까지 인하"]];
r.forEach((x2,i)=>{
  const x=M+(i%2)*6.06, y=1.92+Math.floor(i/2)*1.56;
  card(s,x,y,5.81,1.42,WHITE);
  s.addText(x2[0],{x:x+0.22,y:y+0.14,w:4.2,h:0.3,fontSize:13,bold:true,color:INK,fontFace:KR,isTextBox:true,margin:0});
  card(s,x+4.98,y+0.16,0.6,0.3,x2[1]==="상"?ACC_LT:CARD);
  s.addText(x2[1],{x:x+4.98,y:y+0.19,w:0.6,h:0.24,fontSize:10,bold:true,color:x2[1]==="상"?ACC:MUTED,align:"center",fontFace:KR,isTextBox:true,margin:0});
  s.addText(x2[2],{x:x+0.22,y:y+0.46,w:5.35,h:0.26,fontSize:10,color:MUTED,fontFace:KR,isTextBox:true,margin:0});
  s.addText(x2[3],{x:x+0.22,y:y+0.76,w:5.35,h:0.56,fontSize:10,color:INK2,lineSpacing:13,fontFace:KR,isTextBox:true,margin:0});
});
s.addNotes("리스크를 숨기지 않고 대응책과 함께 제시. 특히 분양 모델 리스크는 먼저 꺼내는 것이 신뢰를 만든다.");
}

/* ══ 19 마무리 ═════════════════════════════ */
{
const s=pres.addSlide(); s.background={color:INK};
s.addShape(pres.ShapeType.rect,{x:M,y:0.47,w:0.1,h:0.1,fill:{color:ACC_DK},line:{color:ACC_DK}});
s.addText("NEXT STEPS",{x:M+0.21,y:0.37,w:9,h:0.28,fontSize:10.5,bold:true,color:ACC_DK,charSpacing:1.6,fontFace:KR,isTextBox:true,margin:0});
s.addText("IR 제출 전 실측치로 교체할 항목",{x:M,y:0.70,w:CW,h:0.6,fontSize:31,bold:true,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
s.addText("본 계획서의 시장·재무 수치는 공개 출처와 명시된 가정에 기반합니다. 아래 회사 실측 데이터는 아직 반영되지 않았습니다.",
  {x:M,y:1.34,w:11.4,h:0.3,fontSize:12,color:"A8A6A1",fontFace:KR,isTextBox:true,margin:0});
const it=[["법인 형태 · 설립일 · 자본금 · 주주 구성",""],
          ["대표자 이력 및 핵심 팀 프로필","투자 심사 최대 가중치 항목"],
          ["자사몰 최근 3년 매출 · 주문 수 · 문의 건수","1호 테넌트 ROI 근거"],
          ["블로그 월 방문자 · 누적 포스트 수","코퍼스 규모 산정"],
          ["유튜브 구독자 · 조회수 · 업로드 주기","파트너 모집 채널 가치"],
          ["기존 챗봇/AI 개발 실적 · 보유 특허","기술 신뢰도"],
          ["현재 인력 구성 및 GCP 운영 경험",""],
          ["기확보 파일럿 고객 · LOI 여부","Traction 섹션 신설"],
          ["기존 투자 유치 · 정부과제 수행 이력",""],
          ["요금 · 분양비의 시장 검증 결과","현재 가정값"]];
it.forEach((r,i)=>{
  const x=M+(i%2)*6.06, y=1.92+Math.floor(i/2)*0.62;
  s.addShape(pres.ShapeType.line,{x,y:y+0.5,w:5.81,h:0,line:{color:"32353A",width:1}});
  s.addText(String(i+1).padStart(2,"0"),{x,y:y+0.08,w:0.42,h:0.3,fontSize:11,bold:true,color:ACC_DK,fontFace:NUM,isTextBox:true,margin:0});
  s.addText(r[0],{x:x+0.5,y:y+0.06,w:3.6,h:0.34,fontSize:11.5,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
  if(r[1]) s.addText(r[1],{x:x+4.1,y:y+0.10,w:1.7,h:0.28,fontSize:9,color:"8E8B86",align:"right",fontFace:KR,isTextBox:true,margin:0});
});
card(s,M,5.28,CW,1.28,"1E2124");
s.addText("챗봇을 회선처럼, 앱을 분양처럼",{x:M+0.32,y:5.48,w:6.5,h:0.4,fontSize:22,bold:true,color:WHITE,fontFace:KR,isTextBox:true,margin:0});
s.addText("Pre-Series A  ·  30억 원  ·  Post-money 150억  ·  지분 20%",{x:M+0.32,y:5.94,w:7,h:0.32,fontSize:12.5,color:ACC_DK,fontFace:KR,isTextBox:true,margin:0});
s.addText("BSM\nnetk.tistory.com\nbsmshop.cafe24.com",{x:9.4,y:5.44,w:3.2,h:0.9,fontSize:10.5,color:"A8A6A1",align:"right",lineSpacing:15,fontFace:KR,isTextBox:true,margin:0});
s.addText("본 문서는 투자 검토 목적의 사업계획서이며, 재무 추정치는 명시된 가정에 기반한 전망으로 확정된 실적이 아닙니다.",
  {x:M,y:6.86,w:11.4,h:0.3,fontSize:8.5,color:"6E6B66",fontFace:KR,isTextBox:true,margin:0});
s.addNotes("마무리. 남은 것은 회사 실측 데이터 10건. 이것만 채우면 즉시 IR 제출 가능한 상태.");
}

pres.writeFile({fileName:"/tmp/claude-0/-home-user-chatbot/7a62990a-0f4b-57ec-af6f-77c2ddc99b78/scratchpad/BSM_AI챗봇_투자유치계획서.pptx"})
  .then(f=>console.log("WROTE",f));
