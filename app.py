# ===============================================
# 📱 Trang Đăng nhập - app.py (FINAL FIXED)
# ===============================================
import streamlit as st
from backend.supabase_client import supabase
from backend.data_service import get_subjects_by_grade
import warnings
import os

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# =============================================================
# 1. CẤU HÌNH TRANG
# =============================================================
st.set_page_config(
    page_title="AI Tutor - Đăng nhập",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# === LOGIC CHUYỂN TRANG (ĐÃ SỬA: BỎ TRY/EXCEPT) ===
# Logic này sẽ chạy ngay khi app reload sau khi đăng nhập thành công
if "role" in st.session_state:
    role = st.session_state["role"]

    # KHÔNG ĐƯỢC DÙNG TRY...EXCEPT Ở ĐÂY
    # Hãy để Streamlit tự do ngắt kết nối để chuyển trang
    if role == "student":
        st.switch_page("pages/students.py")
    elif role == "teacher":
        st.switch_page("pages/teachers.py")
    elif role == "admin":
        st.switch_page("pages/admin_main.py")


# =============================================================
# 2. HÀM XỬ LÝ ĐĂNG NHẬP (CALLBACKS)
# =============================================================
def login_student():
    # Lấy dữ liệu từ widget key
    ma = st.session_state.hs_ma
    mk = st.session_state.hs_mk

    try:
        res = supabase.table("hoc_sinh").select("id, ho_ten, lop_id").eq("ma_hoc_sinh", ma.strip()).eq("mat_khau",
                                                                                                       mk.strip()).execute()

        if res.data:
            hs = res.data[0]
            # Cập nhật Session State
            st.session_state["role"] = "student"
            st.session_state["hoc_sinh_id"] = hs["id"]
            st.session_state["ho_ten"] = hs["ho_ten"]
            st.session_state["hoc_sinh_lop_id"] = hs.get("lop_id")

            # Lấy thông tin lớp
            lop_id = hs.get("lop_id")
            if lop_id:
                lop_res = supabase.table("lop_hoc").select("khoi, ten_lop").eq("id", lop_id).maybe_single().execute()
                if lop_res.data:
                    st.session_state["lop"] = lop_res.data.get("khoi")
                    st.session_state["ten_lop"] = lop_res.data.get("ten_lop")

                    # Lấy môn học
                    try:
                        subs = get_subjects_by_grade(int(lop_res.data.get("khoi")))
                        st.session_state["subject_map"] = {s["ten_mon"]: str(s["id"]) for s in subs}
                    except:
                        pass

            # Hết hàm này -> Streamlit tự rerun -> Gặp logic chuyển trang ở đầu file -> OK
        else:
            st.error("❌ Sai mã học sinh hoặc mã PIN.")
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")


def login_teacher():
    email = st.session_state.gv_email
    mk = st.session_state.gv_mk
    try:
        res = supabase.table("giao_vien").select("id, ho_ten").eq("email", email.strip()).eq("mat_khau",
                                                                                             mk.strip()).execute()
        if res.data:
            gv = res.data[0]
            st.session_state["role"] = "teacher"
            st.session_state["giao_vien_id"] = gv["id"]
            st.session_state["giao_vien_ten"] = gv["ho_ten"]
        else:
            st.error("❌ Sai email hoặc mật khẩu.")
    except Exception as e:
        st.error(f"Lỗi: {e}")


def login_admin():
    tk = st.session_state.qt_tk
    mk = st.session_state.qt_mk
    if tk == "admin" and mk == "admin":
        st.session_state["role"] = "admin"
    else:
        st.error("❌ Sai thông tin quản trị.")


# =============================================================
# 3. GIAO DIỆN & CSS
# =============================================================
st.markdown("""
    <style>
    [data-testid="stSidebarNav"], [data-testid="stSidebar"], #MainMenu, footer {display: none;}
    .stApp {background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);}
    div[data-testid="column"] {background-color: white; padding: 2.5rem 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);}
    h1, h2, h3, h4 {font-family: 'Segoe UI', sans-serif; color: #2c3e50; text-align: center;}

    /* INPUT STYLE CLEAN */
    div[data-testid="stTextInput"] {border: none !important; background: transparent !important;}
    div[data-testid="stTextInput"] > div > div {background-color: white !important; border: 1px solid #ddd !important; border-radius: 10px !important; padding-left: 10px !important;}
    div[data-testid="stTextInput"] > div > div:focus-within {border-color: #ff6600 !important; box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.2) !important;}
    div[data-testid="stTextInput"] input {background-color: transparent !important; border: none !important; padding: 8px 0px !important;}
    div[data-testid="stTextInput"] button {border: none !important; background: transparent !important; margin-right: 5px !important;}

    /* BUTTON STYLE */
    .stButton>button {background: linear-gradient(to right, #ff6600, #ff8533); color: white; font-weight: bold; font-size: 16px; border: none; border-radius: 12px; padding: 0.7rem 1rem; width: 100%; margin-top: 15px; box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3);}
    .stButton>button:hover {transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 102, 0, 0.4); color: white;}
    </style>
""", unsafe_allow_html=True)

# BANNER
current_dir = os.path.dirname(os.path.abspath(__file__))
banner_path = os.path.join(current_dir, 'data', 'banner.jpg')
if os.path.exists(banner_path):
    st.image(banner_path, use_column_width=True)
else:
    st.markdown("<h1>🎓 AI TUTOR</h1>", unsafe_allow_html=True)

# FORM
with st.container():
    st.markdown("#### Chào mừng bạn quay trở lại! 👋")
    st.markdown("<p style='text-align: center; color: #888;'>Vui lòng chọn vai trò</p>", unsafe_allow_html=True)

    vai_tro = st.radio("Vai trò:", ["👩‍🎓 Học sinh", "👨‍🏫 Giáo viên", "⚙️ Quản trị"], horizontal=True,
                       label_visibility="collapsed")
    st.markdown("---")

    if vai_tro == "👩‍🎓 Học sinh":
        # Key ở đây khớp với session_state gọi trong hàm callback
        st.text_input("🔑 Mã học sinh", placeholder="Ví dụ: HS0001", key="hs_ma")
        st.text_input("🔒 Mã PIN (4 số)", type="password", key="hs_mk", max_chars=4)
        st.button("Đăng nhập ngay 🚀", on_click=login_student)

    elif vai_tro == "👨‍🏫 Giáo viên":
        st.text_input("📧 Email", key="gv_email")
        st.text_input("🔒 Mật khẩu", type="password", key="gv_mk")
        st.button("Đăng nhập Giáo viên", on_click=login_teacher)

    elif vai_tro == "⚙️ Quản trị":
        st.text_input("👤 Tài khoản", key="qt_tk")
        st.text_input("🔒 Mật khẩu", type="password", key="qt_mk")
        st.button("Đăng nhập Quản trị", on_click=login_admin)

# FOOTER
st.markdown(
    "<div style='text-align: center; margin-top: 30px; color: #888; font-size: 12px;'><p>AI Tutor - Hệ thống học tập thông minh</p></div>",
    unsafe_allow_html=True)