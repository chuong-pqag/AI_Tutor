# ===============================================
# 🧑‍🏫 Trang giáo viên - teachers.py (PERFORMANCE OPTIMIZED)
# ===============================================
import streamlit as st
import pandas as pd
import os
from backend.supabase_client import supabase
from backend.utils import get_available_avatars, get_img_as_base64

# Import các module render chức năng
from pages.teacher_pages import render_tab_results
from pages.teacher_pages import render_tab_manage_ex
from pages.teacher_pages import render_tab_exam
from pages.teacher_pages import render_tab_practice
from pages.teacher_pages import render_tab_contribute
from pages.teacher_pages import render_tab_classes
from pages.teacher_pages import render_tab_announce

# 1. Page Config
st.set_page_config(page_title="AI Tutor - Giáo viên", page_icon="🧑‍🏫", layout="wide")

# ==========================
# CSS + BANNER
# ==========================
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}

    div[data-testid="stHorizontalBlock"] > div:first-child > div { 
        display: flex; flex-direction: column; align-items: center; text-align: center; 
    }

    div[data-testid="stRadio"] > div {
        background-color: #f0f2f6; padding: 10px; border-radius: 10px;
        display: flex; justify-content: space-around; width: 100%;
    }

    /* FIX NÚT BẤM */
    .stButton>button { 
        background-color: #ff6600; color: #ffffff; font-weight: bold; 
        border: none; border-radius: 8px; transition: background-color 0.3s;
        white-space: nowrap !important;
        padding: 0.25rem 0.5rem; font-size: 14px; min-height: auto;
    }
    .stButton>button:hover { background-color: #e65c00; color: #ffffff; }

    /* FIX ẢNH AVATAR */
    div[data-testid="stExpander"] div[data-testid="stImage"] img {
        width: 80px !important; height: 80px !important;
        object-fit: cover !important; border-radius: 10px !important;
        margin: 0 auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load Banner
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
banner_path = os.path.join(root_dir, 'data', 'banner.jpg')

try:
    if os.path.exists(banner_path):
        st.image(banner_path, use_column_width=True)
    else:
        st.markdown("<h1>🧑‍🏫 TRANG GIÁO VIÊN</h1>", unsafe_allow_html=True)
except:
    pass

# ==========================
# KIỂM TRA ĐĂNG NHẬP
# ==========================
if "role" not in st.session_state or st.session_state["role"] != "teacher":
    st.warning("⚠️ Vui lòng quay lại trang Đăng nhập.")
    if st.button("Về trang chủ", use_container_width=True, type="primary"):
        st.switch_page("app.py")
    st.stop()

giao_vien_id = st.session_state.get("giao_vien_id")
giao_vien_ten = st.session_state.get("giao_vien_ten", "Giáo viên")


# ==========================
# TẢI DỮ LIỆU TỐI ƯU (SERVER-SIDE FILTERING)
# ==========================
# Tăng TTL lên 600s (10 phút) để đỡ phải load lại nhiều lần
@st.cache_data(ttl=600, show_spinner=False)
def load_teacher_data(giao_vien_id_param):
    # 1. Lấy thông tin cá nhân (Nhẹ)
    gv_info_res = supabase.table("giao_vien").select("chuc_vu, avatar, email").eq("id",
                                                                                  giao_vien_id_param).maybe_single().execute()
    gv_data = gv_info_res.data or {}
    chuc_vu = gv_data.get("chuc_vu", "Giáo viên")
    avatar = gv_data.get("avatar")
    email = gv_data.get("email", "")

    # 2. Lấy phân công giảng dạy TRƯỚC (Để biết dạy lớp nào)
    teacher_assignments_res = supabase.table("phan_cong_giang_day").select("lop_id, lop_hoc(khoi, ten_lop)").eq(
        "giao_vien_id", giao_vien_id_param).execute()
    teacher_assignments = teacher_assignments_res.data or []

    # Xử lý danh sách lớp dạy
    teacher_classes = []
    class_ids_taught = []  # List chứa ID các lớp giáo viên dạy

    seen_ids = set()
    for a in teacher_assignments:
        lop_id = a["lop_id"]
        if lop_id not in seen_ids:
            lop = a.get("lop_hoc", {})
            if lop:
                teacher_classes.append({
                    "id": lop_id,
                    "ten_lop": lop.get("ten_lop"),
                    "khoi": lop.get("khoi")
                })
                class_ids_taught.append(lop_id)
                seen_ids.add(lop_id)

    # 3. Lấy danh sách Lớp học toàn trường (Nhẹ - Bảng này thường ít dòng)
    all_classes_res = supabase.table("lop_hoc").select("*").execute()
    all_classes = all_classes_res.data or []

    # 4. [QUAN TRỌNG] Lấy danh sách Học sinh CÓ CHỌN LỌC
    # Thay vì lấy "*", ta dùng .in_() để chỉ lấy HS thuộc các lớp mình dạy
    # Nếu là Ban giám hiệu (xem tất cả) thì mới load hết, còn GV thường chỉ load lớp mình

    all_students = []
    teacher_students = []

    if chuc_vu in ["Ban giám hiệu", "Tổ trưởng"]:
        # Nếu là lãnh đạo, load hết (chấp nhận chậm hơn chút nhưng cần thiết)
        all_students_res = supabase.table("hoc_sinh").select("*").execute()
        all_students = all_students_res.data or []
        # Lọc lại HS của GV
        teacher_students = [s for s in all_students if s.get("lop_id") in class_ids_taught]
    else:
        # Nếu là GV thường -> CHỈ LOAD HS THUỘC LỚP MÌNH DẠY
        if class_ids_taught:
            # Supabase hỗ trợ filter theo list: lop_id in (1, 2, 3...)
            students_res = supabase.table("hoc_sinh").select("*").in_("lop_id", class_ids_taught).execute()
            teacher_students = students_res.data or []
            # Với GV thường, all_students coi như bằng teacher_students để tiết kiệm
            all_students = teacher_students
        else:
            teacher_students = []
            all_students = []

    return chuc_vu, avatar, email, all_classes, all_students, teacher_classes, teacher_students


# Hiển thị Spinner để người dùng biết đang tải
with st.spinner("⏳ Đang tải dữ liệu lớp học..."):
    try:
        current_chuc_vu, current_avatar_file, current_email, all_classes, all_students, teacher_classes, teacher_students = load_teacher_data(
            giao_vien_id)
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        st.stop()

teacher_class_options = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}

# ==========================
# UI KHUNG 2 CỘT ([2, 5])
# ==========================
col1, col2 = st.columns([2, 5])

# ==========================
# CỘT TRÁI – THÔNG TIN GV
# ==========================
with col1:
    avatar_path = os.path.join("data", "avatar", "GV", current_avatar_file) if current_avatar_file else ""
    if os.path.exists(avatar_path):
        img_b64 = get_img_as_base64(avatar_path)
        img_src = f"data:image/png;base64,{img_b64}"
    else:
        img_src = "https://cdn-icons-png.flaticon.com/512/1995/1995574.png"

    st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            <img src="{img_src}" style="border-radius: 50%; border: 3px solid #ff6600; padding: 2px; width: 140px; height: 140px; object-fit: cover; margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <div style="font-family: 'Times New Roman'; font-size: 22px; font-weight: bold; color: #004d99; margin-bottom: 5px;">{giao_vien_ten}</div>
        </div>
    """, unsafe_allow_html=True)

    if current_chuc_vu != "Giáo viên":
        st.caption(f"⭐ Chức vụ: **{current_chuc_vu}**")

    st.divider()

    # Đổi Avatar
    with st.expander("🖼️ Đổi Avatar"):
        avatars = get_available_avatars("GV")
        if not avatars:
            st.warning("Chưa có ảnh trong data/avatar/GV")
        else:
            cols = st.columns(2)
            for i, file_name in enumerate(avatars):
                with cols[i % 2]:
                    file_path = os.path.join("data", "avatar", "GV", file_name)
                    st.image(file_path, width=85)
                    if file_name == current_avatar_file:
                        st.button("✅", key=f"gv_avt_curr_{i}", disabled=True, use_container_width=True)
                    else:
                        if st.button("Chọn", key=f"gv_avt_pick_{i}", use_container_width=True):
                            supabase.table("giao_vien").update({"avatar": file_name}).eq("id", giao_vien_id).execute()
                            load_teacher_data.clear()
                            st.rerun()

    # Sửa thông tin
    with st.expander("📝 Sửa thông tin"):
        with st.form("update_teacher_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=giao_vien_ten)
            new_email = st.text_input("Email", value=current_email)
            if st.form_submit_button("Lưu thông tin", use_container_width=True, type="primary"):
                supabase.table("giao_vien").update({"ho_ten": new_ho_ten, "email": new_email}).eq("id",
                                                                                                  giao_vien_id).execute()
                st.session_state["giao_vien_ten"] = new_ho_ten
                load_teacher_data.clear()
                st.success("Thành công!")
                st.rerun()

    # Đổi mật khẩu
    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            p1 = st.text_input("Mật khẩu mới", type="password")
            p2 = st.text_input("Xác nhận mật khẩu", type="password")
            if st.form_submit_button("Lưu mật khẩu", use_container_width=True, type="primary"):
                if p1 == p2 and p1:
                    supabase.table("giao_vien").update({"mat_khau": p1}).eq("id", giao_vien_id).execute()
                    st.success("Thành công!")
                else:
                    st.error("Mật khẩu không khớp.")

    st.divider()
    if st.button("🔓 Đăng xuất", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.switch_page("app.py")

# ==========================
# CỘT PHẢI – TABS CHÍNH
# ==========================
with col2:
    st.subheader("🧑‍🏫 Bảng điều khiển Giáo viên")

    TAB_NAMES = [
        "📘 Lớp học",
        "📈 Kết quả HS",
        "🗂️ QL Bài tập",
        "🏁 Giao KT Chủ đề",
        "✏️ Giao Luyện tập",
        "📣 Thông báo"
    ]

    SHOW_CONTRIBUTE_TAB = current_chuc_vu in ["Tổ trưởng", "Ban giám hiệu"]
    if SHOW_CONTRIBUTE_TAB:
        TAB_NAMES.append("✍️ Đóng góp câu hỏi")

    default_index = 0
    if "teacher_active_tab_radio" in st.session_state:
        current_selection = st.session_state["teacher_active_tab_radio"]
        if current_selection in TAB_NAMES:
            default_index = TAB_NAMES.index(current_selection)

    selected_tab = st.radio(
        "Điều hướng:",
        TAB_NAMES,
        index=default_index,
        horizontal=True,
        label_visibility="collapsed",
        key="teacher_active_tab_radio"
    )

    st.divider()

    # Render Tabs
    if selected_tab == "📘 Lớp học":
        render_tab_classes.render(teacher_classes, teacher_students, teacher_class_options)
    elif selected_tab == "📈 Kết quả HS":
        render_tab_results.render(teacher_students, teacher_classes, all_classes)
    elif selected_tab == "🗂️ QL Bài tập":
        render_tab_manage_ex.render(giao_vien_id, teacher_classes)
    elif selected_tab == "🏁 Giao KT Chủ đề":
        render_tab_exam.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)
    elif selected_tab == "✏️ Giao Luyện tập":
        render_tab_practice.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)
    elif selected_tab == "📣 Thông báo":
        render_tab_announce.render(giao_vien_id, teacher_class_options, TAB_NAMES)
    elif SHOW_CONTRIBUTE_TAB and selected_tab == "✍️ Đóng góp câu hỏi":
        render_tab_contribute.render(giao_vien_id)