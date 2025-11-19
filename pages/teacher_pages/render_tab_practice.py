# File: pages/teacher_pages/render_tab_practice.py
import streamlit as st
from backend.supabase_client import supabase
from backend.class_test_service import generate_practice_exercise
from backend.data_service import get_lessons_by_topic, get_question_counts


@st.cache_data(ttl=60)
def get_topics_for_test(mon_hoc_name, lop_khoi):
    # Lấy chủ đề theo môn học và khối
    chu_de_res = supabase.table("chu_de").select("id, ten_chu_de, tuan").eq("lop", lop_khoi).eq("mon_hoc",
                                                                                                mon_hoc_name).order(
        "tuan").execute().data or []
    return {f"Tuần {c['tuan']}: {c['ten_chu_de']}": str(c["id"]) for c in chu_de_res}


def render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES):
    st.subheader("✏️ Giao bài Luyện tập Bài học cho lớp")

    if not teacher_class_options:
        st.warning("Bạn cần được phân công lớp để giao bài luyện tập.")
        return

    # 1. CHỌN LỚP
    lop_ten_lt = st.selectbox("1. Chọn lớp (LT)", list(teacher_class_options.keys()), key="lop_lt_select")
    selected_lop_id_lt = teacher_class_options[lop_ten_lt]
    selected_class_info_lt = next((c for c in all_classes if str(c["id"]) == selected_lop_id_lt), None)
    khoi_lt = selected_class_info_lt["khoi"] if selected_class_info_lt else None

    # Lấy thông tin môn học đã phân công cho lớp
    assigned_mon_hocs_lt = supabase.table("phan_cong_giang_day").select("mon_hoc(id, ten_mon)").eq("giao_vien_id",
                                                                                                   giao_vien_id).eq(
        "lop_id", selected_lop_id_lt).execute().data or []
    mon_hoc_options_lt = {item['mon_hoc']['ten_mon']: item['mon_hoc']['id'] for item in assigned_mon_hocs_lt if
                          item.get('mon_hoc')}

    chu_de_id_lt = None
    bai_hoc_id_lt = None

    if not mon_hoc_options_lt:
        st.error(f"Bạn chưa được phân công môn học nào cho lớp {lop_ten_lt}. Vui lòng kiểm tra lại Phân công.")
        return

        # 2. CHỌN MÔN HỌC
    mon_hoc_ten_lt = st.selectbox("2. Chọn Môn học (LT)", list(mon_hoc_options_lt.keys()), key="mon_lt_select")

    # 3. CHỌN CHỦ ĐỀ (Lọc theo Khối VÀ Môn học)
    chu_de_map_lt = get_topics_for_test(mon_hoc_ten_lt, khoi_lt)

    if chu_de_map_lt:
        selected_chu_de_ten_lt = st.selectbox("3. Chọn Chủ đề (LT)", list(chu_de_map_lt.keys()), key="cd_lt_select")
        chu_de_id_lt = chu_de_map_lt[selected_chu_de_ten_lt]

        # 4. CHỌN BÀI HỌC (Lọc theo Chủ đề)
        if chu_de_id_lt:
            lessons = get_lessons_by_topic(chu_de_id_lt)
            if lessons:
                lesson_map_lt = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
                selected_lesson_name_lt = st.selectbox("4. Chọn Bài học (LT)", list(lesson_map_lt.keys()),
                                                       key="bh_lt_select")
                bai_hoc_id_lt = lesson_map_lt[selected_lesson_name_lt]
            else:
                st.warning(f"Chủ đề '{selected_chu_de_ten_lt}' chưa có bài học nào.")
        else:
            st.error("Không tìm thấy chủ đề nào có sẵn.")
    else:
        st.error(f"Không tìm thấy chủ đề nào cho Khối {khoi_lt} - Môn {mon_hoc_ten_lt}.")

    if bai_hoc_id_lt:
        ten_bai_lt = st.text_input("Tên bài luyện tập", key="ten_lt")

        counts_lt = get_question_counts(bai_hoc_id=bai_hoc_id_lt)
        tong_cau_co_san_lt = sum(counts_lt.values())

        if tong_cau_co_san_lt == 0:
            st.error(
                f"Ngân hàng câu hỏi cho bài học '{selected_lesson_name_lt}' hiện đang trống. Vui lòng thêm câu hỏi trước khi giao bài.")
        else:
            tong_cau_yeu_cau_lt = st.number_input(
                "Bạn muốn chọn bao nhiêu câu:",
                min_value=1,
                max_value=tong_cau_co_san_lt,
                value=min(5, tong_cau_co_san_lt),
                step=1,
                key="tong_cau_lt"
            )

            col_bank_lt, col_select_lt = st.columns(2)

            with col_bank_lt:
                st.markdown("**Ngân hàng câu hỏi (Bài học):**")
                st.info(f"🧠 **Biết:** `{counts_lt['biết']}` câu")
                st.info(f"🤔 **Hiểu:** `{counts_lt['hiểu']}` câu")
                st.info(f"🚀 **Vận dụng:** `{counts_lt['vận dụng']}` câu")

            # ---- BỐ CỤC 2 CỘT CON (THEO YÊU CẦU MỚI) ----
            with col_select_lt:
                st.markdown("**Phân bổ số lượng:**")

                col_labels_lt, col_inputs_lt = st.columns([2, 1])  # Cột label rộng hơn

                with col_labels_lt:
                    st.markdown("🧠 **Số câu Biết:**")
                    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)  # Đệm
                    st.markdown("🤔 **Số câu Hiểu:**")
                    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)  # Đệm
                    st.markdown("🚀 **Số câu Vận dụng:**")

                with col_inputs_lt:
                    so_cau_biet_lt = st.number_input(
                        "Số câu Biết", label_visibility="collapsed",
                        min_value=0, max_value=min(counts_lt['biết'], tong_cau_yeu_cau_lt),
                        value=0, step=1, key="scb_lt"
                    )
                    remaining_after_biet_lt = tong_cau_yeu_cau_lt - so_cau_biet_lt
                    so_cau_hieu_lt = st.number_input(
                        "Số câu Hiểu", label_visibility="collapsed",
                        min_value=0, max_value=min(counts_lt['hiểu'], remaining_after_biet_lt),
                        value=0, step=1, key="sch_lt"
                    )
                    so_cau_van_dung_lt = tong_cau_yeu_cau_lt - so_cau_biet_lt - so_cau_hieu_lt
                    st.number_input(
                        "Số câu Vận dụng",
                        value=so_cau_van_dung_lt,
                        disabled=True,
                        key="scvd_lt_display",
                        label_visibility="collapsed"
                    )
            # ---- KẾT THÚC BỐ CỤC 2 CỘT CON ----

            disable_button_lt = False
            if so_cau_van_dung_lt < 0:
                st.error(
                    f"Tổng số câu 'Biết' ({so_cau_biet_lt}) và 'Hiểu' ({so_cau_hieu_lt}) đã vượt quá tổng số bạn yêu cầu ({tong_cau_yeu_cau_lt}).")
                disable_button_lt = True
            elif so_cau_van_dung_lt > counts_lt['vận dụng']:
                st.error(
                    f"Số câu 'Vận dụng' (tự tính: {so_cau_van_dung_lt}) vượt quá số câu có sẵn trong ngân hàng ({counts_lt['vận dụng']}). Vui lòng giảm số câu 'Biết' hoặc 'Hiểu'.")
                disable_button_lt = True

            st.markdown(f"#### **Tổng số câu đã chọn: `{tong_cau_yeu_cau_lt}`**")

            if st.button("🚀 Sinh & Giao bài Luyện tập BH", key="btn_giao_lt", use_container_width=True,
                         disabled=disable_button_lt):
                if not ten_bai_lt:
                    st.error("Vui lòng nhập tên bài luyện tập.")
                elif tong_cau_yeu_cau_lt <= 0:
                    st.error("Tổng số câu phải lớn hơn 0.")
                else:
                    result_lt = generate_practice_exercise(
                        bai_hoc_id=bai_hoc_id_lt, giao_vien_id=giao_vien_id, ten_bai=ten_bai_lt,
                        so_cau_biet=so_cau_biet_lt, so_cau_hieu=so_cau_hieu_lt,
                        so_cau_van_dung=so_cau_van_dung_lt
                    )
                    if result_lt:
                        st.success(
                            f"✅ Đã giao bài LT '{ten_bai_lt}' ({tong_cau_yeu_cau_lt} câu) cho bài học '{selected_lesson_name_lt}'")
                        st.cache_data.clear()
                        st.session_state["teacher_active_tab_index"] = 2
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Không thể tạo bài LT. Lỗi máy chủ (vui lòng kiểm tra log, có thể do không đủ câu hỏi).")