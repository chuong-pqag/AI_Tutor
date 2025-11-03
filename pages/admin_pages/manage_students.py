# ===============================================
# 👧 Module Quản lý Học sinh - manage_students.py
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid # Import uuid để kiểm tra
# Import các hàm tiện ích và supabase client
from . import crud_utils # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase

def render(lop_options):
    """
    Hiển thị giao diện quản lý Học sinh.
    Args:
        lop_options (dict): Dictionary {tên_lớp: uuid_string}
    """
    st.subheader("👧 Quản lý Học sinh")
    tab_list, tab_add, tab_import_hs = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "hoc_sinh"

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_hs_form", clear_on_submit=True):
            ho_ten = st.text_input("Họ tên *")
            ma_hoc_sinh = st.text_input("Mã HS *")
            mat_khau = st.text_input("Mã PIN (4 số) *", type="password", max_chars=4)
            # Chỉ hiển thị selectbox nếu có lớp
            lop_ten = st.selectbox("Lớp *", list(lop_options.keys())) if lop_options else None
            ngay_sinh = st.date_input("Ngày sinh", value=None, min_value=datetime.date(1990, 1, 1), max_value=datetime.date.today())
            gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác", None], index=3)
            email = st.text_input("Email (Tùy chọn)") # Thêm email nếu cần

            submitted = st.form_submit_button("Thêm học sinh")
            if submitted:
                if not lop_options or lop_ten is None:
                    st.error("Chưa có lớp học nào hoặc chưa chọn lớp.")
                elif not ho_ten or not ma_hoc_sinh or not mat_khau:
                    st.error("Nhập đủ thông tin bắt buộc (*).")
                elif len(mat_khau) != 4:
                    st.error("Mã PIN phải là 4 chữ số.")
                else:
                    try:
                        insert_data = {
                            "ho_ten": ho_ten,
                            "ma_hoc_sinh": ma_hoc_sinh,
                            "mat_khau": mat_khau,
                            "lop_id": lop_options.get(lop_ten), # UUID string
                            "ngay_sinh": ngay_sinh.isoformat() if ngay_sinh else None,
                            "gioi_tinh": gioi_tinh,
                            "email": email if email else None # Chỉ thêm nếu có giá trị
                        }
                        supabase.table(table_name).insert(insert_data).execute()
                        st.success("Đã thêm học sinh mới!")
                        crud_utils.clear_cache_and_rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}. Mã HS có thể đã tồn tại.")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        df_hs_original = crud_utils.load_data(table_name) # Dữ liệu gốc
        if not df_hs_original.empty:
            # Tạo DataFrame hiển thị với Tên lớp thay vì ID
            lop_id_map = {str(id_): name for name, id_ in lop_options.items()}
            df_hs_display = df_hs_original.copy()
            df_hs_display['lop_id'] = df_hs_display['lop_id'].astype(str).map(lop_id_map).fillna("Chưa xếp lớp")
            df_hs_display = df_hs_display.rename(columns={"lop_id": "Tên lớp"})
            cols_to_show = ["id", "ho_ten", "ma_hoc_sinh", "Tên lớp", "ngay_sinh", "gioi_tinh", "email"]
            cols_exist = [col for col in cols_to_show if col in df_hs_display.columns]

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_hs_display[cols_exist],
                key="hs_df_select",
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
                original_id = df_hs_display.iloc[selected_index]['id'] # Lấy ID từ bảng hiển thị
                st.session_state['hs_selected_item_id'] = original_id
            # else:
            #      if 'hs_selected_item_id' in st.session_state: del st.session_state['hs_selected_item_id']

            # Lấy item gốc từ session nếu có
            if 'hs_selected_item_id' in st.session_state:
                selected_id = st.session_state['hs_selected_item_id']
                original_item_df = df_hs_original[df_hs_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # Hiển thị form nếu có item gốc được chọn
            if selected_item_original:
                with st.expander("Sửa/Xóa Học sinh đã chọn", expanded=True):
                    with st.form("edit_hs_form"):
                        st.text(f"ID: {selected_item_original['id']}")
                        # Lấy lại options lớp mới nhất
                        lop_df_local = crud_utils.load_data("lop_hoc")
                        lop_options_local = {row["ten_lop"]: str(row["id"]) for _, row in lop_df_local.iterrows()} if not lop_df_local.empty else {}

                        ho_ten_edit = st.text_input("Họ tên", value=selected_item_original.get("ho_ten", ""))
                        st.text_input("Mã HS", value=selected_item_original.get("ma_hoc_sinh", ""), disabled=True) # Không cho sửa Mã HS
                        mat_khau_edit = st.text_input("PIN mới (4 số, bỏ trống nếu k đổi)", type="password", max_chars=4)

                        # Xử lý chọn lớp
                        current_lop_id = str(selected_item_original.get("lop_id", ""))
                        current_lop_name = next((name for name, id_ in lop_options_local.items() if id_ == current_lop_id), None)
                        index = list(lop_options_local.keys()).index(current_lop_name) if current_lop_name in lop_options_local else 0
                        lop_ten_edit = st.selectbox("Lớp", list(lop_options_local.keys()), index=index) if lop_options_local else None

                        # Xử lý ngày sinh
                        ngs_val = selected_item_original.get("ngay_sinh")
                        ngay_sinh_obj = None
                        if ngs_val:
                            try: ngay_sinh_obj = datetime.date.fromisoformat(str(ngs_val))
                            except: pass # Bỏ qua nếu định dạng sai
                        ngay_sinh_edit = st.date_input("Ngày sinh", value=ngay_sinh_obj, min_value=datetime.date(1990, 1, 1), max_value=datetime.date.today())

                        # Xử lý giới tính
                        gt_options = ["Nam", "Nữ", "Khác", None]
                        gt_val = selected_item_original.get("gioi_tinh")
                        gt_index = gt_options.index(gt_val) if gt_val in gt_options else 3
                        gioi_tinh_edit = st.selectbox("Giới tính", gt_options, index=gt_index)
                        email_edit = st.text_input("Email", value=selected_item_original.get("email","") if selected_item_original.get("email") else "") # Hiển thị "" nếu là None


                        col_update, col_delete, col_clear = st.columns(3)

                        # --- Nút Lưu ---
                        if col_update.form_submit_button("Lưu thay đổi"):
                            update_data = {
                                "ho_ten": ho_ten_edit,
                                "lop_id": lop_options_local.get(lop_ten_edit) if lop_ten_edit else None,
                                "ngay_sinh": ngay_sinh_edit.isoformat() if ngay_sinh_edit else None,
                                "gioi_tinh": gioi_tinh_edit,
                                "email": email_edit if email_edit else None
                            }
                            pin_valid = True
                            if mat_khau_edit and len(mat_khau_edit) == 4:
                                update_data["mat_khau"] = mat_khau_edit
                            elif mat_khau_edit:
                                st.warning("Mã PIN mới không hợp lệ (cần 4 số), sẽ không được cập nhật.")
                                pin_valid = False # Đánh dấu PIN không hợp lệ

                            if pin_valid: # Chỉ update nếu PIN hợp lệ hoặc không thay đổi
                                try:
                                    supabase.table(table_name).update(update_data).eq("id", selected_item_original['id']).execute()
                                    st.success("Cập nhật học sinh thành công!")
                                    crud_utils.clear_cache_and_rerun()
                                except Exception as e:
                                    st.error(f"Lỗi cập nhật học sinh: {e}")

                        # --- Nút Xóa ---
                        if col_delete.form_submit_button("❌ Xóa học sinh này"):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning("Đã xóa học sinh!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa học sinh: {e}")

                        # --- Nút Hủy ---
                        if col_clear.form_submit_button("Hủy chọn"):
                             if 'hs_selected_item_id' in st.session_state: del st.session_state['hs_selected_item_id']
                             st.rerun()
        else:
            st.info("Chưa có học sinh nào.")

    # --- Tab Import Excel ---
    with tab_import_hs:
         st.markdown("### 📤 Import danh sách học sinh từ file Excel")
         sample_data_hs = {'ho_ten': ['Nguyễn Test A'], 'ngay_sinh': ['2016-01-01'], 'gioi_tinh': ['Nam'], 'email': ['test@email.com'], 'lop_id': ['UUID CỦA LỚP'], 'ma_hoc_sinh': ['HS9999'], 'mat_khau': ['1234']}
         crud_utils.create_excel_download(pd.DataFrame(sample_data_hs), "mau_import_hoc_sinh.xlsx", sheet_name='DanhSachHocSinh')
         st.caption("Quan trọng: Cột 'lop_id' phải chứa UUID (dạng text) của lớp học.")
         uploaded_file_hs = st.file_uploader("Chọn file Excel HS", type=["xlsx"], key="hs_upload")
         if uploaded_file_hs:
             try:
                 df_upload_hs = pd.read_excel(uploaded_file_hs, dtype=str); st.dataframe(df_upload_hs.head())
                 valid_lop_ids = list(lop_options.values()) if lop_options else [] # Lấy UUIDs từ options đã load

                 if not valid_lop_ids:
                     st.error("Chưa có lớp học nào trong hệ thống để import học sinh.")
                 elif st.button("🚀 Bắt đầu Import Học Sinh"):
                     count_hs = 0; errors_hs = []
                     with st.spinner("Đang import..."):
                         for index, row in df_upload_hs.iterrows():
                             try:
                                 # Validate và chuẩn hóa dữ liệu
                                 ho_ten = str(row['ho_ten']).strip(); ma_hoc_sinh = str(row['ma_hoc_sinh']).strip(); mat_khau = str(row['mat_khau']).strip(); lop_id = str(row['lop_id']).strip()
                                 ngay_sinh_str = str(row.get('ngay_sinh', '')).strip(); gioi_tinh = str(row.get('gioi_tinh', '')).strip().capitalize() if pd.notna(row.get('gioi_tinh')) else None # Chuẩn hóa Nam/Nữ
                                 email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None

                                 if not ho_ten or not ma_hoc_sinh or not mat_khau or not lop_id: raise ValueError("Thiếu thông tin (*).")
                                 if len(mat_khau) != 4: raise ValueError("PIN phải 4 ký tự.")
                                 if lop_id not in valid_lop_ids: raise ValueError(f"Lop ID '{lop_id}' không hợp lệ.")
                                 if gioi_tinh and gioi_tinh not in ["Nam", "Nữ", "Khác"]: raise ValueError(f"Giới tính '{gioi_tinh}' không hợp lệ.")

                                 ngay_sinh_iso = None;
                                 if ngay_sinh_str:
                                     try: ngay_sinh_iso = datetime.datetime.strptime(ngay_sinh_str.split(" ")[0], '%Y-%m-%d').date().isoformat()
                                     except: raise ValueError("Ngày sinh sai (cần YYYY-MM-DD).")

                                 supabase.table(table_name).insert({
                                     "ho_ten": ho_ten, "ma_hoc_sinh": ma_hoc_sinh, "mat_khau": mat_khau,
                                     "lop_id": lop_id, "ngay_sinh": ngay_sinh_iso,
                                     "gioi_tinh": gioi_tinh, "email": email
                                     }).execute(); count_hs += 1
                             except Exception as e: errors_hs.append(f"Dòng {index + 2}: {e}")
                     st.success(f"✅ Import {count_hs} học sinh."); crud_utils.clear_cache_and_rerun()
                     if errors_hs: st.error("Lỗi:"); st.code("\n".join(errors_hs))
             except Exception as e: st.error(f"Lỗi đọc file HS: {e}")