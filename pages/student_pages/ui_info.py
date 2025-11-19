# File: pages/student_pages/ui_info.py
import streamlit as st
import datetime
from backend.supabase_client import supabase
from backend.data_service import get_student

def logout():
    st.session_state.clear()
    st.switch_page("app.py")

def render_student_info(hoc_sinh_id, ho_ten, current_lop, current_ten_lop):
    student_data = get_student(hoc_sinh_id)
    current_ngay_sinh = None
    if student_data and student_data.get("ngay_sinh"):
        try:
            current_ngay_sinh = datetime.date.fromisoformat(student_data["ngay_sinh"])
        except (ValueError, TypeError):
            pass

    st.image("https://cdn-icons-png.flaticon.com/512/1144/1144760.png", width=120)
    st.markdown(f"<h1 class='student-name-title'>{ho_ten}</h1>", unsafe_allow_html=True)
    lop_display = f"Khối {current_lop}" if current_lop is not None else "Chưa có Khối"
    st.subheader(f"{lop_display} - {current_ten_lop}")
    st.divider()

    with st.expander("📝 Thay đổi thông tin"):
        with st.form("update_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=ho_ten)
            new_ngay_sinh = st.date_input("Ngày sinh", value=current_ngay_sinh, min_value=datetime.date(1990, 1, 1),
                                          max_value=datetime.date.today())
            if st.form_submit_button("Lưu thông tin"):
                try:
                    update_payload = {"ho_ten": new_ho_ten,
                                      "ngay_sinh": new_ngay_sinh.isoformat() if new_ngay_sinh else None}
                    supabase.table("hoc_sinh").update(update_payload).eq("id", hoc_sinh_id).execute()
                    st.session_state["ho_ten"] = new_ho_ten
                    st.success("Cập nhật!");
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            new_pass = st.text_input("Mã PIN mới (4 số)", type="password", max_chars=4);
            confirm_pass = st.text_input("Xác nhận Mã PIN", type="password", max_chars=4)
            if st.form_submit_button("Lưu thay đổi"):
                if not new_pass or len(new_pass) != 4:
                    st.error("Mã PIN phải 4 số.")
                elif new_pass != confirm_pass:
                    st.error("Xác nhận không khớp.")
                else:
                    try:
                        supabase.table("hoc_sinh").update({"mat_khau": new_pass}).eq("id",
                                                                                     hoc_sinh_id).execute(); st.success(
                            "Đổi PIN!")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    st.divider()
    if st.button("🔓 Đăng xuất", width='stretch', type="primary"): logout()