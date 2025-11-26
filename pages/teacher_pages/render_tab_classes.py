# File: pages/teacher_pages/render_tab_classes.py
import streamlit as st
import pandas as pd


def render(teacher_classes, teacher_students, teacher_class_options):
    st.subheader("📘 Danh sách lớp bạn phụ trách")

    if not teacher_classes:
        st.info("Bạn chưa được phân công lớp nào.")
        return

    # 1. TẠO BỘ LỌC LỚP HỌC
    class_name_list = sorted(list(teacher_class_options.keys()))
    class_name_list_with_all = ["Tất cả"] + class_name_list

    selected_class_name = st.selectbox(
        "🔎 **Lọc theo Lớp học:**",
        class_name_list_with_all,
        key="class_filter_tab1"
    )

    st.markdown("---")

    # 2. HIỂN THỊ DANH SÁCH HỌC SINH TƯƠNG ỨNG

    if selected_class_name == "Tất cả":
        st.caption(f"Hiển thị chi tiết tất cả **{len(teacher_classes)}** lớp.")

        for c in teacher_classes:
            st.markdown(f"##### **{c['ten_lop']}** (Khối {c['khoi']})")

            # Lọc học sinh cho lớp hiện tại
            hs = [s for s in teacher_students if str(s.get("lop_id")) == str(c.get("id"))]

            if hs:
                hs_df_display = pd.DataFrame(hs)[
                    ["ho_ten", "ma_hoc_sinh", "email", "ngay_sinh", "gioi_tinh"]].rename(
                    columns={"ho_ten": "Họ tên", "ma_hoc_sinh": "Mã HS", "ngay_sinh": "Ngày sinh",
                             "gioi_tinh": "Giới tính"}
                )
                st.dataframe(hs_df_display, use_container_width=True, hide_index=True)
            else:
                st.caption("Lớp này chưa có học sinh nào.")

    else:
        # Xử lý khi chỉ chọn 1 lớp
        selected_lop_id = teacher_class_options[selected_class_name]
        selected_class_info = next((c for c in teacher_classes if str(c['id']) == selected_lop_id), None)

        if selected_class_info:
            st.markdown(f"#### **{selected_class_name}** (Khối {selected_class_info['khoi']})")

            # Lọc học sinh cho lớp đã chọn
            hs = [s for s in teacher_students if str(s.get("lop_id")) == str(selected_lop_id)]

            if hs:
                hs_df_display = pd.DataFrame(hs)[
                    ["ho_ten", "ma_hoc_sinh", "email", "ngay_sinh", "gioi_tinh"]].rename(
                    columns={"ho_ten": "Họ tên", "ma_hoc_sinh": "Mã HS", "ngay_sinh": "Ngày sinh",
                             "gioi_tinh": "Giới tính"}
                )
                st.dataframe(hs_df_display, use_container_width=True, hide_index=True)
            else:
                st.caption("Lớp này chưa có học sinh nào.")
        else:
            st.error("Không tìm thấy thông tin lớp học.")