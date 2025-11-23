# File: pages/teacher_pages/render_tab_results.py
# (CẬP NHẬT: Thêm bộ lọc Năm học)
import streamlit as st
import pandas as pd
from backend.supabase_client import supabase
# (THÊM MỚI) Import các hàm backend
from backend.data_service import get_all_school_years, get_current_school_year


def render(teacher_students, teacher_classes, all_classes):  # <--- Chữ ký hàm giữ nguyên
    st.subheader("📊 Kết quả bài kiểm tra & luyện tập")
    teacher_student_ids = [str(s["id"]) for s in teacher_students]

    if not teacher_student_ids:
        st.info("Chưa có học sinh nào trong các lớp bạn phụ trách.")
        return

    # Tạo maps hỗ trợ lọc
    lop_id_to_ten_map = {str(c['id']): c['ten_lop'] for c in all_classes}
    # (THÊM MỚI) Tạo map Lop ID -> Nam Hoc
    lop_id_to_nam_hoc_map = {str(c['id']): c['nam_hoc'] for c in all_classes}

    # 1. TRUY VẤN DỮ LIỆU GỐC (Giữ nguyên)
    results = supabase.table("ket_qua_test").select(
        "*, hoc_sinh(ho_ten, lop_id), bai_tap(tieu_de, loai_bai_tap), chu_de(ten_chu_de, mon_hoc, lop)").in_(
        "hoc_sinh_id",
        teacher_student_ids).order("ngay_kiem_tra", desc=True).execute().data or []

    if not results:
        st.info("Chưa có kết quả nào được ghi nhận.")
        return

    df_original = pd.DataFrame(results)

    # Thêm cột Lớp và Môn học để dễ dàng lọc (Giữ nguyên)
    df_original['lop_id'] = df_original['hoc_sinh'].apply(lambda x: x.get('lop_id') if isinstance(x, dict) else None)
    df_original['Lớp'] = df_original['lop_id'].astype(str).map(lop_id_to_ten_map).fillna('N/A')
    df_original['Môn học'] = df_original['chu_de'].apply(
        lambda x: x.get('mon_hoc', 'N/A') if isinstance(x, dict) else 'N/A')
    df_original['Chủ đề tên'] = df_original['chu_de'].apply(
        lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) else 'N/A')

    # (THÊM MỚI) Thêm cột 'nam_hoc' vào df_original
    df_original['nam_hoc'] = df_original['lop_id'].astype(str).map(lop_id_to_nam_hoc_map).fillna('N/A')

    # ======================================================
    # 2. BỘ LỌC ĐA CẤP (Đã cập nhật)
    # ======================================================
    st.markdown("##### 🔍 Bộ lọc Báo cáo")
    col_f0, col_f1, col_f2, col_f3 = st.columns(4)  # Thêm 1 cột

    # (THÊM MỚI) Lọc 0: Năm học
    with col_f0:
        all_years = get_all_school_years()
        current_year = get_current_school_year()
        default_index = all_years.index(current_year) if current_year in all_years else 0

        selected_year = st.selectbox("0. Năm học:", all_years, index=default_index, key="result_filter_year")

    # Lọc dữ liệu gốc theo năm học đã chọn
    df_filtered_by_year = df_original[df_original['nam_hoc'] == selected_year].copy()

    if df_filtered_by_year.empty:
        st.info(f"Không tìm thấy kết quả nào cho Năm học: **{selected_year}**.")
        st.stop()

    # Lọc 1: Lớp (Dùng df_filtered_by_year)
    with col_f1:
        lop_list = ["Tất cả"] + sorted(df_filtered_by_year['Lớp'].dropna().unique())
        selected_lop = st.selectbox("1. Lớp:", lop_list, key="result_filter_lop")

    df_filtered = df_filtered_by_year.copy()
    if selected_lop != "Tất cả":
        df_filtered = df_filtered[df_filtered['Lớp'] == selected_lop]

    # Lọc 2: Môn học
    with col_f2:
        mon_hoc_list = ["Tất cả"] + sorted(df_filtered['Môn học'].dropna().unique())
        selected_mon = st.selectbox("2. Môn học:", mon_hoc_list, key="result_filter_mon")

    if selected_mon != "Tất cả":
        df_filtered = df_filtered[df_filtered['Môn học'] == selected_mon]

    # Lọc 3: Chủ đề
    with col_f3:
        chu_de_list = ["Tất cả"] + sorted(df_filtered['Chủ đề tên'].dropna().unique())
        selected_chu_de = st.selectbox("3. Chủ đề:", chu_de_list, key="result_filter_cd")

    if selected_chu_de != "Tất cả":
        df_filtered = df_filtered[df_filtered['Chủ đề tên'] == selected_chu_de]

    st.markdown("---")
    st.info(f"Đã tìm thấy **{len(df_filtered)}** kết quả phù hợp với bộ lọc (Năm học: {selected_year}).")

    # 3. CHUẨN BỊ DATAFRAME HIỂN THỊ (Giữ nguyên)
    df = df_filtered

    def get_nested_value(row, col_name, key):
        data = row.get(col_name)
        return data.get(key, 'N/A') if isinstance(data, dict) else 'N/A'

    df_display = pd.DataFrame({
        'Ngày làm': pd.to_datetime(df['ngay_kiem_tra']).dt.strftime('%Y-%m-%d %H:%M'),
        'Học sinh': df['hoc_sinh'].apply(lambda x: get_nested_value({'hoc_sinh': x}, 'hoc_sinh', 'ho_ten')),
        'Lớp': df['Lớp'],
        'Môn học': df['Môn học'],
        'Chủ đề': df['Chủ đề tên'],
        'Bài tập/KT': df['bai_tap'].apply(lambda x: get_nested_value({'bai_tap': x}, 'bai_tap', 'tieu_de')),

        'Loại': df['bai_tap'].apply(
            lambda x: 'Luyện tập' if isinstance(x, dict) and x.get('loai_bai_tap') == 'luyen_tap' else (
                'Kiểm tra CĐ' if isinstance(x, dict) and x.get(
                    'loai_bai_tap') == 'kiem_tra_chu_de' else 'Không rõ')),

        'Điểm': df['diem'],
        'Kết quả': df.apply(lambda row: f"{row.get('so_cau_dung', '?')}/{row.get('tong_cau', '?')}", axis=1)
    })

    st.dataframe(df_display.dropna(subset=['Chủ đề']), width='stretch', hide_index=True)

    # 4. VẼ BIỂU ĐỒ (Dựa trên dữ liệu đã lọc) (Giữ nguyên)

    df_chart = df_filtered.copy()
    df_chart['loai_bai_tap_flat'] = df_chart['bai_tap'].apply(
        lambda x: x.get('loai_bai_tap') if isinstance(x, dict) else None)

    df_kt = df_chart[df_chart['loai_bai_tap_flat'] == 'kiem_tra_chu_de'].copy()

    if not df_kt.empty:
        df_kt['Chủ đề'] = df_kt['chu_de'].apply(lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) else 'N/A')
        chart_data = df_kt.groupby("Chủ đề")["diem"].mean().dropna()
        if not chart_data.empty:
            st.markdown("##### Điểm trung bình Bài kiểm tra Chủ đề");
            st.bar_chart(chart_data)
        else:
            st.info("Chưa đủ dữ liệu điểm KT Chủ đề để vẽ biểu đồ.")
    else:
        st.info("Không có kết quả Bài kiểm tra Chủ đề nào phù hợp với bộ lọc.")