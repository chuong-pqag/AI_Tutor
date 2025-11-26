# File: pages/teacher_pages/render_tab_exam.py
# (BẢN FINAL: Live Update Logic - Kéo slider nhảy số ngay lập tức)

import streamlit as st
import time
from backend.supabase_client import supabase
from backend.class_test_service import generate_class_test
from backend.data_service import get_question_counts


@st.cache_data(ttl=60)
def get_topics_for_test(mon_hoc_name, lop_khoi):
    """Lấy danh sách chủ đề để cache."""
    try:
        chu_de_res = supabase.table("chu_de").select("id, ten_chu_de, tuan") \
                         .eq("lop", lop_khoi).eq("mon_hoc", mon_hoc_name).order("tuan").execute().data or []
        return {f"Tuần {c['tuan']}: {c['ten_chu_de']}": str(c["id"]) for c in chu_de_res}
    except:
        return {}


def render(giao_vien_id, teacher_class_options, all_classes, TAB_NAMES):
    st.subheader("🏁 Giao bài Kiểm tra Chủ đề")

    if not teacher_class_options:
        st.warning("⚠️ Bạn cần được phân công lớp để sử dụng tính năng này.")
        return

    # =========================================================================
    # PHẦN 1: BỘ LỌC (GIỮ NGUYÊN)
    # =========================================================================
    with st.container(border=True):
        st.markdown("##### 1. Chọn phạm vi kiến thức")
        c1, c2, c3 = st.columns(3)

        with c1:
            lop_ten_kt = st.selectbox("Lớp:", list(teacher_class_options.keys()), key="lop_kt_select")
            selected_lop_id_kt = teacher_class_options[lop_ten_kt]
            selected_class_info_kt = next((c for c in all_classes if str(c["id"]) == selected_lop_id_kt), None)
            khoi_kt = selected_class_info_kt["khoi"] if selected_class_info_kt else None

        assigned_mon_hocs = supabase.table("phan_cong_giang_day").select("mon_hoc(id, ten_mon)") \
                                .eq("giao_vien_id", giao_vien_id).eq("lop_id", selected_lop_id_kt).execute().data or []
        mon_hoc_options_kt = {item['mon_hoc']['ten_mon']: item['mon_hoc']['id'] for item in assigned_mon_hocs if
                              item.get('mon_hoc')}

        if not mon_hoc_options_kt:
            st.error("Chưa có phân công môn học cho lớp này.")
            return

        with c2:
            mon_hoc_ten_kt = st.selectbox("Môn học:", list(mon_hoc_options_kt.keys()), key="mon_kt_select")

        chu_de_map_kt = get_topics_for_test(mon_hoc_ten_kt, khoi_kt)
        with c3:
            if chu_de_map_kt:
                selected_chu_de_ten_kt = st.selectbox("Chủ đề:", list(chu_de_map_kt.keys()), key="cd_kt_select")
                chu_de_id_kt = chu_de_map_kt[selected_chu_de_ten_kt]
            else:
                st.warning("Không có chủ đề nào.")
                chu_de_id_kt = None

    if not chu_de_id_kt: return

    # =========================================================================
    # PHẦN 2: CẤU HÌNH ĐỀ THI (LIVE UPDATE - KHÔNG DÙNG FORM Ở ĐÂY)
    # =========================================================================

    counts_kt = get_question_counts(chu_de_id=chu_de_id_kt)
    total_bank = sum(counts_kt.values())

    if total_bank == 0:
        st.error("❌ Ngân hàng câu hỏi trống. Vui lòng thêm câu hỏi trước.")
        return

    st.markdown("##### 2. Cấu hình đề thi")

    # Tên bài kiểm tra
    ten_bai_kt = st.text_input("Tên bài kiểm tra:", value=f"Kiểm tra: {selected_chu_de_ten_kt}")

    st.markdown("---")

    # --- LAYOUT TƯƠNG TÁC ---
    c_total, c_matrix = st.columns([1, 2])

    with c_total:
        st.markdown("###### Tổng số câu")
        # Widget nhập tổng số câu (Thay đổi ở đây sẽ reload trang ngay lập tức để cập nhật slider bên cạnh)
        tong_cau_yeu_cau_kt = st.number_input(
            "Nhập tổng số câu:",
            min_value=1,
            max_value=total_bank,
            value=min(10, total_bank),
            label_visibility="collapsed"
        )
        st.caption(f"Tối đa: {total_bank} câu trong kho.")

        # Card thống kê kho
        with st.container(border=True):
            st.markdown("**Kho câu hỏi:**")
            st.markdown(f"🧠 Biết: `{counts_kt['biết']}`")
            st.markdown(f"🤔 Hiểu: `{counts_kt['hiểu']}`")
            st.markdown(f"🚀 Vận dụng: `{counts_kt['vận dụng']}`")

    with c_matrix:
        st.markdown("###### Phân bổ mức độ (Kéo để chia)")

        # 1. SLIDER BIẾT
        # Max của Biết = Tổng yêu cầu (hoặc max kho)
        # Ví dụ: Yêu cầu 20 câu -> Max slider Biết là 20.
        max_slider_biet = min(counts_kt['biết'], tong_cau_yeu_cau_kt)

        so_cau_biet = st.slider(
            f"🧠 Số câu Biết (Max: {max_slider_biet})",
            min_value=0,
            max_value=max_slider_biet,
            value=int(max_slider_biet * 0.4),  # Mặc định 40%
            key="slider_biet_kt"
        )

        # 2. SLIDER HIỂU
        # Max của Hiểu = Tổng yêu cầu - Số câu Biết đã chọn (hoặc max kho)
        # Ví dụ: Yêu cầu 20, Biết chọn 10 -> Còn lại 10 -> Max slider Hiểu là 10.
        remaining_after_biet = tong_cau_yeu_cau_kt - so_cau_biet
        max_slider_hieu = min(counts_kt['hiểu'], remaining_after_biet)

        # Xử lý trường hợp remaining = 0 để tránh lỗi slider
        if max_slider_hieu < 0: max_slider_hieu = 0

        so_cau_hieu = st.slider(
            f"🤔 Số câu Hiểu (Max: {max_slider_hieu})",
            min_value=0,
            max_value=max_slider_hieu,
            value=min(int(remaining_after_biet * 0.6), max_slider_hieu),  # Mặc định 60% phần còn lại
            key="slider_hieu_kt"
        )

        # 3. TỰ ĐỘNG TÍNH VẬN DỤNG
        so_cau_van_dung = tong_cau_yeu_cau_kt - so_cau_biet - so_cau_hieu

        # Kiểm tra hợp lệ của Vận dụng
        is_valid_config = True

        if so_cau_van_dung > counts_kt['vận dụng']:
            st.error(f"❌ Cần **{so_cau_van_dung}** câu Vận dụng, nhưng kho chỉ có **{counts_kt['vận dụng']}** câu.")
            is_valid_config = False
        else:
            # Hiển thị kết quả tính toán đẹp mắt
            st.success(f"🚀 Số câu Vận dụng (Tự động tính): **{so_cau_van_dung}**")

    st.markdown("---")

    # NÚT SUBMIT (Vẫn giữ chức năng giao bài)
    if st.button("🚀 Sinh & Giao bài ngay", type="primary", use_container_width=True, disabled=not is_valid_config):
        if not ten_bai_kt:
            st.error("Vui lòng nhập tên bài kiểm tra.")
        else:
            with st.spinner("Đang tạo đề thi..."):
                result_kt = generate_class_test(
                    lop_id=selected_lop_id_kt,
                    giao_vien_id=giao_vien_id,
                    ten_bai=ten_bai_kt,
                    chu_de_id=chu_de_id_kt,
                    so_cau_biet=so_cau_biet,
                    so_cau_hieu=so_cau_hieu,
                    so_cau_van_dung=so_cau_van_dung
                )

            if result_kt:
                st.success(f"✅ Đã giao bài '{ten_bai_kt}' thành công!")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Lỗi khi tạo bài kiểm tra. Vui lòng thử lại.")