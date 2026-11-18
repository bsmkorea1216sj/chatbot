"""CD12 per-slide visible glossary, implementing cloud_architecture/CA강의.md."""
import re
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import fitz
from lxml import etree as E

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
GLOSSARY = {
    'ACID': ('Atomicity, Consistency, Isolation, Durability', '원자성·일관성·격리성·지속성'),
    'AWS': ('Amazon Web Services', '아마존 클라우드'),
    'RDS': ('Relational Database Service', '관리형 관계형 데이터베이스 서비스'),
    'DB': ('Database', '데이터베이스'),
    'DBMS': ('Database Management System', '데이터베이스 관리 시스템'),
    'ER': ('Entity–Relationship', '개체–관계'),
    'ERD': ('Entity–Relationship Diagram', '개체–관계 다이어그램'),
    'IE': ('Information Engineering', '정보공학 표기법'),
    'PK': ('Primary Key', '기본키'),
    'FK': ('Foreign Key', '외래키'),
    'UQ': ('Unique', '고유성 제약'),
    'ID': ('Identifier', '식별자'),
    'SQL': ('Structured Query Language', '구조화 질의 언어'),
    'CRUD': ('Create, Read, Update, Delete', '생성·조회·수정·삭제'),
    'HTTP': ('Hypertext Transfer Protocol', '웹 통신 규약'),
    'URL': ('Uniform Resource Locator', '웹 자원 주소'),
    'HOT': ('Heap-Only Tuple', '인덱스를 바꾸지 않는 같은 페이지 갱신'),
    'WAL': ('Write-Ahead Logging', '선행 기록 로깅'),
    'I/O': ('Input/Output', '입출력'),
    '3NF': ('Third Normal Form', '제3정규형'),
    'TLS': ('Transport Layer Security', '전송 구간 암호화'),
    'VIP': ('Very Important Person', '우수 고객 등급'),
    'A/S': ('After-Sales Service', '판매 후 지원'),
    'VARCHAR': ('Variable-length Character', '가변 길이 문자열 자료형'),
    'SSD': ('Solid-State Drive', '반도체 저장장치'),
    'O/X': ('O / X', '성공 / 실패'),
}
PATTERNS = {
    'A/S': re.compile(r'\bAS\s*관리|A/S'),
    '3NF': re.compile(r'\b3\s*NF\b'),
    'ERD': re.compile(r'\bERD\b|\bER\s*[-–]\s*Diagram\b',re.I),
    'ID': re.compile(r'(?<![a-zA-Z0-9])ID(?![a-zA-Z0-9])',re.I),
    'URL': re.compile(r'(?<![a-zA-Z0-9])URL(?![a-zA-Z0-9])',re.I),
    'SSD': re.compile(r'\bSSD\b|/(?:ssd\d+|fast_ssd)\b',re.I),
    'O/X': re.compile(r'\bO\s*/\s*X\b|\bO\(성공\)'),
}
FOOTER_NAME = 'CD12 abbreviation glossary'
# A legacy glossary may share one line with credentials, notes, commands or costs.
# Retain those segments, and remove only the expanded terms superseded below.
LEGACY = re.compile(r'^(?:DB|DBMS|ACID|AWS|RDS|ERD|IE|PK(?:/FK)?|FK|CRUD|HTTP)(?:\s*[:：])')
font = fitz.Font('cjk')

def wrapped(entries, width, size):
    lines = ['※ 약어']
    for term in entries:
        separator = '  ' if lines[-1]=='※ 약어' else '  ·  '
        if font.text_length(lines[-1]+separator+term,fontsize=size) > width:
            lines.append(term)
        else:
            lines[-1] += separator+term
    return lines

def append_footer(root, page_width, page_height, sw, sh, layout, text_lines, dark):
    tree=root.find(f'.//{{{P}}}spTree')
    ids=[int(e.get('id')) for e in tree.findall('.//{*}cNvPr')]
    left,top,width,size=layout
    scale_x=sw/page_width
    scale_y=sh/page_height
    sp=E.Element(f'{{{P}}}sp')
    nv=E.SubElement(sp,f'{{{P}}}nvSpPr')
    E.SubElement(nv,f'{{{P}}}cNvPr',id=str(max(ids,default=1)+1),name=FOOTER_NAME)
    E.SubElement(nv,f'{{{P}}}cNvSpPr',txBox='1')
    E.SubElement(nv,f'{{{P}}}nvPr')
    props=E.SubElement(sp,f'{{{P}}}spPr')
    transform=E.SubElement(props,f'{{{A}}}xfrm')
    E.SubElement(transform,f'{{{A}}}off',x=str(round(left*scale_x)),y=str(round(top*scale_y)))
    E.SubElement(transform,f'{{{A}}}ext',cx=str(round(width*scale_x)),cy=str(round((len(text_lines)*size*1.20+3)*scale_y)))
    shape=E.SubElement(props,f'{{{A}}}prstGeom',prst='rect')
    E.SubElement(shape,f'{{{A}}}avLst')
    E.SubElement(props,f'{{{A}}}noFill')
    body=E.SubElement(sp,f'{{{P}}}txBody')
    E.SubElement(body,f'{{{A}}}bodyPr',wrap='none',lIns='0',tIns='0',rIns='0',bIns='0')
    E.SubElement(body,f'{{{A}}}lstStyle')
    for line in text_lines:
        para=E.SubElement(body,f'{{{A}}}p')
        par=E.SubElement(para,f'{{{A}}}pPr')
        space=E.SubElement(par,f'{{{A}}}lnSpc')
        E.SubElement(space,f'{{{A}}}spcPts',val=str(round(size*1.16*100)))
        run=E.SubElement(para,f'{{{A}}}r')
        rp=E.SubElement(run,f'{{{A}}}rPr',lang='ko-KR',sz=str(round(size*100)))
        fill=E.SubElement(rp,f'{{{A}}}solidFill')
        E.SubElement(fill,f'{{{A}}}srgbClr',val='FFFFFF' if dark else '17374A')
        E.SubElement(rp,f'{{{A}}}latin',typeface='Noto Sans CJK KR')
        E.SubElement(rp,f'{{{A}}}ea',typeface='Noto Sans CJK KR')
        E.SubElement(run,f'{{{A}}}t').text=line
    ext=tree.find(f'{{{P}}}extLst')
    if ext is None:
        tree.append(sp)
    else:
        tree.insert(tree.index(ext),sp)

def choose_layout(page, terms, ignored):
    w,h=page.rect.width,page.rect.height
    clip=fitz.Rect(w*.07,h*.69,w*.88,h*.98)
    blocked=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            text=''.join(s['text'] for s in line['spans']).strip()
            rect=fitz.Rect(line['bbox'])
            if rect.intersects(clip) and not any(text.startswith(prefix) for prefix in ignored):
                blocked.append(rect)
    # Favor space immediately above any links, then the bottom margin below them.
    link_tops=[l['from'].y0 for l in page.get_links() if l['from'].y0>h*.80]
    bottom_limits=sorted(set([min(link_tops)-4] if link_tops else []),reverse=True)+[h*.982]
    for size in (12,11,10,9):
        left,width=w*.072,w*.803
        lines=wrapped(terms,width*.98,size)
        height=len(lines)*size*1.20+3
        for limit in bottom_limits:
            for y in range(int(limit-height),int(h*.70),-2):
                box=fitz.Rect(left,y-2,left+width,y+height+2)
                if not any(box.intersects(r) for r in blocked):
                    return (left,y,width,size),lines,False
    for size in (11,10,9):
        for left,right in ((.11,.485),(.39,.875),(.075,.72),(.17,.875),(.075,.875)):
            left,width=w*left,w*(right-left)
            lines=wrapped(terms,width*.98,size)
            if any(font.text_length(line,fontsize=size)>width for line in lines):
                continue
            height=len(lines)*size*1.20+3
            for y in range(int(h*.997-height),int(h*.76),-1):
                box=fitz.Rect(left,y-1,left+width,y+height)
                if not any(box.intersects(r) for r in blocked):
                    return (left,y,width,size),lines,False
    raise ValueError(f'No clear footer region on rendered page {page.number+1}: {terms!r}')

def update(source, rendered, target, part):
    with ZipFile(source) as original:
        parts={n:original.read(n) for n in original.namelist()}
    pres=E.fromstring(parts['ppt/presentation.xml'])
    size=pres.find(f'{{{P}}}sldSz')
    sw,sh=int(size.get('cx')),int(size.get('cy'))
    rels={e.get('Id'):e.get('Target') for e in E.fromstring(parts['ppt/_rels/presentation.xml.rels'])}
    order=[rels[e.get(f'{{{R}}}id')] for e in pres.find(f'{{{P}}}sldIdLst')]
    count=0
    with fitz.open(rendered) as pdf:
        assert len(pdf)==len(order)
        for number, path in enumerate(order,1):
            key='ppt/'+path
            root=E.fromstring(parts[key])
            texts=root.findall(f'.//{{{A}}}t')
            visible=' '.join(re.sub(r'https?://\S+','',t.text or '') for t in texts)
            terms=[]
            for word,(full,meaning) in GLOSSARY.items():
                pattern=PATTERNS.get(word) or re.compile(r'(?<![A-Za-z0-9])'+re.escape(word)+r'(?![A-Za-z0-9])')
                if pattern.search(re.sub(r'\bER\s*[-–]\s*Diagram\b','ERD',visible,flags=re.I) if word=='ER' else visible):
                    terms.append(f'{word}: {full} ({meaning})')
            if not terms:
                continue
            ignored=[]
            for t in texts:
                old=t.text or ''
                if not old.startswith('※ '):
                    continue
                remainder=[x for x in old[2:].split(' · ') if not LEGACY.match(x)]
                if not remainder:
                    ignored.append(old[:max(3,min(16,len(old)))])
                t.text='※ '+' · '.join(remainder) if remainder else ''
            layout, lines, congested=choose_layout(pdf[number-1],terms,ignored)
            if congested:
                print('REVIEW density',part,number,layout,lines)
            x,y,w,_=layout
            background = pdf[number-1].get_pixmap(
                matrix=fitz.Matrix(.4,.4), clip=fitz.Rect(x,y,min(x+w,x+155),y+9))
            colors=background.samples
            dark=bool(colors) and sum(colors)/len(colors)<135
            append_footer(root,pdf[number-1].rect.width,pdf[number-1].rect.height,sw,sh,layout,lines,dark)
            parts[key]=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
            print(part,number,layout[1],layout[3],len(lines),[t.split(':',1)[0] for t in terms])
            count+=1
    with ZipFile(target,'w',ZIP_DEFLATED) as output:
        for name, data in parts.items():
            output.writestr(name,data)
    print('TOTAL',part,count,'/',len(order))

if __name__=='__main__':
    base=Path(sys.argv[1])
    output=base/'glossary'
    output.mkdir(exist_ok=True)
    for part in (1,2,3):
        update(base/'sequenced'/f'part{part}.pptx',base/'final-render'/f'part{part}.pdf',output/f'part{part}.pptx',part)
