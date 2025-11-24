# File: pages/student_pages/ui_learning.py
# (BẢN FINAL: Nút Quay lại bảng điều khiển màu cam + Fix lỗi lộ đề + Tối ưu UI)

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from backend.data_service import (
    get_lessons_by_topic,
    get_videos_by_lesson,
    get_practice_exercises_by_lesson,
    get_topic_test_by_topic,
    get_topic_by_id,
    update_learning_status
)
from .ui_quiz_engine import process_and_render_practice, process_and_render_topic_test


def render_content_detail(hoc_sinh_id, current_lop):
    """
    Hiển thị CHI TIẾT NỘI DUNG (Video, PDF, Quiz) cho một Chủ đề đã được chọn.
    """

    # 1. Lấy ID chủ đề & Lớp học từ Session
    selected_topic_id = st.session_state.get('selected_topic_id')
    latest_suggestion_id = st.session_state.get('latest_suggestion_id')

    # --- QUAN TRỌNG: Lấy ID lớp cụ thể để lọc đề thi ---
    student_class_id = st.session_state.get("hoc_sinh_lop_id")
    # ---------------------------------------------------

    if not selected_topic_id:
        st.error("Lỗi: Không tìm thấy chủ đề được chọn.")
        if st.button("Quay lại bảng điều khiển", type="primary"):
            st.session_state['viewing_topic'] = False
            st.rerun()
        st.stop()

    # 2. Lấy thông tin chủ đề
    current_topic_info = get_topic_by_id(selected_topic_id)
    if not current_topic_info:
        st.error(f"Lỗi: Không thể tải thông tin cho Chủ đề ID {selected_topic_id}")
        if st.button("Quay lại bảng điều khiển", type="primary"):
            st.session_state['viewing_topic'] = False
            st.rerun()
        st.stop()

    selected_topic_name = current_topic_info.get("ten_chu_de", "N/A")
    selected_subject_name = current_topic_info.get("mon_hoc", "N/A")
    current_tuan = current_topic_info.get("tuan")

    # 3. NÚT QUAY LẠI (ĐÃ SỬA MÀU VÀ TEXT) & TIÊU ĐỀ
    if st.button("⬅️ Quay lại bảng điều khiển", type="primary"):
        st.session_state['viewing_topic'] = False
        # Xóa các state liên quan đến bài học đang xem để dọn dẹp
        keys_to_remove = ['selected_topic_id', 'latest_suggestion_id']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.title(f"{selected_subject_name} - {selected_topic_name}")
    st.markdown("---")

    # 4. CẬP NHẬT TRẠNG THÁI LỘ TRÌNH (Nếu là AI suggest)
    if latest_suggestion_id:
        try:
            update_learning_status(latest_suggestion_id, "Đang thực hiện")
            st.session_state.pop('latest_suggestion_id', None)  # Chỉ update 1 lần rồi xóa key
            st.toast("Đã cập nhật trạng thái lộ trình!")
        except Exception as e:
            pass  # Fail silently

    # 5. CHỌN BÀI HỌC
    lessons = get_lessons_by_topic(selected_topic_id)
    selected_lesson_id = None
    current_lesson_info = None

    if not lessons:
        st.warning(f"Chủ đề '{selected_topic_name}' chưa có bài học nào.")
    else:
        lesson_map = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
        # Sắp xếp tên bài học
        sorted_lesson_names = sorted(lesson_map.keys())

        selected_lesson_name = st.selectbox(
            "📖 **Chọn Bài học:**",
            sorted_lesson_names,
            key="lesson_select_detail"
        )
        selected_lesson_id = lesson_map[selected_lesson_name]
        current_lesson_info = next((l for l in lessons if str(l['id']) == selected_lesson_id), None)

    # 6. HIỂN THỊ NỘI DUNG BÀI HỌC
    if selected_lesson_id and current_lesson_info:

        # A. Video
        videos = get_videos_by_lesson(selected_lesson_id)
        if videos:
            st.subheader("▶️ Video bài giảng")
            for v in videos:
                with st.expander(f"📺 {v.get('tieu_de', 'Video')}", expanded=True):
                    if v.get('url'):
                        st.video(v['url'])
                    else:
                        st.warning("Video chưa có URL.")

        # B. PDF
        pdf_url = current_lesson_info.get("noi_dung_pdf_url")
        if pdf_url:
            st.subheader("📄 Tài liệu học tập")
            col_link, col_view = st.columns([1, 3])
            with col_link:
                st.link_button("📥 Tải xuống PDF", pdf_url, type="primary")

            with st.expander("👁️ Xem trước tài liệu", expanded=True):
                # Nhúng PDF Viewer
                viewer_url = "https://mozilla.github.io/pdf.js/web/viewer.html"
                encoded_pdf_url = urllib.parse.quote_plus(pdf_url)
                full_viewer_url = f"{viewer_url}?file={encoded_pdf_url}"
                components.html(
                    f'<iframe src="{full_viewer_url}" width="100%" height="600px" style="border: none;"></iframe>',
                    height=600
                )

        # C. Luyện tập (Bài tập nhỏ)
        st.markdown("---")
        st.subheader("✏️ Luyện tập")

        practice_exercises = get_practice_exercises_by_lesson(selected_lesson_id)

        if not practice_exercises:
            st.info("Bài học này chưa có bài luyện tập.")
        else:
            # Sắp xếp bài tập theo mức độ (Biết -> Hiểu -> Vận dụng)
            practice_exercises.sort(key=lambda x: (
                x.get('muc_do') != 'biết',
                x.get('muc_do') != 'hiểu',
                x.get('muc_do') != 'vận dụng',
                x.get('tieu_de')
            ))

            for exercise in practice_exercises:
                ex_title = exercise.get('tieu_de', 'Bài luyện tập')
                ex_muc_do = exercise.get('muc_do', 'N/A').capitalize()

                with st.expander(f"📝 {ex_title} (Mức độ: {ex_muc_do})"):
                    process_and_render_practice(
                        exercise_id=str(exercise['id']),
                        bai_hoc_id=selected_lesson_id,
                        chu_de_id=selected_topic_id,
                        current_tuan=current_tuan,
                        current_lop=current_lop,
                        hoc_sinh_id=hoc_sinh_id
                    )

    # 7. HIỂN THỊ BÀI KIỂM TRA CHỦ ĐỀ (Cuối trang)
    if selected_topic_id:
        st.markdown("---")
        st.header(f"🏁 Kiểm tra Chủ đề")

        # Gọi hàm với lop_id để tránh lộ đề lớp khác
        topic_test = get_topic_test_by_topic(selected_topic_id, lop_id=student_class_id)

        if not topic_test:
            st.info(f"Giáo viên chưa giao bài kiểm tra cho chủ đề này tại lớp của bạn.")
        else:
            test_id = str(topic_test['id'])
            test_title = topic_test.get('tieu_de', 'Bài kiểm tra')

            # Dùng expander mặc định đóng để gọn gàng
            with st.expander(f"🚀 {test_title} (Nhấn để làm bài)", expanded=False):
                process_and_render_topic_test(
                    test_id=test_id,
                    chu_de_id=selected_topic_id,
                    selected_subject_name=selected_subject_name,
                    current_tuan=current_tuan,
                    current_lop=current_lop,
                    hoc_sinh_id=hoc_sinh_id,
                    latest_suggestion_id=latest_suggestion_id
                )