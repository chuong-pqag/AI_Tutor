# File: pages/teacher_pages/render_tab_announce.py
# (BẢN FIX: Đưa bộ chọn ra ngoài Form để tải danh sách HS tức thì)

import streamlit as st
import pandas as pd
from backend.data_service import (
    create_announcement,
    get_announcements_for_teacher,
    delete_announcement,
    get_all_students
)


def render(giao_vien_id, teacher_class_options, TAB_NAMES):
    st.subheader("📣 Quản lý Thông báo")

    if not teacher_class_options:
        st.warning("Bạn cần được phân công lớp để gửi thông báo.")
        return

    st.markdown("#### ✉️ Soạn thông báo mới")

    # ======================================================
    # PHẦN 1: CHỌN ĐỐI TƯỢNG (NẰM NGOÀI FORM ĐỂ TƯƠNG TÁC)
    # ======================================================

    col_lop, col_target = st.columns(2)

    with col_lop:
        # 1. Chọn lớp
        lop_ten = st.selectbox("1. Chọn lớp:", list(teacher_class_options.keys()), key="announce_lop_select")
        selected_lop_id = teacher_class_options.get(lop_ten)

    with col_target:
        # 2. Chọn đối tượng
        target_type = st.radio("2. Gửi đến:", ["👨‍👩‍👧‍👦 Cả lớp", "👤 Học sinh cụ thể"], horizontal=True)

    selected_student_id = None
    selected_student_name_display = ""

    # --- LOGIC TẢI DANH SÁCH HỌC SINH (Sẽ chạy ngay lập tức khi chọn radio) ---
    if target_type == "👤 Học sinh cụ thể":
        if selected_lop_id:
            students_in_class = get_all_students(selected_lop_id)

            if students_in_class:
                student_options = {
                    f"{s['ho_ten']} ({s.get('ma_hoc_sinh', 'N/A')})": s['id']
                    for s in students_in_class
                }

                selected_student_name_display = st.selectbox(
                    "➡ Chọn học sinh nhận tin:",
                    options=list(student_options.keys()),
                    key="announce_student_select"
                )
                selected_student_id = student_options[selected_student_name_display]
            else:
                st.warning("⚠️ Lớp này chưa có học sinh nào.")
        else:
            st.warning("Vui lòng chọn lớp trước.")
    # ======================================================

    # ======================================================
    # PHẦN 2: NHẬP NỘI DUNG (NẰM TRONG FORM ĐỂ GOM GỌN)
    # ======================================================
    with st.form("new_announcement_content_form", clear_on_submit=True):
        tieu_de = st.text_input("3. Tiêu đề *")
        noi_dung = st.text_area("4. Nội dung *")

        submitted = st.form_submit_button("🚀 Gửi ngay", width='stretch')

        if submitted:
            if not tieu_de or not noi_dung:
                st.error("Tiêu đề và Nội dung không được để trống.")
            elif target_type == "👤 Học sinh cụ thể" and not selected_student_id:
                st.error("Vui lòng chọn một học sinh cụ thể.")
            else:
                try:
                    # Gọi hàm tạo thông báo với các biến từ bên ngoài Form
                    create_announcement(
                        giao_vien_id=giao_vien_id,
                        lop_id=selected_lop_id,
                        tieu_de=tieu_de,
                        noi_dung=noi_dung,
                        hoc_sinh_id=selected_student_id
                    )

                    # Tạo thông báo thành công
                    if selected_student_id:
                        # Lấy tên HS từ biến hiển thị
                        hs_name_short = selected_student_name_display.split('(')[0]
                        st.success(f"✅ Đã gửi riêng cho **{hs_name_short}**: '{tieu_de}'")
                    else:
                        st.success(f"✅ Đã gửi cho cả lớp **{lop_ten}**: '{tieu_de}'")

                    # Xóa cache để cập nhật danh sách bên dưới
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"Lỗi khi gửi thông báo: {e}")

    st.markdown("---")

    # --- 3. LỊCH SỬ ĐÃ GỬI ---
    st.subheader("📑 Lịch sử đã gửi")

    try:
        all_announcements = get_announcements_for_teacher(giao_vien_id)

        if not all_announcements:
            st.info("Bạn chưa gửi thông báo nào.")
            return

        df = pd.DataFrame(all_announcements)
        df['Ngày gửi'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
        df['Tên Lớp'] = df['lop_hoc'].apply(lambda x: x.get('ten_lop', 'N/A') if isinstance(x, dict) else 'N/A')

        # Lọc lịch sử
        lop_filter_list = ["Tất cả"] + sorted(list(teacher_class_options.keys()))
        selected_lop_filter = st.selectbox("Lọc lịch sử theo lớp:", lop_filter_list, key="announce_filter_hist")

        df_display = df.copy()
        if selected_lop_filter != "Tất cả":
            df_display = df_display[df_display['Tên Lớp'] == selected_lop_filter]

        if df_display.empty:
            st.caption("Không có thông báo nào.")
        else:
            for index, row in df_display.iterrows():
                with st.expander(f"📅 {row['Ngày gửi']} | {row['tieu_de']} (Lớp: {row['Tên Lớp']})"):
                    st.markdown(f"**Nội dung:** {row['noi_dung']}")

                    if st.button("🗑️ Xóa", key=f"del_ann_{row['id']}"):
                        delete_announcement(row['id'], giao_vien_id)
                        st.success("Đã xóa!")
                        st.cache_data.clear()
                        st.rerun()

    except Exception as e:
        st.error(f"Lỗi tải lịch sử: {e}")