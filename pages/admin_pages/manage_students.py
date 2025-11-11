# ===============================================
# 👧 Module Quản lý Học sinh - manage_students.py (Đã thêm lọc Khối/Lớp)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid  # Import uuid để kiểm tra
# Import các hàm tiện ích và supabase client
from . import crud_utils  # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase


def render(lop_options):
    """
    Hiển thị giao diện quản lý Học sinh.
    Args:
        lop_options (dict): Dictionary {tên_lớp: uuid_string} (truyền từ admin_main)
    """
    st.subheader("👧 Quản lý Học sinh")
    tab_list, tab_add, tab_import_hs = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "hoc_sinh"

    # --- Tab Thêm mới (Giữ nguyên) ---
    with tab_add:
        with st.form("add_hs_form", clear_on_submit=True):
            ho_ten = st.text_input("Họ tên *")
            ma_hoc_sinh = st.text_input("Mã HS *")
            mat_khau = st.text_input("Mã PIN (4 số) *", type="password", max_chars=4)

            lop_ten = st.selectbox("Lớp *", list(lop_options.keys()), key="student_add_lop", index=None,
                                   placeholder="Chọn lớp...") if lop_options else None

            ngay_sinh = st.date_input("Ngày sinh", value=None, min_value=datetime.date(1990, 1, 1),
                                      max_value=datetime.date.today())
            gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác", None], index=3)
            email = st.text_input("Email (Tùy chọn)")

            submitted = st.form_submit_button("➕ Thêm học sinh", use_container_width=True)
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
                            "lop_id": lop_options.get(lop_ten),  # UUID string
                            "ngay_sinh": ngay_sinh.isoformat() if ngay_sinh else None,
                            "gioi_tinh": gioi_tinh,
                            "email": email if email else None
                        }
                        supabase.table(table_name).insert(insert_data).execute()
                        st.success("Đã thêm học sinh mới!")
                        crud_utils.clear_all_cached_data()  # Chỉ xóa cache
                    except Exception as e:
                        st.error(f"Lỗi: {e}. Mã HS có thể đã tồn tại.")

    # --- Tab Danh sách & Sửa/Xóa (ĐÃ SỬA: Thêm bộ lọc) ---
    with tab_list:
        # 1. Tải dữ liệu cần thiết
        df_hs_original = crud_utils.load_data(table_name)  # Dữ liệu gốc

        # Tải dữ liệu bảng lop_hoc để lấy thông tin Khối
        lop_df = crud_utils.load_data("lop_hoc")
        lop_id_to_name_map = {str(row['id']): row['ten_lop'] for _, row in lop_df.iterrows()}
        lop_id_to_khoi_map = {str(row['id']): row['khoi'] for _, row in lop_df.iterrows()}

        # 2. Chuẩn bị DataFrame hiển thị (thêm cột 'Khối' và 'Tên lớp')
        df_hs_display = df_hs_original.copy()
        df_hs_display['lop_id_str'] = df_hs_display['lop_id'].astype(str)
        df_hs_display['Tên lớp'] = df_hs_display['lop_id_str'].map(lop_id_to_name_map).fillna("Chưa xếp lớp")
        df_hs_display['Khối'] = df_hs_display['lop_id_str'].map(lop_id_to_khoi_map)

        df_hs_display = df_hs_display.sort_values(by=["Khối", "Tên lớp", "ho_ten"]).reset_index(drop=True)

        # 3. Tạo Bộ lọc
        st.markdown("##### 🔍 Lọc danh sách")
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            # Tạo danh sách Khối (loại bỏ giá trị None/NaN và sắp xếp)
            khoi_list_raw = df_hs_display['Khối'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])
            selected_khoi = st.selectbox(
                "Lọc theo Khối:",
                khoi_list,
                key="student_filter_khoi",
                index=0  # Mặc định là "Tất cả"
            )

        with col_filter2:
            # Lọc danh sách lớp dựa trên Khối đã chọn
            lop_filter_options = ["Tất cả"]
            if selected_khoi != "Tất cả":
                # Lấy tên các lớp thuộc khối đã chọn
                lop_names_in_khoi = lop_df[lop_df['khoi'] == selected_khoi]['ten_lop'].tolist()
                lop_filter_options.extend(lop_names_in_khoi)
            else:
                # Hiển thị tất cả tên lớp
                lop_filter_options.extend(list(lop_options.keys()))

            selected_lop = st.selectbox(
                "Lọc theo Lớp:",
                lop_filter_options,
                key="student_filter_lop",
                index=0  # Mặc định là "Tất cả"
            )

        # 4. Lọc DataFrame
        df_to_show = df_hs_display.copy()
        if selected_khoi != "Tất cả":
            df_to_show = df_to_show[df_to_show['Khối'] == selected_khoi]
        if selected_lop != "Tất cả":
            df_to_show = df_to_show[df_to_show['Tên lớp'] == selected_lop]

        st.markdown("---")

        if not df_to_show.empty:
            cols_to_show = ["id", "ho_ten", "ma_hoc_sinh", "Khối", "Tên lớp", "ngay_sinh", "gioi_tinh", "email"]
            cols_exist = [col for col in cols_to_show if col in df_to_show.columns]

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_to_show[cols_exist],  # Hiển thị DF đã lọc
                key="hs_df_select",
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']  # Lấy ID từ df_to_show
                st.session_state['hs_selected_item_id'] = original_id

            if 'hs_selected_item_id' in st.session_state:
                selected_id = st.session_state['hs_selected_item_id']
                original_item_df = df_hs_original[df_hs_original['id'] == selected_id]  # Tìm trong df gốc
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 5. Form Sửa/Xóa (Giữ nguyên logic)
            if selected_item_original:
                with st.expander("📝 Sửa/Xóa Học sinh đã chọn", expanded=True):
                    with st.form("edit_hs_form"):
                        st.text(f"ID: {selected_item_original['id']}")

                        # Lấy lại options lớp mới nhất (dùng lop_options đã truyền vào)
                        lop_options_local = lop_options

                        ho_ten_edit = st.text_input("Họ tên", value=selected_item_original.get("ho_ten", ""))
                        st.text_input("Mã HS", value=selected_item_original.get("ma_hoc_sinh", ""), disabled=True)
                        mat_khau_edit = st.text_input("PIN mới (4 số, bỏ trống nếu k đổi)", type="password",
                                                      max_chars=4)

                        current_lop_id = str(selected_item_original.get("lop_id", ""))
                        # Tìm tên lớp từ lop_options (dict {tên: id})
                        current_lop_name = next(
                            (name for name, id_ in lop_options_local.items() if id_ == current_lop_id), None)

                        index = 0  # Mặc định
                        if current_lop_name and current_lop_name in lop_options_local:
                            index = list(lop_options_local.keys()).index(current_lop_name)

                        lop_ten_edit = st.selectbox("Lớp", list(lop_options_local.keys()),
                                                    index=index) if lop_options_local else None

                        ngs_val = selected_item_original.get("ngay_sinh")
                        ngay_sinh_obj = None
                        if ngs_val:
                            try:
                                ngay_sinh_obj = datetime.date.fromisoformat(str(ngs_val))
                            except:
                                pass
                        ngay_sinh_edit = st.date_input("Ngày sinh", value=ngay_sinh_obj,
                                                       min_value=datetime.date(1990, 1, 1),
                                                       max_value=datetime.date.today())

                        gt_options = ["Nam", "Nữ", "Khác", None]
                        gt_val = selected_item_original.get("gioi_tinh")
                        gt_index = gt_options.index(gt_val) if gt_val in gt_options else 3
                        gioi_tinh_edit = st.selectbox("Giới tính", gt_options, index=gt_index)
                        email_edit = st.text_input("Email", value=selected_item_original.get("email",
                                                                                             "") if selected_item_original.get(
                            "email") else "")

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True):
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
                                pin_valid = False

                            if pin_valid:
                                try:
                                    supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                        'id']).execute()
                                    st.success("Cập nhật học sinh thành công!")
                                    crud_utils.clear_cache_and_rerun()
                                except Exception as e:
                                    st.error(f"Lỗi cập nhật học sinh: {e}")

                        if col_delete.form_submit_button("❌ Xóa học sinh này", use_container_width=True):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning("Đã xóa học sinh!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa học sinh: {e}")

                        if col_clear.form_submit_button("Hủy chọn", use_container_width=True):
                            if 'hs_selected_item_id' in st.session_state: del st.session_state['hs_selected_item_id']
                            st.rerun()
        else:
            st.info("Chưa có học sinh nào.")

    # --- Tab Import Excel (Giữ nguyên) ---
    with tab_import_hs:
        st.markdown("### 📤 Import danh sách học sinh từ file Excel")
        sample_data_hs = {'ho_ten': ['Nguyễn Test A'], 'ngay_sinh': ['2016-01-01'], 'gioi_tinh': ['Nam'],
                          'email': ['test@email.com'], 'lop_id': ['UUID CỦA LỚP'], 'ma_hoc_sinh': ['HS9999'],
                          'mat_khau': ['1234']}
        crud_utils.create_excel_download(pd.DataFrame(sample_data_hs), "mau_import_hoc_sinh.xlsx",
                                         sheet_name='DanhSachHocSinh')
        st.caption("Quan trọng: Cột 'lop_id' phải chứa UUID (dạng text) của lớp học.")
        uploaded_file_hs = st.file_uploader("Chọn file Excel HS", type=["xlsx"], key="hs_upload")
        if uploaded_file_hs:
            try:
                df_upload_hs = pd.read_excel(uploaded_file_hs, dtype=str);
                st.dataframe(df_upload_hs.head())
                valid_lop_ids = list(lop_options.values()) if lop_options else []

                if not valid_lop_ids:
                    st.error("Chưa có lớp học nào trong hệ thống để import học sinh.")
                elif st.button("🚀 Bắt đầu Import Học Sinh"):
                    count_hs = 0;
                    errors_hs = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_hs.iterrows():
                            try:
                                ho_ten = str(row['ho_ten']).strip();
                                ma_hoc_sinh = str(row['ma_hoc_sinh']).strip();
                                mat_khau = str(row['mat_khau']).strip();
                                lop_id = str(row['lop_id']).strip()
                                ngay_sinh_str = str(row.get('ngay_sinh', '')).strip();
                                gioi_tinh = str(row.get('gioi_tinh', '')).strip().capitalize() if pd.notna(
                                    row.get('gioi_tinh')) else None
                                email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None

                                if not ho_ten or not ma_hoc_sinh or not mat_khau or not lop_id: raise ValueError(
                                    "Thiếu thông tin (*).")
                                if len(mat_khau) != 4: raise ValueError("PIN phải 4 ký tự.")
                                if lop_id not in valid_lop_ids: raise ValueError(f"Lop ID '{lop_id}' không hợp lệ.")
                                if gioi_tinh and gioi_tinh not in ["Nam", "Nữ", "Khác"]: raise ValueError(
                                    f"Giới tính '{gioi_tinh}' không hợp lệ.")

                                ngay_sinh_iso = None;
                                if ngay_sinh_str:
                                    try:
                                        ngay_sinh_iso = datetime.datetime.strptime(ngay_sinh_str.split(" ")[0],
                                                                                   '%Y-%m-%d').date().isoformat()
                                    except:
                                        raise ValueError("Ngày sinh sai (cần YYYY-MM-DD).")

                                supabase.table(table_name).insert({
                                    "ho_ten": ho_ten, "ma_hoc_sinh": ma_hoc_sinh, "mat_khau": mat_khau,
                                    "lop_id": lop_id, "ngay_sinh": ngay_sinh_iso,
                                    "gioi_tinh": gioi_tinh, "email": email
                                }).execute();
                                count_hs += 1
                            except Exception as e:
                                errors_hs.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import {count_hs} học sinh.");
                    crud_utils.clear_all_cached_data()
                    if errors_hs: st.error("Lỗi:"); st.code("\n".join(errors_hs))
            except Exception as e:
                st.error(f"Lỗi đọc file HS: {e}")