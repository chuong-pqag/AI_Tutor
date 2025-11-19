# File: pages/student_pages/ui_dashboard.py
# (Bản cập nhật đầy đủ – Logic AI chính xác + gọi sau khi chọn môn)

import streamlit as st
import pandas as pd
from backend.data_service import (
    get_student_overall_progress,
    get_latest_ai_recommendation,
    get_topics_status,
    get_topic_by_id
)


def render_dashboard(hoc_sinh_id, current_lop, subject_map):
    """
    Dashboard học sinh – phiên bản đã cập nhật logic AI:
    - Gợi ý AI được lấy đúng môn học đang xem
    - Ưu tiên lộ trình AI trong DB
    - Nếu không có, fallback sang "topic tiếp theo chưa HT"
    """

    # ----------------------------------------------------
    # 1. TẢI TIẾN ĐỘ (không thay đổi)
    # ----------------------------------------------------
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

    # ----------------------------------------------------
    # 2. CHỌN MÔN HỌC TRƯỚC → SAU ĐÓ MỚI LẤY GỢI Ý AI
    # ----------------------------------------------------
    st.subheader("📚 Lộ trình Môn học")

    subject_list = list(subject_map.keys())
    selected_subject_name = st.selectbox(
        "Chọn Môn học để xem tiến độ:",
        subject_list,
        key="dashboard_subject_select",
    )

    # ----------------------------------------------------
    # 3. LẤY GỢI Ý AI CHO ĐÚNG MÔN (ĐIỂM QUAN TRỌNG)
    # ----------------------------------------------------
    latest_rec = get_latest_ai_recommendation(
        hoc_sinh_id,
        mon_hoc=selected_subject_name,
        lop=current_lop
    )

    # Hiển thị gợi ý AI trong cột thứ 3
    with col_metric3:
        st.markdown("**Gợi ý AI Mới nhất:**")
        if latest_rec:
            action_map = {
                'remediate': ('⚠️ Học lại', 'error'),
                'review': ('🤔 Ôn tập', 'warning'),
                'advance': ('🎉 Học tiếp', 'success')
            }
            action_display, icon = action_map.get(latest_rec['action'], ('Chờ gợi ý', 'normal'))
            st.markdown(f"### {icon} {action_display}")

            rec_name = latest_rec.get('ten_chu_de') or latest_rec.get('ten_bai_hoc') or "N/A"
            st.caption(f"Nội dung: {rec_name}")
        else:
            st.info("Hãy hoàn thành bài kiểm tra chủ đề để nhận gợi ý mới!")

    st.markdown("---")

    # ----------------------------------------------------
    # 4. DANH SÁCH CHỦ ĐỀ CHO MÔN HỌC ĐANG CHỌN
    # ----------------------------------------------------
    if selected_subject_name and current_lop is not None:
        try:
            lop_int = int(current_lop)

            topics_list = get_topics_status(hoc_sinh_id, selected_subject_name, lop_int)

            if not topics_list:
                st.warning(f"Môn '{selected_subject_name}' chưa có chủ đề nào cho Khối {current_lop}.")
                st.stop()

            st.markdown("#### Danh sách Chủ đề:")

            suggested_topic_id = latest_rec['chu_de_id'] if latest_rec else None

            # ----------------------------------------------------
            # 4.1 HIỂN THỊ KHỐI ĐỀ XUẤT AI (Nếu thuộc môn hiện tại)
            # ----------------------------------------------------
            if latest_rec:
                suggested_topic_info = get_topic_by_id(latest_rec['chu_de_id'])
                if suggested_topic_info:
                    st.markdown("##### 💡 AI Đề xuất:")
                    with st.container(border=True):
                        col_topic, col_btn = st.columns([4, 1])

                        col_topic.markdown(
                            f"**{suggested_topic_info['ten_chu_de']}** (Tuần {suggested_topic_info['tuan']})"
                        )
                        col_topic.caption(f"Hành động: {latest_rec['action']}")

                        if col_btn.button("Học ngay 🚀", key=f"start_{latest_rec['chu_de_id']}", type="primary"):
                            st.session_state['selected_topic_id'] = latest_rec['chu_de_id']
                            st.session_state['latest_suggestion_id'] = latest_rec.get("id")
                            st.session_state['viewing_topic'] = True
                            st.rerun()

                    st.divider()

            # ----------------------------------------------------
            # 4.2 DANH SÁCH CHỦ ĐỀ CÒN LẠI
            # ----------------------------------------------------
            for topic in topics_list:
                topic_id = topic['id']

                # Tránh trùng lặp: nếu đã hiển thị ở phần đề xuất AI → bỏ qua
                if topic_id == suggested_topic_id:
                    continue

                col_topic, col_status, col_btn = st.columns([3, 1, 1])

                with col_topic:
                    st.markdown(f"**{topic['ten_chu_de']}** (Tuần {topic['tuan']})")

                with col_status:
                    if topic['completed']:
                        st.success("✅ Đã HT")
                    else:
                        st.caption("Chưa HT")

                with col_btn:
                    if st.button("Học", key=f"start_{topic_id}"):
                        st.session_state['selected_topic_id'] = topic_id
                        st.session_state['latest_suggestion_id'] = None
                        st.session_state['viewing_topic'] = True
                        st.rerun()

        except Exception as e:
            st.error(f"Lỗi tải danh sách chủ đề: {e}")
