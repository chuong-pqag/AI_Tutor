# ===============================================
# ❓ Module Quản lý Câu hỏi - manage_questions.py
# (BẢN FINAL: Hỗ trợ Ảnh, TTS Async, Lọc Năm học & Duyệt Đóng góp)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import json
import uuid
import os # Thêm os để xử lý tên file
from . import crud_utils
from backend.supabase_client import supabase

# Bucket để upload ảnh — ưu tiên lấy từ biến môi trường, nếu không có dùng giá trị mặc định
# IMAGE_BUCKET = os.environ.get("IMAGE_BUCKET", "question-images")
IMAGE_BUCKET = "question_images"
# Nếu hệ thống của bạn dùng tên khác, đổi "question-images" thành tên bucket thực tế.

@st.cache_data(ttl=60)
def load_lesson_data_for_questions(active_chu_de_ids):
    """Tải dữ liệu bài học VÀ LỌC theo Chủ đề đang hoạt động."""
    try:
        bai_hoc_df_all = crud_utils.load_data("bai_hoc")

        # LỌC BÀI HỌC THEO CHỦ ĐỀ ĐANG HOẠT ĐỘNG
        bai_hoc_df_filtered = bai_hoc_df_all[bai_hoc_df_all['chu_de_id'].astype(str).isin(active_chu_de_ids)].copy()

        bai_hoc_df_filtered = bai_hoc_df_filtered.sort_values(by=["chu_de_id", "thu_tu"]).reset_index(drop=True)

        bai_hoc_details = {
            str(row['id']): {
                "name": f"{row.get('thu_tu', 0)}. {row['ten_bai_hoc']}",
                "chu_de_id": str(row.get('chu_de_id'))
            }
            for _, row in bai_hoc_df_filtered.iterrows()
        } if not bai_hoc_df_filtered.empty else {}
        return bai_hoc_details
    except Exception:
        return {}


def render(mon_hoc_options):
    """
    Hiển thị giao diện quản lý Câu hỏi.
    """
    st.subheader("❓ Quản lý Câu hỏi")

    # TAB CẤU TRÚC
    tab_list, tab_add, tab_import_q, tab_approve, tab_upload_tools = st.tabs([
        "📝 Danh sách & Sửa/Xóa",
        "➕ Thêm mới",
        "📤 Import Excel",
        "✅ Duyệt đóng góp",
        "🛠️ Upload Ảnh & Lấy Link"  # <-- TAB MỚI
    ])

    table_name = "cau_hoi"

    # === LẤY NĂM HỌC ĐANG CHỌN (Toàn cục) ===
    selected_year = st.session_state.get("global_selected_school_year")
    st.caption(f"Đang quản lý Ngân hàng câu hỏi liên quan đến Năm học: **{selected_year}**")

    # --- LOGIC LỌC CHỦ ĐỀ/BÀI HỌC THEO NĂM HỌC ---
    lop_df_all = crud_utils.load_data("lop_hoc")
    lop_df_filtered = lop_df_all[lop_df_all['nam_hoc'] == selected_year].copy()
    active_khoi_list = lop_df_filtered['khoi'].dropna().unique().tolist()

    # 1. Lọc Chủ đề
    chu_de_df_all = crud_utils.load_data("chu_de")
    chu_de_df_filtered_by_year = chu_de_df_all[chu_de_df_all['lop'].isin(active_khoi_list)].copy()
    active_chu_de_ids = chu_de_df_filtered_by_year['id'].astype(str).tolist()

    # 2. Tái tạo map Chủ đề
    chu_de_options_active = {
        f"{row['ten_chu_de']} (L{row['lop']}-T{row['tuan']})": str(row['id'])
        for _, row in chu_de_df_filtered_by_year.iterrows()
    }

    # 3. Lọc Bài học
    bai_hoc_details_active = load_lesson_data_for_questions(active_chu_de_ids)
    active_bai_hoc_ids = list(bai_hoc_details_active.keys())

    # Lọc Dữ liệu Câu hỏi (Bảng chính - CHỈ LẤY CÂU ĐÃ DUYỆT HOẶC CỦA ADMIN)
    df_quiz_original_all = crud_utils.load_data(table_name)

    # Lọc: Thuộc chủ đề active VÀ (đã duyệt HOẶC dữ liệu cũ chưa có cột duyệt)
    df_quiz_original = df_quiz_original_all[
        df_quiz_original_all['chu_de_id'].astype(str).isin(active_chu_de_ids) &
        (df_quiz_original_all['trang_thai_duyet'].isin(['approved', None, 'NaN']) | df_quiz_original_all[
            'trang_thai_duyet'].isna())
        ].copy()

    LOAI_CAU_HOI_OPTIONS = ["mot_lua_chon", "nhieu_lua_chon", "dien_khuyet"]
    MUC_DO_OPTIONS = ["biết", "hiểu", "vận dụng"]

    # =======================================================
    # TAB 1: THÊM MỚI
    # =======================================================
    with tab_add:
        st.markdown("### ❓ Thêm câu hỏi mới")

        if chu_de_df_filtered_by_year.empty:
            st.warning(
                f"⚠️ Không tìm thấy Chủ đề nào thuộc Khối lớp đang hoạt động trong Năm học: **{selected_year}**.")
            st.stop()

        # 1. Chọn Môn
        selected_mon_hoc_name = st.selectbox("**1. Chọn Môn học***:", list(mon_hoc_options.keys()),
                                             key="q_add_monhoc_select", index=None)

        # 2. Chọn Chủ đề (Lọc theo Môn)
        filtered_chu_de_options_map = {}
        if selected_mon_hoc_name:
            filtered_chu_de_options_map = {
                display_name: id
                for display_name, id in chu_de_options_active.items()
                if not chu_de_df_filtered_by_year[chu_de_df_filtered_by_year['id'] == id].empty and
                   chu_de_df_filtered_by_year[chu_de_df_filtered_by_year['id'] == id].iloc[0][
                       'mon_hoc'] == selected_mon_hoc_name
            }
            filtered_chu_de_options_map = dict(sorted(filtered_chu_de_options_map.items()))

        selected_chu_de_name = st.selectbox(
            "**2. Chọn Chủ đề (Bắt buộc)***:",
            list(filtered_chu_de_options_map.keys()),
            key="q_add_cd_select_main",
            index=None,
            disabled=(not selected_mon_hoc_name or not filtered_chu_de_options_map)
        )
        selected_chu_de_id = filtered_chu_de_options_map.get(selected_chu_de_name)

        # 3. Chọn Bài học (Lọc theo Chủ đề)
        filtered_lesson_options = {}
        if selected_chu_de_id:
            filtered_lesson_options = {
                details["name"]: bh_id
                for bh_id, details in bai_hoc_details_active.items()
                if details["chu_de_id"] == selected_chu_de_id
            }

        lesson_options_with_none = {"(Không thuộc bài học cụ thể / Câu hỏi chung)": "NONE_VALUE"}
        lesson_options_with_none.update(dict(sorted(filtered_lesson_options.items())))

        selected_lesson_name = st.selectbox(
            "**3. Chọn Bài học (Tùy chọn)**:",
            list(lesson_options_with_none.keys()),
            key="q_add_bh_select_filtered",
            index=0,
            disabled=(not selected_chu_de_id)
        )
        selected_lesson_id = lesson_options_with_none.get(selected_lesson_name)
        if selected_lesson_id == "NONE_VALUE": selected_lesson_id = None

        if selected_chu_de_id:
            with st.form("add_question_form", clear_on_submit=True):
                st.markdown("**4. Nội dung chi tiết**")
                col_a, col_b = st.columns(2)
                with col_a:
                    loai = st.selectbox("Loại câu hỏi *", LOAI_CAU_HOI_OPTIONS, key="q_loai")
                with col_b:
                    muc_do = st.selectbox("Mức độ *", MUC_DO_OPTIONS, key="q_muc_do")

                noi_dung = st.text_area("Nội dung (Chữ) *", key="q_noi_dung", height=100)
                hinh_anh_url = st.text_input("Link Ảnh minh họa (Tùy chọn)", key="q_hinh_anh",
                                             help="Dán URL ảnh công khai")

                st.markdown("**Đáp án**")
                dap_an_dung_raw = st.text_area("Đáp án ĐÚNG * (Mỗi dòng 1 đáp án / URL ảnh)", key="q_dung_raw",
                                               height=80)
                dap_an_khac_raw = ""
                if loai != "dien_khuyet":
                    dap_an_khac_raw = st.text_area("Đáp án SAI (Mỗi dòng 1 đáp án / URL ảnh)", key="q_khac_raw",
                                                   height=80)

                diem_so = st.number_input("Điểm", min_value=0, value=1, key="q_diem")

                submitted = st.form_submit_button("➕ Thêm câu hỏi", width='stretch')

                if submitted:
                    dap_an_dung = [s.strip() for s in dap_an_dung_raw.split("\n") if s.strip()]
                    dap_an_khac = [s.strip() for s in dap_an_khac_raw.split("\n") if
                                   s.strip()] if loai != "dien_khuyet" else []

                    if not noi_dung and not hinh_anh_url:
                        st.error("Phải có ít nhất Nội dung (Chữ) hoặc Hình ảnh minh họa.")
                    elif (loai == "mot_lua_chon" and len(dap_an_dung) != 1):
                        st.error("Câu 'Một lựa chọn' cần đúng 1 đáp án đúng.")
                    elif not dap_an_dung:
                        st.error("Phải có ít nhất 1 đáp án đúng.")
                    else:
                        try:
                            new_question_id = str(uuid.uuid4())
                            insert_payload = {
                                "id": new_question_id,
                                "chu_de_id": selected_chu_de_id,
                                "bai_hoc_id": selected_lesson_id,
                                "loai_cau_hoi": loai,
                                "noi_dung": noi_dung,
                                "hinh_anh_url": hinh_anh_url if hinh_anh_url else None,
                                "dap_an_dung": dap_an_dung,
                                "dap_an_khac": dap_an_khac,
                                "muc_do": muc_do,
                                "diem_so": diem_so,
                                "trang_thai_duyet": "approved"  # Admin thêm thì tự duyệt
                            }
                            supabase.table(table_name).insert(insert_payload).execute()

                            # Queue TTS
                            if noi_dung:
                                supabase.table("task_queue").insert({
                                    "task_type": "tts_generation",
                                    "status": "pending",
                                    "payload": {"question_id": new_question_id, "noi_dung": noi_dung}
                                }).execute()
                                st.success(f"Đã thêm câu hỏi! TTS đang xử lý.")
                            else:
                                st.success(f"Đã thêm câu hỏi (Không có TTS).")

                            crud_utils.clear_all_cached_data()
                        except Exception as e:
                            st.error(f"Lỗi thêm câu hỏi: {e}")

    # =======================================================
    # TAB 2: DANH SÁCH & SỬA/XÓA
    # =======================================================
    with tab_list:
        if df_quiz_original.empty:
            st.warning(f"Không tìm thấy Câu hỏi nào thuộc Khối lớp đang hoạt động trong Năm học: **{selected_year}**.")
            st.stop()

        # Chuẩn bị DataFrame hiển thị
        df_quiz_display = df_quiz_original.copy()
        df_quiz_display['chu_de_id_str'] = df_quiz_display['chu_de_id'].astype(str)
        chu_de_df_filtered_by_year['chu_de_id_str'] = chu_de_df_filtered_by_year['id'].astype(str)

        # Merge lấy tên
        df_quiz_display = pd.merge(
            df_quiz_display,
            chu_de_df_filtered_by_year[['chu_de_id_str', 'ten_chu_de', 'mon_hoc', 'lop']],
            on='chu_de_id_str',
            how='left'
        )
        df_quiz_display = df_quiz_display.rename(columns={"lop": "Khối", "mon_hoc": "Môn học", "ten_chu_de": "Chủ đề"})
        df_quiz_display = df_quiz_display.sort_values(by=["Khối", "Môn học", "Chủ đề", "id"]).reset_index(drop=True)

        # Bộ lọc
        st.markdown("##### 🔍 Lọc danh sách")
        col_f1, col_f2, col_f3 = st.columns(3)

        # Lọc Khối
        with col_f1:
            khoi_list_raw = df_quiz_display['Khối'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])
            selected_khoi = st.selectbox("Lọc theo Khối:", khoi_list, key="q_filter_khoi", index=0)

        df_filtered_by_khoi = df_quiz_display
        if selected_khoi != "Tất cả":
            df_filtered_by_khoi = df_quiz_display[df_quiz_display['Khối'] == selected_khoi]

        # Lọc Môn
        with col_f2:
            mon_hoc_list = ["Tất cả"] + sorted(list(df_filtered_by_khoi['Môn học'].dropna().unique()))
            selected_mon_hoc = st.selectbox("Lọc theo Môn học:", mon_hoc_list, key="q_filter_monhoc", index=0)

        # Lọc Chủ đề
        with col_f3:
            df_filtered_by_mon = df_filtered_by_khoi
            if selected_mon_hoc != "Tất cả":
                df_filtered_by_mon = df_filtered_by_khoi[df_filtered_by_khoi['Môn học'] == selected_mon_hoc]
            chu_de_list = ["Tất cả"]
            chu_de_list.extend(sorted(list(df_filtered_by_mon['Chủ đề'].dropna().unique())))
            selected_chu_de = st.selectbox("Lọc theo Chủ đề:", chu_de_list, key="q_filter_chude", index=0)

        df_to_show = df_filtered_by_mon.copy()
        if selected_chu_de != "Tất cả":
            df_to_show = df_to_show[df_to_show['Chủ đề'] == selected_chu_de]

        st.markdown("---")

        if not df_to_show.empty:
            cols_display_q = ['id', 'noi_dung', 'hinh_anh_url', 'Khối', 'Môn học', 'Chủ đề', 'muc_do', 'loai_cau_hoi']
            cols_exist = [col for col in cols_display_q if col in df_to_show.columns]

            st.info("Nhấp vào một hàng để Sửa/Xóa.")
            gb = st.dataframe(
                df_to_show[cols_exist].rename(
                    columns={"hinh_anh_url": "Ảnh", "loai_cau_hoi": "Loại", "muc_do": "Mức độ"}),
                key="quiz_df_select",
                hide_index=True,
                width='stretch',
                on_select="rerun",
                selection_mode="single-row"
            )
            selected_rows = gb.selection.rows
            selected_item_original = None

            if selected_rows:
                original_id = df_to_show.iloc[selected_rows[0]]['id']
                st.session_state['quiz_selected_item_id'] = original_id

            if 'quiz_selected_item_id' in st.session_state:
                selected_id = st.session_state['quiz_selected_item_id']
                original_item_df = df_quiz_original_all[df_quiz_original_all['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # Form Sửa/Xóa
            if selected_item_original:
                is_active = selected_item_original.get('chu_de_id') in active_chu_de_ids
                disabled_editing = not is_active
                if not is_active: st.warning("Câu hỏi thuộc chủ đề không hoạt động trong năm nay.")

                with st.expander("📝 Sửa/Xóa Câu hỏi", expanded=True):
                    with st.form("edit_question_form"):
                        st.text(f"ID: {selected_item_original['id']}")

                        # Các trường nội dung
                        noi_dung_edit = st.text_area("Nội dung", value=selected_item_original.get("noi_dung", ""),
                                                     disabled=disabled_editing)
                        current_img = selected_item_original.get("hinh_anh_url", "")
                        if current_img: st.image(current_img, width=200)
                        hinh_anh_url_edit = st.text_input("Link Ảnh", value=current_img or "",
                                                          disabled=disabled_editing)

                        dap_an_dung_list = selected_item_original.get("dap_an_dung", [])
                        dap_an_dung_raw_edit = st.text_area("Đáp án ĐÚNG", value="\n".join(map(str, dap_an_dung_list)),
                                                            disabled=disabled_editing)

                        dap_an_khac_list = selected_item_original.get("dap_an_khac", [])
                        dap_an_khac_raw_edit = st.text_area("Đáp án SAI", value="\n".join(map(str, dap_an_khac_list)),
                                                            disabled=disabled_editing)

                        md_idx = MUC_DO_OPTIONS.index(selected_item_original.get("muc_do", "biết"))
                        muc_do_edit = st.selectbox("Mức độ", MUC_DO_OPTIONS, index=md_idx, disabled=disabled_editing)

                        diem_so_edit = st.number_input("Điểm", value=selected_item_original.get("diem_so", 1),
                                                       disabled=disabled_editing)

                        regen_tts = st.checkbox("Tạo lại Audio", disabled=disabled_editing)

                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("💾 Lưu", width='stretch', disabled=disabled_editing):
                            d_dung = [s.strip() for s in dap_an_dung_raw_edit.split("\n") if s.strip()]
                            d_sai = [s.strip() for s in dap_an_khac_raw_edit.split("\n") if s.strip()]

                            update_data = {
                                "noi_dung": noi_dung_edit,
                                "hinh_anh_url": hinh_anh_url_edit if hinh_anh_url_edit else None,
                                "dap_an_dung": d_dung,
                                "dap_an_khac": d_sai,
                                "muc_do": muc_do_edit,
                                "diem_so": diem_so_edit
                            }
                            try:
                                supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                    'id']).execute()
                                if regen_tts and noi_dung_edit:
                                    supabase.table("task_queue").insert(
                                        {"task_type": "tts_generation", "status": "pending",
                                         "payload": {"question_id": selected_item_original['id'],
                                                     "noi_dung": noi_dung_edit}}).execute()
                                    st.success("Đã cập nhật & Gửi yêu cầu Audio!")
                                else:
                                    st.success("Cập nhật thành công!")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")

                        if c2.form_submit_button("❌ Xóa", width='stretch', disabled=disabled_editing):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning("Đã xóa!");
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa: {e}")

                        if c3.form_submit_button("Hủy", width='stretch'):
                            del st.session_state['quiz_selected_item_id'];
                            st.rerun()

    # =======================================================
    # TAB 3: IMPORT EXCEL
    # =======================================================
    with tab_import_q:
        st.markdown("### 📤 Import câu hỏi từ Excel")
        st.warning(f"Việc import sẽ áp dụng cho Chủ đề/Bài học đang hoạt động trong Năm học: **{selected_year}**")

        sample_data_q = {
            'chu_de_id': ['UUID CỦA CHỦ ĐỀ'],
            'bai_hoc_id': ['UUID BÀI HỌC (Tùy chọn)'],
            'loai_cau_hoi': ['mot_lua_chon'],
            'noi_dung': ['Nội dung câu hỏi...'],
            'hinh_anh_url': ['https://link-anh.jpg'],
            'dap_an_dung': ['Đáp án đúng'],
            'dap_an_khac': ['Đáp án sai 1; Đáp án sai 2'],
            'muc_do': ['biết'],
            'diem_so': [1]
        }
        crud_utils.create_excel_download(pd.DataFrame(sample_data_q), "mau_import_cau_hoi.xlsx",
                                         sheet_name='DanhSachCauHoi')

        uploaded = st.file_uploader("Chọn file Excel Câu hỏi", type=["xlsx"], key="quiz_upload")
        if uploaded:
            try:
                df_upload = pd.read_excel(uploaded, dtype=str)
                st.dataframe(df_upload.head())

                valid_chu_de_ids = active_chu_de_ids
                if not valid_chu_de_ids:
                    st.error("Chưa có chủ đề nào hoạt động để import.")
                elif st.button("🚀 Import Câu hỏi", width='stretch'):
                    count = 0;
                    errors = []
                    tasks_to_queue = []
                    with st.spinner("Đang import..."):
                        for index, row in df_upload.iterrows():
                            try:
                                cd_id = str(row["chu_de_id"]).strip()
                                if cd_id not in active_chu_de_ids: raise ValueError(
                                    "Chủ đề không hợp lệ (hoặc không thuộc năm học này).")

                                nd = str(row.get("noi_dung", "")).strip()
                                # Xử lý ảnh: nếu là 'nan' thì coi như None
                                raw_img = str(row.get("hinh_anh_url", "")).strip()
                                img = raw_img if raw_img and raw_img.lower() != 'nan' else None

                                if not nd and not img: raise ValueError("Thiếu nội dung/ảnh.")

                                # === FIX LỖI "NAN" UUID TẠI ĐÂY ===
                                raw_bh_id = str(row.get("bai_hoc_id", "")).strip()
                                # Nếu rỗng hoặc là 'nan' thì gán là None
                                bai_hoc_id_clean = None if (not raw_bh_id or raw_bh_id.lower() == 'nan') else raw_bh_id
                                # ==================================

                                new_id = str(uuid.uuid4())
                                insert_data = {
                                    "id": new_id,
                                    "chu_de_id": cd_id,
                                    "bai_hoc_id": bai_hoc_id_clean,  # Sử dụng biến đã làm sạch
                                    "loai_cau_hoi": str(row.get("loai_cau_hoi", "mot_lua_chon")).strip().lower(),
                                    "noi_dung": nd,
                                    "hinh_anh_url": img,
                                    "dap_an_dung": [s.strip() for s in str(row.get("dap_an_dung", "")).split(";") if
                                                    s.strip()],
                                    "dap_an_khac": [s.strip() for s in str(row.get("dap_an_khac", "")).split(";") if
                                                    s.strip()],
                                    "muc_do": str(row.get("muc_do", "biết")).strip().lower(),
                                    "diem_so": int(pd.to_numeric(row.get("diem_so", 1), errors='coerce')),
                                    "trang_thai_duyet": "approved"
                                }
                                supabase.table(table_name).insert(insert_data).execute()
                                if nd:
                                    tasks_to_queue.append({"task_type": "tts_generation", "status": "pending",
                                                           "payload": {"question_id": new_id, "noi_dung": nd}})
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")

                        if tasks_to_queue:
                            supabase.table("task_queue").insert(tasks_to_queue).execute()

                    st.success(f"✅ Import thành công {count} câu hỏi.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file: {e}")

    # =======================================================
    # TAB 4: DUYỆT ĐÓNG GÓP (HOÀN THIỆN)
    # =======================================================
    with tab_approve:
        st.markdown("### ✅ Duyệt câu hỏi đóng góp từ Giáo viên")

        try:
            pending_res = supabase.table("cau_hoi").select(
                "*, giao_vien(ho_ten), chu_de(ten_chu_de, mon_hoc, lop)"
            ).eq("trang_thai_duyet", "pending").order("created_at", desc=True).execute()
            pending_questions = pending_res.data or []
        except Exception:
            pending_questions = []

        if not pending_questions:
            st.success("🎉 Không có câu hỏi nào đang chờ duyệt.")
        else:
            st.info(f"Có **{len(pending_questions)}** câu hỏi đang chờ duyệt.")

            for q in pending_questions:
                teacher_name = q.get('giao_vien', {}).get('ho_ten', 'Unknown')
                chu_de_info = q.get('chu_de', {})
                location = f"Khối {chu_de_info.get('lop')} - {chu_de_info.get('mon_hoc')} - {chu_de_info.get('ten_chu_de')}"

                with st.expander(f"⏳ {teacher_name}: {q['noi_dung'][:50]}... ({q['muc_do']})", expanded=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**Vị trí:** {location}")
                        st.markdown(f"**Nội dung:** {q['noi_dung']}")
                        if q.get('hinh_anh_url'): st.image(q['hinh_anh_url'], width=200)
                        st.markdown("**Đáp án đúng:**");
                        st.code("\n".join(q['dap_an_dung']))
                        st.markdown("**Đáp án sai:**");
                        st.code("\n".join(q.get('dap_an_khac') or []))

                    with c2:
                        with st.form(f"approve_form_{q['id']}"):
                            new_muc_do = st.selectbox("Sửa mức độ:", MUC_DO_OPTIONS,
                                                      index=MUC_DO_OPTIONS.index(q['muc_do']), key=f"lvl_{q['id']}")
                            c_ok, c_no = st.columns(2)
                            if c_ok.form_submit_button("✅ Duyệt", type="primary", use_container_width=True):
                                try:
                                    supabase.table("cau_hoi").update(
                                        {"trang_thai_duyet": "approved", "muc_do": new_muc_do}).eq("id",
                                                                                                   q['id']).execute()
                                    if q.get('noi_dung'):
                                        supabase.table("task_queue").insert(
                                            {"task_type": "tts_generation", "status": "pending",
                                             "payload": {"question_id": q['id'], "noi_dung": q['noi_dung']}}).execute()
                                    st.success("Đã duyệt!");
                                    crud_utils.clear_all_cached_data();
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Lỗi: {e}")

                            if c_no.form_submit_button("❌ Từ chối", use_container_width=True):
                                try:
                                    supabase.table("cau_hoi").update({"trang_thai_duyet": "rejected"}).eq("id", q[
                                        'id']).execute()
                                    st.warning("Đã từ chối.");
                                    crud_utils.clear_all_cached_data();
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Lỗi: {e}")
    # =======================================================
    # 🆕 TAB 5: CÔNG CỤ UPLOAD ẢNH HÀNG LOẠT
    # =======================================================
    with tab_upload_tools:
        st.markdown("### 🛠️ Công cụ Upload ảnh hàng loạt")
        st.info(
            "Sử dụng công cụ này để upload ảnh câu hỏi/đáp án lên Server, sau đó nhận file CSV chứa link để dán vào file Import Excel.")

        uploaded_images = st.file_uploader(
            "Chọn các file ảnh (JPG, PNG)",
            type=['png', 'jpg', 'jpeg', 'gif'],
            accept_multiple_files=True
        )

        if uploaded_images:
            st.write(f"Đã chọn **{len(uploaded_images)}** file.")

            if st.button(f"🚀 Bắt đầu Upload {len(uploaded_images)} ảnh", type="primary"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                total_files = len(uploaded_images)

                for i, img_file in enumerate(uploaded_images):
                    try:
                        # 1. Tạo tên file an toàn (uuid + tên gốc)
                        # Để tránh trùng lặp và lỗi ký tự đặc biệt
                        file_ext = os.path.splitext(img_file.name)[1].lower()
                        clean_name = str(uuid.uuid4())[:8] + "_" + img_file.name
                        storage_path = clean_name  # Lưu ngay thư mục gốc của bucket hoặc subfolder

                        status_text.text(f"Đang upload ({i + 1}/{total_files}): {img_file.name}...")

                        # 2. Upload lên Supabase
                        file_bytes = img_file.getvalue()
                        supabase.storage.from_(IMAGE_BUCKET).upload(
                            path=storage_path,
                            file=file_bytes,
                            file_options={"content-type": img_file.type, "upsert": "false"}
                        )

                        # 3. Lấy Public URL
                        public_url = supabase.storage.from_(IMAGE_BUCKET).get_public_url(storage_path)

                        results.append({
                            "Ten_File_Goc": img_file.name,
                            "URL_Cong_Khai": public_url
                        })

                    except Exception as e:
                        st.error(f"Lỗi khi upload '{img_file.name}': {e}")
                        results.append({
                            "Ten_File_Goc": img_file.name,
                            "URL_Cong_Khai": "ERROR"
                        })

                    # Update tiến độ
                    progress_bar.progress((i + 1) / total_files)

                status_text.success("✅ Đã hoàn thành quá trình upload!")

                # 4. Tạo DataFrame và Nút Download CSV
                if results:
                    df_links = pd.DataFrame(results)
                    st.dataframe(df_links, use_container_width=True)

                    csv = df_links.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Tải danh sách Link (CSV)",
                        data=csv,
                        file_name="danh_sach_link_anh.csv",
                        mime="text/csv",
                    )
                    st.caption(
                        "Mẹo: Mở file CSV này, copy cột 'URL_Cong_Khai' và dán vào file Excel Import Câu hỏi.")