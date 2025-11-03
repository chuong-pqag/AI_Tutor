# ======================================================
# 📘 backend/utils.py
# Các hàm tiện ích dùng chung cho AI Tutor
# ======================================================
import numpy as np

def normalize_score(score, min_score=0, max_score=10):
    """
    Chuẩn hóa điểm số về khoảng [0, 1]
    """
    if score is None:
        return 0.0
    score = max(min(score, max_score), min_score)
    return (score - min_score) / (max_score - min_score)


def moving_average(data, window_size=3):
    """
    Tính trung bình động của danh sách điểm để đánh giá xu hướng học tập.
    """
    if not data or len(data) < window_size:
        return np.mean(data) if data else 0
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')[-1]


def classify_level(score):
    """
    Phân loại trình độ học sinh dựa vào điểm trung bình.
    """
    if score >= 8.5:
        return "Xuất sắc"
    elif score >= 7.0:
        return "Khá"
    elif score >= 5.0:
        return "Trung bình"
    else:
        return "Cần cố gắng hơn"


def suggest_next_topic(current_week, total_weeks=35):
    """
    Gợi ý tuần học tiếp theo trong lộ trình học.
    """
    if current_week < total_weeks:
        return f"Tiếp tục học tuần {current_week + 1}"
    else:
        return "Hoàn thành toàn bộ chương trình 🎉"
