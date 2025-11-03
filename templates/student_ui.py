"""
AI Tutor — Giao diện Học sinh (Student UI)
------------------------------------------
Chức năng:
- Chọn học sinh, lớp, tuần học
- Làm bài luyện tập từ câu hỏi Supabase
- Ghi kết quả & lịch sử học
- Nhận gợi ý AI (tự động log & tạo lộ trình)
"""

import streamlit as st
import random
from backend.data_service import (
    get_student,
    get_topics,
    get_questions_by_topic,
    insert_test_result,
    log_learning_activity,
    get_videos_by_topic,
    get_learning_paths
)
from backend.recommendation_engine import generate_recommendation
from backend.utils import normalize_score


# =========================================================
# 1️⃣ Cấu hình trang
# =========================================================
st.set_page_config(page_title="📘 AI Tutor - Học sinh", page_icon="🤖", layout="centered")
st.title("📚 Học sinh — AI Tutor")

st.markdown("### 🧒 Hệ thống học cá nhân hóa dựa trên kết quả thực tế")


# =========================================================
# 2️⃣ Thông tin học sinh
# =========================================================
hoc_sinh_id = st.text_input("🔑 Nhập mã học sinh (uuid):")
lop = st.selectbox("🏫 Chọn lớp:", [2, 3])
tuan = st.number_input("📆 Chọn tuần học:", min_value=1, max_value=35, step=1, value=1)

if hoc_sinh_id:
    hs = get_student(hoc_sinh_id)
    if not hs:
        st.error("❌ Không tìm thấy học sinh trong hệ thống.")
        st.stop()

    st.success(f"Xin chào **{hs['ho_ten']}** — Lớp {hs['lop_hien_tai']}")
    log_learning_activity(hoc_sinh_id, None, "dang_nhap", f"Học sinh {hs['ho_ten']} đăng nhập hệ thống")

else:
    st.info("Vui lòng nhập mã học sinh để bắt đầu.")
    st.stop()


# =========================================================
# 3️⃣ Chọn chủ đề học
# =========================================================
topics = get_topics(lop, tuan)

if not topics:
    st.warning("⚠️ Chưa có chủ đề cho tuần này.")
    st.stop()

st.subheader("📘 Danh sách chủ đề học:")
topic_titles = [f"Tuần {t['tuan']}: {t['ten_chu_de']}" for t in topics]
selected_title = st.selectbox("Chọn chủ đề để luyện tập:", topic_titles)

selected_topic = topics[topic_titles.index(selected_title)]
chu_de_id = selected_topic["id"]
st.markdown(f"**🧩 Chủ đề:** {selected_topic['ten_chu_de']} — *{selected_topic['muc_do']}*")

videos = get_videos_by_topic(chu_de_id)
if videos:
    st.video(videos[0]["url"])
    log_learning_activity(hoc_sinh_id, chu_de_id, "xem_video", f"Xem video {videos[0]['tieu_de']}")


# =========================================================
# 4️⃣ Làm bài luyện tập (Quiz)
# =========================================================
st.subheader("🧮 Bài luyện tập nhanh")

questions = get_questions_by_topic(chu_de_id)
if not questions:
    st.info("Hiện chưa có câu hỏi cho chủ đề này.")
    st.stop()

# Lấy ngẫu nhiên tối đa 5 câu hỏi
quiz = random.sample(questions, min(5, len(questions)))

user_answers = {}
for i, q in enumerate(quiz, 1):
    options = [q["dap_an_dung"]] + q["dap_an_khac"]
    random.shuffle(options)
    user_answers[q["id"]] = st.radio(f"Câu {i}: {q['noi_dung']}", options, key=f"q_{q['id']}")

if st.button("📤 Nộp bài & Xem kết quả"):
    correct = sum(1 for q in quiz if user_answers[q["id"]] == q["dap_an_dung"])
    score = round((correct / len(quiz)) * 10, 2)
    normalized = normalize_score(score, 10)

    # Lưu kết quả
    insert_test_result(
        hoc_sinh_id,
        chu_de_id,
        bai_tap_id=None,
        diem=score,
        so_cau_dung=correct,
        tong_cau=len(quiz),
        tuan_kiem_tra=tuan
    )

    # Log hành động
    log_learning_activity(hoc_sinh_id, chu_de_id, "nop_bai", f"Học sinh nộp bài {correct}/{len(quiz)}")

    # Hiển thị điểm
    st.success(f"✅ Bạn làm đúng {correct}/{len(quiz)} câu — Điểm: **{score}/10**")

    # Gợi ý AI
    st.subheader("🤖 Gợi ý học tập từ AI")
    reco = generate_recommendation(hoc_sinh_id, chu_de_id, score, lop, tuan)

    action_map = {
        "remediate": "🧩 Ôn lại kiến thức trước",
        "review": "🔁 Luyện tập thêm chủ đề hiện tại",
        "advance": "🚀 Tiến sang chủ đề mới"
    }
    action_text = action_map.get(reco["action"], reco["action"])

    st.info(f"**Hệ thống đề xuất:** {action_text}")
    st.caption(f"Độ tin cậy mô hình: {reco['confidence']*100:.0f}% ({reco['model']})")

    # Hiển thị chủ đề gợi ý tiếp theo (nếu có)
    if reco["chu_de_de_xuat"]:
        st.markdown("### 🎯 Chủ đề được gợi ý tiếp theo:")
        next_topic = get_topics(lop, tuan + 1)
        if next_topic:
            next_titles = [t['ten_chu_de'] for t in next_topic if t['id'] == reco["chu_de_de_xuat"]]
            if next_titles:
                st.success(next_titles[0])
        else:
            st.info("Không tìm thấy chủ đề gợi ý tiếp theo trong dữ liệu.")

    # Hiển thị video gợi ý
    if reco["chu_de_de_xuat"]:
        next_videos = get_videos_by_topic(reco["chu_de_de_xuat"])
        if next_videos:
            st.video(next_videos[0]["url"])


# =========================================================
# 5️⃣ Xem lộ trình học
# =========================================================
st.divider()
st.subheader("📋 Lộ trình học của bạn")

paths = get_learning_paths(hoc_sinh_id)
if paths:
    for p in paths:
        st.markdown(
            f"- Tuần {tuan}: **{p['loai_goi_y']}** → Chủ đề ID `{p['chu_de_id']}` — *{p['trang_thai']}*"
        )
else:
    st.info("Chưa có gợi ý học nào được tạo.")
