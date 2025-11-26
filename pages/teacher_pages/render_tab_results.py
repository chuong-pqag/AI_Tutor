# File: pages/teacher_pages/render_tab_results.py
# (BẢN FINAL: Thêm Biểu đồ Tròn (Xếp loại) & Biểu đồ Đường (Tiến bộ))

import streamlit as st
import pandas as pd
import plotly.express as px  # <-- Cần import thư viện này
from backend.supabase_client import supabase
from backend.data_service import get_all_school_years, get_current_school_year


def classify_student(score):
    """Hàm phân loại học lực dựa trên điểm số."""
    if score is None: return "N/A"
    score = float(score)
    if score >= 9.0:
        return "Xuất sắc (9-10)"
    elif score >= 8.0:
        return "Giỏi (8-9)"
    elif score >= 6.5:
        return "Khá (6.5-8)"
    elif score >= 5.0:
        return "Trung bình (5-6.5)"
    else:
        return "Cần cố gắng (<5)"


def render(teacher_students, teacher_classes, all_classes):
    st.subheader("📊 Kết quả & Thống kê Học tập")

    teacher_student_ids = [str(s["id"]) for s in teacher_students]

    if not teacher_student_ids:
        st.info("Chưa có học sinh nào trong các lớp bạn phụ trách.")
        return

    # Tạo maps hỗ trợ lọc
    lop_id_to_ten_map = {str(c['id']): c['ten_lop'] for c in all_classes}
    lop_id_to_nam_hoc_map = {str(c['id']): c['nam_hoc'] for c in all_classes}

    # 1. TRUY VẤN DỮ LIỆU GỐC
    try:
        results = supabase.table("ket_qua_test").select(
            "*, hoc_sinh(ho_ten, lop_id), bai_tap(tieu_de, loai_bai_tap), chu_de(ten_chu_de, mon_hoc, lop, tuan)"
        ).in_("hoc_sinh_id", teacher_student_ids).order("ngay_kiem_tra", desc=True).execute().data or []
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return

    if not results:
        st.info("Chưa có kết quả nào được ghi nhận.")
        return

    df_original = pd.DataFrame(results)

    # Làm sạch dữ liệu
    df_original['lop_id'] = df_original['hoc_sinh'].apply(lambda x: x.get('lop_id') if isinstance(x, dict) else None)
    df_original['Lớp'] = df_original['lop_id'].astype(str).map(lop_id_to_ten_map).fillna('N/A')
    df_original['nam_hoc'] = df_original['lop_id'].astype(str).map(lop_id_to_nam_hoc_map).fillna('N/A')

    df_original['Môn học'] = df_original['chu_de'].apply(
        lambda x: x.get('mon_hoc', 'N/A') if isinstance(x, dict) else 'N/A')
    df_original['Chủ đề tên'] = df_original['chu_de'].apply(
        lambda x: x.get('ten_chu_de', 'N/A') if isinstance(x, dict) else 'N/A')

    # Lấy tuần từ chủ đề (quan trọng cho biểu đồ đường)
    df_original['Tuần'] = df_original['chu_de'].apply(lambda x: x.get('tuan', 0) if isinstance(x, dict) else 0)

    # Flatten loại bài tập
    df_original['loai_bai_tap_flat'] = df_original['bai_tap'].apply(
        lambda x: x.get('loai_bai_tap') if isinstance(x, dict) else None)

    # ======================================================
    # 2. BỘ LỌC ĐA CẤP
    # ======================================================
    st.markdown("##### 🔍 Bộ lọc")
    col_f0, col_f1, col_f2, col_f3 = st.columns(4)

    # Lọc 0: Năm học
    with col_f0:
        all_years = get_all_school_years()
        current_year = get_current_school_year()
        default_index = all_years.index(current_year) if current_year in all_years else 0
        selected_year = st.selectbox("0. Năm học:", all_years, index=default_index, key="res_year")

    df_filtered_by_year = df_original[df_original['nam_hoc'] == selected_year].copy()

    if df_filtered_by_year.empty:
        st.info(f"Không tìm thấy kết quả nào cho Năm học: **{selected_year}**.")
        st.stop()

    # Lọc 1: Lớp
    with col_f1:
        lop_list = ["Tất cả"] + sorted(df_filtered_by_year['Lớp'].dropna().unique())
        selected_lop = st.selectbox("1. Lớp:", lop_list, key="res_lop")

    df_filtered = df_filtered_by_year.copy()
    if selected_lop != "Tất cả":
        df_filtered = df_filtered[df_filtered['Lớp'] == selected_lop]

    # Lọc 2: Môn học
    with col_f2:
        mon_hoc_list = ["Tất cả"] + sorted(df_filtered['Môn học'].dropna().unique())
        selected_mon = st.selectbox("2. Môn học:", mon_hoc_list, key="res_mon")

    if selected_mon != "Tất cả":
        df_filtered = df_filtered[df_filtered['Môn học'] == selected_mon]

    # Lọc 3: Chủ đề
    with col_f3:
        chu_de_list = ["Tất cả"] + sorted(df_filtered['Chủ đề tên'].dropna().unique())
        selected_chu_de = st.selectbox("3. Chủ đề:", chu_de_list, key="res_cd")

    if selected_chu_de != "Tất cả":
        df_filtered = df_filtered[df_filtered['Chủ đề tên'] == selected_chu_de]

    st.divider()

    # ======================================================
    # 3. DASHBOARD BIỂU ĐỒ (VISUALIZATION) - MỚI
    # ======================================================

    # Chỉ thống kê dựa trên bài "Kiểm tra Chủ đề" để chính xác năng lực
    df_stats = df_filtered[df_filtered['loai_bai_tap_flat'] == 'kiem_tra_chu_de'].copy()

    if not df_stats.empty:
        st.markdown("### 📈 Phân tích Năng lực Lớp học")

        col_chart1, col_chart2 = st.columns(2)

        # --- BIỂU ĐỒ 1: PIE CHART (TỶ LỆ XẾP LOẠI) ---
        with col_chart1:
            st.markdown("**1. Tỷ lệ Xếp loại (Dựa trên điểm)**")

            df_stats['Xếp loại'] = df_stats['diem'].apply(classify_student)

            # Đếm số lượng mỗi loại
            pie_data = df_stats['Xếp loại'].value_counts().reset_index()
            pie_data.columns = ['Loại', 'Số lượng']

            # Vẽ biểu đồ tròn bằng Plotly
            fig_pie = px.pie(
                pie_data,
                values='Số lượng',
                names='Loại',
                color='Loại',
                color_discrete_map={
                    "Xuất sắc (9-10)": "#28a745",  # Xanh lá đậm
                    "Giỏi (8-9)": "#20c997",  # Xanh ngọc
                    "Khá (6.5-8)": "#ffc107",  # Vàng
                    "Trung bình (5-6.5)": "#17a2b8",  # Xanh dương
                    "Cần cố gắng (<5)": "#dc3545"  # Đỏ
                },
                hole=0.4  # Donut chart
            )
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- BIỂU ĐỒ 2: LINE CHART (TIẾN BỘ THEO TUẦN) ---
        with col_chart2:
            st.markdown("**2. Biểu đồ Tiến bộ Trung bình (Theo Tuần)**")

            # Nhóm theo Tuần và tính điểm trung bình
            # Chỉ lấy những dòng có Tuần > 0
            df_line = df_stats[df_stats['Tuần'] > 0].groupby('Tuần')['diem'].mean().sort_index()

            if not df_line.empty:
                st.line_chart(df_line, color="#ff6600", height=300)
                st.caption("Trục ngang: Tuần học | Trục dọc: Điểm trung bình cả lớp")
            else:
                st.info("Chưa đủ dữ liệu tuần để vẽ biểu đồ tiến bộ.")

    # ======================================================
    # 4. BẢNG DỮ LIỆU CHI TIẾT
    # ======================================================
    st.markdown("### 📝 Danh sách chi tiết")

    # Chuẩn bị bảng hiển thị
    def get_nested(row, col, key):
        d = row.get(col)
        return d.get(key, '') if isinstance(d, dict) else ''

    df_display = pd.DataFrame({
        'Ngày': pd.to_datetime(df_filtered['ngay_kiem_tra']).dt.strftime('%d/%m/%Y'),
        'Học sinh': df_filtered['hoc_sinh'].apply(lambda x: get_nested({'h': x}, 'h', 'ho_ten')),
        'Lớp': df_filtered['Lớp'],
        'Chủ đề': df_filtered['Chủ đề tên'],
        'Bài': df_filtered['bai_tap'].apply(lambda x: get_nested({'b': x}, 'b', 'tieu_de')),
        'Loại': df_filtered['loai_bai_tap_flat'].apply(lambda x: 'Luyện tập' if x == 'luyen_tap' else 'Kiểm tra'),
        'Điểm': df_filtered['diem'],
        'Kết quả': df_filtered.apply(lambda r: f"{r.get('so_cau_dung')}/{r.get('tong_cau')}", axis=1)
    })

    st.dataframe(df_display, use_container_width=True, hide_index=True)