# File: pages/student_pages/ui_quiz_engine.py
# (BẢN FIX LỖI: Loại bỏ st.form để hỗ trợ nút chọn ảnh)

import streamlit as st
from backend.data_service import get_questions_for_exercise, save_test_result, log_learning_activity, get_topic_by_id, \
    update_learning_status
from backend.recommendation_engine import generate_recommendation
import random
import time
from datetime import datetime


# --- Hàm hỗ trợ xóa trạng thái quiz ---
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
        # Xóa trạng thái shuffle
        if f"shuffled_{widget_key}" in st.session_state:
            del st.session_state[f"shuffled_{widget_key}"]


# --- Hàm kiểm tra URL ảnh ---
def is_image_url(text: str):
    if not isinstance(text, str): return False
    text_lower = text.lower()
    return text_lower.startswith("http") and (
            text_lower.endswith(".png") or
            text_lower.endswith(".jpg") or
            text_lower.endswith(".jpeg") or
            text_lower.endswith(".gif") or
            "supabase" in text_lower
    )


# --- Hàm tính điểm chi tiết ---
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
        muc_do = q.get("muc_do", "biết")
        if muc_do == "biết":
            scores['total_biet'] += diem_cau_hoi
        elif muc_do == "hiểu":
            scores['total_hieu'] += diem_cau_hoi
        elif muc_do == "vận dụng":
            scores['total_van_dung'] += diem_cau_hoi

        is_correct = False
        loai_cau_hoi = q.get("loai_cau_hoi", "mot_lua_chon")

        # Logic so sánh
        if loai_cau_hoi.startswith("mot_lua_chon"):
            if ans is not None and true_ans_list: is_correct = (ans == true_ans_list[0])
        elif loai_cau_hoi.startswith("nhieu_lua_chon"):
            if ans and true_ans_list: is_correct = (set(ans) == set(true_ans_list))
        else:  # dien_khuyet
            if ans and true_ans_list:
                true_ans_str_list = [str(t).lower().strip() for t in true_ans_list]
                is_correct = (str(ans).strip().lower() in true_ans_str_list)

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


# =========================================================================
# HÀM RENDER WIDGET (Đã bỏ logic Form, dùng Button trực tiếp)
# =========================================================================
def render_question_widget(q, widget_key, current_lop):
    """
    Hàm helper để render (hiển thị) câu hỏi và widget đáp án.
    (CẬP NHẬT: Nút chọn nằm TRÊN ảnh + Cố định vị trí đáp án)
    """

    loai_cau_hoi = q.get("loai_cau_hoi", "mot_lua_chon")

    # 1. RENDER CÂU HỎI
    question_text_label = f"**Câu {q['index'] + 1} ({q['diem_so']} điểm):**"

    if q.get("noi_dung"):
        if is_image_url(q["noi_dung"]):
            st.markdown(question_text_label)
            st.image(q["noi_dung"], width=400)
        else:
            st.markdown(f"{question_text_label} {q['noi_dung']}")

    if q.get("hinh_anh_url"):
        st.image(q["hinh_anh_url"], width=400)

    try:
        lop_int = int(current_lop) if current_lop is not None else 0
    except:
        lop_int = 0

    if lop_int == 1 and q.get('audio_url'):
        st.audio(q['audio_url'], format="audio/mp3", start_time=0)

    # ============================================================
    # 2. CHUẨN BỊ OPTIONS (SỬA LỖI ĐẢO LUNG TUNG)
    # ============================================================
    all_options = q["dap_an_dung"] + q.get("lua_chon", [])

    if not all_options:
        if loai_cau_hoi != "dien_khuyet": pass
        all_options = []
    else:
        # --- LOGIC QUAN TRỌNG: CHỈ SHUFFLE 1 LẦN ---
        # Tạo một key riêng để lưu thứ tự đáp án cho câu hỏi này
        shuffle_key = f"shuffled_order_{widget_key}"

        if shuffle_key not in st.session_state:
            # Nếu chưa có trong bộ nhớ -> Xáo trộn và Lưu lại
            random.shuffle(all_options)
            st.session_state[shuffle_key] = all_options
        else:
            # Nếu đã có -> Lấy ra dùng lại (Không xáo trộn nữa)
            all_options = st.session_state[shuffle_key]
        # -------------------------------------------

    # 3. RENDER WIDGET CHỌN ĐÁP ÁN
    is_image_answer = False
    if all_options:
        is_image_answer = is_image_url(str(all_options[0]))

    # ==== TRƯỜNG HỢP ĐÁP ÁN LÀ HÌNH ẢNH (GIAO DIỆN MỚI) ====
    if is_image_answer and loai_cau_hoi.startswith("mot_lua_chon"):
        st.write("Chọn đáp án đúng:")

        cols = st.columns(len(all_options))
        current_selected = st.session_state.get(widget_key)

        for idx, url in enumerate(all_options):
            with cols[idx]:
                # --- CẬP NHẬT GIAO DIỆN: BUTTON LÊN TRÊN ---

                # Xác định trạng thái nút
                is_selected = (current_selected == url)
                btn_label = "✅ Đã chọn" if is_selected else "Chọn"
                btn_type = "primary" if is_selected else "secondary"

                # 1. Hiển thị Nút trước
                if st.button(btn_label, key=f"btn_{widget_key}_{idx}", type=btn_type, use_container_width=True):
                    st.session_state[widget_key] = url
                    st.rerun()

                    # 2. Hiển thị Ảnh sau (Chiều rộng cố định để cân đối)
                st.image(url, use_container_width=True)
                # -------------------------------------------

    # ==== CÁC TRƯỜNG HỢP KHÁC (TEXT) ====
    elif not is_image_answer and loai_cau_hoi == "mot_lua_chon":
        st.radio("Chọn đáp án:", all_options, key=widget_key,
                 index=None if widget_key not in st.session_state else all_options.index(
                     st.session_state[widget_key]) if st.session_state.get(widget_key) in all_options else None)

    elif not is_image_answer and loai_cau_hoi == "nhieu_lua_chon":
        st.multiselect("Chọn các đáp án đúng:", all_options, key=widget_key,
                       default=st.session_state.get(widget_key, []))

    elif loai_cau_hoi == "dien_khuyet":
        st.text_input("Điền đáp án:", key=widget_key,
                      value=st.session_state.get(widget_key, ""))

    else:
        if all_options: st.error(f"Lỗi hiển thị: {loai_cau_hoi}")


# =========================================================================
# HÀM CHÍNH 1: LUYỆN TẬP (Đã bỏ st.form)
# =========================================================================
def process_and_render_practice(exercise_id, bai_hoc_id, chu_de_id, current_tuan, current_lop, hoc_sinh_id):
    questions = get_questions_for_exercise(exercise_id)
    if not questions:
        st.caption("Chưa có câu hỏi cho bài tập này.")
        return

    form_key_prefix = f"practice_{exercise_id}"
    submitted_key = f"submitted_{form_key_prefix}"

    # 1. HIỂN THỊ KẾT QUẢ
    if st.session_state.get(submitted_key, False):
        st.markdown("#### Kết quả của bạn:")
        scores = calculate_detailed_scores(questions, form_key_prefix)
        score_10 = round(scores['earned_points'] / scores['total_points'] * 10, 2) if scores['total_points'] > 0 else 0

        st.success(f"🎯 Kết quả: **{score_10}/10** ({scores['correct']}/{len(questions)} đúng)")

        if score_10 < 7.0:
            st.warning("🤔 Kết quả chưa tốt! Bạn nên xem lại Video và Tài liệu PDF.")
        else:
            st.success("🎉 Bạn làm tốt lắm!")

        # Nút làm lại
        if st.button("🔄 Làm lại bài", key=f"redo_{form_key_prefix}"):
            clear_quiz_state(form_key_prefix, questions)
            st.rerun()
        st.markdown("---")

    # 2. HIỂN THỊ DANH SÁCH CÂU HỎI (KHÔNG CÓ st.form)
    for i, q in enumerate(questions):
        q['index'] = i
        widget_key = f"{form_key_prefix}_{q['id']}"
        render_question_widget(q, widget_key, current_lop)
        st.markdown("---")  # Phân cách giữa các câu hỏi

    # 3. NÚT NỘP BÀI (Thường)
    # Chỉ hiện nút Nộp nếu chưa nộp
    if not st.session_state.get(submitted_key, False):
        if st.button("📤 Nộp bài luyện tập", key=f"submit_{form_key_prefix}", type="primary"):
            st.session_state[submitted_key] = True

            scores = calculate_detailed_scores(questions, form_key_prefix)
            score_submit = round(scores['earned_points'] / scores['total_points'] * 10, 2) if scores[
                                                                                                  'total_points'] > 0 else 0
            suggestion_text = "Hoàn thành Luyện tập."
            if score_submit < 7.0: suggestion_text = "Kết quả chưa tốt."

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
                    log_learning_activity(hoc_sinh_id, "xem_goi_y_luyen_tap", suggestion_text, chu_de_id, bai_hoc_id)
                except Exception as e:
                    st.error(f"Lỗi lưu KQ: {e}")
            st.rerun()


# =========================================================================
# HÀM CHÍNH 2: KIỂM TRA CHỦ ĐỀ (Đã bỏ st.form)
# =========================================================================
def process_and_render_topic_test(test_id, chu_de_id, selected_subject_name, current_tuan, current_lop, hoc_sinh_id,
                                  latest_suggestion_id):
    questions = get_questions_for_exercise(test_id)
    if not questions:
        st.warning("Bài kiểm tra chưa có câu hỏi.")
        return

    form_key_prefix_test = f"test_{test_id}"
    submitted_key_test = f"submitted_{form_key_prefix_test}"

    # 1. HIỂN THỊ KẾT QUẢ
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

        if st.button("🔄 Làm lại bài kiểm tra", key=f"redo_{form_key_prefix_test}"):
            clear_quiz_state(form_key_prefix_test, questions)
            st.rerun()
        st.markdown("---")

    # 2. HIỂN THỊ DANH SÁCH CÂU HỎI
    for i, q in enumerate(questions):
        q['index'] = i
        widget_key = f"{form_key_prefix_test}_{q['id']}"
        render_question_widget(q, widget_key, current_lop)
        st.markdown("---")

    # 3. NÚT NỘP BÀI
    if not st.session_state.get(submitted_key_test, False):
        if st.button("📤 Nộp bài kiểm tra", key=f"submit_{form_key_prefix_test}", type="primary"):
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

            if current_tuan is not None and current_lop is not None:
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