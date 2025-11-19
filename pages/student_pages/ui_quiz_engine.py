# File: pages/student_pages/ui_quiz_engine.py
# (CẬP NHẬT: Fix lỗi hiển thị Loa - So sánh an toàn Khối lớp)

import streamlit as st
from backend.data_service import get_questions_for_exercise, save_test_result, log_learning_activity, get_topic_by_id, \
    update_learning_status
from backend.recommendation_engine import generate_recommendation
import random
import time
from datetime import datetime


# Hàm hỗ trợ xóa trạng thái quiz (Giữ nguyên)
def clear_quiz_state(form_key_prefix: str, questions: list):
    submitted_key = f"submitted_{form_key_prefix}"
    if submitted_key in st.session_state:
        del st.session_state[submitted_key]
    if "show_test_result" in st.session_state:
        del st.session_state["show_test_result"]
    for q in questions:
        widget_key = f"{form_key_prefix}_{q['id']}"
        if widget_key in st.session_state:
            del st.session_state[widget_key]
        if f"{widget_key}_radio" in st.session_state:
            del st.session_state[f"{widget_key}_radio"]


# Hàm chấm điểm (Giữ nguyên)
def calculate_detailed_scores(questions, form_key_prefix):
    scores = {
        'correct': 0, 'total_points': 0.0, 'earned_points': 0.0,
        'earned_biet': 0.0, 'earned_hieu': 0.0, 'earned_van_dung': 0.0,
        'total_biet': 0.0, 'total_hieu': 0.0, 'total_van_dung': 0.0
    }
    for q in questions:
        widget_key = f"{form_key_prefix}_{q['id']}"
        ans = st.session_state.get(widget_key)
        true_ans_list = q["dap_an_dung"]
        diem_cau_hoi = (q["diem_so"] or 1)
        scores['total_points'] += diem_cau_hoi
        is_correct = False
        muc_do = q.get("muc_do", "biết")

        if muc_do == "biết":
            scores['total_biet'] += diem_cau_hoi
        elif muc_do == "hiểu":
            scores['total_hieu'] += diem_cau_hoi
        elif muc_do == "vận dụng":
            scores['total_van_dung'] += diem_cau_hoi

        loai_cau_hoi_check = q.get("loai_cau_hoi", "mot_lua_chon")

        if loai_cau_hoi_check.startswith("mot_lua_chon"):
            if ans is not None and true_ans_list: is_correct = (ans == true_ans_list[0])
        elif loai_cau_hoi_check.startswith("nhieu_lua_chon"):
            if ans and true_ans_list: is_correct = (set(ans) == set(true_ans_list))
        else:  # dien_khuyet
            if ans and true_ans_list: true_ans_str_list = [t.lower() for t in true_ans_list]; is_correct = (
                        str(ans).strip().lower() in true_ans_str_list)

        if is_correct:
            scores['correct'] += 1
            scores['earned_points'] += diem_cau_hoi
            if muc_do == "biết":
                scores['earned_biet'] += diem_cau_hoi
            elif muc_do == "hiểu":
                scores['earned_hieu'] += diem_cau_hoi
            elif muc_do == "vận dụng":
                scores['earned_van_dung'] += diem_cau_hoi

    return scores


def is_image_url(text: str):
    """Kiểm tra đơn giản xem text có phải là URL hình ảnh không."""
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    return text_lower.startswith("http") and (
            text_lower.endswith(".png") or
            text_lower.endswith(".jpg") or
            text_lower.endswith(".jpeg") or
            text_lower.endswith(".gif")
    )


# =========================================================================
# (ĐÃ SỬA LỖI) HÀM RENDER WIDGET
# =========================================================================
def render_question_widget(q, widget_key, current_lop):
    """
    Hàm helper để render (hiển thị) câu hỏi và widget đáp án
    """

    loai_cau_hoi = q.get("loai_cau_hoi", "mot_lua_chon")

    # 1. RENDER CÂU HỎI (NỘI DUNG)
    question_text = f"**Câu {q['index'] + 1} ({q['diem_so']} điểm):**"

    if is_image_url(q["noi_dung"]):
        st.markdown(question_text)
        st.image(q["noi_dung"], width=400)
    else:
        st.markdown(f"{question_text} {q['noi_dung']}")

    # -----------------------------------------------
    # (FIX) Kiểm tra an toàn để hiển thị TTS (Loa)
    # -----------------------------------------------
    try:
        # Chuyển đổi current_lop sang số nguyên để so sánh
        lop_int = int(current_lop) if current_lop is not None else 0
    except:
        lop_int = 0

    # Chỉ hiển thị nếu là Lớp 1 VÀ có link Audio
    if lop_int == 1 and q.get('audio_url'):
        st.audio(q['audio_url'], format="audio/mp3", start_time=0)
    # -----------------------------------------------

    # 2. CHUẨN BỊ OPTIONS (ĐÁP ÁN)
    all_options = q["dap_an_dung"] + q.get("lua_chon", [])
    if not all_options:
        if loai_cau_hoi != "dien_khuyet":
            # st.error("Lỗi: Câu hỏi trắc nghiệm này không có đáp án nào.") # Ẩn lỗi để UI sạch hơn
            pass
        all_options = []

    random.shuffle(all_options)

    # 3. RENDER WIDGET ĐÁP ÁN
    is_image_answer = False
    if all_options:
        is_image_answer = is_image_url(all_options[0])

    # ---- Trường hợp 1: Đáp án là HÌNH ẢNH (Dùng Markdown) ----
    if is_image_answer and loai_cau_hoi.startswith("mot_lua_chon"):
        options_map = {f"![img]({url}?width=150)": url for url in all_options}

        current_url_value = st.session_state.get(widget_key)
        default_md_key = None
        if current_url_value:
            default_md_key = next((md for md, url in options_map.items() if url == current_url_value), None)

        options_md_list = list(options_map.keys())
        default_index = options_md_list.index(default_md_key) if default_md_key else None

        proxy_key = f"{widget_key}_radio"
        selected_md = st.radio(
            "Chọn (Click vào hình):",
            options_md_list,
            key=proxy_key,
            index=default_index,
            format_func=lambda md: md
        )

        if selected_md:
            st.session_state[widget_key] = options_map[selected_md]

    # ---- Trường hợp 2: Đáp án là TEXT ----
    elif not is_image_answer and loai_cau_hoi == "mot_lua_chon":
        st.radio("Chọn:", all_options, key=widget_key,
                 index=None if widget_key not in st.session_state else all_options.index(
                     st.session_state[widget_key]) if st.session_state.get(widget_key) in all_options else None)

    elif not is_image_answer and loai_cau_hoi == "nhieu_lua_chon":
        st.multiselect("Chọn:", all_options, key=widget_key,
                       default=st.session_state.get(widget_key, []))

    # ---- Trường hợp 3: Điền khuyết ----
    elif loai_cau_hoi == "dien_khuyet":
        st.text_input("Điền:", key=widget_key,
                      value=st.session_state.get(widget_key, ""))

    else:
        if all_options: st.error(f"Lỗi: Không hỗ trợ loại câu hỏi {loai_cau_hoi} với đáp án hình ảnh.")


# =========================================================================
# HÀM CHÍNH 1: process_and_render_practice
# =========================================================================
def process_and_render_practice(exercise_id, bai_hoc_id, chu_de_id, current_tuan, current_lop, hoc_sinh_id):
    questions = get_questions_for_exercise(exercise_id)
    if not questions:
        st.caption("Chưa có câu hỏi cho bài tập này.")
        return

    form_key_prefix = f"practice_{exercise_id}"
    submitted_key = f"submitted_{form_key_prefix}"

    # 1. HIỂN THỊ KẾT QUẢ (nếu đã nộp)
    if st.session_state.get(submitted_key, False):
        st.markdown("#### Kết quả của bạn:")
        scores = calculate_detailed_scores(questions, form_key_prefix)
        score_10 = round(scores['earned_points'] / scores['total_points'] * 10, 2) if scores['total_points'] > 0 else 0
        st.success(f"🎯 Kết quả: **{score_10}/10** ({scores['correct']}/{len(questions)} đúng)")
        if score_10 < 7.0:
            st.warning("🤔 Kết quả chưa tốt! Bạn nên xem lại Video và Tài liệu PDF của bài học này.")
        else:
            st.success("🎉 Bạn làm tốt lắm! Hãy chuyển sang bài học tiếp theo (nếu có).")
        st.button("🔄 Làm lại bài", key=f"redo_{form_key_prefix}", on_click=clear_quiz_state,
                  args=(form_key_prefix, questions))
        st.markdown("---")

    # 2. HIỂN THỊ FORM
    with st.form(f"form_{form_key_prefix}", clear_on_submit=False):
        for i, q in enumerate(questions):
            q['index'] = i
            widget_key = f"{form_key_prefix}_{q['id']}"
            render_question_widget(q, widget_key, current_lop)  # <-- GỌI HÀM ĐÃ FIX

        submitted_practice = st.form_submit_button("📤 Nộp bài luyện tập")

        if submitted_practice:
            st.session_state[submitted_key] = True
            scores = calculate_detailed_scores(questions, form_key_prefix)
            score_submit = round(scores['earned_points'] / scores['total_points'] * 10, 2) if scores[
                                                                                                  'total_points'] > 0 else 0
            suggestion_text_submit = "Hoàn thành Luyện tập."
            if score_submit < 7.0:
                suggestion_text_submit = "Kết quả luyện tập chưa tốt, cần xem lại video/PDF."

            if current_tuan is not None and current_lop is not None:
                try:
                    save_test_result(
                        hoc_sinh_id=hoc_sinh_id, bai_tap_id=exercise_id,
                        chu_de_id=chu_de_id, diem=score_submit,
                        so_cau_dung=scores['correct'], tong_cau=len(questions),
                        tuan_kiem_tra=current_tuan, lop=int(current_lop),
                        diem_biet=scores['earned_biet'], diem_hieu=scores['earned_hieu'],
                        diem_van_dung=scores['earned_van_dung'],
                        tong_diem_biet=scores['total_biet'], tong_diem_hieu=scores['total_hieu'],
                        tong_diem_van_dung=scores['total_van_dung']
                    )
                    log_learning_activity(hoc_sinh_id=hoc_sinh_id, hanh_dong="xem_goi_y_luyen_tap",
                                          noi_dung=suggestion_text_submit,
                                          chu_de_id=chu_de_id,
                                          bai_hoc_id=bai_hoc_id)
                except Exception as e:
                    st.error(f"Lỗi lưu KQ/Log: {e}")
            st.rerun()


# =========================================================================
# HÀM CHÍNH 2: process_and_render_topic_test
# =========================================================================
def process_and_render_topic_test(test_id, chu_de_id, selected_subject_name, current_tuan, current_lop, hoc_sinh_id,
                                  latest_suggestion_id):
    questions = get_questions_for_exercise(test_id)
    if not questions:
        st.warning("Bài kiểm tra chưa có câu hỏi.")
        return

    form_key_prefix_test = f"test_{test_id}"
    submitted_key_test = f"submitted_{form_key_prefix_test}"

    # 1. HIỂN THỊ KẾT QUẢ (Logic hiển thị giữ nguyên)
    if st.session_state.get(submitted_key_test, False):
        if "show_test_result" in st.session_state:
            result = st.session_state["show_test_result"]
            st.markdown("#### Kết quả của bạn:")
            st.success(f"🎯 Kết quả KT: **{result['score']}/10** ({result['correct']}/{result['total']} đúng)")
            st.markdown("---")
            st.subheader("💡 Gợi ý AI")
            if result["action_text"]: st.info(result["action_text"])
            for msg in result["messages"]:
                if msg["type"] == "success":
                    st.success(msg["text"], icon="🎉")
                elif msg["type"] == "warning":
                    st.warning(msg["text"], icon="🤔")
                elif msg["type"] == "error":
                    st.error(msg["text"], icon="⚠️")
        st.button("🔄 Làm lại bài kiểm tra", key=f"redo_{form_key_prefix_test}", on_click=clear_quiz_state,
                  args=(form_key_prefix_test, questions))
        st.markdown("---")

    # 2. HIỂN THỊ FORM
    with st.form(f"form_{form_key_prefix_test}", clear_on_submit=False):
        for i, q in enumerate(questions):
            q['index'] = i
            widget_key = f"{form_key_prefix_test}_{q['id']}"
            render_question_widget(q, widget_key, current_lop)  # <-- GỌI HÀM ĐÃ FIX

        submitted_test = st.form_submit_button("📤 Nộp bài kiểm tra")

        if submitted_test:
            st.session_state[submitted_key_test] = True

            scores = calculate_detailed_scores(questions, form_key_prefix_test)
            score_submit_test = round(scores['earned_points'] / scores['total_points'] * 10, 2) if scores[
                                                                                                       'total_points'] > 0 else 0

            st.session_state["show_test_result"] = {
                "score": score_submit_test,
                "correct": scores['correct'],
                "total": len(questions),
                "messages": [],
                "action_text": ""
            }

            if current_tuan is not None and current_lop is not None and selected_subject_name is not None:
                try:
                    lop_int_kt = int(current_lop)

                    save_test_result(
                        hoc_sinh_id=hoc_sinh_id, bai_tap_id=test_id,
                        chu_de_id=chu_de_id, diem=score_submit_test,
                        so_cau_dung=scores['correct'], tong_cau=len(questions),
                        tuan_kiem_tra=current_tuan, lop=lop_int_kt,
                        diem_biet=scores['earned_biet'], diem_hieu=scores['earned_hieu'],
                        diem_van_dung=scores['earned_van_dung'],
                        tong_diem_biet=scores['total_biet'], tong_diem_hieu=scores['total_hieu'],
                        tong_diem_van_dung=scores['total_van_dung']
                    )

                    rec_data = generate_recommendation(hoc_sinh_id=hoc_sinh_id,
                                                       chu_de_id=chu_de_id,
                                                       diem=score_submit_test,
                                                       lop=lop_int_kt,
                                                       tuan=current_tuan,
                                                       mon_hoc_name=selected_subject_name
                                                       )
                    if latest_suggestion_id: update_learning_status(latest_suggestion_id, "Đã hoàn thành")
                    if rec_data:
                        st.session_state["show_test_result"][
                            "action_text"] = f"Hệ thống: **{rec_data['action']}** (Mô hình: {rec_data['model']}, Conf: {rec_data['confidence']:.2f})"
                        chu_de_de_xuat_id = rec_data.get("suggested_topic_id")
                        ten_chu_de_de_xuat = "N/A"
                        if chu_de_de_xuat_id:
                            topic_suggested_info = get_topic_by_id(chu_de_de_xuat_id)
                            if topic_suggested_info: ten_chu_de_de_xuat = topic_suggested_info["ten_chu_de"]
                        if rec_data["action"] == "advance":
                            msg = f"🎉 **Gợi ý:** Học chủ đề **{ten_chu_de_de_xuat}**."
                            st.session_state["show_test_result"]["messages"].append({"type": "success", "text": msg})
                        elif rec_data["action"] == "review":
                            msg = f"🤔 **Gợi ý:** Ôn tập **{ten_chu_de_de_xuat}**."
                            st.session_state["show_test_result"]["messages"].append({"type": "warning", "text": msg})
                        elif rec_data["action"] == "remediate":
                            msg = f"⚠️ **Gợi ý:** Học lại tiền đề: **{ten_chu_de_de_xuat}**."
                            st.session_state["show_test_result"]["messages"].append({"type": "error", "text": msg})
                    else:
                        st.session_state["show_test_result"]["messages"].append(
                            {"type": "error", "text": "Không thể tạo gợi ý AI."})
                except Exception as e:
                    st.error(f"Lỗi xử lý điểm/gọi AI: {e}")

            st.rerun()