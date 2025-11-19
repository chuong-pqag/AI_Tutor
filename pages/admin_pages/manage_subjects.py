# ===============================================
# 📘 Module Quản lý Môn học - manage_subjects.py (ĐÃ TÁI CẤU TRÚC)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
# Import các hàm tiện ích và supabase client
from . import crud_utils  # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase


# Hàm render() không nhận tham số
def render():
    """Hiển thị giao diện quản lý Môn học."""
    st.subheader("📘 Quản lý Môn học")
    tab_list, tab_add, tab_import_mh = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "mon_hoc"

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_mh_form", clear_on_submit=True):
            ten_mon = st.text_input("Tên môn học *")
            mo_ta = st.text_area("Mô tả (Tùy chọn)")
            khoi_ap_dung_str = st.text_input("Khối áp dụng (VD: 1,2,3)",
                                             help="Nhập các khối lớp cách nhau bởi dấu phẩy.")

            submitted = st.form_submit_button("Thêm môn học", width='stretch')  # <-- ĐÃ CẬP NHẬT
            if submitted:
                if not ten_mon:
                    st.error("Tên môn học không được để trống.")
                else:
                    khoi_ap_dung_list = []
                    error_khoi = False
                    if khoi_ap_dung_str:
                        try:
                            khoi_ap_dung_list = sorted(
                                [int(k.strip()) for k in khoi_ap_dung_str.split(',') if k.strip().isdigit()])
                            if not all(1 <= k <= 12 for k in khoi_ap_dung_list):
                                raise ValueError("Khối lớp phải nằm trong khoảng từ 1 đến 12.")
                        except ValueError as ve:
                            st.error(f"Định dạng Khối áp dụng không hợp lệ: {ve}")
                            error_khoi = True

                    if not error_khoi:
                        try:
                            insert_data = {
                                "ten_mon": ten_mon,
                                "mo_ta": mo_ta if mo_ta else None,
                                "khoi_ap_dung": khoi_ap_dung_list
                            }
                            supabase.table(table_name).insert(insert_data).execute()
                            st.success(f"Đã thêm môn học: {ten_mon}")
                            crud_utils.clear_cache_and_rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}. Tên môn học có thể đã tồn tại.")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        # Tự tải dữ liệu
        df_mh_original = crud_utils.load_data(table_name)

        if not df_mh_original.empty:
            df_mh_sorted = df_mh_original.sort_values(by="ten_mon").reset_index(drop=True)

            df_mh_display = df_mh_sorted.copy()

            if 'khoi_ap_dung' in df_mh_display.columns:
                try:
                    df_mh_display['khoi_ap_dung'] = df_mh_display['khoi_ap_dung'].apply(
                        lambda x: ', '.join(map(str, x)) if isinstance(x, list) and x else ''
                    )
                except Exception as e:
                    st.warning(f"Lỗi định dạng cột Khối áp dụng: {e}")
                    df_mh_display['khoi_ap_dung'] = ''

            df_mh_display = df_mh_display.rename(columns={"khoi_ap_dung": "Khối áp dụng"})

            cols_to_show = ["id", "ten_mon", "mo_ta", "Khối áp dụng"]
            cols_exist = [col for col in cols_to_show if col in df_mh_display.columns]

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_mh_display[cols_exist],
                key="mh_df_select",
                hide_index=True,
                width='stretch',  # <-- ĐÃ CẬP NHẬT
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                selected_index = selected_rows[0]
                original_id = df_mh_display.iloc[selected_index]['id']
                st.session_state['mh_selected_item_id'] = original_id

            if 'mh_selected_item_id' in st.session_state:
                selected_id = st.session_state['mh_selected_item_id']
                original_item_df = df_mh_original[df_mh_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            if selected_item_original:
                with st.expander("Sửa/Xóa Môn học đã chọn", expanded=True):
                    with st.form("edit_mh_form"):
                        st.text(f"ID: {selected_item_original['id']}")
                        ten_mon_edit = st.text_input("Tên môn học", value=selected_item_original.get('ten_mon', ''))
                        mo_ta_edit = st.text_area("Mô tả", value=selected_item_original.get('mo_ta', ''))

                        khoi_ap_dung_current = selected_item_original.get('khoi_ap_dung', [])
                        khoi_ap_dung_str_edit = st.text_input("Khối áp dụng (VD: 1,2,3)", value=', '.join(
                            map(str, khoi_ap_dung_current)) if khoi_ap_dung_current else '')

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("Lưu thay đổi", width='stretch'):  # <-- ĐÃ CẬP NHẬT
                            khoi_ap_dung_list_edit = []
                            if khoi_ap_dung_str_edit:
                                try:
                                    khoi_ap_dung_list_edit = sorted(
                                        [int(k.strip()) for k in khoi_ap_dung_str_edit.split(',') if
                                         k.strip().isdigit()])
                                except ValueError:
                                    st.error("Định dạng Khối áp dụng không hợp lệ.")
                                    st.stop()

                            update_data = {"ten_mon": ten_mon_edit, "mo_ta": mo_ta_edit,
                                           "khoi_ap_dung": khoi_ap_dung_list_edit}
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    "id"]).execute()
                                st.success("Cập nhật thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        if col_delete.form_submit_button("❌ Xóa môn học này", width='stretch'):  # <-- ĐÃ CẬP NHẬT
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original[
                                    "id"]).execute();
                                st.warning(f"Đã xóa!");
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}.")
                        if col_clear.form_submit_button("Hủy chọn", width='stretch'):  # <-- ĐÃ CẬP NHẬT
                            if 'mh_selected_item_id' in st.session_state: del st.session_state['mh_selected_item_id']
                            st.rerun()
        else:
            st.info("Chưa có môn học nào.")

        # --- Tab Import Excel ---
        with tab_import_mh:
            st.markdown("### 📤 Import môn học từ Excel")
            sample_data_mh = {'ten_mon': ['Toán'], 'mo_ta': ['Mô tả môn Toán'], 'khoi_ap_dung': ['1,2,3']}
            crud_utils.create_excel_download(pd.DataFrame(sample_data_mh), "mau_import_mon_hoc.xlsx",
                                             sheet_name='DanhSachMonHoc')
            st.caption("Nhập các khối áp dụng cách nhau bởi dấu phẩy (VD: 1,2,3)")

            uploaded_mh = st.file_uploader("Chọn file Excel Môn học", type=["xlsx"], key="mh_upload")
            if uploaded_mh:
                try:
                    df_upload_mh = pd.read_excel(uploaded_mh, dtype=str)
                    st.dataframe(df_upload_mh.head(), width='stretch')  # <-- ĐÃ CẬP NHẬT

                    if st.button("🚀 Import Môn Học", width='stretch'):  # <-- ĐÃ CẬP NHẬT
                        count = 0;
                        errors = []
                        with st.spinner("Đang import..."):
                            for index, row in df_upload_mh.iterrows():
                                try:
                                    ten_mon = str(row['ten_mon']).strip()
                                    mo_ta = str(row.get('mo_ta', '')).strip() if pd.notna(row.get('mo_ta')) else None
                                    khoi_ap_dung_str = str(row.get('khoi_ap_dung', '')).strip()

                                    if not ten_mon: raise ValueError("Tên môn trống.")

                                    khoi_ap_dung_list = []
                                    if khoi_ap_dung_str:
                                        try:
                                            khoi_ap_dung_list = [int(k.strip()) for k in khoi_ap_dung_str.split(',') if
                                                                 k.strip().isdigit()]
                                            khoi_ap_dung_list.sort()
                                        except ValueError:
                                            raise ValueError(
                                                "Định dạng Khối áp dụng không hợp lệ.")

                                    insert_data = {"ten_mon": ten_mon, "mo_ta": mo_ta,
                                                   "khoi_ap_dung": khoi_ap_dung_list}

                                    supabase.table(table_name).insert(insert_data).execute();
                                    count += 1
                                except Exception as e:
                                    errors.append(f"Dòng {index + 2}: {e}")
                        st.success(f"✅ Import {count} môn học.");
                        crud_utils.clear_all_cached_data()
                        if errors: st.error("Lỗi:"); st.code("\n".join(errors))
                except Exception as e:
                    st.error(f"Lỗi đọc file: {e}")