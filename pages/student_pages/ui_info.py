# File: pages/student_pages/ui_info.py
# (FIX LỖI SESSION INFO: Tách biệt Logic Database và UI Toast)

import streamlit as st
import datetime
import os
import time
from backend.supabase_client import supabase
from backend.data_service import get_student
from backend.utils import get_available_avatars, get_img_as_base64


# =========================================================
# 1. HÀM CALLBACK (CHỈ XỬ LÝ DATA - KHÔNG UI)
# =========================================================
def update_avatar_callback(hoc_sinh_id, file_name):
    """
    Hàm này chạy ngầm. Tuyệt đối KHÔNG dùng st.toast, st.error ở đây.
    Chỉ lưu kết quả vào session_state để hàm chính xử lý hiển thị.
    """
    try:
        supabase.table("hoc_sinh").update({"avatar": file_name}).eq("id", hoc_sinh_id).execute()
        # Đặt cờ thành công
        st.session_state["msg_avatar_success"] = True
    except Exception as e:
        # Đặt cờ báo lỗi
        st.session_state["msg_avatar_error"] = str(e)


def logout():
    st.session_state.clear()
    st.switch_page("app.py")


# =========================================================
# 2. GIAO DIỆN CHÍNH
# =========================================================
def render_student_info(hoc_sinh_id, ho_ten, current_lop, current_ten_lop):
    # --- A. XỬ LÝ THÔNG BÁO (CHECK CỜ HIỆU TỪ CALLBACK) ---
    # Phần này chạy ở luồng chính (Main Thread) nên an toàn tuyệt đối
    if st.session_state.get("msg_avatar_success"):
        st.toast("✅ Đã đổi Avatar thành công!", icon="🎉")
        # Xóa cờ để không hiện lại lần sau
        del st.session_state["msg_avatar_success"]
        # Có thể gọi rerun nhẹ ở đây để refresh ảnh ngay lập tức nếu cần
        # st.rerun()

    if st.session_state.get("msg_avatar_error"):
        st.toast(f"❌ Lỗi: {st.session_state['msg_avatar_error']}", icon="⚠️")
        del st.session_state["msg_avatar_error"]

    # --- B. LẤY DỮ LIỆU ---
    student_data = get_student(hoc_sinh_id)
    current_ngay_sinh = None
    current_avatar_file = "default.png"

    if student_data:
        if student_data.get("ngay_sinh"):
            try:
                current_ngay_sinh = datetime.date.fromisoformat(student_data["ngay_sinh"])
            except:
                pass
        if student_data.get("avatar"):
            current_avatar_file = student_data.get("avatar")

    # --- C. XỬ LÝ ẢNH ---
    avatar_path = os.path.join("data", "avatar", "HS", current_avatar_file)
    if os.path.exists(avatar_path):
        img_b64 = get_img_as_base64(avatar_path)
        img_src = f"data:image/png;base64,{img_b64}"
    else:
        img_src = "https://cdn-icons-png.flaticon.com/512/1144/1144760.png"

    # --- D. HIỂN THỊ HTML ---
    lop_display = f"Khối {current_lop}" if current_lop is not None else "Chưa có Khối"
    full_class_info = f"{lop_display} - {current_ten_lop}"

    st.markdown(f"""
        <style>
            .profile-box {{
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; text-align: center; margin-bottom: 10px;
            }}
            .profile-name {{
                font-family: 'Segoe UI', sans-serif; font-size: 22px; 
                font-weight: bold; color: #31333F; margin-top: 10px; margin-bottom: 0px;
            }}
            .profile-class {{ font-size: 16px; color: #666; font-weight: 500; margin-top: 5px; }}
            .profile-img {{
                border-radius: 50%; border: 3px solid #ff6600; padding: 2px;
                width: 120px; height: 120px; object-fit: cover;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        </style>
        <div class="profile-box">
            <img src="{img_src}" class="profile-img">
            <div class="profile-name">{ho_ten}</div>
            <div class="profile-class">{full_class_info}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- E. CHỨC NĂNG ĐỔI AVATAR ---
    with st.expander("🖼️ Đổi Avatar"):
        avatars = get_available_avatars("HS")
        if not avatars:
            st.warning("Chưa có ảnh nào trong thư mục data/avatar/HS")
        else:
            st.write("Chọn một hình ảnh bên dưới:")
            cols = st.columns(3)
            for i, file_name in enumerate(avatars):
                col_idx = i % 3
                file_path = os.path.join("data", "avatar", "HS", file_name)

                with cols[col_idx]:
                    st.image(file_path, use_column_width=True)

                    if file_name == current_avatar_file:
                        st.button("Đang dùng", key=f"avt_curr_{i}", disabled=True, use_container_width=True)
                    else:
                        # Vẫn dùng on_click, nhưng hàm callback giờ đã an toàn
                        st.button(
                            "Chọn",
                            key=f"avt_pick_{i}",
                            use_container_width=True,
                            on_click=update_avatar_callback,
                            args=(hoc_sinh_id, file_name)
                        )

    # --- F. THAY ĐỔI THÔNG TIN (Logic cũ ổn định) ---
    with st.expander("📝 Thay đổi thông tin"):
        with st.form("update_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=ho_ten)
            new_ngay_sinh = st.date_input("Ngày sinh", value=current_ngay_sinh,
                                          min_value=datetime.date(1990, 1, 1),
                                          max_value=datetime.date.today())

            if st.form_submit_button("Lưu thông tin", use_container_width=True):
                success = False
                try:
                    update_payload = {"ho_ten": new_ho_ten,
                                      "ngay_sinh": new_ngay_sinh.isoformat() if new_ngay_sinh else None}
                    supabase.table("hoc_sinh").update(update_payload).eq("id", hoc_sinh_id).execute()
                    st.session_state["ho_ten"] = new_ho_ten
                    success = True
                except Exception as e:
                    st.error(f"Lỗi: {e}")

                if success:
                    st.success("Cập nhật thành công!")
                    time.sleep(0.5)
                    st.rerun()

    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            new_pass = st.text_input("Mã PIN mới (4 số)", type="password", max_chars=4)
            confirm_pass = st.text_input("Xác nhận Mã PIN", type="password", max_chars=4)

            if st.form_submit_button("Lưu thay đổi", use_container_width=True):
                if not new_pass or len(new_pass) != 4:
                    st.error("Mã PIN phải 4 số.")
                elif new_pass != confirm_pass:
                    st.error("Xác nhận không khớp.")
                else:
                    success = False
                    try:
                        supabase.table("hoc_sinh").update({"mat_khau": new_pass}).eq("id", hoc_sinh_id).execute()
                        success = True
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

                    if success:
                        st.success("Đổi PIN thành công!")
                        time.sleep(0.5)
                        st.rerun()

    st.divider()
    if st.button("🔓 Đăng xuất", key="logout_btn", use_container_width=True, type="primary"):
        logout()