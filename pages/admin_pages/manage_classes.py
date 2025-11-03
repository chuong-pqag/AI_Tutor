# ===============================================
# 🏫 Module Quản lý Lớp học - manage_classes.py
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
# Import các hàm tiện ích và supabase client
from . import crud_utils # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase

def render():
    """Hiển thị giao diện quản lý Lớp học."""
    st.subheader("🏫 Quản lý Lớp học")
    tab_list, tab_add, tab_import = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "lop_hoc"

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_lop_form", clear_on_submit=True):
            ten_lop = st.text_input("Tên lớp *")
            khoi = st.number_input("Khối *", min_value=1, max_value=12, value=3)
            # Lấy năm hiện tại và năm sau làm giá trị mặc định
            current_year = datetime.date.today().year
            nam_hoc = st.text_input("Năm học", value=f"{current_year}-{current_year+1}")
            submitted = st.form_submit_button("Thêm lớp")
            if submitted:
                if not ten_lop:
                    st.error("Tên lớp không được để trống.")
                else:
                    try:
                        supabase.table(table_name).insert({"ten_lop": ten_lop, "khoi": khoi, "nam_hoc": nam_hoc}).execute()
                        st.success(f"Đã thêm lớp: {ten_lop}")
                        # Gọi hàm xóa cache và rerun từ crud_utils
                        crud_utils.clear_cache_and_rerun()
                    except Exception as e:
                        st.error(f"Lỗi thêm lớp: {e}")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        # Sử dụng hàm load_data từ crud_utils
        df_lop_original = crud_utils.load_data(table_name)

        if not df_lop_original.empty:
            # Sắp xếp theo tên lớp trước khi hiển thị
            df_lop_sorted = df_lop_original.sort_values(by="ten_lop").reset_index(drop=True)

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_lop_sorted, # Hiển thị bảng đã sắp xếp
                key="lop_df_select", # Key duy nhất cho dataframe này
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            # Lưu ID được chọn vào session
            if selected_rows:
                selected_index = selected_rows[0]
                original_id = df_lop_sorted.iloc[selected_index]['id'] # Lấy ID từ bảng sắp xếp
                st.session_state['lop_selected_item_id'] = original_id # Lưu ID vào session
            # else: # Xử lý trường hợp bỏ chọn (nếu cần)
            #     if 'lop_selected_item_id' in st.session_state:
            #         del st.session_state['lop_selected_item_id']

            # Lấy item gốc từ session nếu có
            if 'lop_selected_item_id' in st.session_state:
                selected_id = st.session_state['lop_selected_item_id']
                original_item_df = df_lop_original[df_lop_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # Hiển thị form nếu có item gốc được chọn
            if selected_item_original:
                with st.expander("Sửa/Xóa Lớp đã chọn", expanded=True):
                    with st.form("edit_lop_form"):
                        st.text(f"ID: {selected_item_original['id']}")
                        # Các trường input cho form Sửa
                        ten_lop_edit = st.text_input("Tên lớp", value=selected_item_original.get('ten_lop',''))
                        khoi_edit = st.number_input("Khối", min_value=1, max_value=12, value=selected_item_original.get('khoi',1))
                        nam_hoc_edit = st.text_input("Năm học", value=selected_item_original.get('nam_hoc',''))

                        col_update, col_delete, col_clear = st.columns(3)

                        # --- Nút Lưu ---
                        if col_update.form_submit_button("Lưu thay đổi"):
                            update_data = {"ten_lop": ten_lop_edit, "khoi": khoi_edit, "nam_hoc": nam_hoc_edit}
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original["id"]).execute()
                                st.success("Cập nhật thành công!")
                                crud_utils.clear_cache_and_rerun() # Xóa cache và rerun
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        # --- Nút Xóa ---
                        if col_delete.form_submit_button("❌ Xóa mục này"):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original["id"]).execute()
                                st.warning(f"Đã xóa ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun() # Xóa cache và rerun
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}. Có thể lớp này đang được sử dụng.")

                        # --- Nút Hủy ---
                        if col_clear.form_submit_button("Hủy chọn"):
                            # Xóa ID khỏi session và rerun
                            if 'lop_selected_item_id' in st.session_state: del st.session_state['lop_selected_item_id']
                            st.rerun()
        else:
            st.info("Chưa có lớp học nào.")

    # --- Tab Import Excel ---
    with tab_import:
        st.markdown("### 📤 Import lớp từ Excel")
        sample_data = {'ten_lop': ['Lớp 1A'], 'khoi': [1], 'nam_hoc': [f"{datetime.date.today().year}-{datetime.date.today().year+1}"]}
        # Gọi hàm tạo nút tải từ crud_utils
        crud_utils.create_excel_download(pd.DataFrame(sample_data), "mau_import_lop_hoc.xlsx", sheet_name='DanhSachLop')
        uploaded_file = st.file_uploader("Chọn file Excel Lớp", type=["xlsx"], key="lop_upload")
        if uploaded_file:
            try:
                # Đọc dữ liệu, đảm bảo kiểu cột 'khoi' là số nguyên
                df_upload = pd.read_excel(uploaded_file, dtype={'khoi': 'Int64', 'ten_lop': str, 'nam_hoc': str})
                st.dataframe(df_upload.head())
                if st.button("🚀 Import Lớp"):
                    count = 0; errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload.iterrows():
                            try:
                                ten_lop = str(row['ten_lop']).strip()
                                khoi = pd.to_numeric(row['khoi'], errors='coerce') # Chuyển sang số, lỗi trả về NaN
                                nam_hoc = str(row.get('nam_hoc', f"{datetime.date.today().year}-{datetime.date.today().year+1}")).strip()

                                if not ten_lop: raise ValueError("Tên lớp trống")
                                if pd.isna(khoi) or not (1 <= khoi <= 12): raise ValueError("Khối không hợp lệ (cần số từ 1-12)")
                                khoi = int(khoi) # Chuyển sang int sau khi kiểm tra

                                supabase.table(table_name).insert({"ten_lop": ten_lop, "khoi": khoi, "nam_hoc": nam_hoc}).execute(); count += 1
                            except Exception as e: errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import {count} lớp."); crud_utils.clear_cache_and_rerun()
                    if errors: st.error("Lỗi:"); st.code("\n".join(errors))
            except Exception as e: st.error(f"Lỗi đọc file: {e}")