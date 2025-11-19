# ===============================================
# 🏫 Module Quản lý Lớp học - manage_classes.py (Đã thêm lọc Năm học)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
# Import các hàm tiện ích và supabase client
from . import crud_utils
from backend.supabase_client import supabase


def render():
    st.subheader("🏫 Quản lý Lớp học")
    tab_list, tab_add, tab_import = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "lop_hoc"

    # === THÊM MỚI: LẤY NĂM HỌC ĐANG CHỌN ===
    selected_year = st.session_state.get("global_selected_school_year")
    # ========================================

    # --- Tab Thêm mới (Giữ nguyên) ---
    with tab_add:
        # Check if year is selected before adding a class
        if not selected_year:
            st.warning("⚠️ Vui lòng chọn Năm học trước khi thêm lớp mới.")

        with st.form("add_lop_form", clear_on_submit=True):
            st.markdown(f"**Năm học áp dụng:** **{selected_year}**")
            ten_lop = st.text_input("Tên lớp *")
            khoi = st.number_input("Khối *", min_value=1, max_value=12, value=1)

            # Năm học được tự động điền từ biến toàn cục
            nam_hoc_display = st.text_input("Năm học", value=selected_year, disabled=True)

            submitted = st.form_submit_button("➕ Thêm lớp", width='stretch')
            if submitted:
                if not ten_lop:
                    st.error("Tên lớp không được để trống.")
                elif not selected_year:
                    st.error("Không có Năm học được chọn.")
                else:
                    try:
                        # Sử dụng selected_year làm nam_hoc
                        supabase.table(table_name).insert(
                            {"ten_lop": ten_lop, "khoi": khoi, "nam_hoc": selected_year}).execute()
                        st.success(f"Đã thêm lớp: {ten_lop} ({selected_year})")
                        crud_utils.clear_all_cached_data()
                    except Exception as e:
                        st.error(f"Lỗi thêm lớp: {e}")

    # --- Tab Danh sách & Sửa/Xóa (ĐÃ SỬA: Thêm bộ lọc Năm học) ---
    with tab_list:
        # 1. Tải dữ liệu GỐC
        df_lop_original_all = crud_utils.load_data(table_name)

        # === LỌC DỮ LIỆU GỐC THEO NĂM HỌC ===
        df_lop_original = df_lop_original_all[df_lop_original_all['nam_hoc'] == selected_year].copy()

        if df_lop_original.empty and not df_lop_original_all.empty:
            st.warning(f"Không tìm thấy lớp học nào cho Năm học: **{selected_year}**.")

        st.caption(f"Đang hiển thị dữ liệu cho Năm học: **{selected_year}**")
        # ========================================

        # 2. Tạo Bộ lọc Khối
        st.markdown("##### 🔍 Lọc danh sách")
        if not df_lop_original.empty:
            # Lấy danh sách khối duy nhất từ DataFrame đã lọc và sắp xếp
            khoi_list_raw = df_lop_original['khoi'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])

            selected_khoi = st.selectbox(
                "Lọc theo Khối:",
                khoi_list,
                key="class_filter_khoi",
                index=0
            )
        else:
            st.selectbox("Lọc theo Khối:", ["Tất cả"], key="class_filter_khoi", index=0, disabled=True)
            selected_khoi = "Tất cả"  # Set default value

        st.markdown("---")

        # 3. Lọc DataFrame
        df_to_show = df_lop_original.copy()
        if selected_khoi != "Tất cả":
            df_to_show = df_to_show[df_to_show['khoi'] == selected_khoi]

        df_to_show = df_to_show.sort_values(by=["khoi", "ten_lop"]).reset_index(drop=True)

        # 4. Hiển thị DataFrame đã lọc và Form Sửa/Xóa
        if not df_to_show.empty:
            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_to_show,
                key="lop_df_select",
                hide_index=True,
                width='stretch',
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']
                st.session_state['lop_selected_item_id'] = original_id

            if 'lop_selected_item_id' in st.session_state:
                selected_id = st.session_state['lop_selected_item_id']
                # Lấy lại từ df_lop_original_all (DF gốc, không lọc)
                original_item_df = df_lop_original_all[df_lop_original_all['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 5. Form Sửa/Xóa
            if selected_item_original:
                with st.expander("📝 Sửa/Xóa Lớp đã chọn", expanded=True):
                    # Kiểm tra lớp được chọn có thuộc năm học đang xem không
                    is_current_year_class = (selected_item_original.get('nam_hoc') == selected_year)
                    disabled_editing = not is_current_year_class

                    if not is_current_year_class:
                        st.warning(
                            f"Lớp này thuộc Năm học **{selected_item_original.get('nam_hoc')}**. Không thể sửa/xóa khi đang xem năm học **{selected_year}**.")

                    with st.form("edit_lop_form"):
                        st.text(f"ID: {selected_item_original['id']}")

                        ten_lop_edit = st.text_input("Tên lớp", value=selected_item_original.get('ten_lop', ''),
                                                     disabled=disabled_editing)
                        khoi_edit = st.number_input("Khối", min_value=1, max_value=12,
                                                    value=selected_item_original.get('khoi', 1),
                                                    disabled=disabled_editing)
                        # Hiển thị nam_hoc đã lưu, không cho sửa
                        st.text_input("Năm học", value=selected_item_original.get('nam_hoc', ''), disabled=True)

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("💾 Lưu thay đổi", width='stretch',
                                                         disabled=disabled_editing):
                            update_data = {"ten_lop": ten_lop_edit, "khoi": khoi_edit}  # nam_hoc không đổi
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    "id"]).execute()
                                st.success("Cập nhật thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        if col_delete.form_submit_button("❌ Xóa mục này", width='stretch',
                                                         disabled=disabled_editing):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original["id"]).execute()
                                st.warning(f"Đã xóa ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}. Có thể lớp này đang được sử dụng.")

                        if col_clear.form_submit_button("Hủy chọn", width='stretch'):
                            if 'lop_selected_item_id' in st.session_state: del st.session_state['lop_selected_item_id']
                            st.rerun()
        else:
            if df_lop_original_all.empty:
                st.info("Chưa có lớp học nào.")
            else:
                st.info(f"Không tìm thấy lớp học nào cho Năm học: **{selected_year}**.")

    # --- Tab Import Excel (Sử dụng Năm học đã chọn) ---
    with tab_import:
        st.markdown("### 📤 Import lớp từ Excel")
        st.warning(f"Việc import sẽ áp dụng cho Năm học đang chọn: **{selected_year}**")
        sample_data = {'ten_lop': ['Lớp 1A'], 'khoi': [1]}
        crud_utils.create_excel_download(pd.DataFrame(sample_data), "mau_import_lop_hoc.xlsx", sheet_name='DanhSachLop')
        uploaded_file = st.file_uploader("Chọn file Excel Lớp", type=["xlsx"], key="lop_upload")
        if uploaded_file:
            try:
                # Đảm bảo nhập đúng kiểu dữ liệu (Int64 cho khoi)
                df_upload = pd.read_excel(uploaded_file, dtype={'khoi': 'Int64', 'ten_lop': str})
                st.dataframe(df_upload.head())
                if st.button("🚀 Import Lớp"):
                    if not selected_year:
                        st.error("Không có Năm học được chọn.")
                        st.stop()

                    count = 0;
                    errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload.iterrows():
                            try:
                                ten_lop = str(row['ten_lop']).strip()
                                khoi = pd.to_numeric(row['khoi'], errors='coerce')

                                if not ten_lop: raise ValueError("Tên lớp trống")
                                if pd.isna(khoi) or not (1 <= khoi <= 12): raise ValueError(
                                    "Khối không hợp lệ (cần số từ 1-12)")
                                khoi = int(khoi)

                                # Thêm cột nam_hoc từ biến toàn cục
                                supabase.table(table_name).insert(
                                    {"ten_lop": ten_lop, "khoi": khoi, "nam_hoc": selected_year}).execute();
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import {count} lớp.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file: {e}")