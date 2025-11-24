# File: pages/student_pages/ui_info.py
# (BẢN FINAL: Hỗ trợ đổi Avatar từ thư mục data/avatar/HS)

import streamlit as st
import datetime
import os
from backend.supabase_client import supabase
from backend.data_service import get_student
from backend.utils import get_available_avatars, get_img_as_base64  # Import hàm mới


def logout():
    st.session_state.clear()
    st.switch_page("app.py")


def render_student_info(hoc_sinh_id, ho_ten, current_lop, current_ten_lop):
    # 1. Lấy thông tin học sinh
    student_data = get_student(hoc_sinh_id)
    current_ngay_sinh = None
    current_avatar_file = "default.png"  # Giá trị mặc định

    if student_data:
        if student_data.get("ngay_sinh"):
            try:
                current_ngay_sinh = datetime.date.fromisoformat(student_data["ngay_sinh"])
            except:
                pass

        # Lấy avatar từ DB (nếu có)
        if student_data.get("avatar"):
            current_avatar_file = student_data.get("avatar")

    # 2. Xử lý đường dẫn ảnh hiển thị
    # Đường dẫn file thực tế
    avatar_path = os.path.join("data", "avatar", "HS", current_avatar_file)

    # Nếu file không tồn tại, dùng ảnh online mặc định
    if os.path.exists(avatar_path):
        # Chuyển sang base64 để hiển thị trong HTML
        img_b64 = get_img_as_base64(avatar_path)
        img_src = f"data:image/png;base64,{img_b64}"
    else:
        img_src = "https://cdn-icons-png.flaticon.com/512/1144/1144760.png"

    # 3. Hiển thị Profile (HTML/CSS)
    lop_display = f"Khối {current_lop}" if current_lop is not None else "Chưa có Khối"
    full_class_info = f"{lop_display} - {current_ten_lop}"

    st.markdown(f"""
        <style>
            .profile-box {{
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; text-align: center; margin-bottom: 10px;
            }}
            .profile-name {{
                font-family: 'Times New Roman', sans-serif; font-size: 22px; 
                font-weight: bold; color: #31333F; margin-top: 10px; margin-bottom: 0px;
            }}
            .profile-class {{ font-size: 16px; color: #666; font-weight: 500; margin-top: 5px; }}
            .profile-img {{
                border-radius: 50%; border: 3px solid #ff6600; padding: 2px;
                width: 120px; height: 120px; object-fit: cover;
            }}
        </style>
        <div class="profile-box">
            <img src="{img_src}" class="profile-img">
            <div class="profile-name">{ho_ten}</div>
            <div class="profile-class">{full_class_info}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 4. CHỨC NĂNG ĐỔI AVATAR
    with st.expander("🖼️ Đổi Avatar"):
        avatars = get_available_avatars("HS")
        if not avatars:
            st.warning("Chưa có ảnh nào trong thư mục data/avatar/HS")
        else:
            st.write("Chọn một hình ảnh bên dưới:")
            # Chia lưới hiển thị ảnh
            cols = st.columns(3)
            for i, file_name in enumerate(avatars):
                col_idx = i % 3
                file_path = os.path.join("data", "avatar", "HS", file_name)

                with cols[col_idx]:
                    st.image(file_path, width='stretch')
                    # Nếu đang chọn ảnh này thì nút mờ đi
                    if file_name == current_avatar_file:
                        st.button("Đang dùng", key=f"avt_curr_{i}", disabled=True)
                    else:
                        if st.button("Chọn", key=f"avt_pick_{i}"):
                            try:
                                supabase.table("hoc_sinh").update({"avatar": file_name}).eq("id", hoc_sinh_id).execute()
                                st.success("Đã đổi Avatar!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")

    # 5. CÁC CHỨC NĂNG KHÁC
    with st.expander("📝 Thay đổi thông tin"):
        with st.form("update_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=ho_ten)
            new_ngay_sinh = st.date_input("Ngày sinh", value=current_ngay_sinh, min_value=datetime.date(1990, 1, 1),
                                          max_value=datetime.date.today())
            if st.form_submit_button("Lưu thông tin", width='stretch'):
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
            if st.form_submit_button("Lưu thay đổi", width='stretch'):
                if not new_pass or len(new_pass) != 4:
                    st.error("Mã PIN phải 4 số.")
                elif new_pass != confirm_pass:
                    st.error("Xác nhận không khớp.")
                else:
                    try:
                        supabase.table("hoc_sinh").update({"mat_khau": new_pass}).eq("id",
                                                                                     hoc_sinh_id).execute();
                        st.success(
                            "Đổi PIN!")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    st.divider()
    if st.button("🔓 Đăng xuất", key="logout_btn", width='stretch', type="primary"):
        logout()