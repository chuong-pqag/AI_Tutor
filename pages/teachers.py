# ===============================================
# 🧑‍🏫 Trang giáo viên - teachers.py (SỬA LỖI FINAL: TÍCH HỢP LẠI TAB LỚP HỌC)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
from backend.supabase_client import supabase
from backend.class_test_service import generate_class_test, generate_practice_exercise
from backend.data_service import get_lessons_by_topic, get_question_counts
from backend.data_service import get_teacher_exercises, can_delete_exercise, update_exercise_title, \
    delete_exercise_and_links
import streamlit.components.v1 as components

# Import tabs
from pages.teacher_pages import render_tab_results
from pages.teacher_pages import render_tab_manage_ex
from pages.teacher_pages import render_tab_exam
from pages.teacher_pages import render_tab_practice
from pages.teacher_pages import render_tab_announce

st.set_page_config(page_title="AI Tutor - Giáo viên", page_icon="🧑‍🏫", layout="wide")

# ==========================
# CSS + BANNER (GIỮ NGUYÊN)
# ==========================
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    div[data-testid="stHorizontalBlock"] > div:first-child > div { display: flex; flex-direction: column; align-items: center; text-align: center; }
    .teacher-name-title { font-family: 'Times New Roman'; font-size: 14pt !important; font-weight: bold; }
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
    if st.button("Về trang đăng nhập"):
        st.switch_page("app.py")
    st.stop()

giao_vien_id = st.session_state.get("giao_vien_id")
giao_vien_ten = st.session_state.get("giao_vien_ten", "Giáo viên")

# ==========================
# TẢI DỮ LIỆU (GIỮ NGUYÊN)
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

    teacher_students = [s for s in all_students if str(s.get("lop_id")) in teacher_ids]
    return all_classes, all_students, teacher_classes, teacher_students


all_classes, all_students, teacher_classes, teacher_students = load_teacher_data(giao_vien_id)

# ==========================
# UI KHUNG 2 CỘT (GIỮ NGUYÊN)
# ==========================
col1, col2 = st.columns([1, 5])

# ==========================
# CỘT TRÁI – GIỮ NGUYÊN
# ==========================
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995574.png", width=120)
    st.markdown(f"<h1 class='teacher-name-title'>{giao_vien_ten}</h1>", unsafe_allow_html=True)
    st.divider()

    with st.expander("📝 Sửa thông tin cá nhân"):
        with st.form("update_teacher_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=giao_vien_ten)
            current_email = supabase.table("giao_vien").select("email").eq("id", giao_vien_id).execute().data[0]["email"]
            new_email = st.text_input("Email", value=current_email)
            if st.form_submit_button("Lưu thông tin"):
                supabase.table("giao_vien").update({"ho_ten": new_ho_ten, "email": new_email}).eq("id", giao_vien_id).execute()
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
# CỘT PHẢI – TABS (GIỮ NGUYÊN)
# ==========================
with col2:
    st.subheader("🧑‍🏫 Bảng điều khiển Giáo viên")

    TAB_NAMES = [
        "📘 Lớp học",
        "📈 Kết quả học sinh",
        "🗂️ Quản lý Bài tập đã giao",
        "🏁 Giao bài Kiểm tra CĐ",
        "✏️ Giao bài Luyện tập BH",
        "📣 Gửi Thông báo"
    ]

    if "teacher_active_tab_index" not in st.session_state:
        st.session_state["teacher_active_tab_index"] = 0

    # ❌ ĐÃ LOẠI BỎ ĐOẠN JAVASCRIPT GÂY LỖI NHẢY TAB
    # KHÔNG ĐỤNG ĐẾN JS NỮA

    tab1, tab2, tab_manage, tab3, tab4, tab_announce = st.tabs(TAB_NAMES)

    # -------------------------
    # TAB 1: LỚP HỌC
    # -------------------------
    with tab1:
        st.session_state["teacher_active_tab_index"] = 0
        st.subheader("📘 Danh sách lớp bạn phụ trách")

        teacher_class_options = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}
        class_name_list = ["Tất cả"] + sorted(list(teacher_class_options.keys()))

        selected_class_name = st.selectbox(
            "🔎 Lọc theo Lớp học:",
            class_name_list,
            key="class_filter_tab1"
        )

        df_display_students = pd.DataFrame(teacher_students)

        if selected_class_name != "Tất cả":
            selected_id = teacher_class_options[selected_class_name]
            df_display_students = df_display_students[df_display_students['lop_id'].astype(str) == selected_id]

        if not df_display_students.empty:
            hs_df_display = df_display_students[
                ["ho_ten", "ma_hoc_sinh", "email", "ngay_sinh", "gioi_tinh"]
            ].rename(columns={"ho_ten": "Họ tên", "ma_hoc_sinh": "Mã HS"})
            st.dataframe(hs_df_display, width='stretch', hide_index=True)
        else:
            st.caption("Chưa có học sinh nào trong lớp này.")

    # -------------------------
    # TAB 2 – KẾT QUẢ
    # -------------------------
    with tab2:
        st.session_state["teacher_active_tab_index"] = 1
        render_tab_results.render(teacher_students, teacher_classes, all_classes)

    # -------------------------
    # TAB 3 – QUẢN LÝ BÀI TẬP
    # -------------------------
    with tab_manage:
        st.session_state["teacher_active_tab_index"] = 2
        render_tab_manage_ex.render(giao_vien_id, teacher_classes)

    # -------------------------
    # TAB 4 – GIAO KT
    # -------------------------
    with tab3:
        st.session_state["teacher_active_tab_index"] = 3
        render_tab_exam.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)

    # -------------------------
    # TAB 5 – GIAO LUYỆN TẬP
    # -------------------------
    with tab4:
        st.session_state["teacher_active_tab_index"] = 4
        render_tab_practice.render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES)

    # -------------------------
    # TAB 6 – GỬI THÔNG BÁO (MỚI)
    # -------------------------
    with tab_announce:
        st.session_state["teacher_active_tab_index"] = 5
        render_tab_announce.render(giao_vien_id, teacher_class_options, TAB_NAMES)
