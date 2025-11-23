# ===============================================
# 👨‍💼 Trang quản trị Chính - admin_main.py (ĐÃ SỬA LỖI GỌI HÀM RENDER)
# ===============================================
import streamlit as st
import datetime
import pandas as pd
import io
import uuid

# Import các hàm cần thiết để lọc dữ liệu
from backend.data_service import get_all_school_years, get_current_school_year

# Import các module con
try:
    from pages.admin_pages import crud_utils
    from pages.admin_pages import manage_teachers
    from pages.admin_pages import manage_classes
    from pages.admin_pages import manage_students
    from pages.admin_pages import manage_subjects
    from pages.admin_pages import manage_topics
    from pages.admin_pages import manage_lessons
    from pages.admin_pages import manage_videos
    from pages.admin_pages import manage_questions
    from pages.admin_pages import manage_assignments
    from pages.admin_pages import manage_promotion
except ImportError as e:
    st.error(
        f"Lỗi import module quản lý: {e}. Đảm bảo cấu trúc thư mục là 'pages/admin_pages/...' và file này nằm trong 'pages/'.")
    st.stop()

# Import supabase client từ backend
try:
    from backend.supabase_client import supabase
except ImportError:
    st.error("Lỗi: Không tìm thấy backend.supabase_client. Đảm bảo cấu trúc thư mục backend đúng.")
    st.stop()

st.set_page_config(page_title="AI Tutor - Quản trị", page_icon="👨‍💼", layout="wide")

# CSS (Giữ nguyên)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;} 
    div[data-testid="stHorizontalBlock"] > div:first-child > div {
        display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child > div h1 { text-align: center; }
    .stDataFrame { overflow-x: auto; }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", width='stretch')
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", width='stretch')

# 🔐 Kiểm tra đăng nhập
if "role" not in st.session_state or st.session_state["role"] != "admin":
    st.warning("⚠️ Vui lòng đăng nhập với vai trò Quản trị.")
    if st.button("Về trang đăng nhập"): st.switch_page("app.py")
    st.stop()

# ===============================================
# BỐ CỤC 2 CỘT (Info | Nội dung)
# ===============================================
col1, col2 = st.columns([1, 5])

# -----------------------------------------------
# CỘT 1: THÔNG TIN ADMIN & ĐĂNG XUẤT
# -----------------------------------------------
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1077/1077063.png", width=120)
    st.title("Admin")
    st.divider()
    if st.button("🔓 Đăng xuất", width='stretch', type="primary"):
        st.session_state.clear();
        st.switch_page("app.py")

# -----------------------------------------------
# CỘT 2: NỘI DUNG CHÍNH (Menu chọn & Gọi hàm con)
# -----------------------------------------------
with col2:
    st.title("👨‍💼 Quản trị hệ thống AI Tutor")

    # === TẢI VÀ LƯU NĂM HỌC HIỆN TẠI (GLOBAL FILTER) ===
    all_years = get_all_school_years()
    current_year = get_current_school_year()

    selected_year = current_year

    if all_years:
        default_index = all_years.index(current_year) if current_year in all_years else 0

        selected_year = st.selectbox(
            "📅 **Năm học đang xem:**",
            all_years,
            index=default_index,
            key="global_selected_school_year"  # Ghi vào session state
        )
    else:
        st.warning("Chưa có dữ liệu năm học.")

    st.markdown("---")
    # === KẾT THÚC GLOBAL FILTER ===

    menu = st.radio(
        "Chọn khu vực quản lý:",
        ["👩‍🏫 Giáo viên", "🏫 Lớp học", "👧 Học sinh", "📘 Môn học", "📚 Chủ đề", "📝 Bài học", "🎥 Video", "❓ Câu hỏi",
         "🧑‍🏫 Phân công", "🎓 Lên lớp & Năm học"],
        horizontal=True
    )
    st.divider()

    # KHÔNG CẦN TẢI DỮ LIỆU TOÀN CỤC Ở ĐÂY NỮA
    # (Trừ Môn học, vì nó là Master data và không đổi)
    mon_hoc_options_global = {}
    try:
        mon_hoc_df_global = crud_utils.load_data("mon_hoc")
        mon_hoc_options_global = {row["ten_mon"]: str(row["id"]) for _, row in
                                  mon_hoc_df_global.iterrows()} if not mon_hoc_df_global.empty else {}
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu Môn học ban đầu: {e}")
        st.stop()

    # =============================================================
    # GỌI HÀM RENDER (ĐÃ CẬP NHẬT TẤT CẢ CÁC LỆNH GỌI)
    # =============================================================
    try:
        if menu == "👩‍🏫 Giáo viên":
            manage_teachers.render()  # Tự tải
        elif menu == "🏫 Lớp học":
            manage_classes.render()  # Tự tải
        elif menu == "👧 Học sinh":
            manage_students.render()  # Tự tải
        elif menu == "📘 Môn học":
            manage_subjects.render()  # Tự tải

        # === KHU VỰC SỬA LỖI ===
        # Các module này không cần truyền DataFrame vào nữa, chúng sẽ tự tải

        elif menu == "📚 Chủ đề":
            # Lỗi của bạn ở đây. Hàm render() đã tái cấu trúc không nhận tham số
            manage_topics.render()

        elif menu == "📝 Bài học":
            # Lỗi TypeError ở đây. Hàm render() đã tái cấu trúc không nhận DataFrame
            manage_lessons.render(mon_hoc_options=mon_hoc_options_global)  # Chỉ truyền Môn học

        elif menu == "🎥 Video":
            # Lỗi TypeError (trước đó) ở đây.
            manage_videos.render()

        elif menu == "❓ Câu hỏi":
            # Lỗi KeyError (trước đó) ở đây.
            manage_questions.render(mon_hoc_options=mon_hoc_options_global)  # Chỉ truyền Môn học

        # === KẾT THÚC KHU VỰC SỬA LỖI ===

        elif menu == "🧑‍🏫 Phân công":
            manage_assignments.render()  # Tự tải
        elif menu == "🎓 Lên lớp & Năm học":
            manage_promotion.render()  # Tự tải

    except AttributeError as attr_error:
        st.error(
            f"Lỗi thuộc tính khi hiển thị mục '{menu}': {attr_error}. Có thể do module chưa được import đúng hoặc thiếu hàm render().")
        st.exception(attr_error)
    except Exception as render_error:
        st.error(f"Đã xảy ra lỗi khi hiển thị mục '{menu}': {render_error}")
        st.exception(render_error)