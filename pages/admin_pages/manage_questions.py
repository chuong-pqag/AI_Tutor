# ===============================================
# ❓ Module Quản lý Câu hỏi - manage_questions.py (Đã thêm lọc Khối/Môn/Chủ đề)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import io
import json
from . import crud_utils
from backend.supabase_client import supabase


# --- Hàm helper để tải options bài học (MỚI) ---
@st.cache_data(ttl=60)
def load_lesson_data_for_questions():
    """Tải dữ liệu bài học để lọc."""
    bai_hoc_df = crud_utils.load_data("bai_hoc")
    bai_hoc_df = bai_hoc_df.sort_values(by=["chu_de_id", "thu_tu"]).reset_index(drop=True)
    bai_hoc_details = {
        str(row['id']): {
            "name": f"{row.get('thu_tu', 0)}. {row['ten_bai_hoc']}",
            "chu_de_id": str(row.get('chu_de_id'))
        }
        for _, row in bai_hoc_df.iterrows()
    } if not bai_hoc_df.empty else {}
    return bai_hoc_details


# ---- SỬA CHỮ KÝ HÀM RENDER ----
def render(mon_hoc_options, chu_de_df, chu_de_options, chu_de_id_list):
    """
    Hiển thị giao diện quản lý Câu hỏi.
    Args:
        mon_hoc_options (dict): {tên_môn: id}
        chu_de_df (pd.DataFrame): DataFrame của bảng chu_de
        chu_de_options (dict): {tên_chủ_đề_display: id}
        chu_de_id_list (list): List các id chủ đề
    """
    st.subheader("❓ Quản lý Câu hỏi")
    tab_list, tab_add, tab_import_q = st.tabs(["📝 Danh sách & Sửa/Xóa", "➕ Thêm mới", "📤 Import Excel"])
    table_name = "cau_hoi"

    # Tải dữ liệu bài học
    bai_hoc_details = load_lesson_data_for_questions()

    # Định nghĩa các lựa chọn cố định
    LOAI_CAU_HOI_OPTIONS = ["mot_lua_chon", "nhieu_lua_chon", "dien_khuyet"]
    MUC_DO_OPTIONS = ["biết", "hiểu", "vận dụng"]

    # --- Tab Thêm mới (Đã sửa logic lọc 3 bước) ---
    with tab_add:
        st.markdown("### ❓ Thêm câu hỏi mới")

        # 1. Chọn Môn học
        if not mon_hoc_options:
            st.warning("⚠️ Chưa có Môn học nào. Vui lòng thêm Môn học trước.");
            st.stop()

        selected_mon_hoc_name = st.selectbox(
            "**1. Chọn Môn học***:",
            list(mon_hoc_options.keys()),
            key="q_add_monhoc_select",
            index=None,
            placeholder="Chọn môn học..."
        )

        # 2. Lọc Chủ đề theo Môn học
        filtered_chu_de_options_map = {}
        if selected_mon_hoc_name:
            filtered_chu_de_options_map = {
                display_name: id
                for display_name, id in chu_de_options.items()
                if not chu_de_df[chu_de_df['id'] == id].empty and chu_de_df[chu_de_df['id'] == id].iloc[0][
                    'mon_hoc'] == selected_mon_hoc_name
            }
            filtered_chu_de_options_map = dict(sorted(filtered_chu_de_options_map.items()))

        selected_chu_de_name = st.selectbox(
            "**2. Chọn Chủ đề (Bắt buộc)***:",
            list(filtered_chu_de_options_map.keys()),
            key="q_add_cd_select_main",
            index=None,
            placeholder="Chọn chủ đề..." if selected_mon_hoc_name else "Vui lòng chọn Môn học trước",
            disabled=(not selected_mon_hoc_name or not filtered_chu_de_options_map)
        )
        selected_chu_de_id = filtered_chu_de_options_map.get(selected_chu_de_name)

        # 3. Lọc Bài học theo Chủ đề
        filtered_lesson_options = {}
        if selected_chu_de_id:
            filtered_lesson_options = {
                details["name"]: bh_id
                for bh_id, details in bai_hoc_details.items()
                if details["chu_de_id"] == selected_chu_de_id
            }

        lesson_options_with_none = {"(Không thuộc bài học cụ thể / Câu hỏi chung)": "NONE_VALUE"}
        filtered_lesson_options_sorted = dict(sorted(filtered_lesson_options.items()))
        lesson_options_with_none.update(filtered_lesson_options_sorted)

        selected_lesson_name = st.selectbox(
            "**3. Chọn Bài học (Tùy chọn)**:",
            list(lesson_options_with_none.keys()),
            key="q_add_bh_select_filtered",
            index=0,
            placeholder="Chọn bài học nếu câu hỏi này dành riêng cho một bài...",
            disabled=(not selected_chu_de_id)
        )
        selected_lesson_id = lesson_options_with_none.get(selected_lesson_name)
        if selected_lesson_id == "NONE_VALUE":
            selected_lesson_id = None

        # 4. Form nhập liệu
        if selected_chu_de_id:
            with st.form("add_question_form", clear_on_submit=True):
                st.markdown("**4. Nhập nội dung câu hỏi**:")
                loai = st.selectbox("Loại câu hỏi * (Cách trả lời):", LOAI_CAU_HOI_OPTIONS, key="q_loai", index=0,
                                    help="Quyết định cách học sinh trả lời.")
                muc_do = st.selectbox("Mức độ * (Độ khó):", MUC_DO_OPTIONS, key="q_muc_do",
                                      help="Phân loại độ khó của câu hỏi.")

                noi_dung = st.text_area("Nội dung *", key="q_noi_dung")
                dap_an_dung_raw = st.text_area("Đáp án đúng *", key="q_dung_raw",
                                               help="1 dòng cho 'Một lựa chọn'. Nhiều dòng nếu có nhiều đáp án đúng.")

                dap_an_khac_raw = ""
                if loai != "dien_khuyet":
                    dap_an_khac_raw = st.text_area("Đáp án sai / Các lựa chọn khác", key="q_khac_raw",
                                                   help="Các lựa chọn sai (mỗi dòng một).")

                diem_so = st.number_input("Điểm", min_value=0, value=1, key="q_diem")
                submitted = st.form_submit_button("➕ Thêm câu hỏi", use_container_width=True)

                if submitted:
                    dap_an_dung = [s.strip() for s in dap_an_dung_raw.split("\n") if s.strip()]
                    dap_an_khac = [s.strip() for s in dap_an_khac_raw.split("\n") if
                                   s.strip()] if loai != "dien_khuyet" else []

                    if not noi_dung:
                        st.error("Nội dung câu hỏi không được trống.")
                    elif (loai == "mot_lua_chon" and len(dap_an_dung) != 1):
                        st.error("Câu 'Một lựa chọn' cần đúng 1 đáp án đúng.")
                    elif (loai != "mot_lua_chon" and len(dap_an_dung) < 1):
                        st.error("Loại câu hỏi này cần ít nhất 1 đáp án đúng.")
                    else:
                        try:
                            insert_payload = {
                                "chu_de_id": selected_chu_de_id,
                                "bai_hoc_id": selected_lesson_id,
                                "loai_cau_hoi": loai,
                                "noi_dung": noi_dung,
                                "dap_an_dung": dap_an_dung,
                                "dap_an_khac": dap_an_khac,
                                "muc_do": muc_do,
                                "diem_so": diem_so
                            }
                            supabase.table(table_name).insert(insert_payload).execute()
                            st.success(f"Đã thêm câu hỏi vào Chủ đề '{selected_chu_de_name}'!")
                            crud_utils.clear_all_cached_data()
                        except Exception as e:
                            st.error(f"Lỗi khi thêm câu hỏi: {e}")
        else:
            st.info("Vui lòng chọn Môn học và Chủ đề để bắt đầu nhập câu hỏi.")

    # --- Tab Danh sách & Sửa/Xóa (ĐÃ SỬA: Thêm bộ lọc Khối/Môn/Chủ đề) ---
    with tab_list:
        df_quiz_original = crud_utils.load_data(table_name)

        # 1. Chuẩn bị DataFrame (Merge với chu_de_df để lấy Khối, Môn, Tên Chủ đề)
        df_quiz_display = df_quiz_original.copy()
        if not chu_de_df.empty:
            df_quiz_display['chu_de_id_str'] = df_quiz_display['chu_de_id'].astype(str)
            chu_de_df['chu_de_id_str'] = chu_de_df['id'].astype(str)

            # Lấy map tên bài học
            bai_hoc_id_map_quiz = {id_: details["name"] for id_, details in bai_hoc_details.items()}
            df_quiz_display['Bài học'] = df_quiz_display['bai_hoc_id'].astype(str).map(bai_hoc_id_map_quiz).fillna(
                "(Chung)")

            # Merge
            df_quiz_display = pd.merge(
                df_quiz_display,
                chu_de_df[['chu_de_id_str', 'ten_chu_de', 'mon_hoc', 'lop']],
                on='chu_de_id_str',
                how='left'
            )
            df_quiz_display = df_quiz_display.rename(columns={
                "lop": "Khối",
                "mon_hoc": "Môn học",
                "ten_chu_de": "Chủ đề"
            })

        df_quiz_display = df_quiz_display.sort_values(by=["Khối", "Môn học", "Chủ đề", "id"]).reset_index(drop=True)

        # 2. Tạo Bộ lọc
        st.markdown("##### 🔍 Lọc danh sách")
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            # Lọc Khối
            khoi_list_raw = df_quiz_display['Khối'].dropna().unique()
            khoi_list = ["Tất cả"] + sorted([int(k) for k in khoi_list_raw])
            selected_khoi = st.selectbox("Lọc theo Khối:", khoi_list, key="q_filter_khoi", index=0)

        df_filtered_by_khoi = df_quiz_display
        if selected_khoi != "Tất cả":
            df_filtered_by_khoi = df_quiz_display[df_quiz_display['Khối'] == selected_khoi]

        with col_f2:
            # Lọc Môn học (dựa trên Khối)
            mon_hoc_list = ["Tất cả"] + sorted(list(df_filtered_by_khoi['Môn học'].dropna().unique()))
            selected_mon_hoc = st.selectbox("Lọc theo Môn học:", mon_hoc_list, key="q_filter_monhoc", index=0)

        with col_f3:
            # Lọc Chủ đề (dựa trên Môn học)
            chu_de_list = ["Tất cả"]
            df_filtered_by_mon = df_filtered_by_khoi
            if selected_mon_hoc != "Tất cả":
                df_filtered_by_mon = df_filtered_by_khoi[df_filtered_by_khoi['Môn học'] == selected_mon_hoc]

            chu_de_list.extend(sorted(list(df_filtered_by_mon['Chủ đề'].dropna().unique())))
            selected_chu_de = st.selectbox("Lọc theo Chủ đề:", chu_de_list, key="q_filter_chude", index=0)

        # 3. Lọc DataFrame
        df_to_show = df_filtered_by_mon.copy()
        if selected_chu_de != "Tất cả":
            df_to_show = df_to_show[df_to_show['Chủ đề'] == selected_chu_de]

        st.markdown("---")

        if not df_to_show.empty:
            try:
                df_to_show['dap_an_dung_display'] = df_to_show['dap_an_dung'].apply(
                    lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
                df_to_show['dap_an_khac_display'] = df_to_show['dap_an_khac'].apply(
                    lambda x: ', '.join(map(str, x)) if isinstance(x, list) and x else '')
            except Exception as e:
                st.warning(f"Lỗi khi định dạng cột đáp án: {e}")
                df_to_show['dap_an_dung_display'] = ''
                df_to_show['dap_an_khac_display'] = ''

            cols_display_q = ['id', 'noi_dung', 'Khối', 'Môn học', 'Chủ đề', 'Bài học', 'loai_cau_hoi', 'muc_do',
                              'diem_so', 'dap_an_dung_display', 'dap_an_khac_display']
            cols_exist = [col for col in cols_display_q if col in df_to_show.columns]

            st.info("Nhấp vào một hàng trong bảng dưới đây để Sửa hoặc Xóa.")
            gb = st.dataframe(
                df_to_show[cols_exist].rename(columns={"loai_cau_hoi": "Loại", "muc_do": "Mức độ", "diem_so": "Điểm",
                                                       "dap_an_dung_display": "Đ.A Đúng",
                                                       "dap_an_khac_display": "Đ.A Khác"}),
                key="quiz_df_select",
                hide_index=True,
                use_container_width=True,
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
                original_item_df = df_quiz_original[df_quiz_original['id'] == selected_id]
                if not original_item_df.empty:
                    selected_item_original = original_item_df.iloc[0].to_dict()

            # 4. Form Sửa/Xóa (Giữ nguyên logic, chỉ cập nhật Mức độ/Loại)
            if selected_item_original:
                with st.expander("📝 Sửa/Xóa Câu hỏi đã chọn", expanded=True):
                    with st.form("edit_question_form"):
                        st.text(f"ID Câu hỏi: {selected_item_original['id']}")

                        chu_de_opts_local = chu_de_options
                        current_cd_id = str(selected_item_original.get("chu_de_id", ""))
                        # Lấy tên hiển thị đầy đủ của chủ đề (ví dụ: "Tên (L1-T1)")
                        current_cd_name = next(
                            (name for name, id_ in chu_de_opts_local.items() if id_ == current_cd_id), None)
                        cd_idx = list(chu_de_opts_local.keys()).index(
                            current_cd_name) if current_cd_name in chu_de_opts_local else 0
                        chu_de_ten_edit = st.selectbox("Chủ đề *", list(chu_de_opts_local.keys()), index=cd_idx,
                                                       key="q_edit_cd")
                        selected_chu_de_id_edit = chu_de_opts_local.get(chu_de_ten_edit)

                        # Lọc Bài học (Giữ nguyên logic)
                        filtered_lesson_options_edit = {}
                        if selected_chu_de_id_edit:
                            filtered_lesson_options_edit = {details["name"]: bh_id for bh_id, details in
                                                            bai_hoc_details.items() if
                                                            details["chu_de_id"] == selected_chu_de_id_edit}
                        lesson_options_with_none_edit = {"(Không thuộc bài học cụ thể / Câu hỏi chung)": "NONE_VALUE"}
                        filtered_lesson_options_sorted_edit = dict(sorted(filtered_lesson_options_edit.items()))
                        lesson_options_with_none_edit.update(filtered_lesson_options_sorted_edit)
                        current_bh_id = str(selected_item_original.get("bai_hoc_id", "")) if pd.notna(
                            selected_item_original.get("bai_hoc_id")) else ""
                        current_bh_name = {id_: details["name"] for id_, details in bai_hoc_details.items()}.get(
                            current_bh_id, "(Không thuộc bài học cụ thể / Câu hỏi chung)")
                        bh_idx = list(lesson_options_with_none_edit.keys()).index(
                            current_bh_name) if current_bh_name in lesson_options_with_none_edit else 0
                        bai_hoc_ten_edit = st.selectbox("Bài học (Tùy chọn)",
                                                        list(lesson_options_with_none_edit.keys()), index=bh_idx,
                                                        key="q_edit_bh")
                        selected_lesson_id_edit = lesson_options_with_none_edit.get(bai_hoc_ten_edit)
                        if selected_lesson_id_edit == "NONE_VALUE": selected_lesson_id_edit = None

                        # Sửa lỗi Loại/Mức độ
                        loai_val = selected_item_original.get("loai_cau_hoi", "mot_lua_chon")
                        loai_idx = LOAI_CAU_HOI_OPTIONS.index(loai_val) if loai_val in LOAI_CAU_HOI_OPTIONS else 0
                        loai_edit = st.selectbox("Loại câu hỏi * (Cách trả lời):", LOAI_CAU_HOI_OPTIONS, index=loai_idx,
                                                 key="q_edit_loai")
                        md_val = selected_item_original.get("muc_do", "biết")
                        md_idx = MUC_DO_OPTIONS.index(md_val) if md_val in MUC_DO_OPTIONS else 0
                        muc_do_edit = st.selectbox("Mức độ * (Độ khó):", MUC_DO_OPTIONS, index=md_idx, key="q_edit_md")

                        noi_dung_edit = st.text_area("Nội dung *", value=selected_item_original.get("noi_dung", ""),
                                                     key="q_edit_nd")
                        dap_an_dung_list = selected_item_original.get("dap_an_dung", [])
                        dap_an_dung_raw_edit = st.text_area("Đáp án đúng *",
                                                            value="\n".join(map(str, dap_an_dung_list)),
                                                            key="q_edit_dung")
                        dap_an_khac_list = selected_item_original.get("dap_an_khac", [])
                        dap_an_khac_raw_edit = st.text_area("Đáp án sai / Lựa chọn khác",
                                                            value="\n".join(map(str, dap_an_khac_list)),
                                                            key="q_edit_khac")
                        diem_so_edit = st.number_input("Điểm", min_value=0,
                                                       value=selected_item_original.get("diem_so", 1),
                                                       key="q_edit_diem")

                        col_update, col_delete, col_clear = st.columns(3)
                        if col_update.form_submit_button("💾 Lưu thay đổi", use_container_width=True):
                            dap_an_dung_new = [s.strip() for s in dap_an_dung_raw_edit.split("\n") if s.strip()]
                            dap_an_khac_new = [s.strip() for s in dap_an_khac_raw_edit.split("\n") if
                                               s.strip()] if loai_edit != "dien_khuyet" else []
                            if not noi_dung_edit:
                                st.error("Nội dung không được trống.")
                            elif (loai_edit == "mot_lua_chon" and len(dap_an_dung_new) != 1):
                                st.error("'Một lựa chọn' cần đúng 1 đáp án đúng.")
                            elif (loai_edit != "mot_lua_chon" and len(dap_an_dung_new) < 1):
                                st.error("Cần ít nhất 1 đáp án đúng.")
                            else:
                                if not selected_chu_de_id_edit:
                                    st.error("Chủ đề đã chọn không hợp lệ.")
                                else:
                                    update_data = {
                                        "chu_de_id": selected_chu_de_id_edit,
                                        "bai_hoc_id": selected_lesson_id_edit,
                                        "loai_cau_hoi": loai_edit,
                                        "noi_dung": noi_dung_edit,
                                        "dap_an_dung": dap_an_dung_new,
                                        "dap_an_khac": dap_an_khac_new,
                                        "muc_do": muc_do_edit,
                                        "diem_so": diem_so_edit
                                    }
                                    try:
                                        supabase.table(table_name).update(update_data).eq("id", selected_item_original[
                                            'id']).execute()
                                        st.success("Cập nhật câu hỏi thành công!")
                                        crud_utils.clear_cache_and_rerun()
                                    except Exception as e:
                                        st.error(f"Lỗi khi cập nhật câu hỏi: {e}")
                        if col_delete.form_submit_button("❌ Xóa câu hỏi này", use_container_width=True):
                            try:
                                supabase.table(table_name).delete().eq("id", selected_item_original['id']).execute()
                                st.warning(f"Đã xóa câu hỏi ID: {selected_item_original['id']}")
                                crud_utils.clear_cache_and_rerun()
                            except Exception as e:
                                st.error(
                                    f"Lỗi khi xóa: {e}. Có thể câu hỏi đang được liên kết trong 'bai_tap_cau_hoi'.")
                        if col_clear.form_submit_button("Hủy chọn", use_container_width=True):
                            if 'quiz_selected_item_id' in st.session_state: del st.session_state[
                                'quiz_selected_item_id']
                            st.rerun()
        else:
            if df_quiz_original.empty:
                st.info("Chưa có câu hỏi nào trong hệ thống.")
            else:
                st.info("Không tìm thấy câu hỏi nào phù hợp với bộ lọc.")

    # --- Tab Import Excel (Giữ nguyên) ---
    with tab_import_q:
        st.markdown("### 📤 Import câu hỏi từ Excel")
        sample_data_q = {
            'chu_de_id': ['UUID CỦA CHỦ ĐỀ'],
            'bai_hoc_id': ['UUID BÀI HỌC (Tùy chọn)'],
            'loai_cau_hoi': ['mot_lua_chon'],
            'noi_dung': ['1+1=?'],
            'dap_an_dung': ['2'],
            'dap_an_khac': ['1;3;4'],
            'muc_do': ['biết'],
            'diem_so': [1]
        }
        crud_utils.create_excel_download(pd.DataFrame(sample_data_q), "mau_import_cau_hoi.xlsx",
                                         sheet_name='DanhSachCauHoi')
        st.caption("Cột 'loai_cau_hoi' phải là 'mot_lua_chon', 'nhieu_lua_chon' hoặc 'dien_khuyet'.")
        st.caption("Cột 'muc_do' phải là 'biết', 'hiểu' hoặc 'vận dụng'.")

        uploaded = st.file_uploader("Chọn file Excel Câu hỏi", type=["xlsx"], key="quiz_upload")
        if uploaded:
            try:
                df_upload = pd.read_excel(uploaded, dtype=str)
                st.dataframe(df_upload.head())
                valid_chu_de_ids = chu_de_id_list
                valid_bai_hoc_ids = list(bai_hoc_details.keys())
                if not valid_chu_de_ids:
                    st.error("Chưa có chủ đề nào trong hệ thống để import câu hỏi.")
                elif st.button("🚀 Import Câu hỏi"):
                    count = 0;
                    errors = []
                    with st.spinner("Đang import câu hỏi..."):
                        for index, row in df_upload.iterrows():
                            try:
                                chu_de_id_str = str(row["chu_de_id"]).strip()
                                if chu_de_id_str not in valid_chu_de_ids: raise ValueError(
                                    f"Chu de ID '{chu_de_id_str}' không tồn tại.")
                                bai_hoc_id_str = str(row.get("bai_hoc_id", "")).strip() if pd.notna(
                                    row.get("bai_hoc_id")) else None
                                if bai_hoc_id_str and bai_hoc_id_str not in valid_bai_hoc_ids: raise ValueError(
                                    f"Bai hoc ID '{bai_hoc_id_str}' không tồn tại.")
                                if bai_hoc_id_str and bai_hoc_details.get(bai_hoc_id_str) and \
                                        bai_hoc_details[bai_hoc_id_str]['chu_de_id'] != chu_de_id_str:
                                    raise ValueError(
                                        f"Bai hoc ID '{bai_hoc_id_str}' không thuộc Chu de ID '{chu_de_id_str}'.")
                                dap_an_dung = [s.strip() for s in str(row.get("dap_an_dung", "")).split(";") if
                                               s.strip()]
                                dap_an_khac = [s.strip() for s in str(row.get("dap_an_khac", "")).split(";") if
                                               s.strip()]
                                loai_cau_hoi = str(row.get("loai_cau_hoi", "mot_lua_chon")).strip().lower()
                                if loai_cau_hoi not in LOAI_CAU_HOI_OPTIONS: raise ValueError(
                                    f"Loại câu hỏi '{loai_cau_hoi}' không hợp lệ.")
                                noi_dung = str(row["noi_dung"]).strip()
                                muc_do = str(row.get("muc_do", "biết")).strip().lower()
                                if muc_do not in MUC_DO_OPTIONS: raise ValueError(f"Mức độ '{muc_do}' không hợp lệ.")
                                diem_so_val = pd.to_numeric(row.get("diem_so", 1), errors='coerce')
                                if pd.isna(diem_so_val) or diem_so_val < 0: raise ValueError("Điểm số không hợp lệ.")
                                diem_so = int(diem_so_val)
                                if not noi_dung: raise ValueError("Nội dung trống.")
                                if (loai_cau_hoi == "mot_lua_chon" and len(dap_an_dung) != 1): raise ValueError(
                                    "'Một lựa chọn' cần đúng 1 đáp án.")
                                if (loai_cau_hoi != "mot_lua_chon" and len(dap_an_dung) < 1): raise ValueError(
                                    "Cần ít nhất 1 đáp án đúng.")
                                if loai_cau_hoi == "dien_khuyet": dap_an_khac = []
                                supabase.table(table_name).insert({
                                    "chu_de_id": chu_de_id_str, "bai_hoc_id": bai_hoc_id_str,
                                    "loai_cau_hoi": loai_cau_hoi,
                                    "noi_dung": noi_dung, "dap_an_dung": dap_an_dung, "dap_an_khac": dap_an_khac,
                                    "muc_do": muc_do, "diem_so": diem_so
                                }).execute()
                                count += 1
                            except Exception as e:
                                errors.append(f"Dòng {index + 2}: {e}")
                    st.success(f"✅ Import thành công {count} câu hỏi.");
                    crud_utils.clear_all_cached_data()
                    if errors: st.error("Các dòng sau bị lỗi:"); st.code("\n".join(errors))
            except Exception as e:
                st.error(f"Lỗi đọc file câu hỏi: {e}")