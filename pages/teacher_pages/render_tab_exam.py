# File: pages/teacher_pages/render_tab_exam.py
# (ĐÃ SỬA LỖI TÍNH TOÁN SỐ CÂU VẬN DỤNG)
import streamlit as st
from backend.supabase_client import supabase
from backend.class_test_service import generate_class_test
from backend.data_service import get_question_counts


@st.cache_data(ttl=60)
def get_topics_for_test(mon_hoc_name, lop_khoi):
    # Lấy chủ đề theo môn học và khối
    chu_de_res = supabase.table("chu_de").select("id, ten_chu_de, tuan").eq("lop", lop_khoi).eq("mon_hoc",
                                                                                                mon_hoc_name).order(
        "tuan").execute().data or []
    return {f"Tuần {c['tuan']}: {c['ten_chu_de']}": str(c["id"]) for c in chu_de_res}


def render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES):
    st.subheader("🏁 Giao bài Kiểm tra Chủ đề cho lớp")

    if not teacher_class_options:
        st.warning("Bạn cần được phân công lớp để giao bài kiểm tra.")
    else:
        # 1. CHỌN LỚP
        lop_ten_kt = st.selectbox("1. Chọn lớp (KT)", list(teacher_class_options.keys()), key="lop_kt_select")
        selected_lop_id_kt = teacher_class_options[lop_ten_kt]
        selected_class_info_kt = next((c for c in all_classes if str(c["id"]) == selected_lop_id_kt), None)
        khoi_kt = selected_class_info_kt["khoi"] if selected_class_info_kt else None

        # Lấy thông tin môn học đã phân công cho lớp
        assigned_mon_hocs = supabase.table("phan_cong_giang_day").select("mon_hoc(id, ten_mon)").eq("giao_vien_id",
                                                                                                    giao_vien_id).eq(
            "lop_id", selected_lop_id_kt).execute().data or []
        mon_hoc_options_kt = {item['mon_hoc']['ten_mon']: item['mon_hoc']['id'] for item in assigned_mon_hocs if
                              item.get('mon_hoc')}

        chu_de_id_kt = None

        if not mon_hoc_options_kt:
            st.error(f"Bạn chưa được phân công môn học nào cho lớp {lop_ten_kt}. Vui lòng kiểm tra lại Phân công.")
            return  # Dừng

        # 2. CHỌN MÔN HỌC
        mon_hoc_ten_kt = st.selectbox("2. Chọn Môn học (KT)", list(mon_hoc_options_kt.keys()), key="mon_kt_select")

        # 3. CHỌN CHỦ ĐỀ (Lọc theo Khối VÀ Môn học)
        chu_de_map_kt = get_topics_for_test(mon_hoc_ten_kt, khoi_kt)

        if chu_de_map_kt:
            selected_chu_de_ten_kt = st.selectbox("3. Chọn Chủ đề (KT)", list(chu_de_map_kt.keys()), key="cd_kt_select")
            chu_de_id_kt = chu_de_map_kt[selected_chu_de_ten_kt]
        else:
            st.error(f"Không tìm thấy chủ đề nào cho Khối {khoi_kt} - Môn {mon_hoc_ten_kt}.")

        if chu_de_id_kt:
            ten_bai_kt = st.text_input("Tên bài kiểm tra", key="ten_kt")

            counts_kt = get_question_counts(chu_de_id=chu_de_id_kt)
            tong_cau_co_san_kt = sum(counts_kt.values())

            if tong_cau_co_san_kt == 0:
                st.error(
                    f"Ngân hàng câu hỏi cho chủ đề '{selected_chu_de_ten_kt}' hiện đang trống. Vui lòng thêm câu hỏi trước khi giao bài.")
            else:
                tong_cau_yeu_cau_kt = st.number_input(
                    "Bạn muốn chọn bao nhiêu câu:",
                    min_value=1,
                    max_value=tong_cau_co_san_kt,
                    value=min(10, tong_cau_co_san_kt),
                    step=1,
                    key="tong_cau_kt"
                )

                col_bank_kt, col_select_kt = st.columns(2)

                with col_bank_kt:
                    st.markdown("**Ngân hàng đề có:**")
                    st.info(f"🧠 **Biết:** `{counts_kt['biết']}` câu")
                    st.info(f"🤔 **Hiểu:** `{counts_kt['hiểu']}` câu")
                    st.info(f"🚀 **Vận dụng:** `{counts_kt['vận dụng']}` câu")

                # ---- BỐ CỤC 2 CỘT CON (LOGIC TÍNH TOÁN ĐÃ SỬA) ----
                with col_select_kt:
                    st.markdown("**Phân bổ số lượng:**")

                    col_labels_kt, col_inputs_kt = st.columns([2, 1])

                    with col_labels_kt:
                        st.markdown("🧠 **Số câu Biết:**")
                        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)  # Spacer
                        st.markdown("🤔 **Số câu Hiểu:**")
                        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)  # Spacer
                        st.markdown("🚀 **Số câu Vận dụng:**")

                    with col_inputs_kt:
                        # 1. Nhập số câu Biết
                        # Max cho phép là số câu có trong kho hoặc tổng số câu yêu cầu
                        max_biet = min(counts_kt['biết'], tong_cau_yeu_cau_kt)
                        so_cau_biet_kt = st.number_input(
                            "Số câu Biết", label_visibility="collapsed",
                            min_value=0, max_value=max_biet,
                            value=0, step=1, key="scb_kt"
                        )

                        # 2. Nhập số câu Hiểu
                        # Số câu còn lại sau khi trừ câu Biết
                        remaining_after_biet = tong_cau_yeu_cau_kt - so_cau_biet_kt
                        # Max cho phép là số câu có trong kho hoặc số câu còn lại
                        max_hieu = min(counts_kt['hiểu'], remaining_after_biet)

                        so_cau_hieu_kt = st.number_input(
                            "Số câu Hiểu", label_visibility="collapsed",
                            min_value=0, max_value=max_hieu,
                            value=0, step=1, key="sch_kt"
                        )

                        # 3. Tự động tính Vận dụng (QUAN TRỌNG: Tính toán trực tiếp)
                        so_cau_van_dung_kt = tong_cau_yeu_cau_kt - so_cau_biet_kt - so_cau_hieu_kt

                        # Hiển thị kết quả tính toán bằng text_input bị disabled
                        # Dùng value=str(...) để ép hiển thị giá trị mới nhất
                        st.text_input(
                            "Số câu Vận dụng",
                            value=str(so_cau_van_dung_kt),
                            disabled=True,
                            label_visibility="collapsed",
                            key="scvd_kt_display_calc"
                        )

                # ---- KIỂM TRA LOGIC CUỐI CÙNG ----
                disable_button_kt = False

                # Kiểm tra xem số câu Vận dụng tính ra có vượt quá số lượng trong kho không
                if so_cau_van_dung_kt > counts_kt['vận dụng']:
                    st.error(
                        f"Cần **{so_cau_van_dung_kt}** câu Vận dụng, nhưng ngân hàng chỉ có **{counts_kt['vận dụng']}**. Vui lòng giảm số câu Biết hoặc Hiểu.")
                    disable_button_kt = True

                # Kiểm tra tổng thực tế (để chắc chắn)
                tong_thuc_te = so_cau_biet_kt + so_cau_hieu_kt + so_cau_van_dung_kt

                st.markdown(f"#### **Tổng số câu đã chọn: `{tong_thuc_te}`**")

                if st.button("🚀 Sinh & Giao bài Kiểm tra CĐ", key="btn_giao_kt", width='stretch',
                             disabled=disable_button_kt):
                    if not ten_bai_kt:
                        st.error("Vui lòng nhập tên bài kiểm tra.")
                    else:
                        result_kt = generate_class_test(
                            lop_id=selected_lop_id_kt, giao_vien_id=giao_vien_id, ten_bai=ten_bai_kt,
                            chu_de_id=chu_de_id_kt,
                            so_cau_biet=so_cau_biet_kt, so_cau_hieu=so_cau_hieu_kt,
                            so_cau_van_dung=so_cau_van_dung_kt
                        )
                        if result_kt:
                            st.success(
                                f"✅ Đã giao bài KT '{ten_bai_kt}' ({tong_thuc_te} câu) cho lớp {lop_ten_kt}")
                            st.cache_data.clear()
                            st.session_state["teacher_active_tab_index"] = 2
                            st.rerun()
                        else:
                            st.error(
                                f"❌ Không thể tạo bài KT. Lỗi máy chủ (vui lòng kiểm tra log, có thể do không đủ câu hỏi).")