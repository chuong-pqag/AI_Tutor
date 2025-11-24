# ===============================================
# 🧑‍🏫 Trang giáo viên - teachers.py
# (BẢN FIX: Lọc trùng lớp học khi dạy nhiều môn + Button Cam)
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

st.set_page_config(page_title="AI Tutor - Giáo viên", page_icon="🧑‍🏫", layout="wide")

# ==========================
# CSS + BANNER
# ==========================
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    div[data-testid="stHorizontalBlock"] > div:first-child > div { display: flex; flex-direction: column; align-items: center; text-align: center; }
    .teacher-name-title { font-family: 'Times New Roman'; font-size: 14pt !important; font-weight: bold; }

    div[data-testid="stRadio"] > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        display: flex;
        justify-content: space-around;
        width: 100%;
    }

    /* Button Cam */
    .stButton>button { 
        background-color: #ff6600; 
        color: #ffffff; 
        font-weight: bold; 
        border: none; 
        border-radius: 8px; 
        transition: background-color 0.3s; 
    }
    .stButton>button:hover { 
        background-color: #e65c00;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", width='stretch')
except Exception:
    st.warning("Không tải được ảnh banner.")
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", width='stretch')

# ==========================
# KIỂM TRA ĐĂNG NHẬP
# ==========================
if "role" not in st.session_state or st.session_state["role"] != "teacher":
    st.warning("⚠️ Vui lòng quay lại trang Đăng nhập để chọn vai trò Giáo viên.")
    if st.button("Về trang đăng nhập", width='stretch', type="primary"):
        st.switch_page("app.py")
    st.stop()

giao_vien_id = st.session_state.get("giao_vien_id")
giao_vien_ten = st.session_state.get("giao_vien_ten", "Giáo viên")

# ==========================
# LẤY THÔNG TIN CHỨC VỤ
# ==========================
try:
    user_info_res = supabase.table("giao_vien").select("chuc_vu").eq("id", giao_vien_id).maybe_single().execute()
    current_chuc_vu = user_info_res.data.get("chuc_vu", "Giáo viên") if user_info_res.data else "Giáo viên"
except Exception as e:
    current_chuc_vu = "Giáo viên"


# ==========================
# TẢI DỮ LIỆU (ĐÃ SỬA LỖI TRÙNG LẶP)
# ==========================
@st.cache_data(ttl=300)
def load_teacher_data(giao_vien_id_param):
    all_classes_res = supabase.table("lop_hoc").select("*").execute()
    all_students_res = supabase.table("hoc_sinh").select("*").execute()
    teacher_assignments_res = supabase.table("phan_cong_giang_day").select(
        "lop_id, lop_hoc(khoi, ten_lop)"
    ).eq("giao_vien_id", giao_vien_id_param).execute()

    all_classes = all_classes_res.data or []
    all_students = all_students_res.data or []
    teacher_assignments = teacher_assignments_res.data or []

    teacher_classes = []
    # Set dùng để kiểm tra trùng lặp ID lớp
    added_class_ids = set()

    for a in teacher_assignments:
        lop_id = a["lop_id"]

        # --- FIX LỖI: Chỉ thêm nếu lớp chưa có trong danh sách ---
        if lop_id not in added_class_ids:
            lop = a.get("lop_hoc", {})
            if lop:
                teacher_classes.append({
                    "id": lop_id,
                    "ten_lop": lop.get("ten_lop"),
                    "khoi": lop.get("khoi")
                })
                added_class_ids.add(str(lop_id))
        # ---------------------------------------------------------

    teacher_students = [s for s in all_students if str(s.get("lop_id")) in added_class_ids]
    return all_classes, all_students, teacher_classes, teacher_students


all_classes, all_students, teacher_classes, teacher_students = load_teacher_data(giao_vien_id)
teacher_class_options = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}

# ==========================
# UI KHUNG 2 CỘT
# ==========================
col1, col2 = st.columns([1, 5])

# ==========================
# CỘT TRÁI – THÔNG TIN GV
# ==========================
with col1:
    try:
        gv_info = supabase.table("giao_vien").select("avatar").eq("id", giao_vien_id).maybe_single().execute()
        current_avatar_file = gv_info.data.get("avatar") if gv_info.data else None
    except:
        current_avatar_file = None

    avatar_path = os.path.join("data", "avatar", "GV", current_avatar_file) if current_avatar_file else ""

    if os.path.exists(avatar_path):
        img_b64 = get_img_as_base64(avatar_path)
        img_src = f"data:image/png;base64,{img_b64}"
    else:
        img_src = "https://cdn-icons-png.flaticon.com/512/1995/1995574.png"

    st.markdown(f"""
        <style>
            .gv-profile {{
                display: flex; flex-direction: column; align-items: center; text-align: center;
            }}
            .gv-img {{
                border-radius: 50%; border: 3px solid #ff6600; padding: 2px;
                width: 130px; height: 130px; object-fit: cover; margin-bottom: 10px;
            }}
            .gv-name {{
                font-family: 'Times New Roman'; font-size: 20px; font-weight: bold; color: #004d99;
            }}
        </style>
        <div class="gv-profile">
            <img src="{img_src}" class="gv-img">
            <div class="gv-name">{giao_vien_ten}</div>
        </div>
    """, unsafe_allow_html=True)

    if current_chuc_vu != "Giáo viên":
        st.caption(f"⭐ Chức vụ: **{current_chuc_vu}**")

    st.divider()

    with st.expander("🖼️ Đổi Avatar"):
        avatars = get_available_avatars("GV")
        if not avatars:
            st.warning("Chưa có ảnh trong data/avatar/GV")
        else:
            cols = st.columns(3)
            for i, file_name in enumerate(avatars):
                with cols[i % 3]:
                    file_path = os.path.join("data", "avatar", "GV", file_name)
                    st.image(file_path, width='stretch')
                    if file_name == current_avatar_file:
                        st.button("✅", key=f"gv_avt_curr_{i}", disabled=True)
                    else:
                        if st.button("Chọn", key=f"gv_avt_pick_{i}"):
                            supabase.table("giao_vien").update({"avatar": file_name}).eq("id", giao_vien_id).execute()
                            st.success("Đã đổi!")
                            st.rerun()

    with st.expander("📝 Sửa thông tin"):
        with st.form("update_teacher_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=giao_vien_ten)
            try:
                cur_email_res = supabase.table("giao_vien").select("email").eq("id", giao_vien_id).execute()
                cur_email = cur_email_res.data[0]["email"] if cur_email_res.data else ""
            except:
                cur_email = ""

            new_email = st.text_input("Email", value=cur_email)
            if st.form_submit_button("Lưu thông tin", width='stretch', type="primary"):
                supabase.table("giao_vien").update({"ho_ten": new_ho_ten, "email": new_email}).eq("id",
                                                                                                  giao_vien_id).execute()
                st.session_state["giao_vien_ten"] = new_ho_ten
                st.success("Cập nhật thành công!")
                st.rerun()

    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            p1 = st.text_input("Mật khẩu mới", type="password")
            p2 = st.text_input("Xác nhận mật khẩu", type="password")
            if st.form_submit_button("Lưu mật khẩu mới", width='stretch', type="primary"):
                if p1 == p2 and p1:
                    supabase.table("giao_vien").update({"mat_khau": p1}).eq("id", giao_vien_id).execute()
                    st.success("Đổi mật khẩu thành công!")
                else:
                    st.error("Mật khẩu không hợp lệ.")

    st.divider()
    if st.button("🔓 Đăng xuất", width='stretch', type="primary"):
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

    selected_tab = st.radio(
        "Điều hướng:",
        TAB_NAMES,
        horizontal=True,
        label_visibility="collapsed",
        key="teacher_active_tab_radio"
    )

    st.divider()

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