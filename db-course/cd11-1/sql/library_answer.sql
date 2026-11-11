-- ① 개념: 회원 1:N 대출 N:1 도서 (대출 = 회원과 도서를 잇는 개체)
-- ② 논리: 개체 → 테이블, 관계 → FK
CREATE TABLE members (
  member_id  SERIAL PRIMARY KEY,
  name       VARCHAR(30) NOT NULL,
  phone      VARCHAR(20) UNIQUE      -- 같은 번호 중복 가입 방지
);
CREATE TABLE books (
  book_id  SERIAL PRIMARY KEY,
  isbn     CHAR(13) UNIQUE NOT NULL,
  title    VARCHAR(100) NOT NULL,
  author   VARCHAR(50)
);
CREATE TABLE loans (
  loan_id     SERIAL PRIMARY KEY,
  member_id   INT NOT NULL REFERENCES members(member_id), -- 회원 1:N
  book_id     INT NOT NULL REFERENCES books(book_id),     -- 도서 1:N
  loan_date   DATE NOT NULL DEFAULT CURRENT_DATE,
  due_date    DATE NOT NULL DEFAULT CURRENT_DATE + 14,    -- ③ 14일 뒤
  return_date DATE,                                       -- NULL = 미반납
  CHECK (due_date > loan_date)
);
-- ③ 물리: 미반납 대출만 빠르게 찾는 부분 인덱스
CREATE INDEX idx_loans_open ON loans(member_id)
  WHERE return_date IS NULL;

-- 확인: 데이터 넣고 조회
INSERT INTO members(name, phone) VALUES ('김하늘', '010-1234-5678');
INSERT INTO books(isbn, title, author)
  VALUES ('9791100000001', '데이터베이스 첫걸음', '이도윤');
INSERT INTO loans(member_id, book_id, loan_date, due_date)
  VALUES (1, 1, DATE '2026-03-02', DATE '2026-03-16');
SELECT m.name, b.title, l.loan_date, l.due_date
FROM loans l JOIN members m USING (member_id)
             JOIN books b   USING (book_id)
WHERE l.return_date IS NULL;
