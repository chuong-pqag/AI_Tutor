# ===============================================
# 📘 Trang học sinh - students.py (CẬP NHẬT LAYOUT 3 CỘT)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
from backend.supabase_client import supabase
from backend.data_service import (
    get_student,
    get_learning_paths,
    get_topic_by_id,
    get_announcements_for_student  # <-- THÊM MỚI (để dùng ở col3)
)

# --- KHAI BÁO IMPORT CÁC MODULE CON ---
# (Sửa lỗi import bằng cách thêm 'pages.')
from pages.student_pages import ui_info
from pages.student_pages import ui_dashboard
from pages.student_pages import ui_learning
from pages.student_pages import ui_history

# --- KẾT THÚC KHAI BÁO ---

st.set_page_config(page_title="AI Tutor - Học sinh", page_icon="📘", layout="wide")

# CSS (Giữ nguyên)
st.markdown("""
    <style>
    /* ... (CSS giữ nguyên) ... */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    div[data-testid="stHorizontalBlock"] > div:first-child > div { display: flex; flex-direction: column; align-items: center; text-align: center; }
    div[data-testid="stHorizontalBlock"] > div:first-child > div h1, div[data-testid="stHorizontalBlock"] > div:first-child > div h3 { text-align: center; }
    .student-name-title { font-family: 'Times New Roman', Times, serif; font-size: 14pt !important; font-weight: bold; color: #31333F; padding-bottom: 0.5rem; margin-block-start: 0; margin-block-end: 0; text-align: center; }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", width='stretch')
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", width='stretch')

# ===============================================
# KIỂM TRA PHIÊN ĐĂNG NHẬP
# ===============================================
if "hoc_sinh_id" not in st.session_state:
    st.warning("⚠️ Vui lòng đăng nhập từ trang chủ.")
    if st.button("Về trang đăng nhập"): st.switch_page("app.py")
    st.stop()

# Tải dữ liệu từ session
hoc_sinh_id = st.session_state["hoc_sinh_id"]
ho_ten = st.session_state["ho_ten"]
current_lop = st.session_state.get("lop")
current_ten_lop = st.session_state.get("ten_lop", "Chưa xếp lớp")
subject_map = st.session_state.get("subject_map", {})  # Map môn học

# ===============================================
# (ĐÃ THAY ĐỔI) BỐ CỤC 3 CỘT CHÍNH
# ===============================================
col_info, col_main, col_announce = st.columns([1, 4, 1.5])  # Tỷ lệ [Info, Main, Announce]

# CỘT 1: THÔNG TIN HỌC SINH & ĐIỀU HƯỚNG
with col_info:
    ui_info.render_student_info(hoc_sinh_id, ho_ten, current_lop, current_ten_lop)

# CỘT 2: NỘI DUNG CHÍNH (Tabs học tập)
with col_main:
    st.title(f"Chào mừng bạn quay trở lại! 👋")
    st.markdown("---")

    # Kiểm tra điều kiện tiên quyết
    if current_lop is None or not subject_map:
        st.warning("⚠️ Hệ thống chưa sẵn sàng. Vui lòng kiểm tra thông tin lớp học và môn học.")
        st.stop()

    tab_learning, tab_history = st.tabs(["💡 Bài học & Luyện tập", "📜 Lịch sử học tập"])

    # --- TAB 1: BÀI HỌC & LUYỆN TẬP ---
    with tab_learning:
        if st.session_state.get('viewing_topic', False):
            ui_learning.render_content_detail(
                hoc_sinh_id=hoc_sinh_id,
                current_lop=current_lop
            )
        else:
            ui_dashboard.render_dashboard(
                hoc_sinh_id=hoc_sinh_id,
                current_lop=current_lop,
                subject_map=subject_map
            )

    # --- TAB 2: LỊCH SỬ HỌC TẬP ---
    with tab_history:
        ui_history.render_history(hoc_sinh_id)

# ===============================================
# (THÊM MỚI) CỘT 3: THÔNG BÁO
# ===============================================
with col_announce:
    st.subheader("📣 Thông báo")

    # Lấy lop_id của học sinh (cần cho hàm get_announcements_for_student)
    student_data = get_student(hoc_sinh_id)
    student_lop_id = student_data.get('lop_id') if student_data else None

    announcements = []
    if student_lop_id:
        # Lấy 5 thông báo mới nhất
        announcements = get_announcements_for_student(student_lop_id, limit=5)

    if not announcements:
        st.info("Chưa có thông báo nào mới từ giáo viên của bạn.")
    else:
        for ann in announcements:
            gv_name = ann.get('giao_vien', {}).get('ho_ten', 'Giáo viên')
            ngay_gui = pd.to_datetime(ann.get('created_at')).strftime('%d/%m/%Y')

            with st.container(border=True):
                st.markdown(f"**{ann.get('tieu_de')}**")
                st.caption(f"Từ: {gv_name} | Ngày: {ngay_gui}")
                st.markdown(f"{ann.get('noi_dung')}")