# ===============================================
# 📱 Trang Đăng nhập - app.py (Cập nhật tải Môn học & Kiểm tra Lớp)
# ===============================================
import streamlit as st
# import sys
from backend.supabase_client import supabase
# Import hàm mới từ data_service
from backend.data_service import get_subjects_by_grade # Chỉ cần import hàm này

# =============================================================
# Cấu hình giao diện tổng thể và CSS (Giữ nguyên)
# =============================================================
st.set_page_config(
    page_title="AI Tutor - Hệ thống học tập thông minh",
    page_icon="🎓",
    layout="wide"
)
st.markdown("""
    <style>
    /* CSS giữ nguyên như trước */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; background: linear-gradient(135deg, #e6f7ff 0%, #fff7e6 100%); min-height: 100vh; }
    .login-box { padding: 30px; border-radius: 20px; background-color: #ffffff; border: 2px solid #a8c8ff; box-shadow: 0px 8px 15px rgba(0,0,0,0.1); text-align: center; }
    h1 { color: #004d99; }
    h5, h2, h3, h4 { color: #ff6347; }
    .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div { border: 1px solid #7cb342; border-radius: 5px; padding: 5px; background-color: #f0fff0; box-shadow: 0 2px 5px rgba(0, 100, 0, 0.1); }
    .stTextInput>div>div:focus-within, .stNumberInput>div>div:focus-within, .stSelectbox>div>div:focus-within { border-color: #ff6347; box-shadow: 0 2px 8px rgba(255, 99, 71, 0.3); }
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stRadio"] > div { justify-content: center; width: 100%; color: #0066cc; }

    /* --- CẬP NHẬT NÚT BẤM MÀU CAM --- */
    .stButton>button { 
        background-color: #ff6600; /* Màu cam đậm */
        color: #ffffff; /* Chữ trắng */
        font-weight: bold; 
        border: none; 
        border-radius: 8px; 
        transition: background-color 0.3s; 
    }
    .stButton>button:hover { 
        background-color: #e65c00; /* Màu cam tối hơn khi di chuột */
        color: #ffffff;
    }
    /* -------------------------------- */

    div.login-box h3 { text-align: center; color: #ff6347; }
    div[data-testid="stImage"] { width: 100%; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# BANNER FULL WIDTH (Giữ nguyên)
# -------------------------------------------------------------
try:
    st.image("data/banner.jpg", width='stretch')
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", width='stretch')

# -------------------------------------------------------------
# HEADER (TEXT) (Giữ nguyên)
# -------------------------------------------------------------
# st.markdown("<h1 style='text-align:center;'>🤖 AI Tutor - Hệ thống Học tập Thông Minh</h1>", unsafe_allow_html=True)
# st.markdown(
#    "<p style='text-align:center;'>Phát triển bởi <b>Lâm Đạo Chương</b> • Hỗ trợ cá nhân hóa lộ trình học sinh tiểu học</p>",
#    unsafe_allow_html=True)
#st.divider()

# =============================================================
# BỐ CỤC 2 CỘT CHÍNH: ĐĂNG NHẬP | GIỚI THIỆU (Giữ nguyên)
# =============================================================
col_main, col_intro = st.columns([4, 1])

# -------------------------------------------------------------
# CỘT CHÍNH (ĐĂNG NHẬP + VAI TRÒ)
# -------------------------------------------------------------
with col_main:
    col_left_pad, col_center, col_right_pad = st.columns([1, 2, 1])
    with col_center:
        #st.markdown("""<style> div.login-box h3 { text-align: center; color: #ff6347; } </style>""",
        #            unsafe_allow_html=True)
        #st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center;'>Chọn vai trò đăng nhập:</h5>", unsafe_allow_html=True)
        vai_tro = st.radio("Chọn vai trò đăng nhập:", ["👩‍🎓 Học sinh", "👨‍🏫 Giáo viên", "⚙️ Quản trị"], horizontal=True,
                           label_visibility="collapsed")

        # -------------------------------------------------------------
        # FORM ĐĂNG NHẬP HỌC SINH (ĐÃ SỬA)
        # -------------------------------------------------------------
        if vai_tro == "👩‍🎓 Học sinh":
            st.subheader("📘 Đăng nhập Học sinh")
            ma_hoc_sinh = st.text_input("🔑 Mã học sinh (VD: HS0001)", key="hs_ma", max_chars=10)
            mat_khau = st.text_input("🔒 Mã PIN (4 chữ số)", type="password", key="hs_mk", max_chars=4)

            if st.button("Đăng nhập Học sinh", width='stretch'):
                res = supabase.table("hoc_sinh").select("id, ho_ten, lop_id").eq("ma_hoc_sinh", ma_hoc_sinh.strip()).eq(
                    "mat_khau", mat_khau.strip()).execute()

                if res.data:
                    hs = res.data[0]
                    st.session_state.clear() # Xóa session cũ trước khi set mới
                    st.session_state["role"] = "student"
                    st.session_state["hoc_sinh_id"] = hs["id"]
                    st.session_state["ho_ten"] = hs["ho_ten"]
                    # --- THÊM DÒNG NÀY ---
                    st.session_state["hoc_sinh_lop_id"] = hs.get("lop_id")  # Lưu UUID của lớp
                    # ---------------------
                    lop_id = hs.get("lop_id")
                    current_lop = None # Khởi tạo là None
                    current_ten_lop = "Chưa xếp lớp"

                    if lop_id:
                        lop_res = supabase.table("lop_hoc").select("khoi, ten_lop").eq("id", lop_id).maybe_single().execute() # Thêm maybe_single()
                        if lop_res.data:
                            # Chỉ lấy khoi nếu nó không None
                            khoi_value = lop_res.data.get("khoi")
                            if khoi_value is not None:
                                current_lop = khoi_value # Giữ nguyên kiểu dữ liệu (có thể là số)
                                current_ten_lop = lop_res.data.get("ten_lop", "Không có tên lớp")
                            else:
                                st.warning(f"Lớp học (ID: {lop_id}) chưa được gán Khối.") # Thông báo nếu khối là NULL
                        # Không cần else ở đây, current_lop vẫn là None nếu không tìm thấy lớp

                    st.session_state["lop"] = current_lop # Lưu giá trị khoi (hoặc None)
                    st.session_state["ten_lop"] = current_ten_lop

                    # Tải danh sách MÔN HỌC chỉ khi có thông tin Khối hợp lệ
                    subject_map = {}
                    if current_lop is not None: # Kiểm tra current_lop không phải None
                        try:
                            # Đảm bảo chuyển đổi sang int an toàn
                            lop_int = int(current_lop)
                            # Gọi hàm get_subjects_by_grade với số nguyên
                            subjects_res = get_subjects_by_grade(lop_int)
                            if subjects_res:
                                # Tạo map {Tên Môn: ID Môn}
                                subject_map = {s['ten_mon']: str(s['id']) for s in subjects_res}
                        except ValueError:
                             st.error(f"Lỗi: Giá trị Khối '{current_lop}' không phải là số hợp lệ.") # Báo lỗi nếu không chuyển sang int được
                        except Exception as e:
                            st.error(f"Lỗi khi tải danh sách môn học: {e}") # Báo lỗi chung

                    # Lưu subject_map (có thể rỗng nếu có lỗi hoặc không tìm thấy môn)
                    st.session_state["subject_map"] = subject_map
                    st.session_state["chu_de_data"] = [] # Luôn khởi tạo rỗng ở đây

                    # Chuyển trang sau khi xử lý xong
                    st.switch_page("pages/students.py")
                else:
                    st.error("❌ Sai mã học sinh hoặc mã PIN.")

        # -------------------------------------------------------------
        # FORM ĐĂNG NHẬP GIÁO VIÊN (Giữ nguyên)
        # -------------------------------------------------------------
        elif vai_tro == "👨‍🏫 Giáo viên":
            st.subheader("👨‍🏫 Đăng nhập Giáo viên")
            email = st.text_input("📧 Email giáo viên", key="gv_email")
            mat_khau = st.text_input("🔒 Mật khẩu", type="password", key="gv_mk")

            if st.button("Đăng nhập Giáo viên", width='stretch'):
                res = supabase.table("giao_vien").select("id, ho_ten, email").eq("email", email.strip()).eq("mat_khau",
                                                                                                            mat_khau.strip()).execute()
                if res.data:
                    gv = res.data[0]
                    st.session_state.clear()
                    st.session_state["role"] = "teacher"
                    st.session_state["giao_vien_id"] = gv["id"]
                    st.session_state["giao_vien_ten"] = gv["ho_ten"]
                    st.switch_page("pages/teachers.py")
                else:
                    st.error("❌ Email hoặc mật khẩu không đúng.")

        # -------------------------------------------------------------
        # FORM ĐĂNG NHẬP QUẢN TRỊ (Giữ nguyên)
        # -------------------------------------------------------------
        elif vai_tro == "⚙️ Quản trị":
            st.subheader("⚙️ Đăng nhập Quản trị")
            tk = st.text_input("👤 Tên đăng nhập (admin)", key="qt_tk")
            mk = st.text_input("🔒 Mật khẩu (admin)", type="password", key="qt_mk")

            if st.button("Đăng nhập Quản trị", width='stretch'):
                if tk == "admin" and mk == "admin":
                    st.session_state.clear()
                    st.session_state["role"] = "admin"
                    # Đảm bảo tên file admin là admin_main.py (nằm trong pages/)
                    st.switch_page("pages/admin_main.py")
                else:
                    st.error("❌ Tên đăng nhập hoặc mật khẩu không đúng.")

        st.caption("Phiên bản thử nghiệm AI Tutor dành cho học sinh Tiểu học.")
        st.caption("Phát triển bởi: Lâm Đạo Chương - Trường Tiểu học Dương Đông 2")
        st.caption("Địa chỉ: Dương Đông - Phú Quốc - An Giang. Phone: 0942111500")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# CỘT GIỚI THIỆU (CỘT PHỤ) (Giữ nguyên)
# -------------------------------------------------------------
with col_intro:
    if vai_tro == "👩‍🎓 Học sinh":
        st.markdown("## Thông tin")
        with st.expander("ℹ️ Giới thiệu AI Tutor", expanded=True):
            st.markdown("""
            **AI Tutor** là hệ thống học tập thông minh hỗ trợ:
            - Theo dõi tiến độ học sinh
            - Gợi ý bài học & ôn tập cá nhân hóa
            - Tự động chấm điểm & đánh giá năng lực
            """)
    else:
        st.empty()