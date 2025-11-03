# ===============================================
# 📚 Module Quản lý Chủ đề - manage_topics.py
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
# Import các hàm tiện ích và supabase client
from . import crud_utils # Dùng "." vì crud_utils cùng thư mục
from backend.supabase_client import supabase

def render(mon_hoc_options, chu_de_options_all, chu_de_options_with_none, chu_de_id_list):
    """
    Hiển thị giao diện quản lý Chủ đề.
    Args:
        mon_hoc_options (dict): {tên_môn: uuid_string}
        chu_de_options_all (dict): {tên_chủ_đề_hiển_thị: uuid_string}
        chu_de_options_with_none (dict): Giống chu_de_options_all nhưng có thêm "Không có": None
        chu_de_id_list (list): List các uuid_string của chủ đề hợp lệ (để validation import)
    """
    st.subheader("📚 Quản lý Chủ đề")
    tab_list, tab_add, tab_import_cd = st.tabs(["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "chu_de"

    # --- Tab Thêm mới ---
    with tab_add:
         with st.form("add_chu_de_form", clear_on_submit=True):
            ten_chu_de = st.text_input("Tên chủ đề *")
            mon_hoc_ten = st.selectbox("Môn học *", list(mon_hoc_options.keys())) if mon_hoc_options else None
            lop = st.number_input("Khối *", min_value=1, max_value=12, value=3)
            tuan = st.number_input("Tuần *", min_value=1, max_value=52, value=1)
            # Dùng dict đầy đủ để hiển thị tên dễ hiểu hơn
            prereq_ten = st.selectbox("Tiền đề", list(chu_de_options_with_none.keys())) if chu_de_options_with_none else None
            muc_do = st.selectbox("Mức độ", ["cơ bản", "nâng cao"])

            # Đã xóa st.file_uploader cho PDF

            submitted = st.form_submit_button("Thêm chủ đề")
            if submitted:
                if not mon_hoc_options or mon_hoc_ten is None:
                    st.error("Chưa có môn học nào hoặc chưa chọn môn học.")
                elif not ten_chu_de:
                    st.error("Tên chủ đề không được để trống.")
                else:
                    try:
                        # Chỉ insert các trường cơ bản
                        insert_payload = {
                            "ten_chu_de": ten_chu_de,
                            "mon_hoc_id": mon_hoc_options.get(mon_hoc_ten), # UUID string
                            "mon_hoc": mon_hoc_ten, # Lưu tên môn
                            "lop": lop,
                            "tuan": tuan,
                            "prerequisite_id": chu_de_options_with_none.get(prereq_ten) if prereq_ten else None, # UUID string or None
                            "muc_do": muc_do
                        }
                        supabase.table(table_name).insert(insert_payload).execute()
                        st.success("Đã thêm chủ đề!")
                        crud_utils.clear_cache_and_rerun() # Xóa cache và rerun
                    except Exception as e:
                        st.error(f"Lỗi khi thêm chủ đề: {e}")

    # --- Tab Danh sách & Sửa/Xóa ---
    with tab_list:
        df_cd_original = crud_utils.load_data(table_name) # Dữ liệu gốc
        if not df_cd_original.empty:
             # Map ID sang tên để hiển thị
             mon_hoc_id_map = {str(id_): name for name, id_ in mon_hoc_options.items()}
             # Dùng dict đầy đủ (từ admin_main) để map prerequisite
             chu_de_id_map_display = {id_: name for name, id_ in chu_de_options_all.items()}

             df_cd_display = df_cd_original.copy()
             # Xử lý mapping cẩn thận hơn
             df_cd_display['mon_hoc_id'] = df_cd_display['mon_hoc_id'].apply(lambda x: mon_hoc_id_map.get(str(x)) if pd.notna(x) else "N/A")
             df_cd_display['prerequisite_id'] = df_cd_display['prerequisite_id'].apply(lambda x: chu_de_id_map_display.get(str(x)) if pd.notna(x) else "Không có")
             df_cd_display = df_cd_display.rename(columns={"mon_hoc_id":"Môn học", "prerequisite_id":"Tiền đề"})

             # Ẩn các cột không cần thiết (bao gồm cả cột pdf đã xóa khỏi DB)
             cols_display_cd = [col for col in df_cd_display.columns if col not in ['created_at', 'noi_dung_pdf_url', 'trang_thai', 'tag_ki_nang']]
             # Sắp xếp lại thứ tự cột cho dễ nhìn
             cols_order = ['id', 'ten_chu_de', 'Môn học', 'lop', 'tuan', 'Tiền đề', 'muc_do']
             cols_display_cd_ordered = [col for col in cols_order if col in cols_display_cd] + [col for col in cols_display_cd if col not in cols_order]


             st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
             gb = st.dataframe(
                 df_cd_display[cols_display_cd_ordered], # Sử dụng cột đã sắp xếp
                 key="cd_df_select",
                 hide_index=True,
                 use_container_width=True,
                 on_select="rerun",
                 selection_mode="single-row"
             )
             selected_rows = gb.selection.rows; selected_item_original = None

             # Lưu/lấy ID được chọn từ session
             if selected_rows:
                 selected_index = selected_rows[0]
                 original_id = df_cd_display.iloc[selected_index]['id'] # Lấy ID từ bảng hiển thị
                 st.session_state['cd_selected_item_id'] = original_id
             # else:
             #      if 'cd_selected_item_id' in st.session_state: del st.session_state['cd_selected_item_id']

             if 'cd_selected_item_id' in st.session_state:
                 selected_id = st.session_state['cd_selected_item_id']
                 original_item_df = df_cd_original[df_cd_original['id'] == selected_id]
                 if not original_item_df.empty:
                     selected_item_original = original_item_df.iloc[0].to_dict()

             # Hiển thị form Sửa/Xóa
             if selected_item_original:
                 with st.expander("Sửa/Xóa Chủ đề đã chọn", expanded=True):
                     with st.form("edit_cd_form"):
                         st.text(f"ID: {selected_item_original['id']}")
                         # Load lại options mới nhất bên trong form
                         mon_hoc_df_local = crud_utils.load_data("mon_hoc"); mon_hoc_opts_local = {row["ten_mon"]: str(row["id"]) for _, row in mon_hoc_df_local.iterrows()} if not mon_hoc_df_local.empty else {}
                         chu_de_df_local = crud_utils.load_data("chu_de"); chu_de_opts_local = {f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id']) for _, row in chu_de_df_local.iterrows()} if not chu_de_df_local.empty else {}; chu_de_opts_none_local = {"Không có": None}; chu_de_opts_none_local.update(chu_de_opts_local)

                         ten_chu_de_edit = st.text_input("Tên chủ đề", value=selected_item_original.get("ten_chu_de", ""));
                         current_mh_id = str(selected_item_original.get("mon_hoc_id","")); current_mh_name = next((name for name, id_ in mon_hoc_opts_local.items() if id_ == current_mh_id), None); mh_idx = list(mon_hoc_opts_local.keys()).index(current_mh_name) if current_mh_name in mon_hoc_opts_local else 0; mon_hoc_ten_edit = st.selectbox("Môn học", list(mon_hoc_opts_local.keys()), index=mh_idx)
                         lop_edit = st.number_input("Khối", 1, 12, value=selected_item_original.get("lop", 3)); tuan_edit = st.number_input("Tuần", 1, 52, value=selected_item_original.get("tuan", 1));
                         current_pr_id = str(selected_item_original.get("prerequisite_id", "")) if pd.notna(selected_item_original.get("prerequisite_id")) else ""; current_pr_name = next((name for name, id_ in chu_de_opts_local.items() if id_ == current_pr_id), "Không có"); pr_idx = list(chu_de_opts_none_local.keys()).index(current_pr_name) if current_pr_name in chu_de_opts_none_local else 0; prereq_ten_edit = st.selectbox("Tiền đề", list(chu_de_opts_none_local.keys()), index=pr_idx)
                         md_options = ["cơ bản", "nâng cao"]; md_val = selected_item_original.get("muc_do", "cơ bản"); md_idx = md_options.index(md_val) if md_val in md_options else 0; muc_do_edit = st.selectbox("Mức độ", md_options, index=md_idx)

                         # Đã xóa phần xử lý PDF khỏi form sửa

                         col_update, col_delete, col_clear = st.columns(3)
                         if col_update.form_submit_button("Lưu thay đổi"):
                             # Chỉ update các trường cơ bản
                             update_data = {
                                 "ten_chu_de": ten_chu_de_edit, "mon_hoc_id": mon_hoc_opts_local.get(mon_hoc_ten_edit),
                                 "mon_hoc": mon_hoc_ten_edit, "lop": lop_edit, "tuan": tuan_edit,
                                 "prerequisite_id": chu_de_opts_none_local.get(prereq_ten_edit),
                                 "muc_do": muc_do_edit
                             }
                             try:
                                 supabase.table(table_name).update(update_data).eq("id", selected_item_original['id']).execute();
                                 st.success("Cập nhật!"); crud_utils.clear_cache_and_rerun()
                             except Exception as e: st.error(f"Lỗi: {e}")
                         if col_delete.form_submit_button("❌ Xóa"):
                             try: supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute(); st.warning("Đã xóa!"); crud_utils.clear_cache_and_rerun()
                             except Exception as e: st.error(f"Lỗi: {e}. Chủ đề có thể đang được sử dụng (bài học, câu hỏi...).")
                         if col_clear.form_submit_button("Hủy"):
                              if 'cd_selected_item_id' in st.session_state: del st.session_state['cd_selected_item_id']
                              st.rerun()
        else:
            st.info("Chưa có chủ đề nào.")

    # --- Tab Import Excel ---
    with tab_import_cd:
        st.markdown("### 📤 Import chủ đề từ Excel")
        # File mẫu không có PDF URL
        sample_data_cd = {'ten_chu_de': ['Chủ đề A'], 'mon_hoc_id': ['UUID MÔN HỌC'], 'lop': [3], 'tuan': [1], 'prerequisite_id': ['UUID TIỀN ĐỀ'], 'muc_do': ['cơ bản'], 'mon_hoc':['Tên môn']}
        crud_utils.create_excel_download(pd.DataFrame(sample_data_cd), "mau_import_chu_de.xlsx", sheet_name='DanhSachChuDe')
        st.caption("Các cột ID phải chứa UUID dạng text.")
        uploaded_cd = st.file_uploader("Chọn file Excel Chủ đề", type=["xlsx"], key="cd_upload")
        if uploaded_cd:
            try:
                df_upload_cd = pd.read_excel(uploaded_cd, dtype=str); st.dataframe(df_upload_cd.head())
                valid_mon_hoc_ids = list(mon_hoc_options.values()) if mon_hoc_options else []
                valid_chu_de_ids_prereq = [""] + chu_de_id_list # Dùng list ID đã truyền vào

                if not valid_mon_hoc_ids: st.error("Chưa có môn học nào.")
                elif st.button("🚀 Import Chủ đề"):
                    count = 0; errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_cd.iterrows():
                            try:
                                ten_chu_de = str(row['ten_chu_de']).strip(); mon_hoc_id = str(row['mon_hoc_id']).strip();
                                lop = pd.to_numeric(row['lop'], errors='coerce'); tuan = pd.to_numeric(row['tuan'], errors='coerce')
                                prerequisite_id = str(row.get('prerequisite_id', '')).strip() if pd.notna(row.get('prerequisite_id')) else None
                                muc_do = str(row.get('muc_do', 'cơ bản')).strip().lower();
                                mon_hoc_ten = str(row.get('mon_hoc', '')).strip()

                                if not ten_chu_de: raise ValueError("Tên chủ đề trống.")
                                if mon_hoc_id not in valid_mon_hoc_ids: raise ValueError(f"Mon hoc ID '{mon_hoc_id}' không hợp lệ.")
                                if pd.isna(lop) or not (1 <= lop <= 12): raise ValueError("Khối không hợp lệ.")
                                if pd.isna(tuan) or not (1 <= tuan <= 52): raise ValueError("Tuần không hợp lệ.")
                                if prerequisite_id is not None and prerequisite_id not in valid_chu_de_ids_prereq: raise ValueError(f"Prerequisite ID '{prerequisite_id}' không hợp lệ.")
                                if muc_do not in ['cơ bản', 'nâng cao']: raise ValueError("Mức độ không hợp lệ.")
                                if not mon_hoc_ten: mon_hoc_ten = next((name for name, id_ in mon_hoc_options.items() if id_ == mon_hoc_id), "N/A")

                                insert_data = {"ten_chu_de": ten_chu_de, "mon_hoc_id": mon_hoc_id, "lop": int(lop), "tuan": int(tuan), "muc_do": muc_do, "mon_hoc": mon_hoc_ten}
                                if prerequisite_id: insert_data["prerequisite_id"] = prerequisite_id
                                # Không import PDF URL

                                supabase.table(table_name).insert(insert_data).execute(); count += 1
                            except Exception as e: errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import {count} chủ đề."); crud_utils.clear_cache_and_rerun()
                    if errors: st.error("Lỗi:"); st.code("\n".join(errors))
            except Exception as e: st.error(f"Lỗi đọc file: {e}")