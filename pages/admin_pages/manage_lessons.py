# ===============================================
# 📝 Module Quản lý Bài học - manage_lessons.py (ĐÃ TÁI CẤU TRÚC DATA LOADING)
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

# --- Các hàm helper (upload/delete PDF) (Giữ nguyên) ---
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


# --- Hết hàm helper ---


# === THAY ĐỔI CHỮ KÝ HÀM ===
def render(mon_hoc_options):
    """
    Hiển thị giao diện quản lý Bài học.
    (Đã tái cấu trúc: Tự tải dữ liệu Chủ đề)
    """
    st.subheader("📝 Quản lý Bài học")
    tab_list, tab_add, tab_import = st.tabs(["📑 Danh sách & Sửa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "bai_hoc"

    # === TẢI DỮ LIỆU CẦN THIẾT (Tự cung cấp) ===
    selected_year = st.session_state.get("global_selected_school_year")
    st.caption(f"Đang quản lý Bài học liên quan đến Năm học: **{selected_year}**")

    # 1. Lấy Khối (Grades) đang hoạt động trong năm đã chọn
    lop_df_all = crud_utils.load_data("lop_hoc")
    lop_df_filtered = lop_df_all[lop_df_all['nam_hoc'] == selected_year].copy()
    active_khoi_list = lop_df_filtered['khoi'].dropna().unique().tolist()

    # 2. Lọc Chủ đề (Master Data - lọc theo Khối đang hoạt động)
    chu_de_df_all = crud_utils.load_data("chu_de")  # Tải tất cả chủ đề
    chu_de_df_filtered_by_year = chu_de_df_all[chu_de_df_all['lop'].isin(active_khoi_list)].copy()
    active_chu_de_ids = chu_de_df_filtered_by_year['id'].astype(str).tolist()

    # 3. Tái tạo map Chủ đề
    chu_de_options_active = {
        f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id'])
        for _, row in chu_de_df_filtered_by_year.iterrows()
    }

    # 4. Lọc Bài học (Bảng chính)
    df_lesson_original_all = crud_utils.load_data(table_name)
    df_lesson_original = df_lesson_original_all[
        df_lesson_original_all['chu_de_id'].astype(str).isin(active_chu_de_ids)].copy()
    # ---------------------------------------------

    # --- Tab Thêm mới (Cập nhật logic chọn Chủ đề) ---
    with tab_add:
        st.markdown("#### ✨ Thêm bài học mới")

        if chu_de_df_filtered_by_year.empty:
            st.warning(
                f"⚠️ Không tìm thấy Chủ đề nào thuộc Khối lớp đang hoạt động trong Năm học: **{selected_year}**.")
            st.stop()

        # 1. Chọn Môn học
        if not mon_hoc_options:
            st.warning("⚠️ Chưa có Môn học nào. Vui lòng thêm Môn học trước.");
            st.stop()

        selected_mon_hoc_name = st.selectbox(
            "**1. Chọn Môn học***:",
            list(mon_hoc_options.keys()),
            key="lesson_add_monhoc_select",
            index=None,
            placeholder="Chọn môn học..."
        )

        # 2. Lọc Chủ đề theo Môn học (từ list đã lọc theo năm)
        filtered_chu_de_options_map = {}
        if selected_mon_hoc_name:
            filtered_chu_de_options_map = {
                display_name: id
                for display_name, id in chu_de_options_active.items()  # DÙNG MAP ĐÃ LỌC
                if not chu_de_df_filtered_by_year[chu_de_df_filtered_by_year['id'] == id].empty and
                   chu_de_df_filtered_by_year[chu_de_df_filtered_by_year['id'] == id].iloc[0][
                       'mon_hoc'] == selected_mon_hoc_name
            }
            filtered_chu_de_options_map = dict(sorted(filtered_chu_de_options_map.items()))

        # 3. Chọn Chủ đề
        selected_chu_de_name = st.selectbox(
            "**2. Thuộc Chủ đề***:",
            list(filtered_chu_de_options_map.keys()),
            key="lesson_add_cd",
            index=None,
            placeholder="Chọn chủ đề..." if selected_mon_hoc_name else "Vui lòng chọn Môn học trước",
            disabled=(not selected_mon_hoc_name or not filtered_chu_de_options_map)
        )
        selected_chu_de_id = filtered_chu_de_options_map.get(selected_chu_de_name)

        # 4. Form nhập liệu
        if selected_chu_de_id:
            with st.form("add_lesson_form", clear_on_submit=True):
                st.markdown("**3. Nhập thông tin Bài học**:")
                ten_bai_hoc = st.text_input("Tên bài học *")
                thu_tu = st.number_input("Thứ tự", min_value=0, value=0, step=1)
                mo_ta = st.text_area("Mô tả")
                uploaded_pdf = st.file_uploader("Tải Nội dung PDF", type=["pdf"], key="lesson_pdf_upload")

                submitted = st.form_submit_button("➕ Thêm bài học", use_container_width=True)
                if submitted:
                    if not ten_bai_hoc:
                        st.error("Tên bài học trống.")
                    else:
                        try:
                            insert_payload = {"ten_bai_hoc": ten_bai_hoc, "chu_de_id": selected_chu_de_id,
                                              "thu_tu": thu_tu, "mo_ta": mo_ta if mo_ta else None}
                            response = supabase.table(table_name).insert(insert_payload).execute()
                            if response.data and len(response.data) > 0:
                                new_lesson_id = response.data[0]['id'];
                                pdf_url = None
                                if uploaded_pdf:
                                    st.info("Đang tải PDF...")
                                    pdf_url = upload_pdf_to_storage(uploaded_pdf, new_lesson_id)
                                    if pdf_url:
                                        supabase.table(table_name).update({"noi_dung_pdf_url": pdf_url}).eq("id",
                                                                                                            new_lesson_id).execute()
                                        st.success(f"Đã thêm '{ten_bai_hoc}' và PDF!")
                                    else:
                                        st.warning(f"Đã thêm '{ten_bai_hoc}' nhưng lỗi tải PDF.")
                                else:
                                    st.success(f"Đã thêm '{ten_bai_hoc}' (không có PDF).")
                                crud_utils.clear_all_cached_data()
                            else:
                                st.error("Lỗi thêm vào CSDL.")
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

    # --- Tab Danh sách & Sửa/Xóa (ĐÃ THÊM BỘ LỌC) ---
    with tab_list:

        if df_lesson_original.empty:
            st.warning(f"Không tìm thấy Bài học nào thuộc Chủ đề đang hoạt động trong Năm học: **{selected_year}**.")
            st.stop()

        # 1. Chuẩn bị DataFrame hiển thị (thêm cột Khối, Môn, Chủ đề)
        df_lesson_display = df_lesson_original.copy()

        df_lesson_display['chu_de_id_str'] = df_lesson_display['chu_de_id'].astype(str)
        chu_de_df_filtered_by_year['chu_de_id_str'] = chu_de_df_filtered_by_year['id'].astype(str)

        df_lesson_display = pd.merge(
            df_lesson_display,
            chu_de_df_filtered_by_year[['chu_de_id_str', 'ten_chu_de', 'mon_hoc', 'lop']],
            on='chu_de_id_str',
            how='left'
        )
        df_lesson_display = df_lesson_display.rename(columns={
            "lop": "Khối",
            "mon_hoc": "Môn học",
            "ten_chu_de": "Chủ đề"
        })

        df_lesson_display = df_lesson_display.sort_values(by=["Khối", "Môn học", "Chủ đề", "thu_tu"]).reset_index(
            drop=True)

        # 2. Tạo Bộ lọc
        st.markdown("##### 🔍 Lọc danh sách")
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            khoi_list_raw = df_lesson_display['Khối'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])
            selected_khoi = st.selectbox("Lọc theo Khối:", khoi_list, key="lesson_filter_khoi", index=0)

        with col_f2:
            df_filtered_by_khoi = df_lesson_display
            if selected_khoi != "Tất cả":
                df_filtered_by_khoi = df_filtered_by_khoi[df_filtered_by_khoi['Khối'] == selected_khoi]

            mon_hoc_list = ["Tất cả"] + sorted(
                list(df_filtered_by_khoi['Môn học'].dropna().unique()))
            selected_mon_hoc = st.selectbox("Lọc theo Môn học:", mon_hoc_list, key="lesson_filter_monhoc", index=0)

        with col_f3:
            df_filtered_by_mon = df_filtered_by_khoi
            if selected_mon_hoc != "Tất cả":
                df_filtered_by_mon = df_filtered_by_mon[df_filtered_by_mon['Môn học'] == selected_mon_hoc]

            chu_de_list = ["Tất cả"] + sorted(list(df_filtered_by_mon['Chủ đề'].dropna().unique()))
            selected_chu_de = st.selectbox("Lọc theo Chủ đề:", chu_de_list, key="lesson_filter_chude", index=0)

        # 3. Lọc DataFrame
        df_to_show = df_filtered_by_mon.copy()
        if selected_chu_de != "Tất cả":
            df_to_show = df_to_show[df_to_show['Chủ đề'] == selected_chu_de]

        st.markdown("---")

        if not df_to_show.empty:
            cols_display_lesson = ["id", "ten_bai_hoc", "thu_tu", "Chủ đề", "Môn học", "Khối", "noi_dung_pdf_url"]
            cols_exist = [col for col in cols_display_lesson if col in df_to_show.columns]

            st.info("Nhấp vào hàng để Sửa/Xóa.")
            gb = st.dataframe(
                df_to_show[cols_exist].rename(
                    columns={"ten_bai_hoc": "Tên bài học", "thu_tu": "Thứ tự", "noi_dung_pdf_url": "Link PDF"}),
                key="lesson_df_select",
                hide_index=True,
                use_container_width=True,  # <-- ĐÃ CẬP NHẬT
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows;
            selected_item_original = None
            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']
                st.session_state['lesson_selected_item_id'] = original_id

            if 'lesson_selected_item_id' in st.session_state:
                selected_id = st.session_state['lesson_selected_item_id']
                original_item_df = df_lesson_original_all[df_lesson_original_all['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 4. Form Sửa/Xóa
            if selected_item_original:

                is_active_lesson = original_item_df['chu_de_id'].astype(str).iloc[0] in active_chu_de_ids
                disabled_editing = not is_active_lesson

                if not is_active_lesson:
                    st.warning(f"Bài học này không thuộc Chủ đề đang hoạt động trong Năm học **{selected_year}**.")

                with st.expander("📝 Sửa/Xóa Bài học", expanded=True):
                    with st.form("edit_lesson_form"):
                        st.text(f"ID: {selected_item_original['id']}")

                        # Dùng map Chủ đề đã lọc (active)
                        chu_de_opts_local = chu_de_options_active

                        ten_bai_hoc_edit = st.text_input("Tên bài học",
                                                         value=selected_item_original.get("ten_bai_hoc", ""),
                                                         disabled=disabled_editing);

                        current_cd_id = str(selected_item_original.get("chu_de_id", ""));

                        # Tìm tên hiển thị từ map active
                        current_cd_name = next(
                            (name for name, id_ in chu_de_opts_local.items() if id_ == current_cd_id), None);

                        cd_keys_list = list(chu_de_opts_local.keys())
                        cd_idx = cd_keys_list.index(
                            current_cd_name) if current_cd_name in cd_keys_list else 0;

                        chu_de_ten_edit = st.selectbox("Thuộc Chủ đề", cd_keys_list, index=cd_idx,
                                                       disabled=disabled_editing)

                        thu_tu_edit = st.number_input("Thứ tự", value=selected_item_original.get("thu_tu", 0), step=1,
                                                      disabled=disabled_editing);
                        mo_ta_edit = st.text_area("Mô tả", value=selected_item_original.get("mo_ta", "") or "",
                                                  disabled=disabled_editing)

                        current_pdf_url = selected_item_original.get("noi_dung_pdf_url");
                        if current_pdf_url:
                            st.markdown(f"**PDF hiện tại:** [Xem]({current_pdf_url})")
                        else:
                            st.caption("Chưa có PDF.")
                        uploaded_pdf_edit = st.file_uploader("Tải PDF mới", type=["pdf"], key="lesson_pdf_edit",
                                                             disabled=disabled_editing);
                        delete_pdf_flag = st.checkbox("Xóa PDF hiện tại", key="del_pdf_flag", disabled=disabled_editing)

                        col_update, col_delete, col_clear = st.columns(3)
                        if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True, disabled=disabled_editing):
                            update_data = {"ten_bai_hoc": ten_bai_hoc_edit,
                                           "chu_de_id": chu_de_opts_local.get(chu_de_ten_edit),
                                           "thu_tu": thu_tu_edit,
                                           "mo_ta": mo_ta_edit if mo_ta_edit else None, }
                            pdf_url_to_save = current_pdf_url
                            pdf_error = False
                            if delete_pdf_flag:
                                st.info("Đang xóa PDF...");
                                delete_pdf_from_storage(current_pdf_url);
                                pdf_url_to_save = None
                            elif uploaded_pdf_edit:
                                st.info("Đang tải PDF mới...");
                                new_pdf_url = upload_pdf_to_storage(uploaded_pdf_edit, selected_item_original['id'])
                                if new_pdf_url:
                                    if current_pdf_url and current_pdf_url != new_pdf_url: delete_pdf_from_storage(
                                        current_pdf_url)
                                    pdf_url_to_save = new_pdf_url
                                else:
                                    pdf_error = True
                            update_data["noi_dung_pdf_url"] = pdf_url_to_save
                            if pdf_error: st.error("Lỗi tải PDF mới. URL PDF sẽ không được cập nhật.")
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    "id"]).execute();
                                st.success("Cập nhật!");
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi cập nhật CSDL: {e}")

                        if col_delete.form_submit_button("❌ Xóa", use_container_width=True, disabled=disabled_editing):
                            st.info("Đang xóa PDF (nếu có)...");
                            delete_pdf_from_storage(selected_item_original.get("noi_dung_pdf_url"))
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original["id"]).execute();
                                st.warning("Đã xóa!");
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa: {e}")

                        if col_clear.form_submit_button("Hủy", use_container_width=True):
                            if 'lesson_selected_item_id' in st.session_state: del st.session_state[
                                'lesson_selected_item_id']; st.rerun()
        else:
            if df_lesson_original_all.empty:
                st.info("Chưa có bài học nào trong hệ thống.")
            else:
                st.info("Không tìm thấy bài học nào phù hợp với bộ lọc.")

    # --- Tab Import Excel (Sử dụng dữ liệu đã lọc) ---
    with tab_import:
        st.markdown("### 📤 Import bài học từ Excel")
        st.warning(f"Việc import sẽ áp dụng cho Chủ đề đang hoạt động trong Năm học: **{selected_year}**")
        sample_data_lesson = {'ten_bai_hoc': ['Bài 1'], 'chu_de_id': ['UUID CHỦ ĐỀ'], 'thu_tu': [1], 'mo_ta': ['Mô tả'],
                              'noi_dung_pdf_url': ['URL PDF (tùy chọn)']}
        crud_utils.create_excel_download(pd.DataFrame(sample_data_lesson), "mau_import_bai_hoc.xlsx",
                                         sheet_name='DanhSachBaiHoc')
        st.caption("Cột 'chu_de_id' phải chứa UUID (dạng text) của chủ đề đang hoạt động. PDF URL là tùy chọn.")
        uploaded_lesson = st.file_uploader("Chọn file Excel Bài học", type=["xlsx"], key="lesson_upload")
        if uploaded_lesson:
            try:
                df_upload_lesson = pd.read_excel(uploaded_lesson, dtype=str);
                st.dataframe(df_upload_lesson.head())
                # Dùng map ID của các chủ đề đang hoạt động
                valid_chu_de_ids = list(chu_de_options_active.values())

                if not valid_chu_de_ids:
                    st.error(f"Chưa có chủ đề nào hoạt động trong Năm học **{selected_year}** để import bài học.")
                elif st.button("🚀 Import Bài Học", use_container_width=True):
                    count = 0;
                    errors = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload_lesson.iterrows():
                            try:
                                ten_bai_hoc = str(row['ten_bai_hoc']).strip();
                                chu_de_id = str(row['chu_de_id']).strip();
                                thu_tu_val = pd.to_numeric(row.get('thu_tu', 0), errors='coerce');
                                mo_ta = str(row.get('mo_ta', '')).strip() if pd.notna(row.get('mo_ta')) else None;
                                pdf_url = str(row.get('noi_dung_pdf_url', '')).strip() if pd.notna(
                                    row.get('noi_dung_pdf_url')) else None
                                if not ten_bai_hoc: raise ValueError("Tên bài học trống.")

                                if chu_de_id not in valid_chu_de_ids: raise ValueError(
                                    f"Chu de ID '{chu_de_id}' không hợp lệ hoặc không hoạt động trong năm **{selected_year}**.")

                                if pd.isna(thu_tu_val): raise ValueError("Thứ tự không hợp lệ.")
                                thu_tu = int(thu_tu_val)
                                if pdf_url and (not pdf_url.startswith("http://") and not pdf_url.startswith(
                                        "https://")): raise ValueError("PDF URL không hợp lệ.")
                                insert_data = {"ten_bai_hoc": ten_bai_hoc, "chu_de_id": chu_de_id, "thu_tu": thu_tu,
                                               "mo_ta": mo_ta, "noi_dung_pdf_url": pdf_url}
                                supabase.table(table_name).insert(insert_data).execute();
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import {count} bài học.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file: {e}")