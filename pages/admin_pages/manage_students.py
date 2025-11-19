# ===============================================
# 👧 Module Quản lý Học sinh - manage_students.py (ĐÃ TÁI CẤU TRÚC DATA LOADING)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
# Import các hàm tiện ích và supabase client
from . import crud_utils
from backend.supabase_client import supabase


# Hàm render không nhận tham số lop_options nữa
def render():
    """Hiển thị giao diện quản lý Học sinh."""
    st.subheader("👧 Quản lý Học sinh")
    tab_list, tab_add, tab_import_hs = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "hoc_sinh"

    # === TỰ TẢI & LỌC DỮ LIỆU LỚP HỌC (Lop_hoc options) ===
    selected_year = st.session_state.get("global_selected_school_year")

    lop_df_all = crud_utils.load_data("lop_hoc")
    # Lọc chỉ giữ lại các lớp thuộc năm học đang xem
    lop_df = lop_df_all[lop_df_all['nam_hoc'] == selected_year].copy()
    lop_options = {row["ten_lop"]: str(row["id"]) for _, row in lop_df.iterrows()} if not lop_df.empty else {}
    # ========================================================

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_hs_form", clear_on_submit=True):
            ho_ten = st.text_input("Họ tên *")
            ma_hoc_sinh = st.text_input("Mã HS *")
            mat_khau = st.text_input("Mã PIN (4 số) *", type="password", max_chars=4)

            # Lớp học: Selectbox đã được tạo từ lop_options đã lọc theo năm học
            lop_ten = st.selectbox("Lớp *", list(lop_options.keys()), key="student_add_lop", index=None,
                                   placeholder="Chọn lớp...") if lop_options else None

            ngay_sinh = st.date_input("Ngày sinh", value=None, min_value=datetime.date(1990, 1, 1),
                                      max_value=datetime.date.today())
            gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác", None], index=3)
            email = st.text_input("Email (Tùy chọn)")

            submitted = st.form_submit_button("➕ Thêm học sinh", width='stretch')  # <-- ĐÃ CẬP NHẬT
            if submitted:
                if not lop_options or lop_ten is None:
                    st.error(f"Chưa có lớp học nào hoạt động trong năm {selected_year} hoặc chưa chọn lớp.")
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
                        st.success(f"Đã thêm học sinh mới vào lớp {lop_ten}!")
                        crud_utils.clear_all_cached_data()  # Chỉ xóa cache
                    except Exception as e:
                        st.error(f"Lỗi: {e}. Mã HS có thể đã tồn tại.")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        # Tải DF học sinh gốc
        df_hs_original = crud_utils.load_data(table_name)

        # 1. Chuẩn bị DataFrame hiển thị (Áp dụng lọc Năm học)
        lop_id_to_name_map = {str(row['id']): row['ten_lop'] for _, row in lop_df.iterrows()}  # Đã lọc theo năm
        lop_id_to_khoi_map = {str(row['id']): row['khoi'] for _, row in lop_df.iterrows()}  # Đã lọc theo năm

        df_hs_display = df_hs_original.copy()
        df_hs_display['lop_id_str'] = df_hs_display['lop_id'].astype(str)

        # Chỉ giữ lại học sinh thuộc các lớp đang hoạt động trong năm đã chọn HOẶC học sinh chưa xếp lớp/đã tốt nghiệp
        valid_lop_ids = list(lop_id_to_name_map.keys())
        df_hs_display = df_hs_display[
            df_hs_display['lop_id_str'].isin(valid_lop_ids) | df_hs_display['lop_id_str'].str.lower().isin(
                ['nan', 'none', 'null', ''])].copy()

        # Map Khối và Tên lớp dựa trên lop_df đã lọc
        df_hs_display['Tên lớp'] = df_hs_display['lop_id_str'].map(lop_id_to_name_map).fillna("Chưa xếp lớp")
        df_hs_display['Khối'] = df_hs_display['lop_id_str'].map(lop_id_to_khoi_map)

        df_hs_display = df_hs_display.sort_values(by=["Khối", "Tên lớp", "ho_ten"]).reset_index(drop=True)

        # 2. Tạo Bộ lọc (Lọc Khối và Lớp hiện tại)
        st.markdown(f"##### 🔍 Lọc danh sách (Năm học: **{selected_year}**)")
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            khoi_list_raw = df_hs_display['Khối'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])
            selected_khoi = st.selectbox(
                "Lọc theo Khối:",
                khoi_list,
                key="student_filter_khoi",
                index=0
            )

        with col_filter2:
            lop_filter_options = ["Tất cả"]

            # Lấy danh sách tên lớp từ lop_df đã lọc theo năm học
            lop_names_available = lop_df['ten_lop'].tolist()

            if selected_khoi != "Tất cả":
                lop_names_in_khoi = lop_df[lop_df['khoi'] == selected_khoi]['ten_lop'].tolist()
                lop_filter_options.extend(lop_names_in_khoi)
            else:
                lop_filter_options.extend(lop_names_available)

            selected_lop = st.selectbox(
                "Lọc theo Lớp:",
                lop_filter_options,
                key="student_filter_lop",
                index=0
            )

        # 3. Lọc DataFrame
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
                df_to_show[cols_exist],
                key="hs_df_select",
                hide_index=True,
                width='stretch',  # <-- ĐÃ CẬP NHẬT
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']
                st.session_state['hs_selected_item_id'] = original_id

            if 'hs_selected_item_id' in st.session_state:
                selected_id = st.session_state['hs_selected_item_id']
                # Lấy lại từ df_hs_original (DF gốc, không lọc năm học)
                original_item_df = df_hs_original[df_hs_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 4. Form Sửa/Xóa
            if selected_item_original:
                # Kiểm tra lớp học của HS có thuộc năm học đang xem không
                current_lop_id = str(original_item_df['lop_id'].iloc[0])
                # Kiểm tra lop_id có nằm trong danh sách các lớp hoạt động của năm đã chọn không
                is_active_student = current_lop_id in valid_lop_ids
                # Chỉ cho phép sửa nếu học sinh đang ở lớp hoạt động trong năm đã chọn HOẶC học sinh chưa xếp lớp
                disabled_editing = not is_active_student and current_lop_id not in ['nan', 'none', 'null', '']

                if not is_active_student and current_lop_id not in ['nan', 'none', 'null', '']:
                    st.warning(
                        f"Học sinh này thuộc lớp không hoạt động trong Năm học **{selected_year}**. Chỉ có thể sửa khi chuyển sang năm học đó.")

                with st.expander("📝 Sửa/Xóa Học sinh đã chọn", expanded=True):
                    with st.form("edit_hs_form"):
                        st.text(f"ID: {selected_item_original['id']}")

                        # Lấy lại options lớp mới nhất (đã lọc theo năm học)
                        lop_options_local = lop_options

                        ho_ten_edit = st.text_input("Họ tên", value=selected_item_original.get("ho_ten", ""),
                                                    disabled=disabled_editing)
                        st.text_input("Mã HS", value=selected_item_original.get("ma_hoc_sinh", ""), disabled=True)
                        mat_khau_edit = st.text_input("PIN mới (4 số, bỏ trống nếu k đổi)", type="password",
                                                      max_chars=4, disabled=disabled_editing)

                        # Tìm tên lớp từ lop_options_local (dict {tên: id})
                        current_lop_name = lop_id_to_name_map.get(current_lop_id)

                        lop_keys_list = list(lop_options_local.keys())
                        index = 0  # Mặc định
                        if current_lop_name and current_lop_name in lop_keys_list:
                            index = lop_keys_list.index(current_lop_name)

                        # Selectbox Lớp: Chỉ hiển thị các lớp của năm học đang xem
                        lop_ten_edit = st.selectbox("Lớp", lop_keys_list, index=index,
                                                    disabled=disabled_editing) if lop_keys_list else None

                        ngs_val = selected_item_original.get("ngay_sinh")
                        ngay_sinh_obj = None
                        if ngs_val:
                            try:
                                ngay_sinh_obj = datetime.date.fromisoformat(str(ngs_val))
                            except:
                                pass
                        ngay_sinh_edit = st.date_input("Ngày sinh", value=ngay_sinh_obj,
                                                       min_value=datetime.date(1990, 1, 1),
                                                       max_value=datetime.date.today(), disabled=disabled_editing)

                        gt_options = ["Nam", "Nữ", "Khác", None]
                        gt_val = selected_item_original.get("gioi_tinh")
                        gt_index = gt_options.index(gt_val) if gt_val in gt_options else 3
                        gioi_tinh_edit = st.selectbox("Giới tính", gt_options, index=gt_index,
                                                      disabled=disabled_editing)
                        email_edit = st.text_input("Email", value=selected_item_original.get("email",
                                                                                             "") if selected_item_original.get(
                            "email") else "", disabled=disabled_editing)

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("💾 Lưu thay đổi", width='stretch', disabled=disabled_editing):
                            update_data = {
                                "ho_ten": ho_ten_edit,
                                # Lấy lop_id từ lop_options_local (đã lọc)
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

                        if col_delete.form_submit_button("❌ Xóa học sinh này", width='stretch',
                                                         disabled=disabled_editing):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning("Đã xóa học sinh!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa học sinh: {e}")

                        if col_clear.form_submit_button("Hủy chọn", width='stretch'):
                            if 'hs_selected_item_id' in st.session_state: del st.session_state['hs_selected_item_id']
                            st.rerun()
        else:
            st.info("Chưa có học sinh nào.")

    # --- Tab Import Excel (Giữ nguyên logic) ---
    with tab_import_hs:
        st.markdown("### 📤 Import danh sách học sinh từ file Excel")
        st.caption(f"Việc import sẽ áp dụng cho các lớp đang hoạt động trong Năm học: **{selected_year}**")
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
                    st.error(f"Chưa có lớp học nào hoạt động trong năm {selected_year} để import học sinh.")
                elif st.button("🚀 Bắt đầu Import Học Sinh", width='stretch'):
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
                                if lop_id not in valid_lop_ids: raise ValueError(
                                    f"Lop ID '{lop_id}' không hợp lệ hoặc không thuộc năm {selected_year}.")
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