# ===============================================
# 🎥 Module Quản lý Video - manage_videos.py (Sửa lỗi TypeError và tối ưu lọc 4 cấp)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import uuid
import os
from urllib.parse import unquote
from . import crud_utils
from backend.supabase_client import supabase
import xlsxwriter

# --- Cấu hình Supabase Storage (Giữ nguyên) ---
BUCKET_NAME = "topic_pdfs"


def upload_pdf_to_storage(uploaded_file, lesson_id):
    if not uploaded_file: return None
    try:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext != ".pdf":
            st.error("Chỉ chấp nhận file định dạng PDF.")
            return None
        safe_filename = "".join(c if c.isalnum() else "_" for c in os.path.splitext(uploaded_file.name)[0])
        file_name = f"lesson_{lesson_id}_{safe_filename[:50]}{file_ext}"
        storage_path = file_name
        file_content = uploaded_file.getvalue()
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path, file=file_content,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        return public_url
    except Exception as e:
        st.error(f"Lỗi tải file PDF lên Storage '{BUCKET_NAME}': {e}")
        if "policy" in str(e).lower():
            st.warning("Kiểm tra lại Policy của bucket trên Supabase. Cần cho phép insert/update.")
        return None


def delete_pdf_from_storage(pdf_url):
    if not pdf_url: return
    try:
        path_parts = pdf_url.split(f'/{BUCKET_NAME}/')
        if len(path_parts) > 1:
            file_path_encoded = path_parts[1]
            file_path = unquote(file_path_encoded)
            response = supabase.storage.from_(BUCKET_NAME).remove([file_path])
        else:
            st.warning(f"Không thể trích xuất đường dẫn file từ URL: {pdf_url}")
    except Exception as e:
        st.warning(f"Lỗi khi xóa file PDF ({pdf_url}) trên Storage: {e}")
        if "policy" in str(e).lower():
            st.warning("Kiểm tra lại Policy của bucket trên Supabase. Cần cho phép delete.")


# --- Hết hàm helper PDF ---


@st.cache_data(ttl=60)
def load_video_management_data():
    """Tải tất cả dữ liệu cần thiết cho quản lý video."""
    chu_de_df = crud_utils.load_data("chu_de").sort_values(by=["lop", "tuan"])
    bai_hoc_df = crud_utils.load_data("bai_hoc").sort_values(by=["chu_de_id", "thu_tu"])
    mon_hoc_df = crud_utils.load_data("mon_hoc").sort_values(by="ten_mon")
    lop_hoc_df = crud_utils.load_data("lop_hoc")

    mon_hoc_names_all = ["Tất cả"] + list(mon_hoc_df['ten_mon'].unique())
    mon_hoc_names_add = list(mon_hoc_df['ten_mon'].unique())

    chu_de_options = {
        f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id'])
        for _, row in chu_de_df.iterrows()
    } if not chu_de_df.empty else {}

    bai_hoc_details = {
        str(row['id']): {
            "name": f"{row.get('thu_tu', 0)}. {row['ten_bai_hoc']}",
            "ten_bai_hoc": row['ten_bai_hoc'],
            "chu_de_id": str(row.get('chu_de_id'))
        }
        for _, row in bai_hoc_df.iterrows()
    } if not bai_hoc_df.empty else {}
    bai_hoc_name_to_id = {details["ten_bai_hoc"]: bh_id for bh_id, details in bai_hoc_details.items()}

    chu_de_id_to_name_map = {id_: name for name, id_ in chu_de_options.items()}
    chu_de_to_mon_hoc_map = {str(row['id']): row['mon_hoc'] for _, row in chu_de_df.iterrows()}
    chu_de_to_khoi_map = {str(row['id']): row['lop'] for _, row in chu_de_df.iterrows()}

    # Map Khối -> List Tên Môn học (cho lọc 4 cấp)
    khoi_to_mon_hoc_names_map_add = {}
    for _, row in mon_hoc_df.iterrows():
        ten_mon = row['ten_mon']
        for khoi in row.get('khoi_ap_dung', []):
            if khoi not in khoi_to_mon_hoc_names_map_add:
                khoi_to_mon_hoc_names_map_add[khoi] = []
            khoi_to_mon_hoc_names_map_add[khoi].append(ten_mon)

    mon_hoc_to_chu_de_names_map = {}
    for cd_id, cd_name in chu_de_id_to_name_map.items():
        mon_hoc = chu_de_to_mon_hoc_map.get(cd_id)
        if mon_hoc:
            if mon_hoc not in mon_hoc_to_chu_de_names_map:
                mon_hoc_to_chu_de_names_map[mon_hoc] = ["Tất cả"]
            mon_hoc_to_chu_de_names_map[mon_hoc].append(cd_name)

    mon_hoc_to_chu_de_names_map_add = {}
    for cd_id, cd_name in chu_de_id_to_name_map.items():
        mon_hoc = chu_de_to_mon_hoc_map.get(cd_id)
        if mon_hoc:
            if mon_hoc not in mon_hoc_to_chu_de_names_map_add:
                mon_hoc_to_chu_de_names_map_add[mon_hoc] = []
            mon_hoc_to_chu_de_names_map_add[mon_hoc].append(cd_name)

    khoi_list_all = ["Tất cả"] + sorted([int(k) for k in lop_hoc_df['khoi'].dropna().unique()])
    khoi_list_add = sorted([int(k) for k in lop_hoc_df['khoi'].dropna().unique()])

    chu_de_df_filtered = chu_de_df.copy()

    # TRẢ VỀ ĐẦY ĐỦ CÁC GIÁ TRỊ (17 giá trị)
    return (mon_hoc_names_all, mon_hoc_names_add, chu_de_options, bai_hoc_details, bai_hoc_name_to_id,
            chu_de_id_to_name_map, chu_de_to_mon_hoc_map, chu_de_to_khoi_map,
            None, None,
            mon_hoc_to_chu_de_names_map, mon_hoc_to_chu_de_names_map_add, khoi_list_all, khoi_list_add, mon_hoc_df,
            chu_de_df_filtered, khoi_to_mon_hoc_names_map_add)


# --- Hàm callback để lưu tab đã chọn (Giữ nguyên) ---
def set_active_tab(tab_name):
    """Lưu tên tab hiện tại vào session state."""
    st.session_state['video_active_tab'] = tab_name


def render():
    """Hiển thị giao diện quản lý Video bài giảng."""
    st.subheader("🎥 Quản lý Video bài giảng")

    if 'video_active_tab' not in st.session_state:
        st.session_state['video_active_tab'] = "📝 Danh sách & Sửa"

    tab_list, tab_add, tab_import_vid = st.tabs([
        "📝 Danh sách & Sửa",
        "➕ Thêm mới",
        "📤 Import Excel"
    ])
    table_name = "video_bai_giang"

    # HỨNG ĐỦ 17 GIÁ TRỊ
    (mon_hoc_names, mon_hoc_names_add, chu_de_options, bai_hoc_details, bai_hoc_name_to_id,
     chu_de_id_to_name_map, chu_de_to_mon_hoc_map, chu_de_to_khoi_map, bh_to_khoi_map_unused, bh_to_mon_map_unused,
     mon_hoc_to_chu_de_names_map, mon_hoc_to_chu_de_names_map_add, khoi_list_all, khoi_list_add, mon_hoc_df,
     chu_de_df_filtered, khoi_to_mon_hoc_names_map_add) = load_video_management_data()

    # --- Tab Thêm mới (LỌC 4 CẤP) ---
    with tab_add:
        set_active_tab("➕ Thêm mới")
        st.markdown("#### ✨ Thêm video mới")

        if not khoi_list_add:
            st.warning("⚠️ Chưa có Khối lớp nào. Vui lòng thêm Lớp học trước.");
            st.stop()

        # ---- BƯỚC 1: CHỌN KHỐI HỌC ----
        khoi_options_with_none = [None] + khoi_list_add
        selected_khoi_add = st.selectbox(
            "**1. Chọn Khối học***:",
            khoi_options_with_none,
            key="vid_add_khoi_select",
            index=0,
            # SỬA LỖI: Đảm bảo format_func trả về str cho giá trị số
            format_func=lambda x: "Chọn Khối học..." if x is None else str(x),
            on_change=set_active_tab,
            args=("➕ Thêm mới",)
        )

        # ---- BƯỚC 2: CHỌN MÔN HỌC (Lọc theo Khối) ----
        mon_hoc_names_filtered = []
        if selected_khoi_add is not None:
            mon_hoc_names_filtered = khoi_to_mon_hoc_names_map_add.get(selected_khoi_add, [])

        mon_hoc_options_with_none = [None] + mon_hoc_names_filtered

        selected_mon_hoc_name = st.selectbox(
            "**2. Chọn Môn học***:",
            mon_hoc_options_with_none,
            key="vid_add_monhoc_select",
            index=0,
            format_func=lambda x: "Chọn Môn học..." if x is None else x,
            disabled=(selected_khoi_add is None or not mon_hoc_names_filtered),
            on_change=set_active_tab,
            args=("➕ Thêm mới",)
        )

        # ---- BƯỚC 3: CHỌN CHỦ ĐỀ (Lọc theo Khối & Môn học) ----
        filtered_chu_de_options_map = {}
        if selected_khoi_add is not None and selected_mon_hoc_name is not None:
            temp_df = chu_de_df_filtered[
                (chu_de_df_filtered['lop'] == selected_khoi_add) &
                (chu_de_df_filtered['mon_hoc'] == selected_mon_hoc_name)
                ]

            filtered_chu_de_options_map = {
                f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id'])
                for _, row in temp_df.iterrows()
            }
            filtered_chu_de_options_map = dict(sorted(filtered_chu_de_options_map.items()))

        chu_de_options_with_none = [None] + list(filtered_chu_de_options_map.keys())

        selected_chu_de_name = st.selectbox(
            "**3. Chọn Chủ đề***:",
            chu_de_options_with_none,
            key="vid_add_cd_select_main",
            index=0,
            format_func=lambda x: "Chọn Chủ đề..." if x is None else x,
            disabled=(selected_mon_hoc_name is None or not filtered_chu_de_options_map),
            on_change=set_active_tab,
            args=("➕ Thêm mới",)
        )
        selected_chu_de_id = filtered_chu_de_options_map.get(selected_chu_de_name)

        # ---- BƯỚC 4: CHỌN BÀI HỌC (Lọc theo Chủ đề) ----
        filtered_lesson_options = {}
        if selected_chu_de_id:
            filtered_lesson_options = {
                details["name"]: bh_id
                for bh_id, details in bai_hoc_details.items()
                if details["chu_de_id"] == selected_chu_de_id
            }
            filtered_lesson_options = dict(sorted(filtered_lesson_options.items()))

        lesson_options_with_none = [None] + list(filtered_lesson_options.keys())

        selected_lesson_name = st.selectbox(
            "**4. Thuộc Bài học***:",
            lesson_options_with_none,
            key="vid_add_bh_select_filtered",
            index=0,
            format_func=lambda x: "Chọn Bài học..." if x is None else x,
            disabled=(selected_chu_de_id is None or not filtered_lesson_options),
            on_change=set_active_tab,
            args=("➕ Thêm mới",)
        )
        selected_lesson_id = filtered_lesson_options.get(selected_lesson_name)

        # ---- BƯỚC 5: FORM NHẬP LIỆU ----
        if selected_lesson_id:
            with st.form("add_video_details_form", clear_on_submit=True):
                st.markdown("**5. Nhập thông tin Video**:")
                tieu_de = st.text_input("Tiêu đề video *", placeholder="Ví dụ: Giới thiệu phép cộng")
                url = st.text_input("URL video *", placeholder="Dán link video vào đây...")
                mo_ta = st.text_area("Mô tả (Tùy chọn)", placeholder="Nội dung tóm tắt của video...")
                submitted_details = st.form_submit_button("➕ Thêm video", use_container_width=True)
                if submitted_details:
                    final_lesson_id = selected_lesson_id
                    if not final_lesson_id:
                        st.error("Lỗi: ID Bài học không hợp lệ.")
                    elif not tieu_de or not url:
                        st.error("Tiêu đề hoặc URL không được trống.")
                    elif not url.startswith("http://") and not url.startswith("https://"):
                        st.error("URL không hợp lệ.")
                    else:
                        try:
                            insert_data = {"bai_hoc_id": final_lesson_id, "tieu_de": tieu_de, "url": url,
                                           "mo_ta": mo_ta if mo_ta else None}
                            supabase.table(table_name).insert(insert_data).execute();
                            st.success(f"Đã thêm video '{tieu_de}'!")
                            crud_utils.clear_all_cached_data()
                        except Exception as e:
                            st.error(f"Lỗi khi thêm video: {e}")
        elif selected_chu_de_id is not None:
            st.warning("Chủ đề này chưa có bài học nào để thêm video.")
        elif selected_mon_hoc_name is not None:
            st.warning("Môn học/Khối này chưa có chủ đề nào.")

    # --- Tab Danh sách & Sửa (Giữ nguyên) ---
    with tab_list:
        set_active_tab("📝 Danh sách & Sửa")
        df_vid_original = crud_utils.load_data(table_name)
        df_vid_display = df_vid_original.copy()

        def get_display_info(bh_id_str):
            if not bh_id_str or bh_id_str == 'nan' or bh_id_str not in bai_hoc_details:
                return "N/A", "N/A", "N/A", "N/A"
            details = bai_hoc_details.get(bh_id_str, {})
            topic_id = details.get("chu_de_id")
            lesson_name = details.get("name", "N/A")
            topic_name = chu_de_id_to_name_map.get(topic_id, "N/A")
            mon_hoc_name = chu_de_to_mon_hoc_map.get(topic_id, "N/A")
            khoi_val = chu_de_to_khoi_map.get(topic_id, "N/A")
            return lesson_name, topic_name, mon_hoc_name, khoi_val

        display_info = df_vid_display['bai_hoc_id'].astype(str).apply(get_display_info)
        df_vid_display['Bài học'] = display_info.apply(lambda x: x[0])
        df_vid_display['Chủ đề'] = display_info.apply(lambda x: x[1])
        df_vid_display['Môn học'] = display_info.apply(lambda x: x[2])
        df_vid_display['Khối'] = display_info.apply(lambda x: x[3])
        df_vid_display = df_vid_display.sort_values(by=["Khối", "Môn học", "Chủ đề", "Bài học", "tieu_de"]).reset_index(
            drop=True)

        st.markdown("##### 🔍 Lọc danh sách")
        col_filter1, col_filter2, col_filter3 = st.columns(3)

        df_temp = df_vid_display.copy()

        with col_filter1:
            selected_khoi = st.selectbox(
                "Lọc theo Khối:",
                khoi_list_all,
                key="vid_filter_khoi",
                index=0
            )

        if selected_khoi != "Tất cả":
            df_temp = df_temp[df_temp['Khối'] == selected_khoi]

        with col_filter2:
            mon_hoc_list_filter = ["Tất cả"] + sorted(list(df_temp['Môn học'].dropna().unique()))
            selected_mon_hoc = st.selectbox(
                "Lọc theo Môn học:",
                mon_hoc_list_filter,
                key="vid_filter_monhoc",
                index=0
            )

        if selected_mon_hoc != "Tất cả":
            df_temp = df_temp[df_temp['Môn học'] == selected_mon_hoc]

        with col_filter3:
            chu_de_filter_options = ["Tất cả"] + sorted(list(df_temp['Chủ đề'].dropna().unique()))
            selected_chu_de_name = st.selectbox(
                "Lọc theo Chủ đề:",
                chu_de_filter_options,
                key="vid_filter_chude",
                index=0
            )

        df_to_show = df_temp.copy()
        if selected_chu_de_name != "Tất cả":
            df_to_show = df_to_show[df_to_show['Chủ đề'] == selected_chu_de_name]

        st.markdown("---")

        cols_display_vid = ["id", "tieu_de", "Bài học", "Chủ đề", "Môn học", "Khối", "url"]
        cols_exist = [col for col in cols_display_vid if col in df_to_show.columns]

        st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
        gb = st.dataframe(
            df_to_show[cols_exist],
            key="vid_df_select",
            hide_index=True,
            use_container_width=True,
            on_select=crud_utils.clear_cache_and_rerun,
            selection_mode="single-row"
        )

        selected_rows = gb.selection.rows
        selected_item_original = None

        if selected_rows:
            original_id = df_to_show.iloc[selected_rows[0]]['id']
            st.session_state['vid_selected_item_id'] = original_id

        if 'vid_selected_item_id' in st.session_state:
            selected_id = st.session_state['vid_selected_item_id']
            original_item_df = df_vid_original[df_vid_original['id'] == selected_id]
            if not original_item_df.empty:
                selected_item_original = original_item_df.iloc[0].to_dict()

        if selected_item_original:
            with st.expander("📝 Sửa/Xóa Video đã chọn", expanded=True):
                with st.form("edit_vid_form"):
                    st.text(f"ID Video: {selected_item_original['id']}")
                    current_bh_id = str(selected_item_original.get("bai_hoc_id", "")) if pd.notna(
                        selected_item_original.get("bai_hoc_id")) else ""
                    current_cd_id = None;
                    current_bh_name_display = "N/A"
                    if current_bh_id in bai_hoc_details: current_bh_details = bai_hoc_details[
                        current_bh_id]; current_cd_id = current_bh_details.get(
                        "chu_de_id"); current_bh_name_display = current_bh_details.get("name")
                    current_cd_name = chu_de_id_to_name_map.get(current_cd_id);
                    # Lấy Khối và Môn hiện tại để đặt giá trị mặc định cho selectbox
                    current_khoi = chu_de_to_khoi_map.get(current_cd_id)
                    current_mon_hoc_name = chu_de_to_mon_hoc_map.get(current_cd_id)

                    # --- Lọc 4 cấp trong Form Sửa ---
                    # 1. Khối
                    khoi_options_add_edit = [None] + khoi_list_add
                    khoi_idx_edit = khoi_options_add_edit.index(
                        current_khoi) if current_khoi in khoi_options_add_edit else 0
                    khoi_ten_edit = st.selectbox(
                        "Thuộc Khối *",
                        khoi_options_add_edit,
                        index=khoi_idx_edit,
                        key="vid_edit_khoi",
                        format_func=lambda x: "Chọn Khối học..." if x is None else str(x)
                    )

                    # 2. Môn học
                    mon_hoc_names_filtered_edit = []
                    if khoi_ten_edit is not None:
                        mon_hoc_names_filtered_edit = khoi_to_mon_hoc_names_map_add.get(khoi_ten_edit, [])
                    mon_hoc_options_edit = [None] + mon_hoc_names_filtered_edit

                    mon_hoc_idx_edit = mon_hoc_options_edit.index(
                        current_mon_hoc_name) if current_mon_hoc_name in mon_hoc_options_edit else 0
                    mon_hoc_ten_edit = st.selectbox(
                        "Thuộc Môn học *",
                        mon_hoc_options_edit,
                        index=mon_hoc_idx_edit,
                        key="vid_edit_monhoc",
                        format_func=lambda x: "Chọn Môn học..." if x is None else x,
                        disabled=(khoi_ten_edit is None)
                    )

                    # 3. Chủ đề
                    chu_de_options_edit_map = {}
                    if khoi_ten_edit is not None and mon_hoc_ten_edit is not None:
                        temp_df_edit = chu_de_df_filtered[
                            (chu_de_df_filtered['lop'] == khoi_ten_edit) &
                            (chu_de_df_filtered['mon_hoc'] == mon_hoc_ten_edit)
                            ]
                        chu_de_options_edit_map = {
                            f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id'])
                            for _, row in temp_df_edit.iterrows()
                        }

                    cd_keys_list_edit = list(chu_de_options_edit_map.keys())
                    chu_de_options_with_none_edit = [None] + cd_keys_list_edit
                    cd_idx_edit = chu_de_options_with_none_edit.index(
                        current_cd_name) if current_cd_name in chu_de_options_with_none_edit else 0

                    chu_de_ten_edit = st.selectbox(
                        "Thuộc Chủ đề *",
                        chu_de_options_with_none_edit,
                        index=cd_idx_edit,
                        key="vid_edit_cd",
                        format_func=lambda x: "Chọn Chủ đề..." if x is None else x,
                        disabled=(mon_hoc_ten_edit is None)
                    )
                    selected_chu_de_id_edit = chu_de_options_edit_map.get(chu_de_ten_edit)

                    # 4. Bài học
                    filtered_lesson_options_edit = {};
                    if selected_chu_de_id_edit:
                        filtered_lesson_options_edit = {details["name"]: bh_id for
                                                        bh_id, details in
                                                        bai_hoc_details.items() if details[
                                                            "chu_de_id"] == selected_chu_de_id_edit}
                    lesson_options_with_none_edit = [None] + list(filtered_lesson_options_edit.keys())
                    current_bh_name = bai_hoc_details.get(current_bh_id, {}).get("name")

                    bh_idx = lesson_options_with_none_edit.index(
                        current_bh_name) if current_bh_name in lesson_options_with_none_edit else 0

                    bai_hoc_ten_edit = st.selectbox("Thuộc Bài học *",
                                                    lesson_options_with_none_edit,
                                                    index=bh_idx,
                                                    key="vid_edit_bh",
                                                    format_func=lambda x: "Chọn Bài học..." if x is None else x,
                                                    disabled=(selected_chu_de_id_edit is None)
                                                    )
                    selected_lesson_id_edit = filtered_lesson_options_edit.get(bai_hoc_ten_edit)
                    # --- Kết thúc Lọc 4 cấp trong Form Sửa ---

                    tieu_de_edit = st.text_input("Tiêu đề *", value=selected_item_original.get("tieu_de", ""),
                                                 placeholder="Nhập tiêu đề video...")
                    url_edit = st.text_input("URL *", value=selected_item_original.get("url", ""),
                                             placeholder="Dán link video...")
                    mo_ta_edit = st.text_area("Mô tả", value=selected_item_original.get("mo_ta",
                                                                                        "") if selected_item_original.get(
                        "mo_ta") else "", placeholder="Nhập mô tả...")

                    col_update, col_delete, col_clear = st.columns(3)
                    if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True):
                        if not selected_lesson_id_edit:
                            st.error("Vui lòng chọn Bài học hợp lệ.")
                        elif not tieu_de_edit or not url_edit:
                            st.error("Tiêu đề/URL không được trống.")
                        elif not url_edit.startswith("http://") and not url_edit.startswith("https://"):
                            st.error("URL không hợp lệ.")
                        else:
                            update_data = {"bai_hoc_id": selected_lesson_id_edit, "tieu_de": tieu_de_edit,
                                           "url": url_edit, "mo_ta": mo_ta_edit if mo_ta_edit else None}
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    'id']).execute();
                                st.success("Cập nhật!");
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật: {e}")
                    if col_delete.form_submit_button("❌ Xóa video này", use_container_width=True):
                        try:
                            supabase.table(table_name).delete().eq("id",
                                                                   selected_item_original['id']).execute();
                            st.warning(
                                "Đã xóa!");
                            crud_utils.clear_cache_and_rerun()
                        except Exception as e:
                            st.error(f"Lỗi xóa: {e}")
                    if col_clear.form_submit_button("Hủy chọn", use_container_width=True):
                        if 'vid_selected_item_id' in st.session_state: del st.session_state[
                            'vid_selected_item_id']; crud_utils.clear_cache_and_rerun()
        else:
            st.info("Chưa có video bài giảng nào.")

    # --- Tab Import Excel (Giữ nguyên) ---
    with tab_import_vid:
        set_active_tab("📤 Import Excel")
        st.markdown("### 📤 Import video từ Excel")

        st.markdown("##### 🔍 Chọn điều kiện để tải File mẫu")
        col_import1, col_import2 = st.columns(2)

        selected_khoi_import = None
        with col_import1:
            selected_khoi_import = st.selectbox(
                "Khối:",
                ["Chọn Khối"] + khoi_list_add,
                key="vid_import_khoi",
                index=0
            )

        selected_mon_hoc_import = None
        with col_import2:
            mon_hoc_list_import = ["Chọn Môn học"]
            if selected_khoi_import != "Chọn Khối":
                mon_hoc_list_import.extend(
                    mon_hoc_df[mon_hoc_df['khoi_ap_dung'].apply(
                        lambda x: selected_khoi_import in x if isinstance(x, list) else False)]['ten_mon'].tolist()
                )

            selected_mon_hoc_import = st.selectbox(
                "Môn học:",
                mon_hoc_list_import,
                key="vid_import_monhoc",
                index=0,
                disabled=(selected_khoi_import == "Chọn Khối")
            )

        bai_hoc_list_for_sample = []
        bai_hoc_name_to_id_filtered = {}

        if selected_khoi_import != "Chọn Khối" and selected_mon_hoc_import != "Chọn Môn học":
            mon_hoc_id_import = mon_hoc_df[mon_hoc_df['ten_mon'] == selected_mon_hoc_import]['id'].iloc[0]

            chu_de_ids_of_mon_khoi = chu_de_df_filtered[
                (chu_de_df_filtered['lop'] == selected_khoi_import) &
                (chu_de_df_filtered['mon_hoc'] == selected_mon_hoc_import)
                ]['id'].tolist()

            lessons_of_mon_khoi = crud_utils.load_data("bai_hoc")[
                crud_utils.load_data("bai_hoc")['chu_de_id'].astype(str).isin([str(i) for i in chu_de_ids_of_mon_khoi])
            ]

            if not lessons_of_mon_khoi.empty:
                bai_hoc_name_to_id_filtered = {
                    row['ten_bai_hoc']: str(row['id'])
                    for _, row in lessons_of_mon_khoi.iterrows()
                }
                bai_hoc_list_for_sample = sorted(list(bai_hoc_name_to_id_filtered.keys()))

                sample_data_vid = {
                    'bai_hoc_ten': bai_hoc_list_for_sample[:1] or ['Tên bài học'],
                    'tieu_de': ['Video bài giảng A'],
                    'url': ['https://youtube.com/link'],
                    'mo_ta': ['Mô tả video']
                }
                crud_utils.create_excel_download(pd.DataFrame(sample_data_vid),
                                                 f"mau_import_video_{selected_khoi_import}_{selected_mon_hoc_import}.xlsx",
                                                 sheet_name='DanhSachVideo')
                st.caption(
                    f"File mẫu đang hiển thị các Bài học thuộc **Khối {selected_khoi_import} - Môn {selected_mon_hoc_import}**.")
            else:
                st.info("Không tìm thấy Bài học nào phù hợp để tạo file mẫu.")
        else:
            sample_data_vid_default = {'bai_hoc_ten': ['Tên bài học'], 'tieu_de': ['Video bài giảng A'],
                                       'url': ['https://youtube.com/link'], 'mo_ta': ['Mô tả video']}
            crud_utils.create_excel_download(pd.DataFrame(sample_data_vid_default), "mau_import_video_default.xlsx",
                                             sheet_name='DanhSachVideo')
            st.warning("Vui lòng chọn Khối và Môn học để tạo file mẫu chính xác hơn.")

        st.markdown("---")
        st.caption("Cột **bai_hoc_ten** sẽ được dùng để tra cứu ID Bài học.")

        uploaded_vid = st.file_uploader("Chọn file Excel Video", type=["xlsx"], key="vid_upload")
        if uploaded_vid:
            try:
                df_upload_vid = pd.read_excel(uploaded_vid, dtype=str);
                st.dataframe(df_upload_vid.head())

                all_bai_hoc_df = crud_utils.load_data("bai_hoc")
                all_bai_hoc_name_to_id = {row['ten_bai_hoc']: str(row['id']) for _, row in all_bai_hoc_df.iterrows()}

                if not all_bai_hoc_name_to_id:
                    st.error("Chưa có bài học nào trong hệ thống để import video.")
                elif st.button("🚀 Import Video"):
                    count = 0;
                    errors = []
                    with st.spinner("Đang import video..."):
                        for index, row in df_upload_vid.iterrows():
                            try:
                                bai_hoc_ten = str(row['bai_hoc_ten']).strip();
                                bai_hoc_id = all_bai_hoc_name_to_id.get(bai_hoc_ten)

                                tieu_de = str(row['tieu_de']).strip();
                                url = str(row['url']).strip();
                                mo_ta = str(row.get('mo_ta', '')).strip() if pd.notna(row.get('mo_ta')) else None

                                if not bai_hoc_ten or not bai_hoc_id: raise ValueError(
                                    f"Không tìm thấy ID cho Bài học tên '{bai_hoc_ten}'.")
                                if not tieu_de or not url: raise ValueError("Thiếu thông tin bắt buộc (tieu_de, url).")
                                if not url.startswith("http://") and not url.startswith("https://"): raise ValueError(
                                    "URL không hợp lệ.")

                                insert_data = {"bai_hoc_id": bai_hoc_id, "tieu_de": tieu_de, "url": url, "mo_ta": mo_ta}
                                supabase.table(table_name).insert(insert_data).execute();
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import thành công {count} video.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file Excel: {e}")

    if st.session_state['video_active_tab'] != "📝 Danh sách & Sửa":
        st.markdown(f"""
        <script>
            var tab_names = ["📝 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"];
            var active_tab_index = tab_names.indexOf("{st.session_state['video_active_tab']}");
            var tabs = window.parent.document.querySelectorAll('[role="tab"]');

            if (active_tab_index !== -1 && tabs.length > active_tab_index) {{
                tabs[active_tab_index].click();
            }}
        </script>
        """, unsafe_allow_html=True)