# ===============================================
# 🧑‍🏫 Trang giáo viên - teachers.py (Cập nhật bố cục 2 cột con)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
from backend.supabase_client import supabase
from backend.class_test_service import generate_class_test, generate_practice_exercise
from backend.data_service import get_lessons_by_topic, get_question_counts

st.set_page_config(page_title="AI Tutor - Giáo viên", page_icon="🧑‍🏫", layout="wide")

# CSS (Giữ nguyên)
st.markdown("""
    <style>
    /* ... (CSS của bạn giữ nguyên) ... */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    div[data-testid="stHorizontalBlock"] > div:first-child > div { display: flex; flex-direction: column; align-items: center; text-align: center; }
    div[data-testid="stHorizontalBlock"] > div:first-child > div h1, div[data-testid="stHorizontalBlock"] > div:first-child > div h3 { text-align: center; }
    .teacher-name-title { font-family: 'Times New Roman', Times, serif; font-size: 14pt !important; font-weight: bold; color: #31333F; padding-bottom: 0.5rem; margin-block-start: 0; margin-block-end: 0; text-align: center; }
    div[data-testid="stInfo"] { padding: 0.5rem 1rem; margin-bottom: 0.5rem; }
    div[data-testid="stNumberInput"] { padding-bottom: 0.25rem; }

    /* Căn chỉnh text trong cột label (cho bố cục 2 cột con) */
    .st-emotion-cache-1b2q840 .stMarkdown {
        padding-top: 0.5rem; /* Căn giữa text với ô input */
    }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", use_container_width=True)
except Exception:
    st.warning("Không tải được ảnh banner.")
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", use_container_width=True)

# KIỂM TRA ĐĂNG NHẬP (Giữ nguyên)
if "role" not in st.session_state or st.session_state["role"] != "teacher":
    st.warning("⚠️ Vui lòng quay lại trang Đăng nhập để chọn vai trò Giáo viên.")
    if st.button("Về trang đăng nhập"):
        st.switch_page("app.py")
    st.stop()

# TẢI DỮ LIỆU (Giữ nguyên)
giao_vien_id = st.session_state.get("giao_vien_id")
giao_vien_ten = st.session_state.get("giao_vien_ten", "Giáo viên")
gv_res = supabase.table("giao_vien").select("ho_ten, email").eq("id", giao_vien_id).execute()
teacher_data = gv_res.data[0] if gv_res.data else {}
current_email = teacher_data.get("email", "")


@st.cache_data(ttl=300)
def load_teacher_data(giao_vien_id_param):
    all_classes_res = supabase.table("lop_hoc").select("*").execute()
    all_students_res = supabase.table("hoc_sinh").select("*").execute()
    teacher_assignments_res = supabase.table("phan_cong_giang_day").select("lop_id").eq("giao_vien_id",
                                                                                        giao_vien_id_param).execute()
    all_classes = all_classes_res.data or []
    all_students = all_students_res.data or []
    teacher_assignments = teacher_assignments_res.data or []
    teacher_class_ids = {item["lop_id"] for item in teacher_assignments}
    teacher_classes = [c for c in all_classes if str(c["id"]) in teacher_class_ids]
    student_class_ids_str = {str(c["id"]) for c in teacher_classes}
    teacher_students = [s for s in all_students if str(s.get("lop_id")) in student_class_ids_str]
    return all_classes, all_students, teacher_classes, teacher_students


all_classes, all_students, teacher_classes, teacher_students = load_teacher_data(giao_vien_id)

# BỐ CỤC 2 CỘT (Giữ nguyên)
col1, col2 = st.columns([1, 5])

# CỘT 1: THÔNG TIN GIÁO VIÊN (Giữ nguyên)
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995574.png", width=120)
    st.markdown(f"<h1 class='teacher-name-title'>{giao_vien_ten}</h1>", unsafe_allow_html=True)
    st.divider()
    with st.expander("📝 Sửa thông tin cá nhân"):
        with st.form("update_teacher_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=giao_vien_ten)
            new_email = st.text_input("Email", value=current_email)
            if st.form_submit_button("Lưu thông tin"):
                try:
                    update_payload = {"ho_ten": new_ho_ten, "email": new_email}
                    supabase.table("giao_vien").update(update_payload).eq("id", giao_vien_id).execute()
                    st.session_state["giao_vien_ten"] = new_ho_ten
                    st.success("Cập nhật thông tin thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
    with st.expander("🔑 Đổi mật khẩu"):
        with st.form("change_teacher_password_form", clear_on_submit=True):
            new_pass = st.text_input("Mật khẩu mới", type="password")
            confirm_pass = st.text_input("Xác nhận mật khẩu", type="password")
            if st.form_submit_button("Lưu mật khẩu mới"):
                if not new_pass:
                    st.error("Mật khẩu không được để trống.")
                elif new_pass != confirm_pass:
                    st.error("Mật khẩu xác nhận không khớp.")
                else:
                    try:
                        supabase.table("giao_vien").update({"mat_khau": new_pass}).eq("id", giao_vien_id).execute()
                        st.success("Đổi mật khẩu thành công!")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    st.divider()
    if st.button("🔓 Đăng xuất", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.switch_page("app.py")

# CỘT 2: NỘI DUNG CHÍNH (Tabs chức năng)
with col2:
    st.subheader(f"🧑‍🏫 Bảng điều khiển Giáo viên")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📘 Lớp học",
        "📈 Kết quả học sinh",
        "🏁 Giao bài Kiểm tra CĐ",
        "✏️ Giao bài Luyện tập BH"
    ])

    # TAB 1 - LỚP HỌC (Giữ nguyên)
    with tab1:
        st.subheader("📘 Danh sách lớp bạn phụ trách")
        if teacher_classes:
            for c in teacher_classes:
                st.markdown(f"**{c['ten_lop']}** (Khối {c['khoi']})")
                hs = [s for s in teacher_students if str(s.get("lop_id")) == str(c.get("id"))]
                if hs:
                    hs_df_display = pd.DataFrame(hs)[
                        ["ho_ten", "ma_hoc_sinh", "email", "ngay_sinh", "gioi_tinh"]].rename(
                        columns={"ho_ten": "Họ tên", "ma_hoc_sinh": "Mã HS", "ngay_sinh": "Ngày sinh",
                                 "gioi_tinh": "Giới tính"}
                    )
                    st.dataframe(hs_df_display, use_container_width=True, hide_index=True)
                else:
                    st.caption("Chưa có học sinh nào trong lớp này.")
        else:
            st.info("Bạn chưa được phân công lớp nào.")

    # TAB 2 - KẾT QUẢ HỌC SINH (Giữ nguyên)
    with tab2:
        st.subheader("📊 Kết quả bài kiểm tra & luyện tập")
        teacher_student_ids = [str(s["id"]) for s in teacher_students]
        if not teacher_student_ids:
            st.info("Chưa có học sinh nào trong các lớp bạn phụ trách.")
        else:
            results = supabase.table("ket_qua_test").select(
                "*, hoc_sinh(ho_ten), bai_tap(tieu_de, loai_bai_tap), chu_de(ten_chu_de)").in_("hoc_sinh_id",
                                                                                               teacher_student_ids).order(
                "ngay_kiem_tra", desc=True).execute().data or []
            if results:
                df = pd.DataFrame(results)
                df_display = pd.DataFrame({
                    'Ngày làm': pd.to_datetime(df['ngay_kiem_tra']).dt.strftime('%Y-%m-%d %H:%M'),
                    'Học sinh': df['hoc_sinh'].apply(
                        lambda x: x.get('ho_ten', 'N/A') if isinstance(x, dict) else 'N/A'),
                    'Chủ đề': df['chu_de'].apply(
                        lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) else 'N/A'),
                    'Bài tập/KT': df['bai_tap'].apply(
                        lambda x: x.get('tieu_de', 'N/A') if isinstance(x, dict) else 'N/A'),
                    'Loại': df['bai_tap'].apply(
                        lambda x: 'Luyện tập' if isinstance(x, dict) and x.get('loai_bai_tap') == 'luyen_tap' else (
                            'Kiểm tra CĐ' if isinstance(x, dict) and x.get(
                                'loai_bai_tap') == 'kiem_tra_chu_de' else 'Không rõ')),
                    'Điểm': df['diem'],
                    'Kết quả': df.apply(lambda row: f"{row.get('so_cau_dung', '?')}/{row.get('tong_cau', '?')}", axis=1)
                })
                st.dataframe(df_display.dropna(subset=['Chủ đề']), use_container_width=True, hide_index=True)
                df_kt = df[
                    df['bai_tap'].apply(lambda x: isinstance(x, dict) and x.get('loai_bai_tap') == 'kiem_tra_chu_de')]
                if not df_kt.empty:
                    df_kt['Chủ đề'] = df_kt['chu_de'].apply(
                        lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) else 'N/A')
                    chart_data = df_kt.groupby("Chủ đề")["diem"].mean().dropna()
                    if not chart_data.empty:
                        st.markdown("##### Điểm trung bình Bài kiểm tra Chủ đề"); st.bar_chart(chart_data)
                    else:
                        st.info("Chưa đủ dữ liệu điểm KT Chủ đề để vẽ biểu đồ.")
                else:
                    st.info("Chưa có kết quả Bài kiểm tra Chủ đề nào.")
            else:
                st.info("Chưa có kết quả nào được ghi nhận.")

    # ===============================================
    # TAB 3 - GIAO BÀI KIỂM TRA CĐ (ĐÃ SỬA BỐ CỤC)
    # ===============================================
    with tab3:
        st.subheader("🏁 Giao bài Kiểm tra Chủ đề cho lớp")

        if not teacher_classes:
            st.warning("Bạn cần được phân công lớp để giao bài kiểm tra.")
        else:
            lop_options_kt = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}
            lop_ten_kt = st.selectbox("Chọn lớp (KT)", list(lop_options_kt.keys()), key="lop_kt_select")
            selected_lop_id_kt = lop_options_kt[lop_ten_kt]
            selected_class_info_kt = next((c for c in teacher_classes if str(c["id"]) == selected_lop_id_kt), None)
            chu_de_id_kt = None

            if selected_class_info_kt:
                khoi_kt = selected_class_info_kt["khoi"]
                chu_de_res_kt = supabase.table("chu_de").select("id, ten_chu_de").eq("lop", khoi_kt).order(
                    "tuan").execute().data or []
                chu_de_map_kt = {c["ten_chu_de"]: str(c["id"]) for c in chu_de_res_kt}
                if chu_de_map_kt:
                    selected_chu_de_ten_kt = st.selectbox("Chọn Chủ đề (KT)", list(chu_de_map_kt.keys()),
                                                          key="cd_kt_select")
                    chu_de_id_kt = chu_de_map_kt[selected_chu_de_ten_kt]
                else:
                    st.error(f"Không tìm thấy chủ đề nào cho Khối {khoi_kt}.")
            else:
                st.error("Không tìm thấy thông tin khối lớp.")

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

                    # ---- BỐ CỤC 2 CỘT CON (THEO YÊU CẦU MỚI) ----
                    with col_select_kt:
                        st.markdown("**Phân bổ số lượng:**")

                        # Tạo 2 cột con bên trong col_select_kt
                        col_labels_kt, col_inputs_kt = st.columns([2, 1])  # Cột label rộng hơn

                        with col_labels_kt:
                            st.markdown("🧠 **Số câu Biết:**")
                            st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)  # Đệm
                            st.markdown("🤔 **Số câu Hiểu:**")
                            st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)  # Đệm
                            st.markdown("🚀 **Số câu Vận dụng:**")

                        with col_inputs_kt:
                            so_cau_biet_kt = st.number_input(
                                "Số câu Biết", label_visibility="collapsed",
                                min_value=0, max_value=min(counts_kt['biết'], tong_cau_yeu_cau_kt),
                                value=0, step=1, key="scb_kt"
                            )
                            remaining_after_biet_kt = tong_cau_yeu_cau_kt - so_cau_biet_kt
                            so_cau_hieu_kt = st.number_input(
                                "Số câu Hiểu", label_visibility="collapsed",
                                min_value=0, max_value=min(counts_kt['hiểu'], remaining_after_biet_kt),
                                value=0, step=1, key="sch_kt"
                            )
                            so_cau_van_dung_kt = tong_cau_yeu_cau_kt - so_cau_biet_kt - so_cau_hieu_kt
                            st.number_input(
                                "Số câu Vận dụng",
                                value=so_cau_van_dung_kt,
                                disabled=True,
                                key="scvd_kt_display",
                                label_visibility="collapsed"
                            )
                    # ---- KẾT THÚC BỐ CỤC 2 CỘT CON ----

                    disable_button_kt = False
                    if so_cau_van_dung_kt < 0:
                        st.error(
                            f"Tổng số câu 'Biết' ({so_cau_biet_kt}) và 'Hiểu' ({so_cau_hieu_kt}) đã vượt quá tổng số bạn yêu cầu ({tong_cau_yeu_cau_kt}).")
                        disable_button_kt = True
                    elif so_cau_van_dung_kt > counts_kt['vận dụng']:
                        st.error(
                            f"Số câu 'Vận dụng' (tự tính: {so_cau_van_dung_kt}) vượt quá số câu có sẵn trong ngân hàng ({counts_kt['vận dụng']}). Vui lòng giảm số câu 'Biết' hoặc 'Hiểu'.")
                        disable_button_kt = True

                    st.markdown(f"#### **Tổng số câu đã chọn: `{tong_cau_yeu_cau_kt}`**")

                    if st.button("🚀 Sinh & Giao bài Kiểm tra CĐ", key="btn_giao_kt", use_container_width=True,
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
                                    f"✅ Đã giao bài KT '{ten_bai_kt}' ({tong_cau_yeu_cau_kt} câu) cho lớp {lop_ten_kt}")
                            else:
                                st.error(
                                    f"❌ Không thể tạo bài KT. Lỗi máy chủ (vui lòng kiểm tra log, có thể do không đủ câu hỏi).")

    # ===============================================
    # ---- TAB 4 - GIAO BÀI LUYỆN TẬP BH (ĐÃ SỬA BỐ CỤC) ----
    # ===============================================
    with tab4:
        st.subheader("✏️ Giao bài Luyện tập Bài học cho lớp")

        if not teacher_classes:
            st.warning("Bạn cần được phân công lớp để giao bài luyện tập.")
        else:
            lop_options_lt = {c["ten_lop"]: str(c["id"]) for c in teacher_classes}
            lop_ten_lt = st.selectbox("Chọn lớp (LT)", list(lop_options_lt.keys()), key="lop_lt_select")
            selected_lop_id_lt = lop_options_lt[lop_ten_lt]
            selected_class_info_lt = next((c for c in teacher_classes if str(c["id"]) == selected_lop_id_lt), None)
            chu_de_id_lt = None
            bai_hoc_id_lt = None
            if selected_class_info_lt:
                khoi_lt = selected_class_info_lt["khoi"]
                chu_de_res_lt = supabase.table("chu_de").select("id, ten_chu_de").eq("lop", khoi_lt).order(
                    "tuan").execute().data or []
                chu_de_map_lt = {c["ten_chu_de"]: str(c["id"]) for c in chu_de_res_lt}
                if chu_de_map_lt:
                    selected_chu_de_ten_lt = st.selectbox("Chọn Chủ đề (LT)", list(chu_de_map_lt.keys()),
                                                          key="cd_lt_select")
                    chu_de_id_lt = chu_de_map_lt[selected_chu_de_ten_lt]
                    if chu_de_id_lt:
                        lessons = get_lessons_by_topic(chu_de_id_lt)
                        if lessons:
                            lesson_map_lt = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
                            selected_lesson_name_lt = st.selectbox("Chọn Bài học (LT)", list(lesson_map_lt.keys()),
                                                                   key="bh_lt_select")
                            bai_hoc_id_lt = lesson_map_lt[selected_lesson_name_lt]
                        else:
                            st.warning(f"Chủ đề '{selected_chu_de_ten_lt}' chưa có bài học nào.")
                else:
                    st.error(f"Không tìm thấy chủ đề nào cho Khối {khoi_lt}.")
            else:
                st.error("Không tìm thấy thông tin khối lớp.")

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
                            else:
                                st.error(
                                    f"❌ Không thể tạo bài LT. Lỗi máy chủ (vui lòng kiểm tra log, có thể do không đủ câu hỏi).")