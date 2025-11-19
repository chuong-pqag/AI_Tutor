# File: pages/student_pages/ui_learning.py
# (CẬP NHẬT GIAI ĐOẠN 3 - THU GỌN QUIZ)

import streamlit as st
import streamlit.components.v1 as components
from backend.data_service import get_topics_by_subject_and_class, get_lessons_by_topic, get_videos_by_lesson, \
    get_practice_exercises_by_lesson, get_topic_test_by_topic, get_topic_by_id, update_learning_status
from .ui_quiz_engine import process_and_render_practice, process_and_render_topic_test
import urllib.parse  # Thêm import này


def render_content_detail(hoc_sinh_id, current_lop):
    """
    Hiển thị CHI TIẾT NỘI DUNG (Video, PDF, Quiz) cho một Chủ đề đã được chọn.
    """

    # Lấy ID chủ đề đã được Dashboard lưu vào session
    selected_topic_id = st.session_state.get('selected_topic_id')
    latest_suggestion_id = st.session_state.get('latest_suggestion_id')  # Lấy ID lộ trình

    if not selected_topic_id:
        st.error("Lỗi: Không tìm thấy chủ đề được chọn.")
        if st.button("Quay lại Dashboard"):
            st.session_state['viewing_topic'] = False
            st.rerun()
        st.stop()

    # Lấy thông tin chủ đề
    current_topic_info = get_topic_by_id(selected_topic_id)
    if not current_topic_info:
        st.error(f"Lỗi: Không thể tải thông tin cho Chủ đề ID {selected_topic_id}")
        if st.button("Quay lại Dashboard"):
            st.session_state['viewing_topic'] = False
            st.rerun()
        st.stop()

    selected_topic_name = current_topic_info.get("ten_chu_de", "N/A")
    selected_subject_name = current_topic_info.get("mon_hoc", "N/A")
    current_tuan = current_topic_info.get("tuan")

    # ---- NÚT QUAY LẠI ----
    if st.button("⬅️ Quay lại Dashboard"):
        st.session_state['viewing_topic'] = False
        st.session_state.pop('selected_topic_id', None)  # Xóa ID đã chọn
        st.session_state.pop('latest_suggestion_id', None)
        st.rerun()

    st.title(f"{selected_subject_name} - {selected_topic_name}")
    st.markdown("---")

    # --- Cập nhật trạng thái lộ trình (Nếu đây là gợi ý AI) ---
    if latest_suggestion_id:
        try:
            # Đánh dấu là "Đang thực hiện"
            update_learning_status(latest_suggestion_id, "Đang thực hiện")
            # Clear ID để không bị gọi lại
            st.session_state.pop('latest_suggestion_id', None)
            st.toast("Đã cập nhật lộ trình học!")
        except Exception as e:
            st.warning(f"Lỗi cập nhật trạng thái lộ trình: {e}")

    # --- Bước 3 (cũ): Chọn Bài học (Giữ nguyên) ---
    lessons = get_lessons_by_topic(selected_topic_id)
    selected_lesson_id = None
    current_lesson_info = None

    if not lessons:
        st.warning(f"Chủ đề '{selected_topic_name}' chưa có bài học nào.")
    else:
        lesson_map = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
        selected_lesson_name = st.selectbox("📖 **Bước 1:** Chọn Bài học:", list(lesson_map.keys()),
                                            key="lesson_select_detail")
        selected_lesson_id = lesson_map[selected_lesson_name]
        current_lesson_info = next((l for l in lessons if str(l['id']) == selected_lesson_id), None)

    # ---- HIỂN THỊ NỘI DUNG (Video, PDF) (Giữ nguyên) ----
    if selected_lesson_id and current_lesson_info:
        st.markdown(f"## {selected_lesson_name}")

        videos = get_videos_by_lesson(selected_lesson_id)
        if videos:
            st.subheader("▶️ Video")
            for v in videos:
                video_url = v.get('url')
                if video_url:
                    try:
                        st.video(video_url)
                    except Exception as e:
                        st.error(f"Lỗi khi hiển thị video từ URL: {video_url} - Lỗi: {e}")
                else:
                    st.warning(f"Video '{v.get('tieu_de', 'Không có tiêu đề')}' thiếu URL.")

        pdf_url = current_lesson_info.get("noi_dung_pdf_url")
        if pdf_url:
            st.subheader("📄 Tài liệu");
            st.link_button("📥 Tải xuống PDF", pdf_url, type="primary")

            viewer_url = "https://mozilla.github.io/pdf.js/web/viewer.html"
            encoded_pdf_url = urllib.parse.quote_plus(pdf_url)
            full_viewer_url = f"{viewer_url}?file={encoded_pdf_url}"
            try:
                components.html(
                    f'<iframe src="{full_viewer_url}" width="100%" height="600px" style="border: none;"></iframe>',
                    height=610, scrolling=True)
            except Exception as e:
                st.warning(f"Không thể nhúng PDF viewer: {e}. Vui lòng tải về.")

        # ===============================================
        # ---- (ĐÃ CẬP NHẬT) PHẦN LUYỆN TẬP (st.expander) ----
        # ===============================================
        st.markdown("---");
        st.subheader("✏️ Luyện tập")
        practice_exercises = get_practice_exercises_by_lesson(selected_lesson_id)
        if not practice_exercises:
            st.info("Bài học này chưa có bài luyện tập.")
        else:
            practice_exercises.sort(key=lambda x: (
                x.get('muc_do') != 'biết', x.get('muc_do') != 'hiểu', x.get('muc_do') != 'vận dụng', x.get('tieu_de')))

            for exercise in practice_exercises:
                # Lấy thông tin cho tiêu đề expander
                ex_title = exercise.get('tieu_de', 'Bài luyện tập')
                ex_muc_do = exercise.get('muc_do', 'N/A')

                # Bọc mỗi bài luyện tập trong một expander
                with st.expander(f"✏️ Luyện tập: {ex_title} (Mức độ: {ex_muc_do})"):
                    process_and_render_practice(
                        exercise_id=str(exercise['id']),
                        bai_hoc_id=selected_lesson_id,
                        chu_de_id=selected_topic_id,
                        current_tuan=current_tuan,
                        current_lop=current_lop,
                        hoc_sinh_id=hoc_sinh_id
                    )

    # ---- (ĐÃ CẬP NHẬT) HIỂN THỊ BÀI KIỂM TRA CHỦ ĐỀ (expanded=False) ----
    if selected_topic_id:
        st.markdown("---")
        st.header(f"🏁 Kiểm tra Chủ đề: {selected_topic_name}")
        topic_test = get_topic_test_by_topic(selected_topic_id)
        if not topic_test:
            st.info(f"Chủ đề '{selected_topic_name}' chưa có bài kiểm tra.")
        else:
            test_id = str(topic_test['id'])
            test_title = f"📝 **{topic_test.get('tieu_de', f'Kiểm tra {selected_topic_name}')}** (Nhấp để làm)"

            # Đặt expanded=False để thu gọn mặc định
            with st.expander(test_title, expanded=False):
                process_and_render_topic_test(
                    test_id=test_id,
                    chu_de_id=selected_topic_id,
                    selected_subject_name=selected_subject_name,
                    current_tuan=current_tuan,
                    current_lop=current_lop,
                    hoc_sinh_id=hoc_sinh_id,
                    # Chuyển ID lộ trình gốc (nếu có) để Quiz Engine cập nhật sau khi nộp
                    latest_suggestion_id=st.session_state.get('latest_suggestion_id_for_test', latest_suggestion_id)
                )