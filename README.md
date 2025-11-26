---
title: AI Tutor
emoji: 🎓
colorFrom: blue
colorTo: pink
sdk: streamlit
sdk_version: 1.37.0
app_file: app.py
pinned: false
---

# 🤖 AI TUTOR: HỆ THỐNG GIA SƯ CÁ NHÂN HÓA THÍCH ỨNG

AI Tutor là nền tảng học tập thông minh dành cho học sinh Tiểu học, tập
trung vào: - Chẩn đoán năng lực (Biết -- Hiểu -- Vận dụng) - Gợi ý học
tập thích ứng bằng Machine Learning (Decision Tree) - Cá nhân hóa lộ
trình học dựa trên dữ liệu

link demo: aitutor-v1.streamlit.app
------------------------------------------------------------------------

## I. Tính năng Nổi bật & Giá trị Cốt lõi

### 1. Bảng tính năng

  ------------------------------------------------------------------------------
  Tính năng                Mô tả                   Trạng thái
  ------------------------ ----------------------- -----------------------------
  Gợi ý Thích ứng (AI)     AI chẩn đoán điểm kiểm  Đã kích hoạt
                           tra và dùng Decision    
                           Tree để đề xuất         
                           Remediate / Review /    
                           Advance                 

  Sư phạm Chuyên sâu       Quản lý ngân hàng câu   Hoàn thiện
                           hỏi theo 3 mức độ nhận  
                           thức                    

  Quản lý Bài tập          CRUD + xoá an toàn +    Hoàn thiện
                           xem chi tiết câu hỏi    

  Lọc đa cấp               Lọc theo Lớp → Môn học  Hoàn thiện
                           → Chủ đề → Bài học      

  Kiến trúc Multi-tenant   Sẵn sàng                Sẵn sàng
                           Database-per-Tenant +   
                           Horizontal Sharding     
  ------------------------------------------------------------------------------

------------------------------------------------------------------------

## II. Kiến trúc Hệ thống & Công nghệ

### 1. Kiến trúc phân tầng

  ----------------------------------------------------------------------------
  Tầng             Thư mục                      Chức năng
  ---------------- ---------------------------- ------------------------------
  Giao diện        pages/, teacher_pages/,      Streamlit UI cho 3 vai trò
  (Frontend)       student_pages/               

  Logic nghiệp vụ  backend/                     Sinh đề, xử lý dữ liệu, AI
                                                recommendation

  Data Layer       backend/supabase_client.py   Kết nối Supabase/PostgreSQL
  ----------------------------------------------------------------------------

### 2. Công nghệ sử dụng

-   Python\
-   Streamlit\
-   PostgreSQL (Supabase)\
-   Scikit-learn (Decision Tree)\
-   Pandas

------------------------------------------------------------------------

## III. Cấu trúc Cơ sở Dữ liệu

### 1. Bảng chính trong hệ thống

  Bảng           Mục đích                    Cột quan trọng
  -------------- --------------------------- -------------------------------------
  cau_hoi        Ngân hàng câu hỏi           muc_do, trang_thai
  bai_tap        Danh sách bài tập đã giao   giao_vien_id, loai_bai_tap
  ket_qua_test   Dữ liệu huấn luyện ML       diem, tuan_kiem_tra, tong_cau
  lo_trinh_hoc   Lưu kết quả gợi ý AI        loai_goi_y, chu_de_id
  chu_de         Cấu trúc nội dung học       mon_hoc, lop, tuan, prerequisite_id

------------------------------------------------------------------------

## IV. Hướng dẫn Cài đặt & Vận hành

### 1. Cài đặt môi trường

    git clone [Your Repo URL]
    cd AI_Tutor

Tạo môi trường ảo:

    python -m venv .venv
    .\.venv\Scriptsctivate   # Windows
    # source .venv/bin/activate  # Linux/Mac

Cài thư viện:

    pip install -r requirements.txt

------------------------------------------------------------------------

### 2. Thiết lập CSDL (Supabase) & biến môi trường

Tạo file **.env** tại thư mục gốc:

    SUPABASE_URL="your_supabase_url"
    SUPABASE_KEY="your_supabase_anon_key"

------------------------------------------------------------------------

### 3. Huấn luyện mô hình AI

    python backend/train_model.py

Sinh ra file: `model_recommender.pkl`

------------------------------------------------------------------------

### 4. Khởi chạy ứng dụng

    streamlit run app.py

------------------------------------------------------------------------

## V. Hướng Phát triển

-   Chuyển sang Django + Horizontal Sharding\
-   Hoàn thiện LMS: Forum, Chat, Thông báo\
-   Dashboard HS trực quan hơn + game hóa\
-   Tích hợp Text-to-Speech cho trẻ lớp 1

------------------------------------------------------------------------

(End of README.md)
