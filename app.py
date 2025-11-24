# ===============================================
# 📱 Trang Đăng nhập - app.py
# (BẢN FINAL: Căn giữa Radio Buttons + Giao diện Card)
# ===============================================
import streamlit as st
from backend.supabase_client import supabase
from backend.data_service import get_subjects_by_grade

# =============================================================
# 1. CẤU HÌNH & CSS TÙY BIẾN (THEME)
# =============================================================
st.set_page_config(
    page_title="AI Tutor - Đăng nhập",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Tùy chỉnh nâng cao
st.markdown("""
    <style>
    /* Ẩn thành phần mặc định */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Container chính (Card) */
    div[data-testid="column"] {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #2c3e50;
        text-align: center;
    }

    /* Input fields */
    .stTextInput>div>div {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 5px 10px;
    }
    .stTextInput>div>div:focus-within {
        border-color: #ff6600;
        box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.2);
    }

    /* --- CĂN GIỮA RADIO BUTTON (SỬA ĐỔI QUAN TRỌNG) --- */
    div[data-testid="stRadio"] {
        display: flex;
        justify-content: center; /* Căn giữa container lớn */
        width: 100%;
    }

    div[data-testid="stRadio"] > div {
        display: flex;
        justify-content: center; /* Căn giữa các nút bên trong */
        gap: 15px;
        background-color: #f1f3f5; /* Màu nền xám nhạt */
        padding: 8px 20px;
        border-radius: 50px; /* Bo tròn hình viên thuốc */
        width: auto; /* Co giãn theo nội dung */
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); /* Đổ bóng chìm */
    }

    /* Chỉnh lại label của radio cho đẹp hơn */
    div[data-testid="stRadio"] label {
        font-weight: 500;
        cursor: pointer;
    }
    /* -------------------------------------------------- */

    /* Nút bấm màu cam */
    .stButton>button { 
        background-color: #ff6600; 
        color: #ffffff; 
        font-weight: bold; 
        font-size: 16px;
        border: none; 
        border-radius: 12px; 
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%; 
        box-shadow: 0 4px 6px rgba(255, 102, 0, 0.3);
    }
    .stButton>button:hover { 
        background-color: #e65c00; 
        transform: translateY(-2px); 
        box-shadow: 0 6px 8px rgba(255, 102, 0, 0.4);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================
# 2. BANNER
# =============================================================
st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
try:
    st.image("data/banner.jpg", use_container_width=True)
except Exception:
    st.markdown("<h1>🎓 AI TUTOR</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# =============================================================
# 3. FORM ĐĂNG NHẬP
# =============================================================

with st.container():
    st.markdown("<h4 style='text-align: center; color: #666; margin-bottom: 5px;'>Chào mừng bạn quay trở lại! 👋</h4>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; font-size: 14px; color: #888; margin-bottom: 20px;'>Vui lòng chọn vai trò để tiếp tục</p>",
        unsafe_allow_html=True)

    # Selector Vai trò
    vai_tro = st.radio(
        "Vai trò:",
        ["👩‍🎓 Học sinh", "👨‍🏫 Giáo viên", "⚙️ Quản trị"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # --- LOGIC ĐĂNG NHẬP ---

    # 1. HỌC SINH
    if vai_tro == "👩‍🎓 Học sinh":
        col_user, col_pass = st.columns(2)

        ma_hoc_sinh = st.text_input("🔑 Mã học sinh", placeholder="Ví dụ: HS0001", key="hs_ma", max_chars=10)
        mat_khau = st.text_input("🔒 Mã PIN (4 số)", type="password", placeholder="****", key="hs_mk", max_chars=4)

        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

        if st.button("Đăng nhập ngay 🚀", key="btn_login_hs", width='stretch'):
            with st.spinner("Đang kiểm tra thông tin..."):
                try:
                    res = supabase.table("hoc_sinh").select("id, ho_ten, lop_id").eq("ma_hoc_sinh",
                                                                                     ma_hoc_sinh.strip()).eq("mat_khau",
                                                                                                             mat_khau.strip()).execute()

                    if res.data:
                        hs = res.data[0]
                        st.session_state.clear()
                        st.session_state["role"] = "student"
                        st.session_state["hoc_sinh_id"] = hs["id"]
                        st.session_state["ho_ten"] = hs["ho_ten"]
                        st.session_state["hoc_sinh_lop_id"] = hs.get("lop_id")

                        lop_id = hs.get("lop_id")
                        current_lop = None
                        current_ten_lop = "Chưa xếp lớp"

                        if lop_id:
                            lop_res = supabase.table("lop_hoc").select("khoi, ten_lop").eq("id",
                                                                                           lop_id).maybe_single().execute()
                            if lop_res.data:
                                current_lop = lop_res.data.get("khoi")
                                current_ten_lop = lop_res.data.get("ten_lop", "Không có tên lớp")

                        st.session_state["lop"] = current_lop
                        st.session_state["ten_lop"] = current_ten_lop

                        subject_map = {}
                        if current_lop is not None:
                            try:
                                subjects_res = get_subjects_by_grade(int(current_lop))
                                if subjects_res:
                                    subject_map = {s['ten_mon']: str(s['id']) for s in subjects_res}
                            except Exception:
                                pass

                        st.session_state["subject_map"] = subject_map
                        st.switch_page("pages/students.py")
                    else:
                        st.error("❌ Sai mã số hoặc mã PIN.")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

    # 2. GIÁO VIÊN
    elif vai_tro == "👨‍🏫 Giáo viên":
        email = st.text_input("📧 Email", placeholder="nguyenvana@email.com", key="gv_email")
        mat_khau = st.text_input("🔒 Mật khẩu", type="password", key="gv_mk")

        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

        if st.button("Đăng nhập Giáo viên", key="btn_login_gv", width='stretch'):
            try:
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
                    st.error("❌ Sai email hoặc mật khẩu.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # 3. QUẢN TRỊ
    elif vai_tro == "⚙️ Quản trị":
        tk = st.text_input("👤 Tài khoản", key="qt_tk")
        mk = st.text_input("🔒 Mật khẩu", type="password", key="qt_mk")

        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

        if st.button("Đăng nhập Quản trị", key="btn_login_admin", width='stretch'):
            if tk == "admin" and mk == "admin":
                st.session_state.clear()
                st.session_state["role"] = "admin"
                st.switch_page("pages/admin_main.py")
            else:
                st.error("❌ Sai thông tin đăng nhập.")

# =============================================================
# 4. FOOTER
# =============================================================
st.markdown("""
    <div style='text-align: center; margin-top: 30px; color: #888; font-size: 12px;'>
        <p>AI Tutor - Hệ thống học tập thông minh</p>
        <p>Phát triển bởi: Lâm Đạo Chương • Phone: 0942111500</p>
    </div>
""", unsafe_allow_html=True)