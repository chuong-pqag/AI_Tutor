# ===============================================
# 👩‍🏫 Module Quản lý Giáo viên - manage_teachers.py
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
# Import các hàm tiện ích và supabase client
from . import crud_utils # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase

def render():
    """Hiển thị giao diện quản lý Giáo viên."""
    st.subheader("👩‍🏫 Quản lý Giáo viên")
    tab_list, tab_add, tab_import_gv = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "giao_vien"

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_gv_form", clear_on_submit=True):
            ho_ten = st.text_input("Họ tên *")
            email = st.text_input("Email *")
            mat_khau = st.text_input("Mật khẩu *", type="password")
            # Thêm các trường tùy chọn khác nếu cần (mon_hoc, vai_tro)
            submitted = st.form_submit_button("Thêm giáo viên")
            if submitted:
                if not ho_ten or not email or not mat_khau:
                    st.error("Vui lòng nhập đủ thông tin bắt buộc (*).")
                else:
                    try:
                        insert_data = {"ho_ten": ho_ten, "email": email, "mat_khau": mat_khau}
                        supabase.table(table_name).insert(insert_data).execute()
                        st.success(f"Đã thêm giáo viên: {ho_ten}")
                        crud_utils.clear_cache_and_rerun()
                    except Exception as e:
                        st.error(f"Lỗi thêm giáo viên: {e}. Email có thể đã tồn tại.")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        df_gv_original = crud_utils.load_data(table_name) # Dữ liệu gốc

        if not df_gv_original.empty:
            # Sắp xếp theo họ tên
            df_gv_sorted = df_gv_original.sort_values(by="ho_ten").reset_index(drop=True)
            # Chọn cột hiển thị
            cols_display = [col for col in df_gv_sorted.columns if col not in ['mat_khau', 'created_at']] # Ẩn mật khẩu, ngày tạo

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_gv_sorted[cols_display],
                key="gv_df_select",
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
                original_id = df_gv_sorted.iloc[selected_index]['id']
                st.session_state['gv_selected_item_id'] = original_id
            # else:
            #      if 'gv_selected_item_id' in st.session_state: del st.session_state['gv_selected_item_id']

            # Lấy item gốc từ session nếu có
            if 'gv_selected_item_id' in st.session_state:
                selected_id = st.session_state['gv_selected_item_id']
                original_item_df = df_gv_original[df_gv_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # Hiển thị form nếu có item gốc được chọn
            if selected_item_original:
                with st.expander("Sửa/Xóa Giáo viên đã chọn", expanded=True):
                    with st.form("edit_gv_form"):
                        st.text(f"ID: {selected_item_original['id']}")
                        ho_ten_edit = st.text_input("Họ tên", value=selected_item_original.get('ho_ten',''))
                        email_edit = st.text_input("Email", value=selected_item_original.get('email',''))
                        mat_khau_edit = st.text_input("Mật khẩu mới (bỏ trống nếu không đổi)", type="password")
                        # Thêm các trường khác nếu cần sửa (mon_hoc, vai_tro)

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("Lưu thay đổi"):
                            update_data = {"ho_ten": ho_ten_edit, "email": email_edit}
                            if mat_khau_edit:
                                update_data["mat_khau"] = mat_khau_edit
                            # Xử lý các trường khác nếu có
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original['id']).execute()
                                st.success("Cập nhật thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        if col_delete.form_submit_button("❌ Xóa giáo viên này"):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning(f"Đã xóa ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}. Giáo viên có thể đang được phân công.")

                        if col_clear.form_submit_button("Hủy chọn"):
                             if 'gv_selected_item_id' in st.session_state: del st.session_state['gv_selected_item_id']
                             st.rerun()
        else:
            st.info("Chưa có giáo viên nào.")

    # --- Tab Import Excel ---
    with tab_import_gv:
        st.markdown("### 📤 Import giáo viên từ Excel")
        sample_data_gv = {'ho_ten': ['Nguyễn Văn B'], 'email': ['b.nv@email.com'], 'mat_khau': ['matkhau123']}
        # Gọi hàm tạo nút tải từ crud_utils
        crud_utils.create_excel_download(pd.DataFrame(sample_data_gv), "mau_import_giao_vien.xlsx", sheet_name='DanhSachGiaoVien')

        uploaded_gv = st.file_uploader("Chọn file Excel GV", type=["xlsx"], key="gv_upload")
        if uploaded_gv:
            try:
                df_upload_gv = pd.read_excel(uploaded_gv, dtype=str) # Đọc tất cả là chuỗi
                st.dataframe(df_upload_gv.head())
                if st.button("🚀 Import Giáo Viên"):
                    count = 0; errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_gv.iterrows():
                            try:
                                ho_ten = str(row['ho_ten']).strip()
                                email = str(row['email']).strip()
                                mat_khau = str(row['mat_khau']).strip()

                                if not ho_ten or not email or not mat_khau:
                                    raise ValueError("Thiếu thông tin bắt buộc (ho_ten, email, mat_khau).")
                                # Thêm kiểm tra định dạng email cơ bản
                                if "@" not in email or "." not in email.split('@')[-1]: # Kiểm tra @ và dấu . sau @
                                    raise ValueError("Định dạng email không hợp lệ.")

                                insert_data = {"ho_ten": ho_ten, "email": email, "mat_khau": mat_khau}
                                # Thêm các cột tùy chọn khác từ Excel nếu có (mon_hoc, vai_tro)
                                # if 'mon_hoc' in row and pd.notna(row['mon_hoc']): insert_data['mon_hoc'] = str(row['mon_hoc']).strip()
                                # if 'vai_tro' in row and pd.notna(row['vai_tro']): insert_data['vai_tro'] = str(row['vai_tro']).strip()

                                supabase.table(table_name).insert(insert_data).execute()
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")

                    st.success(f"✅ Import thành công {count} giáo viên."); crud_utils.clear_cache_and_rerun()
                    if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file Excel: {e}")