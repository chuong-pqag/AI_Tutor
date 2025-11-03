-- =========================================
-- AI Tutor — Cấu trúc CSDL mở rộng
-- Phiên bản: 2.0 (có tracking & bài tập)
-- =========================================

-- =========================
-- 1️⃣ Bảng học sinh
-- =========================
CREATE TABLE IF NOT EXISTS hoc_sinh (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ho_ten text NOT NULL,
  ngay_sinh date,
  gioi_tinh text CHECK (gioi_tinh IN ('Nam','Nữ','Khác')),
  lop_hien_tai int NOT NULL,
  email text,
  diem_trung_binh numeric DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- =========================
-- 2️⃣ Bảng chủ đề học
-- =========================
CREATE TABLE IF NOT EXISTS chu_de (
  id serial PRIMARY KEY,
  mon_hoc text NOT NULL DEFAULT 'Toán',
  lop int NOT NULL,
  tuan int NOT NULL,
  ten_chu_de text NOT NULL,
  tag_ki_nang text,
  prerequisite_id int REFERENCES chu_de(id),
  muc_do text CHECK (muc_do IN ('cơ bản','nâng cao')) DEFAULT 'cơ bản',
  trang_thai boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

-- =========================
-- 3️⃣ Bảng video bài giảng
-- =========================
CREATE TABLE IF NOT EXISTS video_bai_giang (
  id serial PRIMARY KEY,
  chu_de_id int REFERENCES chu_de(id) ON DELETE CASCADE,
  tieu_de text NOT NULL,
  mo_ta text,
  url text NOT NULL,
  thoi_luong int,
  nguon text DEFAULT 'YouTube',
  created_at timestamptz DEFAULT now()
);

-- =========================
-- 4️⃣ Bảng câu hỏi luyện tập
-- =========================
CREATE TABLE IF NOT EXISTS cau_hoi (
  id serial PRIMARY KEY,
  chu_de_id int REFERENCES chu_de(id) ON DELETE CASCADE,
  noi_dung text NOT NULL,
  dap_an_dung text NOT NULL,
  dap_an_khac jsonb,
  muc_do text CHECK (muc_do IN ('cơ bản','nâng cao')) DEFAULT 'cơ bản',
  diem_so int DEFAULT 1
);

-- =========================
-- 5️⃣ Bảng bài tập (gồm nhiều câu hỏi)
-- =========================
CREATE TABLE IF NOT EXISTS bai_tap (
  id serial PRIMARY KEY,
  chu_de_id int REFERENCES chu_de(id) ON DELETE CASCADE,
  tieu_de text NOT NULL,
  mo_ta text,
  muc_do text DEFAULT 'cơ bản',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bai_tap_cau_hoi (
  bai_tap_id int REFERENCES bai_tap(id) ON DELETE CASCADE,
  cau_hoi_id int REFERENCES cau_hoi(id) ON DELETE CASCADE,
  PRIMARY KEY (bai_tap_id, cau_hoi_id)
);

-- =========================
-- 6️⃣ Bảng kết quả kiểm tra / luyện tập
-- =========================
CREATE TABLE IF NOT EXISTS ket_qua_test (
  id serial PRIMARY KEY,
  hoc_sinh_id uuid REFERENCES hoc_sinh(id) ON DELETE CASCADE,
  chu_de_id int REFERENCES chu_de(id),
  bai_tap_id int REFERENCES bai_tap(id),
  diem numeric CHECK (diem >= 0 AND diem <= 10),
  so_cau_dung int,
  tong_cau int,
  tuan_kiem_tra int,
  ngay_kiem_tra timestamptz DEFAULT now()
);

-- =========================
-- 7️⃣ Bảng lộ trình học (AI gợi ý)
-- =========================
CREATE TABLE IF NOT EXISTS lo_trinh_hoc (
  id serial PRIMARY KEY,
  hoc_sinh_id uuid REFERENCES hoc_sinh(id) ON DELETE CASCADE,
  chu_de_id int REFERENCES chu_de(id),
  video_id int REFERENCES video_bai_giang(id),
  loai_goi_y text CHECK (loai_goi_y IN ('remediate','review','advance')),
  muc_do_de_xuat text CHECK (muc_do_de_xuat IN ('cơ bản','nâng cao')) DEFAULT 'cơ bản',
  trang_thai text DEFAULT 'Chưa thực hiện',
  ngay_goi_y timestamptz DEFAULT now(),
  diem_truoc_goi_y numeric
);

-- =========================
-- 8️⃣ Bảng lịch sử học (theo dõi chi tiết)
-- =========================
CREATE TABLE IF NOT EXISTS lich_su_hoc (
  id serial PRIMARY KEY,
  hoc_sinh_id uuid REFERENCES hoc_sinh(id) ON DELETE CASCADE,
  chu_de_id int REFERENCES chu_de(id),
  hanh_dong text CHECK (hanh_dong IN ('xem_video','luyen_tap','nop_bai','xem_goi_y')),
  noi_dung text,
  thoi_gian timestamptz DEFAULT now()
);

-- =========================
-- 9️⃣ Bảng ghi nhận kết quả AI gợi ý
-- =========================
CREATE TABLE IF NOT EXISTS ai_recommendation_log (
  id serial PRIMARY KEY,
  hoc_sinh_id uuid REFERENCES hoc_sinh(id),
  input_features jsonb,
  action text CHECK (action IN ('remediate','review','advance')),
  chu_de_nguon int REFERENCES chu_de(id),
  chu_de_de_xuat int REFERENCES chu_de(id),
  model_version text DEFAULT 'rule-based',
  confidence numeric,
  created_at timestamptz DEFAULT now()
);

-- =========================
-- 🔟 Seed dữ liệu mẫu
-- =========================

-- Học sinh
INSERT INTO hoc_sinh (ho_ten, gioi_tinh, lop_hien_tai, email)
VALUES 
('Nguyễn An', 'Nam', 2, 'an2@example.com'),
('Trần Bình', 'Nam', 3, 'binh3@example.com'),
('Lê Mai', 'Nữ', 2, 'mai2@example.com');

-- Chủ đề
INSERT INTO chu_de (mon_hoc, lop, tuan, ten_chu_de, tag_ki_nang, muc_do)
VALUES
('Toán', 2, 5, 'Cộng có nhớ trong phạm vi 100', 'cong_nho', 'cơ bản'),
('Toán', 2, 6, 'Trừ có nhớ trong phạm vi 100', 'tru_nho', 'cơ bản'),
('Toán', 3, 4, 'Cộng có nhớ trong phạm vi 1000', 'cong_nho', 'cơ bản');

-- Video
INSERT INTO video_bai_giang (chu_de_id, tieu_de, mo_ta, url, thoi_luong)
VALUES
(1, 'Cộng có nhớ (Lớp 2 - Tuần 5)', 'Ví dụ minh họa', 'https://www.youtube.com/watch?v=xxxxxx', 180),
(2, 'Trừ có nhớ (Lớp 2 - Tuần 6)', 'Bài giảng minh họa', 'https://www.youtube.com/watch?v=yyyyyy', 210);

-- Câu hỏi
INSERT INTO cau_hoi (chu_de_id, noi_dung, dap_an_dung, dap_an_khac, muc_do)
VALUES
(1, '5 + 7 = ?', '12', '["11","13","10"]', 'cơ bản'),
(1, '9 + 8 = ?', '17', '["16","18","15"]', 'cơ bản'),
(2, '14 - 9 = ?', '5', '["4","6","7"]', 'cơ bản');

-- Bài tập mẫu
INSERT INTO bai_tap (chu_de_id, tieu_de, mo_ta)
VALUES (1, 'Bài luyện tập cộng có nhớ', 'Gồm 5 câu cộng có nhớ');

-- Gắn câu hỏi vào bài tập
INSERT INTO bai_tap_cau_hoi (bai_tap_id, cau_hoi_id) VALUES (1, 1), (1, 2);

-- Kết quả mẫu
INSERT INTO ket_qua_test (hoc_sinh_id, chu_de_id, bai_tap_id, diem, so_cau_dung, tong_cau, tuan_kiem_tra)
SELECT id, 1, 1, 8.0, 4, 5, 5 FROM hoc_sinh WHERE ho_ten='Nguyễn An';

-- Gợi ý học mẫu
INSERT INTO lo_trinh_hoc (hoc_sinh_id, chu_de_id, loai_goi_y, muc_do_de_xuat, diem_truoc_goi_y)
SELECT id, 2, 'advance', 'cơ bản', 8.0 FROM hoc_sinh WHERE ho_ten='Nguyễn An';

-- Lịch sử học
INSERT INTO lich_su_hoc (hoc_sinh_id, chu_de_id, hanh_dong, noi_dung)
SELECT id, 1, 'xem_video', 'Học sinh xem video cộng có nhớ' FROM hoc_sinh WHERE ho_ten='Nguyễn An';

-- Log AI recommendation
INSERT INTO ai_recommendation_log (hoc_sinh_id, input_features, action, chu_de_nguon, chu_de_de_xuat, confidence)
SELECT id, '{"diem":8.0,"lop":2,"tuan":5}', 'advance', 1, 2, 0.9 FROM hoc_sinh WHERE ho_ten='Nguyễn An';

-- =========================
-- ✅ Hoàn tất khởi tạo
-- =========================
