# ===============================================
# 🧑‍🏫 Trang giáo viên - teachers.py (BẢN FIX: GHI NHỚ TAB)
# ===============================================
import streamlit as st
import pandas as pd
from backend.supabase_client import supabase

# Import các module render (đảm bảo cấu trúc thư mục đúng)
from pages.teacher_pages import render_tab_results
from pages.teacher_pages import render_tab_manage_ex
from pages.teacher_pages import render_tab_exam
from pages.teacher_pages import render_tab_practice
from pages.teacher_pages import render_tab_contribute
from pages.teacher_pages import render_tab_classes
from pages.teacher_pages import render_tab_announce  # Import thêm module Thông báo

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

    /* Tùy chỉnh Radio button cho giống Menu Tab */
    div[data-testid="stRadio"] > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        display: flex;
        justify-content: space-around;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", use_container_width=True)
except Exception:
    st.warning("Không tải được ảnh banner.")
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", use_container_width=True)

# ==========================
# KIỂM TRA ĐĂNG NHẬP
# ==========================
if "role" not in st.session_state or st.session_state["role"] != "teacher":
    st.warning("⚠️ Vui lòng quay lại trang Đăng nhập để chọn vai trò Giáo viên.")
    if st.button("Về trang đăng nhập"):
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
    print(f"Lỗi lấy chức vụ: {e}")
    current_chuc_vu = "Giáo viên"


# ==========================
# TẢI DỮ LIỆU
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
    teacher_ids = set()

    for a in teacher_assignments:
        lop = a.get("lop_hoc", {})
        if lop:
            teacher_classes.append({
                "id": a["lop_id"],
                "ten_lop": lop.get("ten_lop"),
                "khoi": lop.get("khoi")
            })
            teacher_ids.add(str(a["lop_id"]))

    # Lọc học sinh thuộc các lớp giáo viên dạy
    teacher_students = [s for s in all_students if str(s.get("lop_id")) in teacher_ids]
    return all_classes, all_students, teacher_classes, teacher_students


all_classes, all_students, teacher_classes, teacher_students = load_teacher_data(giao_vien_id)

# Tạo options lớp học cho các selectbox
teacher_class_options = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}

# ==========================
# UI KHUNG 2 CỘT
# ==========================
col1, col2 = st.columns([1, 5])

# ==========================
# CỘT TRÁI – THÔNG TIN GV
# ==========================
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995574.png", width=120)
    st.markdown(f"<h1 class='teacher-name-title'>{giao_vien_ten}</h1>", unsafe_allow_html=True)

    if current_chuc_vu != "Giáo viên":
        st.caption(f"⭐ Chức vụ: **{current_chuc_vu}**")

    st.divider()

    with st.expander("📝 Sửa thông tin cá nhân"):
        with st.form("update_teacher_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=giao_vien_ten)
            try:
                current_email_res = supabase.table("giao_vien").select("email").eq("id", giao_vien_id).execute()
                current_email = current_email_res.data[0]["email"] if current_email_res.data else ""
            except:
                current_email = ""

            new_email = st.text_input("Email", value=current_email)
            if st.form_submit_button("Lưu thông tin"):
                supabase.table("giao_vien").update({"ho_ten": new_ho_ten, "email": new_email}).eq("id",
                                                                                                  giao_vien_id).execute()
                st.session_state["giao_vien_ten"] = new_ho_ten
                st.success("Cập nhật thành công!")
                st.rerun()

    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            p1 = st.text_input("Mật khẩu mới", type="password")
            p2 = st.text_input("Xác nhận mật khẩu", type="password")
            if st.form_submit_button("Lưu mật khẩu mới"):
                if p1 == p2 and p1:
                    supabase.table("giao_vien").update({"mat_khau": p1}).eq("id", giao_vien_id).execute()
                    st.success("Đổi mật khẩu thành công!")
                else:
                    st.error("Mật khẩu không hợp lệ.")

    st.divider()
    if st.button("🔓 Đăng xuất", width='stretch'):
        st.session_state.clear()
        st.switch_page("app.py")

# ==========================
# CỘT PHẢI – TABS CHÍNH (SỬ DỤNG RADIO ĐỂ LƯU TRẠNG THÁI)
# ==========================
with col2:
    st.subheader("🧑‍🏫 Bảng điều khiển Giáo viên")

    # 1. ĐỊNH NGHĨA DANH SÁCH TAB
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

    # 2. SỬ DỤNG RADIO BUTTON THAY VÌ ST.TABS
    # Tham số `key` giúp Streamlit tự động lưu trạng thái khi reload
    selected_tab = st.radio(
        "Điều hướng:",
        TAB_NAMES,
        horizontal=True,
        label_visibility="collapsed",
        key="teacher_active_tab_radio"  # <-- KEY QUAN TRỌNG
    )

    st.divider()

    # 3. HIỂN THỊ NỘI DUNG TƯƠNG ỨNG
    # -------------------------
    # TAB 1: LỚP HỌC
    # -------------------------
    if selected_tab == "📘 Lớp học":
        render_tab_classes.render(teacher_classes, teacher_students, teacher_class_options)

    # -------------------------
    # TAB 2: KẾT QUẢ
    # -------------------------
    elif selected_tab == "📈 Kết quả HS":
        render_tab_results.render(teacher_students, teacher_classes, all_classes)

    # -------------------------
    # TAB 3: QUẢN LÝ BÀI TẬP
    # -------------------------
    elif selected_tab == "🗂️ QL Bài tập":
        render_tab_manage_ex.render(giao_vien_id, teacher_classes)

    # -------------------------
    # TAB 4: GIAO KIỂM TRA
    # -------------------------
    elif selected_tab == "🏁 Giao KT Chủ đề":
        render_tab_exam.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)

    # -------------------------
    # TAB 5: GIAO LUYỆN TẬP
    # -------------------------
    elif selected_tab == "✏️ Giao Luyện tập":
        render_tab_practice.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)

    # -------------------------
    # TAB 6: THÔNG BÁO (Mới)
    # -------------------------
    elif selected_tab == "📣 Thông báo":
        render_tab_announce.render(giao_vien_id, teacher_class_options, TAB_NAMES)

    # -------------------------
    # TAB 7: ĐÓNG GÓP
    # -------------------------
    elif SHOW_CONTRIBUTE_TAB and selected_tab == "✍️ Đóng góp câu hỏi":
        render_tab_contribute.render(giao_vien_id)