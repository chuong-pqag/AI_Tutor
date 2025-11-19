# File: pages/teacher_pages/render_tab_announce.py
import streamlit as st
import pandas as pd
from backend.data_service import (
    create_announcement,
    get_announcements_for_teacher,
    delete_announcement
)


def render(giao_vien_id, teacher_class_options, TAB_NAMES):
    st.subheader("📣 Gửi Thông báo Chung")

    if not teacher_class_options:
        st.warning("Bạn cần được phân công lớp để gửi thông báo.")
        return

    # --- 1. FORM GỬI THÔNG BÁO ---
    with st.form("new_announcement_form", clear_on_submit=True):
        st.markdown("#### Tạo thông báo mới")

        # Lấy danh sách lớp
        lop_ten = st.selectbox("1. Chọn lớp nhận thông báo:", list(teacher_class_options.keys()),
                               key="announce_lop_select")
        selected_lop_id = teacher_class_options.get(lop_ten)

        tieu_de = st.text_input("2. Tiêu đề thông báo *")
        noi_dung = st.text_area("3. Nội dung *")

        submitted = st.form_submit_button("🚀 Gửi thông báo", use_container_width=True)

        if submitted:
            if not tieu_de or not noi_dung:
                st.error("Tiêu đề và Nội dung không được để trống.")
            elif not selected_lop_id:
                st.error("Lỗi: Không tìm thấy ID Lớp học.")
            else:
                try:
                    create_announcement(
                        giao_vien_id=giao_vien_id,
                        lop_id=selected_lop_id,
                        tieu_de=tieu_de,
                        noi_dung=noi_dung
                    )
                    st.success(f"Đã gửi thông báo '{tieu_de}' đến lớp {lop_ten}!")
                    st.cache_data.clear()  # Xóa cache để tải lại danh sách
                except Exception as e:
                    st.error(f"Lỗi khi gửi thông báo: {e}")

    st.markdown("---")

    # --- 2. DANH SÁCH THÔNG BÁO ĐÃ GỬI ---
    st.subheader("📑 Lịch sử thông báo đã gửi")

    try:
        all_announcements = get_announcements_for_teacher(giao_vien_id)

        if not all_announcements:
            st.info("Bạn chưa gửi thông báo nào.")
            return

        df = pd.DataFrame(all_announcements)
        df['Ngày gửi'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        df['Lớp'] = df['lop_hoc'].apply(lambda x: x.get('ten_lop', 'N/A') if isinstance(x, dict) else 'N/A')

        # Lọc (nếu cần)
        lop_filter_list = ["Tất cả"] + sorted(list(teacher_class_options.keys()))
        selected_lop_filter = st.selectbox("Lọc theo lớp:", lop_filter_list, key="announce_filter_lop")

        df_display = df.copy()
        if selected_lop_filter != "Tất cả":
            df_display = df_display[df_display['Lớp'] == selected_lop_filter]

        if df_display.empty:
            st.info("Không tìm thấy thông báo nào cho lớp này.")
            return

        # Hiển thị
        for index, row in df_display.iterrows():
            with st.expander(f"**{row['tieu_de']}** (Lớp: {row['Lớp']} - Ngày: {row['Ngày gửi']})"):
                st.markdown(row['noi_dung'])

                # Nút Xóa
                if st.button("❌ Xóa thông báo này", key=f"del_announce_{row['id']}", type="secondary"):
                    try:
                        delete_announcement(row['id'], giao_vien_id)
                        st.success(f"Đã xóa thông báo '{row['tieu_de']}'!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi xóa: {e}")

    except Exception as e:
        st.error(f"Lỗi khi tải lịch sử thông báo: {e}")