# File: pages/teacher_pages/render_tab_practice.py
# (BẢN FINAL FIX: Xử lý lỗi Slider crash khi max_value = 0)

import streamlit as st
import time
from backend.supabase_client import supabase
from backend.class_test_service import generate_practice_exercise
from backend.data_service import get_lessons_by_topic, get_question_counts


@st.cache_data(ttl=60)
def get_topics_for_practice(mon_hoc_name, lop_khoi):
    """Cache danh sách chủ đề để load nhanh."""
    try:
        chu_de_res = supabase.table("chu_de").select("id, ten_chu_de, tuan") \
                         .eq("lop", lop_khoi).eq("mon_hoc", mon_hoc_name).order("tuan").execute().data or []
        return {f"Tuần {c['tuan']}: {c['ten_chu_de']}": str(c["id"]) for c in chu_de_res}
    except:
        return {}


def render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES):
    st.subheader("✏️ Giao bài Luyện tập (Theo Bài học)")

    if not teacher_class_options:
        st.warning("⚠️ Bạn cần được phân công lớp để sử dụng tính năng này.")
        return

    # =========================================================================
    # PHẦN 1: BỘ LỌC 4 CẤP (LAYOUT 4 CỘT)
    # =========================================================================
    with st.container(border=True):
        st.markdown("##### 1. Chọn nội dung luyện tập")
        c1, c2, c3, c4 = st.columns(4)

        # 1. Chọn Lớp
        with c1:
            lop_ten_lt = st.selectbox("Lớp:", list(teacher_class_options.keys()), key="lop_lt_select")
            selected_lop_id_lt = teacher_class_options[lop_ten_lt]
            selected_class_info_lt = next((c for c in all_classes if str(c["id"]) == selected_lop_id_lt), None)
            khoi_lt = selected_class_info_lt["khoi"] if selected_class_info_lt else None

        # Lấy môn học
        assigned_mon_hocs = supabase.table("phan_cong_giang_day").select("mon_hoc(id, ten_mon)") \
                                .eq("giao_vien_id", giao_vien_id).eq("lop_id", selected_lop_id_lt).execute().data or []
        mon_hoc_options_lt = {item['mon_hoc']['ten_mon']: item['mon_hoc']['id'] for item in assigned_mon_hocs if
                              item.get('mon_hoc')}

        if not mon_hoc_options_lt:
            st.error("Chưa có phân công môn học.")
            return

        # 2. Chọn Môn
        with c2:
            mon_hoc_ten_lt = st.selectbox("Môn học:", list(mon_hoc_options_lt.keys()), key="mon_lt_select")

        # 3. Chọn Chủ đề
        chu_de_map_lt = get_topics_for_practice(mon_hoc_ten_lt, khoi_lt)
        with c3:
            if chu_de_map_lt:
                selected_chu_de_ten_lt = st.selectbox("Chủ đề:", list(chu_de_map_lt.keys()), key="cd_lt_select")
                chu_de_id_lt = chu_de_map_lt[selected_chu_de_ten_lt]
            else:
                st.warning("Không có chủ đề.")
                chu_de_id_lt = None

        # 4. Chọn Bài học (Khác biệt so với Exam)
        bai_hoc_id_lt = None
        with c4:
            if chu_de_id_lt:
                lessons = get_lessons_by_topic(chu_de_id_lt)
                if lessons:
                    lesson_map_lt = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
                    selected_lesson_name_lt = st.selectbox("Bài học:", list(lesson_map_lt.keys()), key="bh_lt_select")
                    bai_hoc_id_lt = lesson_map_lt[selected_lesson_name_lt]
                else:
                    st.warning("Chủ đề trống.")
            else:
                st.empty()

    if not bai_hoc_id_lt: return

    # =========================================================================
    # PHẦN 2: CẤU HÌNH BÀI TẬP (LIVE UPDATE LOGIC)
    # =========================================================================

    # Lấy thống kê câu hỏi (Theo Bài học)
    counts_lt = get_question_counts(bai_hoc_id=bai_hoc_id_lt)
    total_bank = sum(counts_lt.values())

    if total_bank == 0:
        st.error(f"❌ Ngân hàng câu hỏi cho bài học '{selected_lesson_name_lt}' đang trống.")
        return

    st.markdown("##### 2. Cấu hình bài tập")

    # Tên bài luyện tập
    default_name = f"Luyện tập: {selected_lesson_name_lt.split('. ', 1)[-1]}"
    ten_bai_lt = st.text_input("Tên bài tập:", value=default_name, key="name_lt_input")

    st.markdown("---")

    # --- LAYOUT TƯƠNG TÁC ---
    c_total, c_matrix = st.columns([1, 2])

    with c_total:
        st.markdown("###### Tổng số câu")
        # Widget nhập tổng số câu
        tong_cau_yeu_cau_lt = st.number_input(
            "Nhập tổng số câu:",
            min_value=1,
            max_value=total_bank,
            value=min(10, total_bank),  # Mặc định 5 câu cho luyện tập
            label_visibility="collapsed",
            key="total_lt_input"
        )
        st.caption(f"Tối đa: {total_bank} câu trong kho.")

        # Card thống kê kho
        with st.container(border=True):
            st.markdown("**Kho câu hỏi (Bài này):**")
            st.markdown(f"🧠 Biết: `{counts_lt['biết']}`")
            st.markdown(f"🤔 Hiểu: `{counts_lt['hiểu']}`")
            st.markdown(f"🚀 Vận dụng: `{counts_lt['vận dụng']}`")

    with c_matrix:
        st.markdown("###### Phân bổ mức độ (Kéo để chia)")

        # 1. SLIDER BIẾT
        max_slider_biet = min(counts_lt['biết'], tong_cau_yeu_cau_lt)

        # --- FIX LỖI 1: Nếu max=0, không hiện slider ---
        if max_slider_biet > 0:
            so_cau_biet = st.slider(
                f"🧠 Số câu Biết (Max: {max_slider_biet})",
                min_value=0,
                max_value=max_slider_biet,
                value=int(max_slider_biet * 0.5),
                key="slider_biet_lt"
            )
        else:
            so_cau_biet = 0
            st.text_input("🧠 Số câu Biết", value=0, disabled=True, key="disp_biet_0")

        # 2. SLIDER HIỂU
        remaining_after_biet = tong_cau_yeu_cau_lt - so_cau_biet
        max_slider_hieu = min(counts_lt['hiểu'], remaining_after_biet)

        # --- FIX LỖI 2: Xử lý khi max_slider_hieu = 0 (tránh lỗi StreamlitAPIException) ---
        if max_slider_hieu > 0:
            so_cau_hieu = st.slider(
                f"🤔 Số câu Hiểu (Max: {max_slider_hieu})",
                min_value=0,
                max_value=max_slider_hieu,
                value=min(int(remaining_after_biet * 0.8), max_slider_hieu),
                key="slider_hieu_lt"
            )
        else:
            so_cau_hieu = 0
            st.text_input("🤔 Số câu Hiểu", value=0, disabled=True, key="disp_hieu_0")

        # 3. TỰ ĐỘNG TÍNH VẬN DỤNG
        so_cau_van_dung = tong_cau_yeu_cau_lt - so_cau_biet - so_cau_hieu

        # Kiểm tra hợp lệ
        is_valid_config = True

        if so_cau_van_dung > counts_lt['vận dụng']:
            st.error(f"❌ Cần **{so_cau_van_dung}** câu Vận dụng, nhưng kho chỉ có **{counts_lt['vận dụng']}** câu.")
            is_valid_config = False
        else:
            # Hiển thị kết quả
            if so_cau_van_dung > 0:
                st.success(f"🚀 Số câu Vận dụng (Tự động): **{so_cau_van_dung}**")
            else:
                st.info(f"🚀 Số câu Vận dụng: **0**")

    st.markdown("---")

    # NÚT SUBMIT
    if st.button("🚀 Sinh & Giao bài Luyện tập ngay", type="primary", use_container_width=True,
                 disabled=not is_valid_config):
        if not ten_bai_lt:
            st.error("Vui lòng nhập tên bài tập.")
        else:
            with st.spinner("Đang tạo bài luyện tập..."):
                result_lt = generate_practice_exercise(
                    bai_hoc_id=bai_hoc_id_lt,
                    giao_vien_id=giao_vien_id,
                    ten_bai=ten_bai_lt,
                    so_cau_biet=so_cau_biet,
                    so_cau_hieu=so_cau_hieu,
                    so_cau_van_dung=so_cau_van_dung,
                    lop_id=selected_lop_id_lt
                )

            if result_lt:
                st.toast(f"✅ Đã giao bài '{ten_bai_lt}' thành công!", icon="🎉")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Lỗi khi tạo bài tập. Vui lòng thử lại.")