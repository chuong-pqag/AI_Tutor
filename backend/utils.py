# ======================================================
# 📘 backend/utils.py
# Các hàm tiện ích dùng chung cho AI Tutor
# ======================================================
import numpy as np
import os
import base64

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


def get_available_avatars(role):
    """
    Lấy danh sách file ảnh trong thư mục data/avatar/{role}
    role: 'GV' hoặc 'HS'
    """
    # Đường dẫn tương đối từ thư mục gốc
    folder_path = os.path.join("data", "avatar", role)

    # Tạo thư mục nếu chưa có để tránh lỗi
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return []

    # Lấy danh sách file ảnh
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return sorted(files)


def get_img_as_base64(file_path):
    """Chuyển file ảnh thành chuỗi base64 để hiển thị trong HTML."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None
