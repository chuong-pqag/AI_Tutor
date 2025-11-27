# File: pages/student_pages/ui_quiz_engine.py
# (BẢN FIX FINAL: Đồng bộ tên tham số chính xác với ui_learning.py)

import streamlit as st
import random
import time
from datetime import datetime
from backend.data_service import (
    get_questions_for_exercise,
    save_test_result,
    log_learning_activity,
    get_topic_by_id,
    update_learning_status
)
from backend.recommendation_engine import generate_recommendation

# --- CƠ CHẾ TỰ ĐỘNG TƯƠNG THÍCH FRAGMENT ---
try:
    from streamlit import fragment
except ImportError:
    def fragment(func):
        return func


# =========================================================================
# 🤖 HÀM HELPER
# =========================================================================

def get_friendly_message(action, confidence, topic_name):
    if action == "remediate":
        return {"icon": "🛡️", "title": "Củng cố kiến thức nền",
                "msg": f"Có vẻ phần này hơi khó nhằn nhỉ? 😅 Đừng lo, AI nhận thấy em cần **ôn lại bài cũ** một chút để nắm chắc gốc rễ hơn. Cố lên nhé!",
                "color": "error"}
    elif action == "review":
        return {"icon": "💪", "title": "Rèn luyện thêm",
                "msg": f"Em làm khá tốt! 👍 Tuy nhiên, để đạt điểm tối đa, em nên **luyện tập thêm** chủ đề **{topic_name}** này cho thật nhuần nhuyễn nha.",
                "color": "warning"}
    elif action == "advance":
        return {"icon": "🚀", "title": "Học bài mới",
                "msg": f"Tuyệt vời! 🎉 Em đã làm chủ được kiến thức này rồi. Hệ thống đề xuất em **học bài tiếp theo** luôn nhé!",
                "color": "success"}
    return {"icon": "🤖", "title": "Gợi ý học tập", "msg": "Hệ thống đang tính toán lộ trình phù hợp nhất cho em.",
            "color": "info"}


def clear_quiz_state(form_key_prefix: str, questions: list, questions_key: str = None):
    submitted_key = f"submitted_{form_key_prefix}"
    keys_to_del = [submitted_key, "show_test_result"]

    if questions:
        for q in questions:
            keys_to_del.append(f"{form_key_prefix}_{q['id']}")
            keys_to_del.append(f"shuffled_order_{form_key_prefix}_{q['id']}")

    if questions_key: keys_to_del.append(questions_key)

    for k in keys_to_del:
        if k in st.session_state: del st.session_state[k]


def is_image_url(text: str):
    if not isinstance(text, str): return False
    text = text.lower()
    return text.startswith("http") and any(
        text.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']) or "supabase" in text


def calculate_detailed_scores(questions, form_key_prefix):
    scores = {'correct': 0, 'total_points': 0.0, 'earned_points': 0.0,
              'earned_biet': 0, 'earned_hieu': 0, 'earned_van_dung': 0,
              'total_biet': 0, 'total_hieu': 0, 'total_van_dung': 0}

    for q in questions:
        widget_key = f"{form_key_prefix}_{q['id']}"
        ans = st.session_state.get(widget_key)
        true_ans = q["dap_an_dung"]
        pts = q.get("diem_so", 1) or 1
        muc_do = q.get("muc_do", "biết")

        scores['total_points'] += pts
        if muc_do == "biết":
            scores['total_biet'] += pts
        elif muc_do == "hiểu":
            scores['total_hieu'] += pts
        elif muc_do == "vận dụng":
            scores['total_van_dung'] += pts

        is_correct = False
        loai = q.get("loai_cau_hoi", "mot_lua_chon")

        if loai.startswith("mot_lua_chon") and ans and true_ans:
            is_correct = (ans == true_ans[0])
        elif loai.startswith("nhieu_lua_chon") and ans and true_ans:
            is_correct = (set(ans) == set(true_ans))
        elif loai == "dien_khuyet" and ans and true_ans:
            user_val = str(ans).strip().lower()
            true_vals = [str(t).lower().strip() for t in true_ans]
            is_correct = (user_val in true_vals)

        if is_correct:
            scores['correct'] += 1
            scores['earned_points'] += pts
            if muc_do == "biết":
                scores['earned_biet'] += pts
            elif muc_do == "hiểu":
                scores['earned_hieu'] += pts
            elif muc_do == "vận dụng":
                scores['earned_van_dung'] += pts

    return scores


# =========================================================================
# 🖼️ UI COMPONENTS
# =========================================================================

def render_question_widget(q, widget_key, current_lop):
    label = f"**Câu {q['index'] + 1} ({q.get('diem_so', 1)} điểm):**"
    if q.get("noi_dung"):
        if is_image_url(q["noi_dung"]):
            st.markdown(label);
            st.image(q["noi_dung"], width=400)
        else:
            st.markdown(f"{label} {q['noi_dung']}")

    if q.get("hinh_anh_url"): st.image(q["hinh_anh_url"], width=400)

    try:
        lop_int = int(current_lop) if current_lop else 0
    except:
        lop_int = 0
    if lop_int == 1 and q.get('audio_url'): st.audio(q['audio_url'])

    options = q["dap_an_dung"] + q.get("lua_chon", [])
    if options:
        shuf_key = f"shuffled_order_{widget_key}"
        if shuf_key not in st.session_state:
            random.shuffle(options)
            st.session_state[shuf_key] = options
        else:
            options = st.session_state[shuf_key]

    loai = q.get("loai_cau_hoi", "mot_lua_chon")
    is_img = options and is_image_url(str(options[0]))

    if is_img and loai.startswith("mot_lua_chon"):
        cols = st.columns(len(options))
        cur_val = st.session_state.get(widget_key)
        for i, opt in enumerate(options):
            with cols[i]:
                is_sel = (cur_val == opt)
                if st.button("✅ Đã chọn" if is_sel else "Chọn", key=f"btn_{widget_key}_{i}",
                             type="primary" if is_sel else "secondary", use_column_width=True):
                    st.session_state[widget_key] = opt
                    st.rerun()
                st.image(opt, use_column_width=True)
    elif loai == "mot_lua_chon":
        st.radio("Chọn đáp án:", options, key=widget_key, index=None)
    elif loai == "nhieu_lua_chon":
        st.multiselect("Chọn đáp án:", options, key=widget_key)
    elif loai == "dien_khuyet":
        st.text_input("Điền đáp án:", key=widget_key)


@fragment
def render_question_block(questions, current_lop, form_key_prefix):
    for i, q in enumerate(questions):
        q['index'] = i
        wk = f"{form_key_prefix}_{q['id']}"
        render_question_widget(q, wk, current_lop)
        st.markdown("---")


# =========================================================================
# 🚀 MAIN 1: LUYỆN TẬP
# =========================================================================

def process_and_render_practice(exercise_id, bai_hoc_id, chu_de_id, current_tuan, current_lop, hoc_sinh_id):
    # 1. Đóng băng câu hỏi
    q_key = f"q_prac_{exercise_id}"
    if q_key not in st.session_state:
        st.session_state[q_key] = get_questions_for_exercise(exercise_id)
    questions = st.session_state[q_key]

    if not questions: st.caption("Chưa có câu hỏi."); return

    prefix = f"prac_{exercise_id}"
    sub_key = f"sub_{prefix}"

    if st.session_state.get(sub_key):
        sc = calculate_detailed_scores(questions, prefix)
        s10 = round(sc['earned_points'] / sc['total_points'] * 10, 2) if sc['total_points'] else 0
        if s10 >= 8.0: st.balloons()
        st.success(f"🎯 Kết quả: **{s10}/10**")
        if st.button("🔄 Làm lại", key=f"redo_{prefix}"):
            clear_quiz_state(prefix, questions, q_key);
            st.rerun()
        st.markdown("---")

    if not st.session_state.get(sub_key): st.caption("📱 Dùng trình duyệt Chrome/Safari trên điện thoại.")
    render_question_block(questions, current_lop, prefix)

    if not st.session_state.get(sub_key):
        if st.button("📤 Nộp bài", key=f"s_{prefix}", type="primary"):
            st.session_state[sub_key] = True
            final_scores = calculate_detailed_scores(questions, prefix)
            final_10 = round(final_scores['earned_points'] / final_scores['total_points'] * 10, 2) if final_scores[
                'total_points'] else 0

            if current_tuan and current_lop:
                try:
                    save_test_result(
                        hoc_sinh_id, exercise_id, chu_de_id, final_10,
                        final_scores['correct'], len(questions), current_tuan, int(current_lop),
                        final_scores['earned_biet'], final_scores['earned_hieu'], final_scores['earned_van_dung'],
                        final_scores['total_biet'], final_scores['total_hieu'], final_scores['total_van_dung']
                    )
                    log_learning_activity(hoc_sinh_id, "luyen_tap", f"Hoàn thành bài tập (Điểm: {final_10})", chu_de_id,
                                          bai_hoc_id)
                except Exception as e:
                    st.error(f"Lỗi lưu: {e}")
            st.rerun()


# =========================================================================
# 🚀 MAIN 2: KIỂM TRA CHỦ ĐỀ (ĐÃ SỬA TÊN THAM SỐ KHỚP VỚI UI_LEARNING)
# =========================================================================

def process_and_render_topic_test(test_id, chu_de_id, selected_subject_name, current_tuan, current_lop, hoc_sinh_id,
                                  latest_suggestion_id):
    # 1. Đóng băng câu hỏi
    q_key = f"q_test_{test_id}"
    if q_key not in st.session_state:
        st.session_state[q_key] = get_questions_for_exercise(test_id)
    questions = st.session_state[q_key]

    if not questions: st.warning("Đề trống."); return

    prefix = f"test_{test_id}"
    sub_key = f"sub_{prefix}"

    # 2. Kết quả & AI
    if st.session_state.get(sub_key):
        if "show_test_result" in st.session_state:
            res = st.session_state["show_test_result"]
            st.success(f"🎯 Kết quả KT: **{res['score']}/10**")
            st.subheader("💡 AI Nhắn nhủ:")
            for msg in res.get("messages", []):
                if msg["type"] == "success":
                    st.success(msg["text"])
                elif msg["type"] == "warning":
                    st.warning(msg["text"])
                elif msg["type"] == "error":
                    st.error(msg["text"])
                else:
                    st.info(msg["text"])

        if st.button("🔄 Làm lại", key=f"redo_{prefix}"):
            clear_quiz_state(prefix, questions, q_key);
            st.rerun()
        st.markdown("---")

    # 3. Render câu hỏi
    if not st.session_state.get(sub_key): st.caption("📱 Dùng trình duyệt Chrome/Safari trên điện thoại.")
    render_question_block(questions, current_lop, prefix)

    # 4. Nộp bài
    if not st.session_state.get(sub_key):
        if st.button("📤 Nộp bài thi", key=f"s_{prefix}", type="primary"):
            st.session_state[sub_key] = True

            sc = calculate_detailed_scores(questions, prefix)
            s10 = round(sc['earned_points'] / sc['total_points'] * 10, 2) if sc['total_points'] else 0

            st.session_state["show_test_result"] = {"score": s10, "messages": []}

            if current_tuan and current_lop:
                try:
                    # A. Lưu điểm
                    save_test_result(
                        hoc_sinh_id, test_id, chu_de_id, s10,
                        sc['correct'], len(questions), current_tuan, int(current_lop),
                        sc['earned_biet'], sc['earned_hieu'], sc['earned_van_dung'],
                        sc['total_biet'], sc['total_hieu'], sc['total_van_dung']
                    )

                    # B. Ghi log
                    log_learning_activity(hoc_sinh_id, "nop_bai", f"Hoàn thành kiểm tra (Điểm: {s10})", chu_de_id)

                    # C. Gọi AI
                    rec = generate_recommendation(hoc_sinh_id, chu_de_id, s10, int(current_lop), current_tuan,
                                                  selected_subject_name)
                    if latest_suggestion_id: update_learning_status(latest_suggestion_id, "Đã hoàn thành")

                    if rec:
                        log_learning_activity(hoc_sinh_id, "xem_goi_y", f"AI gợi ý: {rec['action']}", chu_de_id)

                        next_tpc = "bài tiếp theo"
                        if rec.get("suggested_topic_id"):
                            inf = get_topic_by_id(rec["suggested_topic_id"])
                            if inf: next_tpc = inf["ten_chu_de"]

                        friendly = get_friendly_message(rec['action'], rec.get('confidence', 0), next_tpc)
                        st.session_state["show_test_result"]["messages"].append({
                            "type": friendly["color"],
                            "text": f"{friendly['icon']} **{friendly['title']}:** {friendly['msg']}"
                        })
                except Exception as e:
                    st.error(f"Lỗi xử lý: {e}")
            st.rerun()
