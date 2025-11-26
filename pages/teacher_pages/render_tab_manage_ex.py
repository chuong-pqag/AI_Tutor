# File: pages/teacher_pages/render_tab_manage_ex.py
# (BẢN FINAL: Fix lỗi bộ lọc hiển thị N/A + Tối ưu UI)

import streamlit as st
import pandas as pd
from backend.supabase_client import supabase
from backend.data_service import (
    get_teacher_exercises,
    can_delete_exercise,
    update_exercise_title,
    delete_exercise_and_links
)


def render(giao_vien_id, teacher_classes):
    st.subheader("🗂️ Bài tập đã giao (Kiểm tra & Luyện tập)")

    # 1. TẢI DỮ LIỆU
    all_exercises = get_teacher_exercises(giao_vien_id)

    if not all_exercises:
        st.info("Bạn chưa giao bài tập nào trong hệ thống.")
        return

    # 2. CHUẨN BỊ DATAFRAME
    df_original = pd.DataFrame(all_exercises)
    df_original['Ngày tạo'] = pd.to_datetime(df_original['created_at']).dt.strftime('%Y-%m-%d %H:%M')

    # Tạo map ID lớp -> Tên lớp
    lop_id_to_ten_map = {str(c['id']): c['ten_lop'] for c in teacher_classes}
    lop_khoi_to_ten_map = {c['khoi']: c['ten_lop'] for c in teacher_classes}

    # Hàm helper để lấy tên lớp an toàn
    def get_ten_lop_from_exercise(row):
        # Ưu tiên 1: Lấy từ lop_id trực tiếp (nếu có)
        lop_id_from_ex = row.get('lop_id')
        if lop_id_from_ex and str(lop_id_from_ex) in lop_id_to_ten_map:
            return lop_id_to_ten_map[str(lop_id_from_ex)]

        # Ưu tiên 2: Suy luận từ Khối của Chủ đề (Logic cũ - fallback)
        chu_de = row.get('chu_de')
        if isinstance(chu_de, dict) and chu_de.get('lop'):
            lop_khoi = chu_de.get('lop')
            if lop_khoi in lop_khoi_to_ten_map:
                return lop_khoi_to_ten_map[lop_khoi]

        return "N/A"

    # Áp dụng mapping
    df_original['lop_ten'] = df_original.apply(get_ten_lop_from_exercise, axis=1)

    df_original['Môn học'] = df_original['chu_de'].apply(
        lambda x: x.get('mon_hoc', 'N/A') if isinstance(x, dict) and x else 'N/A')

    df_original['Chủ đề tên'] = df_original['chu_de'].apply(
        lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) and x else 'N/A')

    df_original['Bài học tên'] = df_original['bai_hoc'].apply(
        lambda x: x.get('ten_bai_hoc', 'N/A') if isinstance(x, dict) and x else 'N/A')

    df_original['Loại'] = df_original['loai_bai_tap'].apply(
        lambda x: 'Luyện tập' if x == 'luyen_tap' else 'KT Chủ đề'
    )

    # 3. BỘ LỌC ĐA CẤP
    st.markdown("##### 🔍 Lọc bài tập")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # --- Lọc Lớp (ĐÃ SỬA LỖI N/A) ---
    with col_f1:
        # Lấy danh sách unique, loại bỏ None/NaN
        unique_lops = df_original['lop_ten'].dropna().unique()
        # Loại bỏ chuỗi "N/A" khỏi danh sách chọn
        clean_lop_list = [x for x in unique_lops if x != "N/A"]

        lop_list = ["Tất cả"] + sorted(clean_lop_list)
        selected_lop = st.selectbox("1. Lớp:", lop_list, key="manage_filter_lop")

    df_filtered = df_original.copy()
    if selected_lop != "Tất cả":
        df_filtered = df_filtered[df_filtered['lop_ten'] == selected_lop]

    # --- Lọc Môn học ---
    with col_f2:
        mon_hoc_list = ["Tất cả"] + sorted(df_filtered['Môn học'].dropna().unique())
        selected_mon = st.selectbox("2. Môn học:", mon_hoc_list, key="manage_filter_mon")

    if selected_mon != "Tất cả":
        df_filtered = df_filtered[df_filtered['Môn học'] == selected_mon]

    # --- Lọc Chủ đề ---
    with col_f3:
        chu_de_list = ["Tất cả"] + sorted(df_filtered['Chủ đề tên'].dropna().unique())
        selected_chu_de = st.selectbox("3. Chủ đề:", chu_de_list, key="manage_filter_cd")

    if selected_chu_de != "Tất cả":
        df_filtered = df_filtered[df_filtered['Chủ đề tên'] == selected_chu_de]

    # --- Lọc Bài học (Chỉ hiện bài học có trong danh sách đã lọc) ---
    with col_f4:
        bh_list_raw = df_filtered[df_filtered['Loại'] == 'Luyện tập']['Bài học tên'].dropna().unique()
        bh_list = ["Tất cả"] + sorted([b for b in bh_list_raw if b != 'N/A'])
        selected_bh = st.selectbox("4. Bài học:", bh_list, key="manage_filter_bh")

    if selected_bh != "Tất cả":
        df_filtered = df_filtered[df_filtered['Bài học tên'] == selected_bh]

    st.markdown("---")
    st.info(f"Đã tìm thấy **{len(df_filtered)}** bài tập phù hợp với bộ lọc.")

    # 4. HIỂN THỊ DANH SÁCH
    # Đổi tên cột cho đẹp
    rename_map = {
        'id': 'ID',
        'tieu_de': 'Tiêu đề',
        'lop_ten': 'Lớp',
        'Chủ đề tên': 'Chủ đề',
        'Bài học tên': 'Bài học',
    }
    # Chỉ rename những cột có trong dataframe (phòng hờ lỗi)
    rename_map = {k: v for k, v in rename_map.items() if k in df_filtered.columns}

    df_display = df_filtered.rename(columns=rename_map)

    # Chọn cột hiển thị
    cols_to_show = [col for col in ['ID', 'Tiêu đề', 'Loại', 'Lớp', 'Môn học', 'Chủ đề', 'Bài học', 'Ngày tạo']
                    if col in df_display.columns]

    df_display = df_display[cols_to_show]

    gb = st.dataframe(
        df_display,
        key="teacher_ex_df_select",
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    selected_rows = gb.selection.rows

    # 5. XỬ LÝ SỬA / XÓA
    if selected_rows:
        selected_id = df_display.iloc[selected_rows[0]]['ID']
        # Lấy dữ liệu gốc của dòng được chọn
        selected_ex = df_original[df_original['id'] == selected_id].iloc[0].to_dict()

        with st.expander(f"📝 Quản lý Bài tập: {selected_ex['tieu_de']}", expanded=True):

            st.markdown(f"**ID:** `{selected_id}` | **Loại:** `{selected_ex['loai_bai_tap']}`")
            st.markdown(f"**Mô tả:** {selected_ex['mo_ta']}")

            # Lấy danh sách câu hỏi để hiển thị preview
            try:
                questions = supabase.table("bai_tap_cau_hoi") \
                    .select("cau_hoi_id, cau_hoi(noi_dung, muc_do)") \
                    .eq("bai_tap_id", selected_id) \
                    .execute().data
            except Exception as e:
                st.error(f"Lỗi cập nhật: {e}")
                questions = []

            # 5.1 FORM SỬA TIÊU ĐỀ
            with st.form(f"edit_ex_form_{selected_id}"):
                new_title = st.text_input("Sửa Tiêu đề Bài tập/Kiểm tra", value=selected_ex['tieu_de'])

                if st.form_submit_button("💾 Lưu tiêu đề mới", use_container_width=True):
                    if new_title and new_title != selected_ex['tieu_de']:
                        try:
                            update_exercise_title(selected_id, new_title)
                            st.success("Cập nhật tiêu đề thành công!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi cập nhật: {e}")
                    else:
                        st.warning("Tiêu đề không thay đổi.")

            # 5.2 NÚT XÓA & XEM (Layout 2 cột)
            col_delete_btn, col_view = st.columns([1, 1])

            is_safe_to_delete = can_delete_exercise(selected_id)

            with col_delete_btn:
                if st.button("❌ Xóa Bài tập này", key=f"delete_ex_{selected_id}", use_container_width=True,
                             disabled=not is_safe_to_delete):
                    try:
                        delete_exercise_and_links(selected_id)
                        st.success(f"Đã xóa bài tập ID: {selected_id}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi xóa bài tập: {e}")

                if not is_safe_to_delete:
                    st.caption("⚠️ *Không thể xóa vì đã có học sinh làm bài.*")

            with col_view:
                with st.popover("👁️ Xem Nội dung câu hỏi", use_container_width=True):
                    st.markdown(f"##### {selected_ex['tieu_de']} ({len(questions)} câu)")
                    if questions:
                        for i, q_link in enumerate(questions):
                            q = q_link.get('cau_hoi')
                            if q:
                                st.markdown(f"**Câu {i + 1}** ({q.get('muc_do', 'N/A')})")
                                st.caption(q.get('noi_dung', 'Không có nội dung'))
                    else:
                        st.info("Bài tập này chưa có câu hỏi nào.")