# ===============================================
# 📘 Trang học sinh - students.py (Sửa lỗi chấm 0/10 + Thêm nút Làm lại)
# ===============================================
import streamlit as st
import pandas as pd
import datetime
import random
import streamlit.components.v1 as components
from backend.data_service import (
    get_student,
    get_topics_by_subject_and_class,
    get_lessons_by_topic,
    get_videos_by_lesson,
    get_practice_exercises_by_lesson,
    get_topic_test_by_topic,
    get_questions_for_exercise,
    save_test_result,
    get_student_all_results,
    get_learning_paths,
    get_topic_by_id,
    update_learning_status,
    log_learning_activity
)
from backend.recommendation_engine import generate_recommendation
from backend.supabase_client import supabase

st.set_page_config(page_title="AI Tutor - Học sinh", page_icon="📘", layout="wide")

# CSS (Giữ nguyên)
st.markdown("""
    <style>
    /* ... (CSS giữ nguyên) ... */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    div[data-testid="stHorizontalBlock"] > div:first-child > div { display: flex; flex-direction: column; align-items: center; text-align: center; }
    div[data-testid="stHorizontalBlock"] > div:first-child > div h1, div[data-testid="stHorizontalBlock"] > div:first-child > div h3 { text-align: center; }
    .student-name-title { font-family: 'Times New Roman', Times, serif; font-size: 14pt !important; font-weight: bold; color: #31333F; padding-bottom: 0.5rem; margin-block-start: 0; margin-block-end: 0; text-align: center; }
    </style>
""", unsafe_allow_html=True)

try:
    st.image("data/banner.jpg", use_container_width=True)
except Exception:
    st.image("https://via.placeholder.com/1200x200/4CAF50/FFFFFF?text=AI+Tutor+Banner", use_container_width=True)


# HÀM HỖ TRỢ (Giữ nguyên)
def logout():
    st.session_state.clear()
    st.switch_page("app.py")


# ===============================================
# ---- HÀM HỖ TRỢ MỚI CHO BÀI TẬP ----
# ===============================================
def clear_quiz_state(form_key_prefix: str, questions: list):
    """Xóa các giá trị câu trả lời và cờ 'submitted' cho một bài tập."""
    # Xóa cờ đã nộp
    submitted_key = f"submitted_{form_key_prefix}"
    if submitted_key in st.session_state:
        del st.session_state[submitted_key]

    # Xóa các câu trả lời đã lưu
    for q in questions:
        widget_key = f"{form_key_prefix}_{q['id']}"
        if widget_key in st.session_state:
            del st.session_state[widget_key]

    # st.rerun() # Không cần rerun ở đây, on_click sẽ xử lý rerun


# ===============================================
# KIỂM TRA PHIÊN ĐĂNG NHẬP (Giữ nguyên)
# ===============================================
if "hoc_sinh_id" not in st.session_state:
    st.warning("⚠️ Vui lòng đăng nhập từ trang chủ.")
    if st.button("Về trang đăng nhập"): st.switch_page("app.py")
    st.stop()

# Tải dữ liệu từ session VÀ DB (Giữ nguyên)
hoc_sinh_id = st.session_state["hoc_sinh_id"]
ho_ten = st.session_state["ho_ten"]
current_lop = st.session_state.get("lop")
current_ten_lop = st.session_state.get("ten_lop", "Chưa xếp lớp")
subject_map = st.session_state.get("subject_map", {})

student_data = get_student(hoc_sinh_id)
if not student_data:
    st.error("Không thể tải thông tin học sinh.");
    st.stop()
current_ngay_sinh_str = student_data.get("ngay_sinh");
current_ngay_sinh = None
if current_ngay_sinh_str:
    try:
        current_ngay_sinh = datetime.date.fromisoformat(current_ngay_sinh_str)
    except (ValueError, TypeError):
        pass

# BỐ CỤC 2 CỘT CHÍNH (Giữ nguyên)
col1, col2 = st.columns([1, 5])

# CỘT 1: THÔNG TIN HỌC SINH & ĐIỀU HƯỚNG (Giữ nguyên)
with col1:
    # ... (code cột 1 giữ nguyên) ...
    st.image("https://cdn-icons-png.flaticon.com/512/1144/1144760.png", width=120)
    st.markdown(f"<h1 class='student-name-title'>{ho_ten}</h1>", unsafe_allow_html=True)
    lop_display = f"Khối {current_lop}" if current_lop is not None else "Chưa có Khối"
    st.subheader(f"{lop_display} - {current_ten_lop}")
    st.divider()
    with st.expander("📝 Thay đổi thông tin"):
        with st.form("update_info_form"):
            new_ho_ten = st.text_input("Họ tên", value=ho_ten)
            new_ngay_sinh = st.date_input("Ngày sinh", value=current_ngay_sinh, min_value=datetime.date(1990, 1, 1),
                                          max_value=datetime.date.today())
            if st.form_submit_button("Lưu thông tin"):
                try:
                    update_payload = {"ho_ten": new_ho_ten,
                                      "ngay_sinh": new_ngay_sinh.isoformat() if new_ngay_sinh else None}
                    supabase.table("hoc_sinh").update(update_payload).eq("id", hoc_sinh_id).execute()
                    st.session_state["ho_ten"] = new_ho_ten;
                    st.success("Cập nhật!");
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
    with st.expander("Đổi mật khẩu"):
        with st.form("change_password_form", clear_on_submit=True):
            new_pass = st.text_input("PIN mới (4 số)", type="password", max_chars=4);
            confirm_pass = st.text_input("Xác nhận PIN", type="password", max_chars=4)
            if st.form_submit_button("Lưu thay đổi"):
                if not new_pass or len(new_pass) != 4:
                    st.error("PIN phải 4 số.")
                elif new_pass != confirm_pass:
                    st.error("Xác nhận không khớp.")
                else:
                    try:
                        supabase.table("hoc_sinh").update({"mat_khau": new_pass}).eq("id",
                                                                                     hoc_sinh_id).execute(); st.success(
                            "Đổi PIN!")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    st.divider()
    if st.button("🔓 Đăng xuất", use_container_width=True, type="primary"): logout()

# -----------------------------------------------
# CỘT 2: NỘI DUNG CHÍNH (Tabs học tập)
# -----------------------------------------------
with col2:
    st.title(f"Chào mừng bạn quay trở lại! 👋")
    st.markdown("---")

    tab_learning, tab_history = st.tabs(["💡 Bài học & Luyện tập", "📜 Lịch sử học tập"])

    # --- TAB 1: BÀI HỌC & LUYỆN TẬP ---
    with tab_learning:
        # ---- KIỂM TRA ĐIỀU KIỆN TIÊN QUYẾT (Giữ nguyên) ----
        if current_lop is None:
            st.warning(
                "⚠️ Bạn chưa được xếp vào lớp hoặc lớp của bạn chưa có thông tin Khối. Vui lòng liên hệ giáo viên.")
            st.stop()
        if not subject_map:
            st.warning(
                f"📚 Không tìm thấy môn học nào phù hợp với Khối {current_lop} của bạn. Vui lòng kiểm tra lại cấu hình môn học.")
            st.stop()
        # ---- HẾT KIỂM TRA ----

        # --- Logic tải Lộ trình AI (Giữ nguyên) ---
        default_subject_index = 0
        default_topic_index = 0
        suggestion_message = None
        suggested_topic_name_from_ai = None
        suggested_subject_name_from_ai = None
        latest_suggestion_id = None
        all_paths = get_learning_paths(hoc_sinh_id)
        latest_suggestion = None
        if all_paths:
            latest_suggestion = next((path for path in all_paths if path.get('trang_thai') == 'Chưa thực hiện'), None)
        if latest_suggestion:
            suggested_topic_id = latest_suggestion.get('chu_de_id')
            latest_suggestion_id = latest_suggestion.get('id')
            if suggested_topic_id:
                topic_details = get_topic_by_id(suggested_topic_id)
                if topic_details:
                    suggested_subject_name_from_ai = topic_details.get('mon_hoc')
                    suggested_topic_name_from_ai = topic_details.get('ten_chu_de')
                    action_vn = {'remediate': 'Học lại', 'review': 'Ôn tập', 'advance': 'Học tiếp'}.get(
                        latest_suggestion.get('loai_goi_y'), 'tiếp tục')
                    suggestion_message = f"💡 **Gợi ý từ AI:** Bạn nên **{action_vn}** chủ đề **'{suggested_topic_name_from_ai}'**."
                    subject_list_ai = list(subject_map.keys())
                    if suggested_subject_name_from_ai in subject_list_ai:
                        default_subject_index = subject_list_ai.index(suggested_subject_name_from_ai)
        if suggestion_message:
            st.info(suggestion_message)
        # --- Hết logic tải Lộ trình AI ---

        # ---- BỐ CỤC 3 CỘT CHO PHẦN CHỌN (Giữ nguyên) ----
        col_select_left, col_select_center, col_select_right = st.columns([1, 2, 1])
        selected_subject_name = None
        selected_topic_id = None
        selected_topic_name = None
        selected_lesson_id = None
        selected_lesson_name = None
        current_lesson_info = None
        current_tuan = None

        with col_select_center:
            # --- Bước 1 & 2 (Giữ nguyên) ---
            subject_list = list(subject_map.keys())
            selected_subject_name = st.selectbox("📚 **Bước 1:** Chọn Môn học:", subject_list, key="subject_select",
                                                 index=default_subject_index)
            topics_data = []
            if selected_subject_name and current_lop is not None:
                try:
                    lop_int = int(current_lop)
                    topics_data = get_topics_by_subject_and_class(selected_subject_name, lop_int)
                except Exception as e:
                    st.error(f"Lỗi tải chủ đề: {e}")
                    topics_data = []

                if not topics_data:
                    st.warning(f"Môn '{selected_subject_name}' chưa có chủ đề nào cho Khối {current_lop}.")
                else:
                    chu_de_map = {c["ten_chu_de"]: str(c["id"]) for c in topics_data}
                    topic_list = list(chu_de_map.keys())
                    current_default_topic_index = 0
                    if suggested_topic_name_from_ai and selected_subject_name == suggested_subject_name_from_ai:
                        if suggested_topic_name_from_ai in topic_list:
                            current_default_topic_index = topic_list.index(suggested_topic_name_from_ai)

                    selected_topic_name = st.selectbox("📘 **Bước 2:** Chọn Chủ đề học:", topic_list, key="topic_select",
                                                       index=current_default_topic_index)
                    selected_topic_id = chu_de_map[selected_topic_name]
                    current_topic_info = next((c for c in topics_data if str(c["id"]) == selected_topic_id), None)

                    if current_topic_info and current_topic_info.get("tuan") is not None:
                        try:
                            current_tuan = int(current_topic_info["tuan"])
                        except ValueError:
                            st.warning("Giá trị 'tuần' của chủ đề không hợp lệ.")

                    if latest_suggestion_id and selected_topic_id == latest_suggestion.get('chu_de_id'):
                        try:
                            update_learning_status(latest_suggestion_id, "Đang thực hiện")
                            st.toast("Đã cập nhật trạng thái lộ trình AI.")
                        except Exception as e:
                            st.warning(f"Lỗi cập nhật trạng thái lộ trình: {e}")

            # --- Bước 3 (Giữ nguyên) ---
            if selected_topic_id:
                lessons = get_lessons_by_topic(selected_topic_id)
                if not lessons:
                    st.warning(f"Chủ đề '{selected_topic_name}' chưa có bài học nào.")
                else:
                    lesson_map = {f"{l.get('thu_tu', 0)}. {l['ten_bai_hoc']}": str(l['id']) for l in lessons}
                    selected_lesson_name = st.selectbox("📖 **Bước 3:** Chọn Bài học:", list(lesson_map.keys()),
                                                        key="lesson_select")
                    selected_lesson_id = lesson_map[selected_lesson_name]
                    current_lesson_info = next((l for l in lessons if str(l['id']) == selected_lesson_id), None)

            st.markdown("---")

        # ---- HIỂN THỊ NỘI DUNG (Video, PDF) (Giữ nguyên) ----
        if selected_lesson_id and current_lesson_info:
            st.markdown(f"## {selected_lesson_name}")
            # ... (Code hiển thị Video và PDF giữ nguyên) ...
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
                viewer_url = "https.://mozilla.github.io/pdf.js/web/viewer.html"
                import urllib.parse

                encoded_pdf_url = urllib.parse.quote_plus(pdf_url)
                full_viewer_url = f"{viewer_url}?file={encoded_pdf_url}"
                try:
                    components.html(
                        f'<iframe src="{full_viewer_url}" width="100%" height="600px" style="border: none;"></iframe>',
                        height=610, scrolling=True)
                except Exception as e:
                    st.warning(f"Không thể nhúng PDF viewer: {e}. Vui lòng tải về.")

            # ===============================================
            # ---- PHẦN LUYỆN TẬP (ĐÃ SỬA LỖI CHẤM ĐIỂM + LÀM LẠI) ----
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
                    exercise_id = str(exercise['id'])
                    muc_do_display = f" (Mức độ: {exercise.get('muc_do', 'N/A').capitalize()})"
                    exercise_title = f"📝 **{exercise.get('tieu_de', f'Bài luyện tập {exercise_id[:6]}')}{muc_do_display}**"

                    with st.expander(exercise_title, expanded=False):
                        questions = get_questions_for_exercise(exercise_id)
                        if not questions:
                            st.caption("Chưa có câu hỏi cho bài tập này.")
                            continue

                            # ---- LOGIC TÁCH BIỆT KẾT QUẢ VÀ FORM ----
                        form_key_prefix = f"practice_{exercise_id}"
                        submitted_key = f"submitted_{form_key_prefix}"

                        # 1. HIỂN THỊ KẾT QUẢ VÀ NÚT LÀM LẠI (nếu đã nộp)
                        if st.session_state.get(submitted_key, False):
                            st.markdown("#### Kết quả của bạn:")
                            correct = 0
                            total_points = 0.0
                            earned_points = 0.0

                            for q in questions:
                                widget_key = f"{form_key_prefix}_{q['id']}"
                                ans = st.session_state.get(widget_key)
                                true_ans_list = q["dap_an_dung"]  # Đây là list[str] từ data_service

                                total_points += (q["diem_so"] or 1)
                                is_correct = False

                                # Logic chấm (chuỗi vs chuỗi)
                                if q["loai_cau_hoi"] == "mot_lua_chon":
                                    if ans is not None and true_ans_list:
                                        is_correct = (ans == true_ans_list[0])
                                elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                    if ans and true_ans_list:
                                        is_correct = (set(ans) == set(true_ans_list))
                                else:  # dien_khuyet
                                    if ans and true_ans_list:
                                        true_ans_str_list = [t.lower() for t in true_ans_list]
                                        is_correct = (ans.strip().lower() in true_ans_str_list)

                                if is_correct:
                                    correct += 1
                                    earned_points += (q["diem_so"] or 1)

                            score = round(earned_points / total_points * 10, 2) if total_points > 0 else 0
                            st.success(f"🎯 Kết quả: **{score}/10** ({correct}/{len(questions)} đúng)")

                            # Gợi ý vi mô
                            if score < 7.0:
                                st.warning(
                                    "🤔 Kết quả chưa tốt! Bạn nên xem lại Video và Tài liệu PDF của bài học này trước khi tiếp tục.")
                            else:
                                st.success("🎉 Bạn làm tốt lắm! Hãy chuyển sang bài học tiếp theo (nếu có).")

                            # Nút Làm lại
                            st.button(
                                "🔄 Làm lại bài",
                                key=f"redo_{form_key_prefix}",
                                on_click=clear_quiz_state,
                                args=(form_key_prefix, questions)
                            )
                            st.markdown("---")  # Phân cách kết quả với form

                        # 2. HIỂN THỊ FORM (luôn hiển thị, giữ nguyên lựa chọn)
                        with st.form(f"form_{form_key_prefix}", clear_on_submit=False):
                            for i, q in enumerate(questions):
                                q_id_str = str(q['id'])
                                widget_key = f"{form_key_prefix}_{q_id_str}"
                                st.markdown(f"**Câu {i + 1} ({q['diem_so']} điểm):** {q['noi_dung']}")

                                # Lấy tất cả tùy chọn (đã là list[str])
                                all_options = q["dap_an_dung"] + q.get("lua_chon", [])
                                random.shuffle(all_options)

                                if q["loai_cau_hoi"] == "mot_lua_chon":
                                    st.radio("Chọn:", all_options, key=widget_key,
                                             index=None if widget_key not in st.session_state else all_options.index(
                                                 st.session_state[widget_key]) if st.session_state[
                                                                                      widget_key] in all_options else None)
                                elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                    st.multiselect("Chọn:", all_options, key=widget_key,
                                                   default=st.session_state.get(widget_key, []))
                                else:
                                    st.text_input("Điền:", key=widget_key, value=st.session_state.get(widget_key, ""))

                            submitted_practice = st.form_submit_button("📤 Nộp bài luyện tập")

                            if submitted_practice:
                                # Đánh dấu là đã nộp
                                st.session_state[submitted_key] = True

                                # Tính điểm chỉ để LƯU CSDL (logic chấm y hệt như trên)
                                correct_submit = 0;
                                total_points_submit = 0.0;
                                earned_points_submit = 0.0
                                suggestion_text_submit = ""
                                for q in questions:
                                    widget_key = f"{form_key_prefix}_{q['id']}";
                                    ans = st.session_state.get(widget_key);
                                    true_ans_list = q["dap_an_dung"]
                                    total_points_submit += (q["diem_so"] or 1);
                                    is_correct_submit = False
                                    if q["loai_cau_hoi"] == "mot_lua_chon":
                                        if ans is not None and true_ans_list: is_correct_submit = (
                                                    ans == true_ans_list[0])
                                    elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                        if ans and true_ans_list: is_correct_submit = (set(ans) == set(true_ans_list))
                                    else:
                                        if ans and true_ans_list: true_ans_str_list = [t.lower() for t in
                                                                                       true_ans_list]; is_correct_submit = (
                                                    ans.strip().lower() in true_ans_str_list)
                                    if is_correct_submit: correct_submit += 1; earned_points_submit += (
                                                q["diem_so"] or 1)
                                score_submit = round(earned_points_submit / total_points_submit * 10,
                                                     2) if total_points_submit > 0 else 0

                                # Lấy text gợi ý
                                if score_submit < 7.0:
                                    suggestion_text_submit = "Kết quả chưa tốt! Bạn nên xem lại Video và Tài liệu PDF của bài học này trước khi tiếp tục."
                                else:
                                    suggestion_text_submit = "Bạn làm tốt lắm! Hãy chuyển sang bài học tiếp theo (nếu có)."

                                # Lưu CSDL
                                if current_tuan is not None and current_lop is not None:
                                    try:
                                        save_test_result(hoc_sinh_id=hoc_sinh_id, bai_tap_id=exercise_id,
                                                         chu_de_id=selected_topic_id, diem=score_submit,
                                                         so_cau_dung=correct_submit, tong_cau=len(questions),
                                                         tuan_kiem_tra=current_tuan, lop=int(current_lop))
                                        log_learning_activity(hoc_sinh_id=hoc_sinh_id, hanh_dong="xem_goi_y_luyen_tap",
                                                              noi_dung=suggestion_text_submit,
                                                              chu_de_id=selected_topic_id,
                                                              bai_hoc_id=selected_lesson_id)
                                    except Exception as e:
                                        st.error(f"Lỗi lưu KQ/Log: {e}")
                                else:
                                    st.warning("Thiếu thông tin Tuần hoặc Lớp để lưu kết quả.")

                                # Rerun để hiển thị kết quả
                                st.rerun()
            # ===============================================
            # ---- KẾT THÚC PHẦN LUYỆN TẬP ----
            # ===============================================

        # ---- HIỂN THỊ BÀI KIỂM TRA CHỦ ĐỀ (ĐÃ SỬA LỖI CHẤM ĐIỂM + LÀM LẠI) ----
        if selected_topic_id:
            st.markdown("---")
            st.header(f"🏁 Kiểm tra Chủ đề: {selected_topic_name}")
            topic_test = get_topic_test_by_topic(selected_topic_id)
            if not topic_test:
                st.info(f"Chủ đề '{selected_topic_name}' chưa có bài kiểm tra.")
            else:
                test_title = f"📝 **{topic_test.get('tieu_de', f'Kiểm tra {selected_topic_name}')}**"
                with st.expander(test_title, expanded=True):
                    test_id = str(topic_test['id'])
                    test_questions = get_questions_for_exercise(test_id)
                    if not test_questions:
                        st.warning("Bài kiểm tra chưa có câu hỏi.")
                    else:
                        # ---- LOGIC TÁCH BIỆT KẾT QUẢ VÀ FORM ----
                        form_key_prefix_test = f"test_{test_id}"
                        submitted_key_test = f"submitted_{form_key_prefix_test}"

                        # 1. HIỂN THỊ KẾT QUẢ VÀ NÚT LÀM LẠI (nếu đã nộp)
                        if st.session_state.get(submitted_key_test, False):
                            st.markdown("#### Kết quả của bạn:")
                            correct_test = 0;
                            total_points_test = 0.0;
                            earned_points_test = 0.0

                            for q in test_questions:
                                widget_key = f"{form_key_prefix_test}_{q['id']}"
                                ans = st.session_state.get(widget_key)
                                true_ans_list = q["dap_an_dung"]  # list[str]
                                total_points_test += (q["diem_so"] or 1)
                                is_correct = False
                                if q["loai_cau_hoi"] == "mot_lua_chon":
                                    if ans is not None and true_ans_list: is_correct = (ans == true_ans_list[0])
                                elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                    if ans and true_ans_list: is_correct = (set(ans) == set(true_ans_list))
                                else:
                                    if ans and true_ans_list: true_ans_str_list = [t.lower() for t in
                                                                                   true_ans_list]; is_correct = (
                                                ans.strip().lower() in true_ans_str_list)
                                if is_correct: correct_test += 1; earned_points_test += (q["diem_so"] or 1)

                            score_test = round(earned_points_test / total_points_test * 10,
                                               2) if total_points_test > 0 else 0
                            st.success(f"🎯 Kết quả KT: **{score_test}/10** ({correct_test}/{len(test_questions)} đúng)")

                            # Nút Làm lại
                            st.button(
                                "🔄 Làm lại bài kiểm tra",
                                key=f"redo_{form_key_prefix_test}",
                                on_click=clear_quiz_state,
                                args=(form_key_prefix_test, test_questions)
                            )
                            st.markdown("---")  # Phân cách kết quả với form

                        # 2. HIỂN THỊ FORM
                        with st.form(f"form_{form_key_prefix_test}", clear_on_submit=False):
                            for i, q in enumerate(test_questions):
                                q_id_str = str(q['id'])
                                widget_key = f"{form_key_prefix_test}_{q_id_str}"
                                st.markdown(f"**Câu {i + 1} ({q['diem_so']} điểm):** {q['noi_dung']}")
                                all_options = [str(opt) for opt in (q["dap_an_dung"] + q.get("lua_chon", []))]
                                random.shuffle(all_options)

                                if q["loai_cau_hoi"] == "mot_lua_chon":
                                    st.radio("Chọn:", all_options, key=widget_key,
                                             index=None if widget_key not in st.session_state else all_options.index(
                                                 st.session_state[widget_key]) if st.session_state[
                                                                                      widget_key] in all_options else None)
                                elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                    st.multiselect("Chọn:", all_options, key=widget_key,
                                                   default=st.session_state.get(widget_key, []))
                                else:
                                    st.text_input("Điền:", key=widget_key, value=st.session_state.get(widget_key, ""))

                            submitted_test = st.form_submit_button("📤 Nộp bài kiểm tra")

                            if submitted_test:
                                # Đánh dấu là đã nộp
                                st.session_state[submitted_key_test] = True

                                # Tính điểm chỉ để LƯU CSDL và GỌI AI
                                correct_submit_test = 0;
                                total_points_submit_test = 0.0;
                                earned_points_submit_test = 0.0
                                for q in test_questions:
                                    widget_key = f"{form_key_prefix_test}_{q['id']}";
                                    ans = st.session_state.get(widget_key);
                                    true_ans_list = q["dap_an_dung"]
                                    total_points_submit_test += (q["diem_so"] or 1);
                                    is_correct_submit_test = False
                                    if q["loai_cau_hoi"] == "mot_lua_chon":
                                        if ans is not None and true_ans_list: is_correct_submit_test = (
                                                    ans == true_ans_list[0])
                                    elif q["loai_cau_hoi"] == "nhieu_lua_chon":
                                        if ans and true_ans_list: is_correct_submit_test = (
                                                    set(ans) == set(true_ans_list))
                                    else:
                                        if ans and true_ans_list: true_ans_str_list = [t.lower() for t in
                                                                                       true_ans_list]; is_correct_submit_test = (
                                                    ans.strip().lower() in true_ans_str_list)
                                    if is_correct_submit_test: correct_submit_test += 1; earned_points_submit_test += (
                                                q["diem_so"] or 1)
                                score_submit_test = round(earned_points_submit_test / total_points_submit_test * 10,
                                                          2) if total_points_submit_test > 0 else 0

                                # Gọi AI và xử lý gợi ý
                                if current_tuan is not None and current_lop is not None:
                                    try:
                                        lop_int_kt = int(current_lop)
                                        save_test_result(hoc_sinh_id=hoc_sinh_id, bai_tap_id=test_id,
                                                         chu_de_id=selected_topic_id, diem=score_submit_test,
                                                         so_cau_dung=correct_submit_test, tong_cau=len(test_questions),
                                                         tuan_kiem_tra=current_tuan, lop=lop_int_kt)

                                        # Chỉ hiển thị gợi ý AI sau khi nộp bài KT
                                        st.markdown("---");
                                        st.subheader("💡 Gợi ý AI")
                                        rec_data = generate_recommendation(hoc_sinh_id=hoc_sinh_id,
                                                                           chu_de_id=selected_topic_id,
                                                                           diem=score_submit_test, lop=lop_int_kt,
                                                                           tuan=current_tuan)
                                        if latest_suggestion_id:
                                            try:
                                                update_learning_status(latest_suggestion_id, "Đã hoàn thành")
                                            except Exception as e:
                                                st.warning(f"Lỗi cập nhật trạng thái gợi ý cũ: {e}")
                                        if rec_data:
                                            st.info(
                                                f"Hệ thống: **{rec_data['action']}** (Mô hình: {rec_data['model']}, Conf: {rec_data['confidence']:.2f})")
                                            chu_de_de_xuat_id = rec_data.get("suggested_topic_id")
                                            ten_chu_de_de_xuat = selected_topic_name
                                            if chu_de_de_xuat_id:
                                                topic_suggested_info = get_topic_by_id(chu_de_de_xuat_id)
                                                if topic_suggested_info: ten_chu_de_de_xuat = topic_suggested_info[
                                                    "ten_chu_de"]
                                            if rec_data["action"] == "advance":
                                                st.success(f"🎉 **Gợi ý:** Học chủ đề **{ten_chu_de_de_xuat}**.")
                                            elif rec_data["action"] == "review":
                                                st.warning(f"🤔 **Gợi ý:** Ôn tập **{selected_topic_name}**.")
                                            elif rec_data["action"] == "remediate":
                                                if chu_de_de_xuat_id != selected_topic_id:
                                                    st.error(
                                                        f"⚠️ **Gợi ý:** Học lại tiền đề: **{ten_chu_de_de_xuat}**.")
                                                else:
                                                    st.error(f"⚠️ **Gợi ý:** Học lại **{selected_topic_name}**.")
                                        else:
                                            st.error("Không thể tạo gợi ý AI.")
                                    except Exception as e:
                                        st.error(f"Lỗi xử lý điểm/gọi AI: {e}")
                                else:
                                    st.warning("Thiếu thông tin Tuần hoặc Lớp để lưu KQ & gợi ý AI.")

                                # Rerun để hiển thị kết quả và gợi ý
                                st.rerun()

    # --- TAB 2: LỊCH SỬ HỌC TẬP (Giữ nguyên) ---
    with tab_history:
        # ... (code tab lịch sử giữ nguyên) ...
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
            st.dataframe(df_display, use_container_width=True, hide_index=True)
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
            st.dataframe(pd.DataFrame(df_paths_processed), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có lộ trình học nào.")