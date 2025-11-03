# ===============================================
# 🧑‍🏫 Module Quản lý Phân công Giảng dạy - manage_assignments.py
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
# Import các hàm tiện ích và supabase client
from . import crud_utils # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase

def render():
    """Hiển thị giao diện quản lý Phân công Giảng dạy."""
    st.subheader("🧑‍🏫 Quản lý Phân công Giảng dạy")
    tab_list, tab_add, tab_import = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "phan_cong_giang_day"

    # --- Tải dữ liệu cần thiết cho Select Boxes ---
    gv_df = crud_utils.load_data("giao_vien")
    gv_options = {row["ho_ten"]: str(row["id"]) for _, row in gv_df.iterrows()} if not gv_df.empty else {}
    gv_email_to_id = {row["email"]: str(row["id"]) for _, row in gv_df.iterrows()} if not gv_df.empty else {} # Dùng cho import

    lop_df = crud_utils.load_data("lop_hoc")
    lop_options = {row["ten_lop"]: str(row["id"]) for _, row in lop_df.iterrows()} if not lop_df.empty else {}

    mh_df = crud_utils.load_data("mon_hoc")
    mh_options = {row["ten_mon"]: str(row["id"]) for _, row in mh_df.iterrows()} if not mh_df.empty else {}

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_assignment_form", clear_on_submit=True):
            st.markdown("#### Thêm phân công mới")
            # Kiểm tra xem có đủ dữ liệu để tạo phân công không
            if not gv_options or not lop_options or not mh_options:
                st.warning("⚠️ Cần có ít nhất một Giáo viên, Lớp học và Môn học trong hệ thống để tạo phân công.")
                st.form_submit_button("Thêm phân công", disabled=True) # Vô hiệu hóa nút
            else:
                gv_ten = st.selectbox("Chọn Giáo viên *", list(gv_options.keys()))
                lop_ten = st.selectbox("Chọn Lớp học *", list(lop_options.keys()))
                mh_ten = st.selectbox("Chọn Môn học *", list(mh_options.keys()))
                vai_tro = st.selectbox("Vai trò", ["Giảng dạy", "Chủ nhiệm"])
                # Lấy năm hiện tại và năm sau làm giá trị mặc định
                current_year = datetime.date.today().year
                nam_hoc = st.text_input("Năm học", value=f"{current_year}-{current_year+1}")

                submitted = st.form_submit_button("Thêm phân công")
                if submitted:
                    selected_gv_id = gv_options.get(gv_ten)
                    selected_lop_id = lop_options.get(lop_ten)
                    selected_mh_id = mh_options.get(mh_ten)

                    if not selected_gv_id or not selected_lop_id or not selected_mh_id:
                        st.error("Lựa chọn Giáo viên, Lớp hoặc Môn học không hợp lệ.")
                    else:
                        try:
                            insert_data = {
                                "giao_vien_id": selected_gv_id,
                                "lop_id": selected_lop_id,
                                "mon_hoc_id": selected_mh_id,
                                "vai_tro": vai_tro,
                                "nam_hoc": nam_hoc
                            }
                            supabase.table(table_name).insert(insert_data).execute()
                            st.success(f"Đã phân công GV {gv_ten} dạy môn {mh_ten} cho lớp {lop_ten}.")
                            crud_utils.clear_cache_and_rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi thêm phân công: {e}")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        df_assign_original = crud_utils.load_data(table_name) # Dữ liệu gốc

        if not df_assign_original.empty:
            # Map UUIDs sang Tên để hiển thị
            gv_id_map = {id_: name for name, id_ in gv_options.items()}
            lop_id_map = {id_: name for name, id_ in lop_options.items()}
            mh_id_map = {id_: name for name, id_ in mh_options.items()}

            df_assign_display = df_assign_original.copy()
            df_assign_display['giao_vien_id'] = df_assign_display['giao_vien_id'].astype(str).map(gv_id_map).fillna("N/A")
            df_assign_display['lop_id'] = df_assign_display['lop_id'].astype(str).map(lop_id_map).fillna("N/A")
            df_assign_display['mon_hoc_id'] = df_assign_display['mon_hoc_id'].astype(str).map(mh_id_map).fillna("N/A")

            df_assign_display = df_assign_display.rename(columns={
                "giao_vien_id": "Giáo viên",
                "lop_id": "Lớp học",
                "mon_hoc_id": "Môn học",
                "vai_tro": "Vai trò",
                "nam_hoc": "Năm học"
            })
            cols_display_assign = ["id", "Giáo viên", "Lớp học", "Môn học", "Vai trò", "Năm học"] # Các cột cần hiển thị

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_assign_display[cols_display_assign],
                key="assign_df_select",
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
                original_id = df_assign_display.iloc[selected_index]['id'] # Lấy ID từ bảng hiển thị
                st.session_state['assign_selected_item_id'] = original_id
            # else:
            #      if 'assign_selected_item_id' in st.session_state: del st.session_state['assign_selected_item_id']

            # Lấy item gốc từ session nếu có
            if 'assign_selected_item_id' in st.session_state:
                selected_id = st.session_state['assign_selected_item_id']
                original_item_df = df_assign_original[df_assign_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # Hiển thị form nếu có item gốc được chọn
            if selected_item_original:
                with st.expander("Sửa/Xóa Phân công đã chọn", expanded=True):
                    with st.form("edit_assign_form"):
                        st.text(f"ID Phân công: {selected_item_original['id']}")
                        # Hiển thị thông tin GV, Lớp, Môn (không cho sửa trực tiếp ở đây)
                        st.text(f"Giáo viên: {gv_id_map.get(str(selected_item_original.get('giao_vien_id')), 'N/A')}")
                        st.text(f"Lớp học: {lop_id_map.get(str(selected_item_original.get('lop_id')), 'N/A')}")
                        st.text(f"Môn học: {mh_id_map.get(str(selected_item_original.get('mon_hoc_id')), 'N/A')}")

                        # Cho phép sửa Vai trò và Năm học
                        vai_tro_options = ["Giảng dạy", "Chủ nhiệm"]
                        current_vai_tro = selected_item_original.get('vai_tro', 'Giảng dạy')
                        vai_tro_idx = vai_tro_options.index(current_vai_tro) if current_vai_tro in vai_tro_options else 0
                        vai_tro_edit = st.selectbox("Vai trò", vai_tro_options, index=vai_tro_idx)
                        nam_hoc_edit = st.text_input("Năm học", value=selected_item_original.get('nam_hoc',''))

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("Lưu thay đổi"):
                            update_data = {
                                "vai_tro": vai_tro_edit,
                                "nam_hoc": nam_hoc_edit
                            }
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original["id"]).execute()
                                st.success("Cập nhật phân công thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        if col_delete.form_submit_button("❌ Xóa phân công này"):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original["id"]).execute()
                                st.warning(f"Đã xóa phân công ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}")

                        if col_clear.form_submit_button("Hủy chọn"):
                             if 'assign_selected_item_id' in st.session_state: del st.session_state['assign_selected_item_id']
                             st.rerun()
        else:
            st.info("Chưa có phân công giảng dạy nào.")

    # --- Tab Import Excel ---
    with tab_import:
        st.markdown("### 📤 Import phân công từ Excel")
        sample_data_assign = {
            'giao_vien_email': ['b.nv@email.com'], # Dùng email để tìm ID GV
            'lop_ten': ['Lớp 3A'],           # Dùng tên lớp để tìm ID Lớp
            'mon_hoc_ten': ['Toán'],         # Dùng tên môn để tìm ID Môn
            'vai_tro': ['Giảng dạy'],
            'nam_hoc': [f"{datetime.date.today().year}-{datetime.date.today().year+1}"]
        }
        crud_utils.create_excel_download(pd.DataFrame(sample_data_assign), "mau_import_phan_cong.xlsx", sheet_name='PhanCong')
        st.caption("Sử dụng Email giáo viên, Tên lớp, Tên môn học để hệ thống tự động tìm ID.")

        uploaded_assign = st.file_uploader("Chọn file Excel Phân công", type=["xlsx"], key="assign_upload")
        if uploaded_assign:
            try:
                df_upload_assign = pd.read_excel(uploaded_assign, dtype=str) # Đọc tất cả là chuỗi
                st.dataframe(df_upload_assign.head())

                # Kiểm tra xem có đủ dữ liệu GV, Lớp, Môn để map không
                if not gv_email_to_id or not lop_options or not mh_options:
                    st.error("Lỗi: Thiếu dữ liệu Giáo viên, Lớp học hoặc Môn học trong hệ thống để thực hiện import.")
                elif st.button("🚀 Import Phân công"):
                    count = 0; errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_assign.iterrows():
                            try:
                                gv_email = str(row['giao_vien_email']).strip()
                                lop_ten = str(row['lop_ten']).strip()
                                mh_ten = str(row['mon_hoc_ten']).strip()
                                vai_tro = str(row.get('vai_tro', 'Giảng dạy')).strip().capitalize() # Chuẩn hóa
                                nam_hoc = str(row.get('nam_hoc', f"{datetime.date.today().year}-{datetime.date.today().year+1}")).strip()

                                # Tìm UUIDs dựa trên thông tin từ Excel
                                gv_id = gv_email_to_id.get(gv_email)
                                lop_id = lop_options.get(lop_ten)
                                mh_id = mh_options.get(mh_ten)

                                if not gv_id: raise ValueError(f"Không tìm thấy giáo viên với email '{gv_email}'.")
                                if not lop_id: raise ValueError(f"Không tìm thấy lớp học '{lop_ten}'.")
                                if not mh_id: raise ValueError(f"Không tìm thấy môn học '{mh_ten}'.")
                                if vai_tro not in ['Giảng dạy', 'Chủ nhiệm']: raise ValueError("Vai trò không hợp lệ (chỉ 'Giảng dạy' hoặc 'Chủ nhiệm').")

                                insert_data = {
                                    "giao_vien_id": gv_id,
                                    "lop_id": lop_id,
                                    "mon_hoc_id": mh_id,
                                    "vai_tro": vai_tro,
                                    "nam_hoc": nam_hoc
                                }
                                # Có thể thêm kiểm tra trùng lặp phân công nếu cần
                                supabase.table(table_name).insert(insert_data).execute(); count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import thành công {count} phân công."); crud_utils.clear_cache_and_rerun()
                    if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file Excel: {e}")