# ===============================================
# 📘 Trang học sinh - students.py (CẬP NHẬT: THÔNG BÁO 2 CẤP)
# ===============================================
import streamlit as st
import pandas as pd
from backend.data_service import (
    get_student,
    get_announcements_for_student  # Hàm này đã được update ở Bước 2
)

# Import UI modules
from pages.student_pages import ui_info
from pages.student_pages import ui_dashboard
from pages.student_pages import ui_learning
from pages.student_pages import ui_history

st.set_page_config(page_title="AI Tutor - Học sinh", page_icon="📘", layout="wide")

# CSS
st.markdown("""
    <style>
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] {display: none;}
    .student-name-title { font-family: 'Times New Roman'; font-size: 14pt; font-weight: bold; text-align: center; }
    div.stContainer { border: 1px solid #f0f2f6; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", width='stretch')
except:
    pass

if "hoc_sinh_id" not in st.session_state:
    st.switch_page("app.py")

# Tải dữ liệu session
hoc_sinh_id = st.session_state["hoc_sinh_id"]
ho_ten = st.session_state["ho_ten"]
current_lop = st.session_state.get("lop")
current_ten_lop = st.session_state.get("ten_lop", "Chưa xếp lớp")
subject_map = st.session_state.get("subject_map", {})


# ===============================================
# HÀM HELPER ĐỂ HIỂN THỊ DANH SÁCH RÚT GỌN
# ===============================================
def render_announcement_list(messages, title, empty_msg):
    st.markdown(f"###### {title}")

    if not messages:
        st.caption(f"*{empty_msg}*")
        return

    # 1. Hiển thị 2 tin mới nhất
    latest_msgs = messages[:2]
    for msg in latest_msgs:
        gv_name = msg.get('giao_vien', {}).get('ho_ten', 'Giáo viên')
        ngay = pd.to_datetime(msg.get('created_at')).strftime('%d/%m')

        with st.container():
            st.markdown(f"**{msg['tieu_de']}**")
            st.caption(f"👨‍🏫 {gv_name} | 📅 {ngay}")
            st.markdown(f"{msg['noi_dung']}")

    # 2. Nếu còn tin cũ hơn -> Nút xem thêm
    older_msgs = messages[2:]
    if older_msgs:
        with st.expander(f"📂 Xem thêm ({len(older_msgs)} tin cũ)"):
            for msg in older_msgs:
                gv_name = msg.get('giao_vien', {}).get('ho_ten', 'GV')
                ngay = pd.to_datetime(msg.get('created_at')).strftime('%d/%m')
                st.markdown(f"---")
                st.markdown(f"**{msg['tieu_de']}** ({ngay})")
                st.markdown(msg['noi_dung'])


# ===============================================
# LAYOUT 3 CỘT
# ===============================================
col_info, col_main, col_announce = st.columns([1, 4, 1.5])

# CỘT 1: INFO
with col_info:
    ui_info.render_student_info(hoc_sinh_id, ho_ten, current_lop, current_ten_lop)

# CỘT 2: MAIN
with col_main:
    st.subheader(f"Chào mừng bạn quay trở lại! 👋")
    st.markdown("---")

    if current_lop is None or not subject_map:
        st.warning("Hệ thống chưa sẵn sàng (Lỗi Lớp/Môn).")
        st.stop()

    tab_learning, tab_history = st.tabs(["💡 Bài học & Luyện tập", "📜 Lịch sử học tập"])

    with tab_learning:
        if st.session_state.get('viewing_topic', False):
            ui_learning.render_content_detail(hoc_sinh_id, current_lop)
        else:
            ui_dashboard.render_dashboard(hoc_sinh_id, current_lop, subject_map)

    with tab_history:
        ui_history.render_history(hoc_sinh_id)

# CỘT 3: THÔNG BÁO (CẬP NHẬT)
with col_announce:
    st.subheader("📣 Thông báo")

    # Lấy lop_id
    student_data = get_student(hoc_sinh_id)
    student_lop_id = student_data.get('lop_id') if student_data else None

    if student_lop_id:
        # Gọi hàm lấy 2 loại thông báo (Đã update ở Backend)
        data = get_announcements_for_student(student_lop_id, hoc_sinh_id, limit=10)

        general_msgs = data.get('general', [])
        private_msgs = data.get('private', [])

        # 1. THÔNG BÁO RIÊNG (Ưu tiên hiển thị trước nếu có)
        if private_msgs:
            st.info("💌 **Có tin nhắn riêng cho bạn!**")
            render_announcement_list(private_msgs, "Của riêng bạn:", "Không có tin nhắn riêng.")
            st.divider()

        # 2. THÔNG BÁO CHUNG
        render_announcement_list(general_msgs, "Thông báo lớp:", "Lớp chưa có thông báo mới.")

    else:
        st.warning("Chưa cập nhật thông tin lớp.")