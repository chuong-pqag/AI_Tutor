# ===============================================
# 👨‍💼 Trang quản trị Chính - admin_main.py
# (BẢN FINAL: Thêm chức năng đổi Avatar Admin)
# ===============================================
import streamlit as st
import datetime
import pandas as pd
import io
import uuid
import os

# Import các hàm cần thiết
from backend.data_service import get_all_school_years, get_current_school_year
from backend.utils import get_available_avatars, get_img_as_base64
from backend.supabase_client import supabase
import warnings

# --- THÊM ĐOẠN NÀY ĐỂ TẮT CẢNH BÁO ---
# Tắt cảnh báo use_column_width (do lệch phiên bản)
warnings.filterwarnings("ignore", message=".*use_column_width.*")
# -------------------------------------

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
    st.error(f"Lỗi import module quản lý: {e}")
    st.stop()

st.set_page_config(page_title="AI Tutor - Quản trị", page_icon="👨‍💼", layout="wide")

# CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;} 
    div[data-testid="stHorizontalBlock"] > div:first-child > div {
        display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .stDataFrame { overflow-x: auto; }

    /* Button Cam đồng bộ */
    .stButton>button { 
        background-color: #ff6600; color: #ffffff; font-weight: bold; border: none; border-radius: 8px; transition: background-color 0.3s; 
    }
    .stButton>button:hover { background-color: #e65c00; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", use_column_width=True)
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", use_column_width=True)

# 🔐 Kiểm tra đăng nhập
if "role" not in st.session_state or st.session_state["role"] != "admin":
    st.warning("⚠️ Vui lòng đăng nhập với vai trò Quản trị.")
    if st.button("Về trang đăng nhập", type="primary"): st.switch_page("app.py")
    st.stop()

# ===============================================
# BỐ CỤC 2 CỘT (Info | Nội dung)
# ===============================================
col1, col2 = st.columns([1, 5])

# -----------------------------------------------
# CỘT 1: THÔNG TIN ADMIN & ĐỔI AVATAR
# -----------------------------------------------
with col1:
    # 1. Lấy Avatar từ cau_hinh_chung
    try:
        res = supabase.table("cau_hinh_chung").select("value").eq("key", "admin_avatar").maybe_single().execute()
        current_avatar_file = res.data.get("value") if res.data else "default.png"
    except:
        current_avatar_file = "default.png"

    # 2. Xử lý hiển thị
    # Lưu ý: Bạn cần tạo thư mục data/avatar/ADMIN và chép ảnh vào
    avatar_path = os.path.join("data", "avatar", "ADMIN", current_avatar_file)

    if os.path.exists(avatar_path):
        img_b64 = get_img_as_base64(avatar_path)
        img_src = f"data:image/png;base64,{img_b64}"
    else:
        # Fallback ảnh online nếu chưa có file local
        img_src = "https://cdn-icons-png.flaticon.com/512/1077/1077063.png"

    # 3. HTML Profile
    st.markdown(f"""
        <style>
            .admin-profile {{
                display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 15px;
            }}
            .admin-img {{
                border-radius: 50%; border: 3px solid #ff6600; padding: 2px;
                width: 130px; height: 130px; object-fit: cover; margin-bottom: 10px;
            }}
            .admin-name {{
                font-family: 'Times New Roman'; font-size: 20px; font-weight: bold; color: #333;
            }}
        </style>
        <div class="admin-profile">
            <img src="{img_src}" class="admin-img">
            <div class="admin-name">Administrator</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 4. Chức năng Đổi Avatar
    with st.expander("🖼️ Đổi Avatar"):
        # Hàm này sẽ quét thư mục data/avatar/ADMIN
        avatars = get_available_avatars("ADMIN")

        if not avatars:
            st.warning("Chưa có ảnh trong data/avatar/ADMIN")
        else:
            cols = st.columns(3)
            for i, file_name in enumerate(avatars):
                with cols[i % 3]:
                    file_path = os.path.join("data", "avatar", "ADMIN", file_name)
                    st.image(file_path, use_column_width=True)

                    if file_name == current_avatar_file:
                        st.button("✅", key=f"adm_avt_curr_{i}", disabled=True)
                    else:
                        if st.button("Chọn", key=f"adm_avt_pick_{i}"):
                            # Cập nhật vào bảng cau_hinh_chung
                            try:
                                supabase.table("cau_hinh_chung").upsert(
                                    {"key": "admin_avatar", "value": file_name, "description": "Avatar Admin"}
                                ).execute()
                                st.success("Đã đổi!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")

    if st.button("🔓 Đăng xuất", use_container_width=True, type="primary"):
        st.session_state.clear();
        st.switch_page("app.py")

# -----------------------------------------------
# CỘT 2: NỘI DUNG CHÍNH
# -----------------------------------------------
with col2:
    st.title("👨‍💼 Quản trị hệ thống AI Tutor")

    # === GLOBAL FILTER ===
    all_years = get_all_school_years()
    current_year = get_current_school_year()
    selected_year = current_year

    if all_years:
        default_index = all_years.index(current_year) if current_year in all_years else 0
        selected_year = st.selectbox(
            "📅 **Năm học đang xem:**",
            all_years,
            index=default_index,
            key="global_selected_school_year"
        )
    else:
        st.warning("Chưa có dữ liệu năm học.")

    st.markdown("---")

    # === MENU QUẢN LÝ ===
    menu = st.radio(
        "Chọn khu vực quản lý:",
        ["👩‍🏫 Giáo viên", "🏫 Lớp học", "👧 Học sinh", "📘 Môn học", "📚 Chủ đề", "📝 Bài học", "🎥 Video", "❓ Câu hỏi",
         "🧑‍🏫 Phân công", "🎓 Lên lớp & Năm học"],
        horizontal=True
    )
    st.divider()

    # Tải options môn học toàn cục (cho các module con)
    mon_hoc_options_global = {}
    try:
        mon_hoc_df_global = crud_utils.load_data("mon_hoc")
        mon_hoc_options_global = {row["ten_mon"]: str(row["id"]) for _, row in
                                  mon_hoc_df_global.iterrows()} if not mon_hoc_df_global.empty else {}
    except:
        pass

    # === RENDER MODULES ===
    try:
        if menu == "👩‍🏫 Giáo viên":
            manage_teachers.render()
        elif menu == "🏫 Lớp học":
            manage_classes.render()
        elif menu == "👧 Học sinh":
            manage_students.render()
        elif menu == "📘 Môn học":
            manage_subjects.render()
        elif menu == "📚 Chủ đề":
            manage_topics.render()
        elif menu == "📝 Bài học":
            manage_lessons.render(mon_hoc_options=mon_hoc_options_global)
        elif menu == "🎥 Video":
            manage_videos.render()
        elif menu == "❓ Câu hỏi":
            manage_questions.render(mon_hoc_options=mon_hoc_options_global)
        elif menu == "🧑‍🏫 Phân công":
            manage_assignments.render()
        elif menu == "🎓 Lên lớp & Năm học":
            manage_promotion.render()

    except Exception as render_error:
        st.error(f"Đã xảy ra lỗi khi hiển thị mục '{menu}': {render_error}")