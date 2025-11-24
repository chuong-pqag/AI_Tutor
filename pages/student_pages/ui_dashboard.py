# File: pages/student_pages/ui_dashboard.py
# (BẢN HYBRID MODEL: Phân loại Hoàn thành (Vàng) vs Thành thạo (Xanh))

import streamlit as st
import pandas as pd
from backend.data_service import (
    get_student_overall_progress,
    get_latest_ai_recommendation,
    get_topics_status,
    get_topic_by_id
)


def render_dashboard(hoc_sinh_id, current_lop, subject_map):
    # 1. Tải tiến độ
    progress_data = get_student_overall_progress(hoc_sinh_id)

    st.subheader("📊 Bảng điều khiển Tiến độ")
    col_metric1, col_metric2, col_metric3 = st.columns(3)

    col_metric1.metric(
        label="Điểm TB Kiểm tra CĐ",
        value=f"{progress_data['avg_score']:.1f}",
        delta=f"{progress_data['latest_score']:.1f} (Gần nhất)",
        delta_color="off"
    )
    col_metric2.metric(
        label="Chủ đề đã Hoàn thành",
        value=progress_data['completed_topics_count']
    )

    # 2. Chọn Môn học
    st.subheader("📚 Lộ trình Môn học")
    subject_list = list(subject_map.keys())
    selected_subject_name = st.selectbox("Chọn Môn học:", subject_list, key="dashboard_subject_select")

    # 3. Gợi ý AI
    latest_rec = get_latest_ai_recommendation(hoc_sinh_id, mon_hoc=selected_subject_name, lop=current_lop)

    with col_metric3:
        st.markdown("**Gợi ý AI Mới nhất:**")
        if latest_rec:
            action_map = {
                'remediate': ('⚠️ Học lại', 'error'),
                'review': ('🤔 Ôn tập', 'warning'),
                'advance': ('🎉 Học tiếp', 'success')
            }
            action_display, _ = action_map.get(latest_rec['action'], ('Chờ gợi ý', 'normal'))
            st.markdown(f"### {action_display}")

            rec_name = latest_rec.get('ten_chu_de') or latest_rec.get('ten_bai_hoc') or "N/A"
            st.caption(f"Nội dung: {rec_name}")
        else:
            st.info("Hoàn thành bài kiểm tra để nhận gợi ý!")

    st.markdown("---")

    # 4. DANH SÁCH CHỦ ĐỀ (HYBRID DISPLAY)
    if selected_subject_name and current_lop is not None:
        try:
            lop_int = int(current_lop)
            topics_list = get_topics_status(hoc_sinh_id, selected_subject_name, lop_int)

            if not topics_list:
                st.warning(f"Môn '{selected_subject_name}' chưa có chủ đề.")
                st.stop()

            st.markdown("#### Danh sách Chủ đề:")
            suggested_topic_id = latest_rec['chu_de_id'] if latest_rec else None

            # 4.1 HIỂN THỊ GỢI Ý AI (Nổi bật)
            if latest_rec:
                suggested_topic_info = get_topic_by_id(latest_rec['chu_de_id'])
                if suggested_topic_info:
                    st.markdown("##### 💡 AI Đề xuất:")
                    with st.container(border=True):
                        c_topic, c_btn = st.columns([4, 1])
                        c_topic.markdown(
                            f"**{suggested_topic_info['ten_chu_de']}** (Tuần {suggested_topic_info['tuan']})")

                        vn_action = {'remediate': 'Củng cố kiến thức', 'review': 'Ôn tập lại',
                                     'advance': 'Học bài mới'}.get(latest_rec['action'], latest_rec['action'])
                        c_topic.caption(f"Hành động: {vn_action}")

                        if c_btn.button("Học ngay 🚀", key=f"start_rec_{latest_rec['chu_de_id']}", type="primary"):
                            st.session_state['selected_topic_id'] = latest_rec['chu_de_id']
                            st.session_state['latest_suggestion_id'] = latest_rec.get("id")
                            st.session_state['viewing_topic'] = True
                            st.rerun()
                    st.divider()

            # 4.2 DANH SÁCH CÒN LẠI (PHÂN LOẠI VÀNG/XANH)
            for topic in topics_list:
                t_id = topic['id']
                if t_id == suggested_topic_id: continue

                col_t, col_s, col_b = st.columns([3, 1.5, 1])  # Chỉnh tỷ lệ cột

                with col_t:
                    st.markdown(f"**{topic['ten_chu_de']}** (Tuần {topic['tuan']})")

                with col_s:
                    if topic['completed']:
                        score = topic.get('best_score', 0)
                        # --- LOGIC HYBRID ---
                        if score >= 8.0:
                            st.success(f"✅ Thành thạo ({score})")
                        else:
                            st.warning(f"🟡 Hoàn thành ({score})")
                        # --------------------
                    else:
                        st.caption("⚪ Chưa học")

                with col_b:
                    if st.button("Vào học", key=f"start_{t_id}"):
                        st.session_state['selected_topic_id'] = t_id
                        st.session_state['latest_suggestion_id'] = None
                        st.session_state['viewing_topic'] = True
                        st.rerun()

        except Exception as e:
            st.error(f"Lỗi tải danh sách: {e}")