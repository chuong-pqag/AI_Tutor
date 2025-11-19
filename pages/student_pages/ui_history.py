# File: pages/student_pages/ui_history.py
import streamlit as st
import pandas as pd
from backend.data_service import get_student_all_results, get_learning_paths


def render_history(hoc_sinh_id):
    st.subheader("📜 Lịch sử & Lộ trình")
    st.markdown("#### Kết quả gần nhất")

    all_results = get_student_all_results(hoc_sinh_id)
    if all_results:
        df_results = pd.DataFrame(all_results)
        df_display = pd.DataFrame({
            'Ngày làm': pd.to_datetime(df_results['ngay_kiem_tra']).dt.strftime(
                '%Y-%m-%d %H:%M') if 'ngay_kiem_tra' in df_results.columns else None,
            'Chủ đề': df_results.apply(
                lambda row: row.get('chu_de', {}).get('ten_chu_de', 'N/A') if isinstance(row.get('chu_de'),
                                                                                         dict) else 'N/A', axis=1),
            'Bài tập/KT': df_results.apply(
                lambda row: row.get('bai_tap', {}).get('tieu_de', 'N/A') if isinstance(row.get('bai_tap'),
                                                                                       dict) else 'N/A', axis=1),
            'Loại': df_results.apply(
                lambda row: 'Luyện tập' if isinstance(row.get('bai_tap'), dict) and row['bai_tap'].get(
                    'loai_bai_tap') == 'luyen_tap' else (
                    'Kiểm tra CĐ' if isinstance(row.get('bai_tap'), dict) and row['bai_tap'].get(
                        'loai_bai_tap') == 'kiem_tra_chu_de' else 'Không rõ'), axis=1),
            'Điểm': df_results['diem'] if 'diem' in df_results.columns else None,
            'Kết quả': df_results.apply(lambda row: f"{row.get('so_cau_dung', '?')}/{row.get('tong_cau', '?')}",
                                        axis=1)
        }).dropna(subset=['Ngày làm'])
        st.dataframe(df_display, width='stretch', hide_index=True)
    else:
        st.info("Chưa có kết quả bài làm.")

    st.markdown("#### Lộ trình đề xuất (AI)")
    learning_paths = get_learning_paths(hoc_sinh_id)
    if learning_paths:
        df_paths_processed = []
        for path in learning_paths:
            ngay_goi_y = pd.to_datetime(path.get('ngay_goi_y')).strftime('%Y-%m-%d') if path.get(
                'ngay_goi_y') else 'N/A'
            loai_goi_y_vn = {'remediate': 'Học lại', 'review': 'Ôn tập', 'advance': 'Học tiếp'}.get(
                path.get('loai_goi_y'), 'Không rõ')
            noi_dung = 'N/A'
            bai_hoc_data = path.get('suggested_lesson');
            chu_de_data_lp = path.get('suggested_topic')
            if isinstance(bai_hoc_data, dict) and bai_hoc_data.get('ten_bai_hoc'):
                noi_dung = f"Bài: {bai_hoc_data['ten_bai_hoc']}"
            elif isinstance(chu_de_data_lp, dict) and chu_de_data_lp.get('ten_chu_de'):
                noi_dung = f"Chủ đề: {chu_de_data_lp['ten_chu_de']}"
            trang_thai = path.get('trang_thai', 'Chưa thực hiện')
            df_paths_processed.append(
                {'Ngày gợi ý': ngay_goi_y, 'Gợi ý': loai_goi_y_vn, 'Nội dung': noi_dung, 'Trạng thái': trang_thai})
        st.dataframe(pd.DataFrame(df_paths_processed), width='stretch', hide_index=True)
    else:
        st.info("Chưa có lộ trình học nào.")