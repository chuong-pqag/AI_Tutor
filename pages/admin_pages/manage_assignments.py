# ===============================================
# 🧑‍🏫 Module Quản lý Phân công Giảng dạy - manage_assignments.py (ĐÃ TÁI CẤU TRÚC)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
# Import các hàm tiện ích và supabase client
from . import crud_utils  # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase


# Hàm render không nhận tham số nữa
def render():
    """Hiển thị giao diện quản lý Phân công Giảng dạy."""
    st.subheader("🧑‍🏫 Quản lý Phân công Giảng dạy")
    tab_list, tab_add, tab_import = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "phan_cong_giang_day"

    # === TẢI DỮ LIỆU CẦN THIẾT (Tự cung cấp) ===
    selected_year = st.session_state.get("global_selected_school_year")
    st.caption(f"Đang quản lý Phân công của Năm học: **{selected_year}**")

    # 1. Tải GV (Master Data - không lọc)
    gv_df = crud_utils.load_data("giao_vien")
    gv_options = {row["ho_ten"]: str(row["id"]) for _, row in gv_df.iterrows()} if not gv_df.empty else {}
    gv_id_map = {str(row["id"]): row["ho_ten"] for _, row in gv_df.iterrows()} if not gv_df.empty else {}
    gv_email_to_id = {row["email"]: str(row["id"]) for _, row in
                      gv_df.iterrows()} if not gv_df.empty else {}  # Dùng cho import

    # 2. Tải Môn học (Master Data - không lọc)
    mh_df = crud_utils.load_data("mon_hoc")
    mh_options = {row["ten_mon"]: str(row["id"]) for _, row in mh_df.iterrows()} if not mh_df.empty else {}
    mh_id_map = {str(row["id"]): row["ten_mon"] for _, row in mh_df.iterrows()} if not mh_df.empty else {}

    # 3. Tải Lớp học (FILTERED by year)
    lop_df_all = crud_utils.load_data("lop_hoc")
    lop_df = lop_df_all[lop_df_all['nam_hoc'] == selected_year].copy()
    lop_options = {row["ten_lop"]: str(row["id"]) for _, row in lop_df.iterrows()} if not lop_df.empty else {}
    lop_id_map = {str(row["id"]): row["ten_lop"] for _, row in lop_df.iterrows()} if not lop_df.empty else {}

    # 4. Tải Phân công (FILTERED by year)
    df_assign_original_all = crud_utils.load_data(table_name)  # Dữ liệu gốc toàn bộ
    df_assign_original = df_assign_original_all[df_assign_original_all['nam_hoc'] == selected_year].copy()
    # ===================================================

    # --- Tab Thêm mới ---
    with tab_add:
        with st.form("add_assignment_form", clear_on_submit=True):
            st.markdown("#### Thêm phân công mới")
            if not gv_options or not lop_options or not mh_options:
                st.warning(
                    f"⚠️ Cần có ít nhất một Giáo viên, Môn học, và Lớp học (của năm {selected_year}) trong hệ thống để tạo phân công.")
                st.form_submit_button("Thêm phân công", disabled=True, use_container_width=True)
            else:
                gv_ten = st.selectbox("Chọn Giáo viên *", list(gv_options.keys()), index=None,
                                      placeholder="Chọn giáo viên...")
                # Selectbox Lớp học đã được lọc tự động theo selected_year
                lop_ten = st.selectbox("Chọn Lớp học *", list(lop_options.keys()), index=None,
                                       placeholder="Chọn lớp học...")
                mh_ten = st.selectbox("Chọn Môn học *", list(mh_options.keys()), index=None,
                                      placeholder="Chọn môn học...")
                vai_tro = st.selectbox("Vai trò", ["Giảng dạy", "Chủ nhiệm"])

                # Năm học sẽ lấy từ biến toàn cục
                nam_hoc_display = st.text_input("Năm học", value=selected_year, disabled=True)

                submitted = st.form_submit_button("➕ Thêm phân công", use_container_width=True)
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
                                "nam_hoc": selected_year  # SỬ DỤNG BIẾN TOÀN CỤC
                            }
                            supabase.table(table_name).insert(insert_data).execute()
                            st.success(
                                f"Đã phân công GV {gv_ten} dạy môn {mh_ten} cho lớp {lop_ten} ({selected_year}).")
                            crud_utils.clear_all_cached_data()
                        except Exception as e:
                            st.error(f"Lỗi khi thêm phân công: {e}")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:

        if df_assign_original.empty and not df_assign_original_all.empty:
            st.warning(f"Không tìm thấy phân công giảng dạy nào cho Năm học: **{selected_year}**.")

        # 1. Chuẩn bị DataFrame hiển thị (Thêm Tên)
        df_assign_display = df_assign_original.copy()

        if not df_assign_original.empty:
            # Sử dụng map đã tải ở trên
            df_assign_display['Giáo viên'] = df_assign_display['giao_vien_id'].astype(str).map(gv_id_map).fillna("N/A")
            df_assign_display['Lớp học'] = df_assign_display['lop_id'].astype(str).map(lop_id_map).fillna("N/A")
            df_assign_display['Môn học'] = df_assign_display['mon_hoc_id'].astype(str).map(mh_id_map).fillna("N/A")

            df_assign_display = df_assign_display.rename(columns={"vai_tro": "Vai trò", "nam_hoc": "Năm học"})
            df_assign_display = df_assign_display.sort_values(by=["Lớp học", "Giáo viên"]).reset_index(drop=True)

        # 2. TẠO BỘ LỌC
        st.markdown("##### 🔍 Lọc danh sách")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            # Lớp học đã được lọc theo năm học ở trên
            lop_filter_list = ["Tất cả"] + sorted(list(lop_options.keys()))
            selected_lop_filter = st.selectbox(
                "Lọc theo Lớp học:",
                lop_filter_list,
                key="assign_filter_lop"
            )
        with col_f2:
            gv_filter_list = ["Tất cả"] + sorted(list(gv_options.keys()))
            selected_gv_filter = st.selectbox(
                "Lọc theo Giáo viên:",
                gv_filter_list,
                key="assign_filter_gv"
            )

        # 3. Lọc DataFrame
        df_to_show = df_assign_display.copy()
        if selected_lop_filter != "Tất cả":
            df_to_show = df_to_show[df_to_show['Lớp học'] == selected_lop_filter]
        if selected_gv_filter != "Tất cả":
            df_to_show = df_to_show[df_to_show['Giáo viên'] == selected_gv_filter]

        st.markdown("---")

        # 4. Hiển thị DataFrame đã lọc và Form Sửa/Xóa
        if not df_to_show.empty:
            cols_display_assign = ["id", "Giáo viên", "Lớp học", "Môn học", "Vai trò", "Năm học"]
            cols_exist = [col for col in cols_display_assign if col in df_to_show.columns]

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_to_show[cols_exist],
                key="assign_df_select",
                hide_index=True,
                use_container_width=True,  # <-- ĐÃ CẬP NHẬT
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']
                st.session_state['assign_selected_item_id'] = original_id

            if 'assign_selected_item_id' in st.session_state:
                selected_id = st.session_state['assign_selected_item_id']
                # Tìm trong DF GỐC để lấy đầy đủ dữ liệu
                original_item_df = df_assign_original_all[df_assign_original_all['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 5. Form Sửa/Xóa
            if selected_item_original:

                is_current_year_assignment = (selected_item_original.get('nam_hoc') == selected_year)
                disabled_editing = not is_current_year_assignment

                if not is_current_year_assignment:
                    st.warning(
                        f"Chỉ có thể sửa/xóa phân công của năm học **{selected_year}**. Phân công này thuộc năm **{selected_item_original.get('nam_hoc')}**.")

                with st.expander("📝 Sửa/Xóa Phân công đã chọn", expanded=True):
                    with st.form("edit_assign_form"):
                        st.text(f"ID Phân công: {selected_item_original['id']}")

                        # Sử dụng map TẤT CẢ GIAO VIÊN
                        st.text(f"Giáo viên: {gv_id_map.get(str(selected_item_original.get('giao_vien_id')), 'N/A')}")
                        # Sử dụng map LỚP HỌC (TẤT CẢ) để hiển thị tên
                        lop_id_map_all = {str(row['id']): row['ten_lop'] for _, row in lop_df_all.iterrows()}
                        st.text(f"Lớp học: {lop_id_map_all.get(str(selected_item_original.get('lop_id')), 'N/A')}")
                        st.text(f"Môn học: {mh_id_map.get(str(selected_item_original.get('mon_hoc_id')), 'N/A')}")

                        vai_tro_options = ["Giảng dạy", "Chủ nhiệm"]
                        current_vai_tro = selected_item_original.get('vai_tro', 'Giảng dạy')
                        vai_tro_idx = vai_tro_options.index(
                            current_vai_tro) if current_vai_tro in vai_tro_options else 0

                        vai_tro_edit = st.selectbox("Vai trò", vai_tro_options, index=vai_tro_idx,
                                                    disabled=disabled_editing)
                        nam_hoc_edit = st.text_input("Năm học", value=selected_item_original.get('nam_hoc', ''),
                                                     disabled=True)

                        col_update, col_delete, col_clear = st.columns(3)

                        if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True, disabled=disabled_editing):
                            update_data = {"vai_tro": vai_tro_edit}  # nam_hoc không được phép sửa
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    "id"]).execute()
                                st.success("Cập nhật phân công thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")

                        if col_delete.form_submit_button("❌ Xóa phân công này", use_container_width=True,
                                                         disabled=disabled_editing):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original["id"]).execute()
                                st.warning(f"Đã xóa phân công ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}")

                        if col_clear.form_submit_button("Hủy chọn", use_container_width=True):
                            if 'assign_selected_item_id' in st.session_state: del st.session_state[
                                'assign_selected_item_id']
                            st.rerun()
        else:
            if df_assign_original_all.empty:
                st.info("Chưa có phân công giảng dạy nào.")
            else:
                st.info(f"Không tìm thấy phân công nào cho Năm học {selected_year}.")

    # --- Tab Import Excel ---
    with tab_import:
        st.markdown("### 📤 Import phân công từ Excel")
        st.warning(f"Việc import sẽ áp dụng cho Năm học đang chọn: **{selected_year}**")
        sample_data_assign = {
            'giao_vien_email': ['b.nv@email.com'],
            'lop_ten': ['Lớp 3A'],
            'mon_hoc_ten': ['Toán'],
            'vai_tro': ['Giảng dạy']
        }
        crud_utils.create_excel_download(pd.DataFrame(sample_data_assign), "mau_import_phan_cong.xlsx",
                                         sheet_name='PhanCong')
        st.caption("Sử dụng Email giáo viên, Tên lớp, Tên môn học để hệ thống tự động tìm ID.")

        uploaded_assign = st.file_uploader("Chọn file Excel Phân công", type=["xlsx"], key="assign_upload")
        if uploaded_assign:
            try:
                df_upload_assign = pd.read_excel(uploaded_assign, dtype=str)
                st.dataframe(df_upload_assign.head())

                if not gv_email_to_id or not lop_options or not mh_options:
                    st.error(
                        f"Lỗi: Thiếu dữ liệu Giáo viên, Lớp học hoặc Môn học (của năm học {selected_year}) trong hệ thống để thực hiện import.")
                elif st.button("🚀 Import Phân công", use_container_width=True):
                    if not selected_year:
                        st.error("Không có Năm học được chọn.")
                        st.stop()

                    count = 0;
                    errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_assign.iterrows():
                            try:
                                gv_email = str(row['giao_vien_email']).strip()
                                lop_ten = str(row['lop_ten']).strip()
                                mh_ten = str(row['mon_hoc_ten']).strip()
                                vai_tro = str(row.get('vai_tro', 'Giảng dạy')).strip().capitalize()

                                gv_id = gv_email_to_id.get(gv_email)
                                lop_id = lop_options.get(lop_ten)  # Lớp ID đã được lọc theo năm học
                                mh_id = mh_options.get(mh_ten)

                                if not gv_id: raise ValueError(f"Không tìm thấy giáo viên với email '{gv_email}'.")
                                if not lop_id: raise ValueError(
                                    f"Không tìm thấy lớp học '{lop_ten}' trong năm **{selected_year}**.")
                                if not mh_id: raise ValueError(f"Không tìm thấy môn học '{mh_ten}'.")
                                if vai_tro not in ['Giảng dạy', 'Chủ nhiệm']: raise ValueError(
                                    "Vai trò không hợp lệ (chỉ 'Giảng dạy' hoặc 'Chủ nhiệm').")

                                insert_data = {
                                    "giao_vien_id": gv_id,
                                    "lop_id": lop_id,
                                    "mon_hoc_id": mh_id,
                                    "vai_tro": vai_tro,
                                    "nam_hoc": selected_year  # SỬ DỤNG BIẾN TOÀN CỤC
                                }
                                supabase.table(table_name).insert(insert_data).execute();
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import thành công {count} phân công.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file Excel: {e}")