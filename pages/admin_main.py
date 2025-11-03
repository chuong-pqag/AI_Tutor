# ===============================================
# 👨‍💼 Trang quản trị Chính - admin_main.py (Nằm trong pages/)
# (Chịu trách nhiệm bố cục và điều hướng)
# ===============================================
import streamlit as st
import datetime
import pandas as pd
import io
import uuid

# 💥 THAY ĐỔI IMPORT: Chỉ rõ đường dẫn từ thư mục gốc 'pages'
try:
    # Giả định thư mục 'admin_pages' nằm BÊN TRONG thư mục 'pages'
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
except ImportError as e:
    st.error(f"Lỗi import module quản lý: {e}. Đảm bảo cấu trúc thư mục là 'pages/admin_pages/...' và file này nằm trong 'pages/'.")
    st.stop()

# Import supabase client từ backend
try:
    from backend.supabase_client import supabase
except ImportError:
    st.error("Lỗi: Không tìm thấy backend.supabase_client. Đảm bảo cấu trúc thư mục backend đúng.")
    st.stop()


st.set_page_config(page_title="AI Tutor - Quản trị", page_icon="👨‍💼", layout="wide")

# CSS: Ẩn sidebar chính VÀ CANH GIỮA CỘT 1
# Bỏ ẩn SidebarNav để thấy tên trang
st.markdown("""
    <style>
    /* [data-testid="stSidebarNav"] {display: none;} */ /* Bỏ ẩn Nav */
    [data-testid="stSidebar"] {display: none;} /* Vẫn ẩn sidebar chính */
    div[data-testid="stHorizontalBlock"] > div:first-child > div {
        display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child > div h1 { text-align: center; }
    .stDataFrame { overflow-x: auto; } /* Chống tràn bảng */
    </style>
""", unsafe_allow_html=True)

try:
    # Điều chỉnh đường dẫn ảnh nếu cần, tính từ thư mục gốc AI_Tutor
    st.image("data/banner.jpg", use_container_width=True)
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", use_container_width=True)

# 🔐 Kiểm tra đăng nhập
if "role" not in st.session_state or st.session_state["role"] != "admin":
    st.warning("⚠️ Vui lòng đăng nhập với vai trò Quản trị.")
    if st.button("Về trang đăng nhập"): st.switch_page("app.py")
    st.stop()

# ===============================================
# BỐ CỤC 2 CỘT (Trái: Info | Phải: Nội dung)
# ===============================================
col1, col2 = st.columns([1, 5]) # Tỷ lệ 1:5

# -----------------------------------------------
# CỘT 1: THÔNG TIN ADMIN & ĐĂNG XUẤT
# -----------------------------------------------
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1077/1077063.png", width=120)
    st.title("Admin")
    st.divider()
    if st.button("🔓 Đăng xuất", width='stretch', type="primary"): # Đã sửa width
        st.session_state.clear(); st.switch_page("app.py")

# -----------------------------------------------
# CỘT 2: NỘI DUNG CHÍNH (Menu chọn & Gọi hàm con)
# -----------------------------------------------
with col2:
    st.title("👨‍💼 Quản trị hệ thống AI Tutor")
    st.markdown("---")
    menu = st.radio(
        "Chọn khu vực quản lý:",
        ["👩‍🏫 Giáo viên", "🏫 Lớp học", "👧 Học sinh", "📘 Môn học", "📚 Chủ đề", "📝 Bài học", "🎥 Video", "❓ Câu hỏi", "🧑‍🏫 Phân công"],
        horizontal=True
    )
    st.divider()

    # --- Tải dữ liệu dùng chung ---
    # Sử dụng hàm load_data từ crud_utils
    # Đặt trong try-except để xử lý lỗi nếu bảng không tồn tại hoặc lỗi kết nối
    try:
        lop_df_global = crud_utils.load_data("lop_hoc")
        lop_options_global = {row["ten_lop"]: str(row["id"]) for _, row in lop_df_global.iterrows()} if not lop_df_global.empty else {}

        gv_df_global = crud_utils.load_data("giao_vien")
        gv_options_global = {row["ho_ten"]: str(row["id"]) for _, row in gv_df_global.iterrows()} if not gv_df_global.empty else {}

        mon_hoc_df_global = crud_utils.load_data("mon_hoc")
        mon_hoc_options_global = {row["ten_mon"]: str(row["id"]) for _, row in mon_hoc_df_global.iterrows()} if not mon_hoc_df_global.empty else {}

        chu_de_df_global = crud_utils.load_data("chu_de")
        chu_de_options_global = {f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id']) for _, row in chu_de_df_global.iterrows()} if not chu_de_df_global.empty else {}
        chu_de_id_list_global = [str(row['id']) for _, row in chu_de_df_global.iterrows()] if not chu_de_df_global.empty else []
        chu_de_options_with_none_global = {"Không có": None}; chu_de_options_with_none_global.update(chu_de_options_global)

        bai_hoc_df_global = crud_utils.load_data("bai_hoc")
        bai_hoc_options_global = {}
        if not bai_hoc_df_global.empty and not chu_de_df_global.empty:
             # Tạo map ID chủ đề -> Tên chủ đề để hiển thị trong options bài học
             chu_de_id_to_name_map = {str(row['id']): row['ten_chu_de'] for _, row in chu_de_df_global.iterrows()}
             bai_hoc_options_global = {
                 # Hiển thị tên bài học kèm tên chủ đề (lấy từ map)
                 f"{row['ten_bai_hoc']} ({chu_de_id_to_name_map.get(str(row.get('chu_de_id')), 'N/A')})": str(row['id'])
                 for _, row in bai_hoc_df_global.iterrows()
             }
        elif not bai_hoc_df_global.empty: # Fallback nếu không có chủ đề
            bai_hoc_options_global = {f"{row['ten_bai_hoc']} (ID: {str(row['id'])[:8]}...)": str(row['id']) for _, row in bai_hoc_df_global.iterrows()}

    except Exception as data_load_error:
        st.error(f"Lỗi tải dữ liệu ban đầu: {data_load_error}. Vui lòng kiểm tra kết nối CSDL và cấu trúc bảng.")
        # Gán giá trị rỗng để tránh lỗi khi truyền tham số
        lop_options_global, gv_options_global, mon_hoc_options_global = {}, {}, {}
        chu_de_options_global, chu_de_id_list_global, chu_de_options_with_none_global = {}, [], {"Không có": None}
        bai_hoc_options_global = {}


    # =============================================================
    # GỌI HÀM RENDER TƯƠNG ỨNG TỪ MODULE CON
    # =============================================================
    try:
        if menu == "👩‍🏫 Giáo viên":
            manage_teachers.render()
        elif menu == "🏫 Lớp học":
            manage_classes.render()
        elif menu == "👧 Học sinh":
            manage_students.render(lop_options=lop_options_global)
        elif menu == "📘 Môn học":
            manage_subjects.render()
        elif menu == "📚 Chủ đề":
            manage_topics.render(
                mon_hoc_options=mon_hoc_options_global,
                chu_de_options_all=chu_de_options_global, # Dict {name_display: id}
                chu_de_options_with_none=chu_de_options_with_none_global, # Dict {name_display: id} + None
                chu_de_id_list=chu_de_id_list_global # List [id]
            )
        elif menu == "📝 Bài học":
            manage_lessons.render(chu_de_options=chu_de_options_global) # Truyền {name_display: id} của Chủ đề
        elif menu == "🎥 Video":
            manage_videos.render()
        elif menu == "❓ Câu hỏi":
            manage_questions.render(
                chu_de_options=chu_de_options_global, # Truyền {name_display: id} của Chủ đề
                chu_de_id_list=chu_de_id_list_global # Truyền list [id] của Chủ đề
            )
        elif menu == "🧑‍🏫 Phân công":
            # Hàm render của Phân công tự load options bên trong nó
            manage_assignments.render()

    except AttributeError as attr_error:
         st.error(f"Lỗi thuộc tính khi hiển thị mục '{menu}': {attr_error}. Có thể do module chưa được import đúng hoặc thiếu hàm render().")
         st.exception(attr_error)
    except Exception as render_error:
        st.error(f"Đã xảy ra lỗi khi hiển thị mục '{menu}': {render_error}")
        st.exception(render_error) # In traceback đầy đủ để debug