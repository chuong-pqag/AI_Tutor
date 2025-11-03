# ===============================================
# 🎥 Module Quản lý Video - manage_videos.py (Quản lý Tab State)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
from . import crud_utils
from backend.supabase_client import supabase

# --- Hàm helper load_topic_and_lesson_options (Giữ nguyên) ---
@st.cache_data(ttl=60)
def load_topic_and_lesson_options():
    # ... (code hàm này giữ nguyên) ...
    chu_de_df = crud_utils.load_data("chu_de")
    chu_de_df = chu_de_df.sort_values(by=["lop", "tuan"]).reset_index(drop=True)
    chu_de_options = { f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id']) for _, row in chu_de_df.iterrows()} if not chu_de_df.empty else {}
    bai_hoc_df = crud_utils.load_data("bai_hoc")
    bai_hoc_df = bai_hoc_df.sort_values(by=["chu_de_id", "thu_tu"]).reset_index(drop=True)
    bai_hoc_details = { str(row['id']): {"name": f"{row.get('thu_tu', 0)}. {row['ten_bai_hoc']}", "chu_de_id": str(row.get('chu_de_id'))} for _, row in bai_hoc_df.iterrows()} if not bai_hoc_df.empty else {}
    chu_de_id_to_name_map = {id_: name for name, id_ in chu_de_options.items()}
    return chu_de_options, bai_hoc_details, chu_de_id_to_name_map

def render():
    st.subheader("🎥 Quản lý Video bài giảng")

    # ---- QUẢN LÝ TRẠNG THÁI TAB ----
    # Khởi tạo session state nếu chưa có, mặc định là tab 0 (Danh sách)
    if 'manage_videos_active_tab' not in st.session_state:
        st.session_state.manage_videos_active_tab = 0

    # Hàm callback để cập nhật trạng thái khi tab thay đổi (nếu cần theo dõi thủ công)
    # Tuy nhiên, st.tabs thường tự quản lý state nếu key được cung cấp
    # def set_active_tab():
    #      # Cập nhật state dựa trên key của st.tabs (cần kiểm tra lại cách lấy giá trị tab hiện tại)
    #      pass # Tạm thời chưa cần phức tạp

    # Tạo tabs và gán key để Streamlit quản lý state tốt hơn
    tab_list, tab_add, tab_import_vid = st.tabs(
        ["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"],
        # key='manage_videos_tabs' # Gán key cho widget tabs
    )
    # ---------------------------------

    table_name = "video_bai_giang"
    chu_de_options, bai_hoc_details, chu_de_id_to_name_map = load_topic_and_lesson_options()

    # --- Tab Thêm mới ---
    # Sử dụng created tab object `tab_add`
    with tab_add:
        # Cập nhật state khi vào tab này (nếu cần thiết, thường không cần nếu dùng key cho tabs)
        # st.session_state.manage_videos_active_tab = 1
        st.markdown("#### ✨ Thêm video mới")

        # ---- BƯỚC 1: CHỌN CHỦ ĐỀ ----
        if not chu_de_options: st.warning("⚠️ Chưa có Chủ đề nào."); st.stop()
        selected_chu_de_name = st.selectbox( "**1. Chọn Chủ đề***:", list(chu_de_options.keys()), key="vid_add_cd_select_main", index=None, placeholder="Chọn chủ đề liên quan...")
        selected_chu_de_id = chu_de_options.get(selected_chu_de_name)

        # ---- BƯỚC 2: CHỌN BÀI HỌC (ĐÃ LỌC) ----
        filtered_lesson_options = {}
        if selected_chu_de_id: filtered_lesson_options = {details["name"]: bh_id for bh_id, details in bai_hoc_details.items() if details["chu_de_id"] == selected_chu_de_id}
        selected_lesson_name = st.selectbox( "**2. Thuộc Bài học***:", list(filtered_lesson_options.keys()), key="vid_add_bh_select_filtered", index=None, placeholder="Chọn bài học..." if filtered_lesson_options else ("Chủ đề này chưa có bài học" if selected_chu_de_id else "Vui lòng chọn Chủ đề trước"), disabled=(not selected_chu_de_id or not filtered_lesson_options))
        selected_lesson_id = filtered_lesson_options.get(selected_lesson_name)

        # ---- BƯỚC 3: FORM NHẬP THÔNG TIN VIDEO ----
        if selected_lesson_id:
            with st.form("add_video_details_form", clear_on_submit=True):
                st.markdown("**3. Nhập thông tin Video**:")
                tieu_de = st.text_input("Tiêu đề video *", placeholder="Ví dụ: Giới thiệu phép cộng")
                url = st.text_input("URL video *", placeholder="Dán link video vào đây...")
                mo_ta = st.text_area("Mô tả (Tùy chọn)", placeholder="Nội dung tóm tắt của video...")
                submitted_details = st.form_submit_button("➕ Thêm video", use_container_width=True)

                if submitted_details:
                    final_lesson_id = selected_lesson_id
                    if not final_lesson_id: st.error("Lỗi: ID Bài học không hợp lệ.")
                    elif not tieu_de or not url: st.error("Tiêu đề hoặc URL không được trống.")
                    elif not url.startswith("http://") and not url.startswith("https://"): st.error("URL không hợp lệ.")
                    else:
                        try:
                            insert_data = {"bai_hoc_id": final_lesson_id, "tieu_de": tieu_de, "url": url, "mo_ta": mo_ta if mo_ta else None}
                            supabase.table(table_name).insert(insert_data).execute()
                            st.success(f"Đã thêm video '{tieu_de}'!")
                            crud_utils.clear_all_cached_data() # Chỉ xóa cache
                            # ---- GHI NHỚ TAB HIỆN TẠI ----
                            # st.session_state.manage_videos_active_tab = 1 # Lưu lại index của tab "Thêm mới"
                            # Không cần rerun ở đây, vì clear_on_submit=True đã làm form reset
                            # Việc không rerun sẽ giữ nguyên tab hiện tại.
                            # ---- --------------------
                        except Exception as e: st.error(f"Lỗi khi thêm video: {e}")
        elif selected_chu_de_id and not filtered_lesson_options:
             st.warning("Chủ đề này chưa có bài học nào để thêm video.")

    # --- Tab Danh sách & Sửa ---
    # Sử dụng created tab object `tab_list`
    with tab_list:
        # Cập nhật state khi vào tab này (nếu cần thiết)
        # st.session_state.manage_videos_active_tab = 0
        # ... (Code của tab list giữ nguyên như trước) ...
        df_vid_original = crud_utils.load_data(table_name)
        if not df_vid_original.empty:
            # ... (code map dữ liệu và hiển thị dataframe giữ nguyên) ...
            df_vid_display = df_vid_original.copy()
            def get_lesson_display_info(bh_id_str):
                 if not bh_id_str or bh_id_str == 'nan' or bh_id_str not in bai_hoc_details: return "N/A", "N/A"
                 details = bai_hoc_details[bh_id_str]; lesson_name = details.get("name", "N/A"); topic_id = details.get("chu_de_id"); topic_name = chu_de_id_to_name_map.get(topic_id, "N/A")
                 return lesson_name, topic_name
            display_info = df_vid_display['bai_hoc_id'].astype(str).apply(get_lesson_display_info)
            df_vid_display['Bài học'] = display_info.apply(lambda x: x[0]); df_vid_display['Chủ đề'] = display_info.apply(lambda x: x[1])
            df_vid_display = df_vid_display.sort_values(by=["Chủ đề", "Bài học", "tieu_de"]).reset_index(drop=True)
            cols_display_vid = ["id", "tieu_de", "Bài học", "Chủ đề", "url"]; cols_exist = [col for col in cols_display_vid if col in df_vid_display.columns]
            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(df_vid_display[cols_exist], key="vid_df_select", hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row")
            selected_rows = gb.selection.rows; selected_item_original = None
            if selected_rows: original_id = df_vid_display.iloc[selected_rows[0]]['id']; st.session_state['vid_selected_item_id'] = original_id
            if 'vid_selected_item_id' in st.session_state:
                selected_id = st.session_state['vid_selected_item_id']; original_item_df = df_vid_original[df_vid_original['id'] == selected_id]
                if not original_item_df.empty: selected_item_original = original_item_df.iloc[0].to_dict()

            if selected_item_original:
                with st.expander("📝 Sửa/Xóa Video đã chọn", expanded=True):
                    with st.form("edit_vid_form"):
                        # ... (code form sửa giữ nguyên) ...
                        st.text(f"ID Video: {selected_item_original['id']}")
                        current_bh_id = str(selected_item_original.get("bai_hoc_id","")) if pd.notna(selected_item_original.get("bai_hoc_id")) else ""
                        current_cd_id = None; current_bh_name_display = "N/A"
                        if current_bh_id in bai_hoc_details: current_bh_details = bai_hoc_details[current_bh_id]; current_cd_id = current_bh_details.get("chu_de_id"); current_bh_name_display = current_bh_details.get("name")
                        current_cd_name = chu_de_id_to_name_map.get(current_cd_id); cd_idx = list(chu_de_options.keys()).index(current_cd_name) if current_cd_name in chu_de_options else 0
                        chu_de_ten_edit = st.selectbox("Thuộc Chủ đề *", list(chu_de_options.keys()), index=cd_idx, key="vid_edit_cd")
                        selected_chu_de_id_edit = chu_de_options.get(chu_de_ten_edit)
                        filtered_lesson_options_edit = {};
                        if selected_chu_de_id_edit: filtered_lesson_options_edit = {details["name"]: bh_id for bh_id, details in bai_hoc_details.items() if details["chu_de_id"] == selected_chu_de_id_edit}
                        bai_hoc_ten_edit = None; selected_lesson_id_edit = None
                        if not filtered_lesson_options_edit: st.warning("Chủ đề này chưa có bài học."); st.selectbox("Thuộc Bài học *", [], disabled=True)
                        else:
                            bh_keys_list = list(filtered_lesson_options_edit.keys()); bh_idx = bh_keys_list.index(current_bh_name_display) if current_bh_name_display in bh_keys_list else 0
                            bai_hoc_ten_edit = st.selectbox("Thuộc Bài học *", bh_keys_list, index=bh_idx, key="vid_edit_bh")
                            selected_lesson_id_edit = filtered_lesson_options_edit.get(bai_hoc_ten_edit)
                        tieu_de_edit = st.text_input("Tiêu đề *", value=selected_item_original.get("tieu_de",""), placeholder="Nhập tiêu đề video...")
                        url_edit = st.text_input("URL *", value=selected_item_original.get("url",""), placeholder="Dán link video...")
                        mo_ta_edit = st.text_area("Mô tả", value=selected_item_original.get("mo_ta","") if selected_item_original.get("mo_ta") else "", placeholder="Nhập mô tả...")
                        col_update, col_delete, col_clear = st.columns(3)
                        if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True):
                            if not selected_lesson_id_edit: st.error("Vui lòng chọn Bài học.")
                            elif not tieu_de_edit or not url_edit: st.error("Tiêu đề/URL không được trống.")
                            elif not url_edit.startswith("http://") and not url_edit.startswith("https://"): st.error("URL không hợp lệ.")
                            else:
                                update_data = {"bai_hoc_id": selected_lesson_id_edit, "tieu_de": tieu_de_edit, "url": url_edit, "mo_ta": mo_ta_edit if mo_ta_edit else None}
                                try: supabase.table(table_name).update(update_data).eq("id", selected_item_original['id']).execute(); st.success("Cập nhật!"); crud_utils.clear_cache_and_rerun()
                                except Exception as e: st.error(f"Lỗi cập nhật: {e}")
                        if col_delete.form_submit_button("❌ Xóa video này", use_container_width=True):
                            try: supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute(); st.warning("Đã xóa!"); crud_utils.clear_cache_and_rerun()
                            except Exception as e: st.error(f"Lỗi xóa: {e}")
                        if col_clear.form_submit_button("Hủy chọn", use_container_width=True):
                             if 'vid_selected_item_id' in st.session_state: del st.session_state['vid_selected_item_id']; crud_utils.clear_cache_and_rerun()
        else:
            st.info("Chưa có video bài giảng nào.")


    # --- Tab Import Excel ---
    # Sử dụng created tab object `tab_import_vid`
    with tab_import_vid:
        # Cập nhật state khi vào tab này (nếu cần thiết)
        # st.session_state.manage_videos_active_tab = 2
        # ... (Code import giữ nguyên) ...
        st.markdown("### 📤 Import video từ Excel")
        sample_data_vid = {'bai_hoc_id': ['UUID CỦA BÀI HỌC'], 'tieu_de': ['Video bài giảng A'], 'url': ['https://youtube.com/link'], 'mo_ta': ['Mô tả video']}
        crud_utils.create_excel_download(pd.DataFrame(sample_data_vid), "mau_import_video.xlsx", sheet_name='DanhSachVideo')
        st.caption("Cột 'bai_hoc_id' phải chứa UUID (dạng text).")
        uploaded_vid = st.file_uploader("Chọn file Excel Video", type=["xlsx"], key="vid_upload")
        if uploaded_vid:
             try:
                 df_upload_vid = pd.read_excel(uploaded_vid, dtype=str); st.dataframe(df_upload_vid.head())
                 bai_hoc_df_import = crud_utils.load_data("bai_hoc")
                 valid_bai_hoc_ids = [str(row['id']) for _, row in bai_hoc_df_import.iterrows()] if not bai_hoc_df_import.empty else []
                 if not valid_bai_hoc_ids: st.error("Chưa có bài học nào trong hệ thống để import video.")
                 elif st.button("🚀 Import Video"):
                     count = 0; errors = []
                     with st.spinner("Đang import video..."):
                         for index, row in df_upload_vid.iterrows():
                             try:
                                 bai_hoc_id = str(row['bai_hoc_id']).strip(); tieu_de = str(row['tieu_de']).strip(); url = str(row['url']).strip(); mo_ta = str(row.get('mo_ta', '')).strip() if pd.notna(row.get('mo_ta')) else None
                                 if not bai_hoc_id or not tieu_de or not url: raise ValueError("Thiếu thông tin bắt buộc (bai_hoc_id, tieu_de, url).")
                                 if bai_hoc_id not in valid_bai_hoc_ids: raise ValueError(f"Bai hoc ID '{bai_hoc_id}' không hợp lệ hoặc không tồn tại.")
                                 if not url.startswith("http://") and not url.startswith("https://"): raise ValueError("URL không hợp lệ.")
                                 insert_data = {"bai_hoc_id": bai_hoc_id, "tieu_de": tieu_de, "url": url, "mo_ta": mo_ta}
                                 supabase.table(table_name).insert(insert_data).execute(); count += 1
                             except Exception as e: errors.append(f"Dòng {index + 2}: {e}")
                     st.success(f"✅ Import thành công {count} video."); crud_utils.clear_all_cached_data()
                     # ---- GHI NHỚ TAB HIỆN TẠI ----
                     # st.session_state.manage_videos_active_tab = 2 # Lưu lại index của tab "Import"
                     # ---- --------------------
                     if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
             except Exception as e: st.error(f"Lỗi đọc file Excel: {e}")