# File: backend/recommendation_engine.py
# (BẢN CHÍNH THỨC: Tương thích với Lõi AI Mới & Fix Logic ID)

import joblib
import pandas as pd
import os
from backend.data_service import (
    get_topic_by_id,
    insert_learning_path,
    log_ai_recommendation,
    get_student_all_results
)
from backend.utils import normalize_score
from backend.supabase_client import supabase

# --- Cấu hình Đường dẫn Model (Tuyệt đối) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, 'model_recommender.pkl')


# =========================================================
# 1️⃣ RULE-BASED ENGINE (SMART FALLBACK)
# =========================================================
def recommend_rule_based_topic(diem_normalized: float, current_topic_info: dict):
    """
    Logic fallback cũ (chỉ dựa trên điểm tổng).
    Vẫn giữ lại để phòng trường hợp không tính được điểm chi tiết.
    """
    if not current_topic_info:
        return {"action": "review", "suggested_topic_id": None, "confidence": 0.5}

    current_topic_id = str(current_topic_info.get("id"))
    prerequisite_id = current_topic_info.get("prerequisite_id")
    if prerequisite_id is not None:
        prerequisite_id = str(prerequisite_id)

    if diem_normalized < 0.6:
        if prerequisite_id:
            return {"action": "remediate", "suggested_topic_id": prerequisite_id, "confidence": 0.9}
        else:
            return {"action": "remediate", "suggested_topic_id": current_topic_id, "confidence": 0.85}
    elif diem_normalized < 0.8:
        return {"action": "review", "suggested_topic_id": current_topic_id, "confidence": 0.7}
    else:
        return {"action": "advance", "suggested_topic_id": None, "confidence": 0.8}


# =========================================================
# 2️⃣ ML ENGINE (Sử dụng Pipeline Mới)
# =========================================================

def load_model():
    """Tải mô hình (Pipeline) nếu tồn tại."""
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception as e:
        print(f"Lỗi tải model AI: {e}")
        return None


def recommend_ml_topic(student_features_df: pd.DataFrame):
    """
    Dự đoán hành động bằng mô hình ML mới.
    Input: DataFrame 1 dòng với 5 cột ['pct_biet', 'pct_hieu', 'pct_van_dung', 'lop', 'mon_hoc']
    """
    model = load_model()
    if not model:
        return None

    try:
        # Dự đoán hành động (0: remediate, 1: review, 2: advance)
        pred = model.predict(student_features_df)

        mapping = {0: "remediate", 1: "review", 2: "advance"}
        predicted_action = mapping.get(int(pred[0]), "review")

        confidence = 0.9
        if hasattr(model, "predict_proba"):
            try:
                # Lấy xác suất cao nhất
                confidence = model.predict_proba(student_features_df)[0].max()
            except:
                pass

        return {"action": predicted_action, "confidence": confidence}

    except Exception as e:
        print(f"Lỗi khi dự đoán ML: {e}")
        return None


# =========================================================
# 3️⃣ HÀM HỖ TRỢ TÌM CHỦ ĐỀ TIẾP THEO
# =========================================================

def find_next_topic(lop: int, current_tuan: int, mon_hoc_name: str):
    """
    Tìm chủ đề có tuần > hiện tại, cùng lớp và môn.
    """
    if lop is None or current_tuan is None or not mon_hoc_name: return None
    try:
        res = (
            supabase.table("chu_de")
            .select("id")
            .eq("lop", lop)
            .eq("mon_hoc", mon_hoc_name)
            .gt("tuan", current_tuan)
            .order("tuan", desc=False)
            .limit(1)
            .execute()
        )
        if res.data and len(res.data) > 0:
            return str(res.data[0]["id"])
        return None
    except Exception as e:
        print(f"Lỗi khi tìm chủ đề tiếp theo: {e}")
        return None


# =========================================================
# 4️⃣ WRAPPER CHÍNH — SINH GỢI Ý
# =========================================================

def generate_recommendation(hoc_sinh_id: str, chu_de_id: str, diem: float, lop: int, tuan: int, mon_hoc_name: str):
    """
    Sinh gợi ý học tập thông minh.
    Quy trình:
    1. Lấy kết quả chi tiết (điểm thành phần) mới nhất.
    2. Tính toán Tỷ lệ % (Biết/Hiểu/Vận dụng).
    3. Gửi vào Model AI để lấy Hành động (Action).
    4. Ánh xạ Action sang Chủ đề cụ thể (Next/Current/Prerequisite).
    5. Lưu lộ trình.
    """

    # 1. Lấy thông tin chủ đề hiện tại
    current_topic_info = get_topic_by_id(chu_de_id)
    if not current_topic_info:
        print(f"Lỗi: Không tìm thấy thông tin chủ đề ID {chu_de_id}")
        return None

    # 2. Lấy bản ghi ket_qua_test MỚI NHẤT (để lấy 6 cột điểm chi tiết)
    latest_result = None
    try:
        res_data = get_student_all_results(hoc_sinh_id)
        if res_data:
            latest_result = res_data[0]  # Giả định bản ghi đầu tiên là mới nhất (do order by desc)
    except Exception as e:
        print(f"Lỗi khi lấy kết quả test mới nhất: {e}")

    # 3. Chuẩn bị Features (X) cho Model
    student_features_df = None
    pct_biet = 0;
    pct_hieu = 0;
    pct_van_dung = 0  # Default

    if latest_result:
        try:
            # Lấy điểm đạt được
            diem_biet = float(latest_result.get('diem_biet', 0) or 0)
            diem_hieu = float(latest_result.get('diem_hieu', 0) or 0)
            diem_van_dung = float(latest_result.get('diem_van_dung', 0) or 0)
            # Lấy điểm tối đa
            tong_biet = float(latest_result.get('tong_diem_biet', 0) or 0)
            tong_hieu = float(latest_result.get('tong_diem_hieu', 0) or 0)
            tong_van_dung = float(latest_result.get('tong_diem_van_dung', 0) or 0)

            # Tính toán Tỷ lệ % (tránh chia cho 0)
            pct_biet = (diem_biet / tong_biet) if tong_biet > 0 else 0
            pct_hieu = (diem_hieu / tong_hieu) if tong_hieu > 0 else 0
            pct_van_dung = (diem_van_dung / tong_van_dung) if tong_van_dung > 0 else 0

            # Tạo DataFrame đúng chuẩn features
            student_features_df = pd.DataFrame({
                'pct_biet': [pct_biet],
                'pct_hieu': [pct_hieu],
                'pct_van_dung': [pct_van_dung],
                'lop': [lop],
                'mon_hoc': [mon_hoc_name]
            })
        except Exception as e:
            print(f"Lỗi khi tính toán Tỷ lệ %: {e}")
            student_features_df = None

    # 4. Quyết định Hành động (ACTION)
    action = "review"
    confidence = 0.5
    model_version = "Rule-based (Default)"

    ml_rec = None
    if student_features_df is not None:
        # Gọi Model AI đã huấn luyện
        ml_rec = recommend_ml_topic(student_features_df)

    if ml_rec:
        action = ml_rec["action"]
        confidence = ml_rec.get("confidence", 0.9)
        model_version = "AI Model (Lần 2 - Tỷ lệ %)"
    else:
        # Fallback: Tự áp dụng Logic Thông minh (Smart Rules) nếu Model chưa sẵn sàng
        if student_features_df is not None:
            pct_tong = diem / 10.0
            if (pct_biet < 0.5) or (pct_hieu < 0.5):
                action = "remediate"
            elif (pct_tong >= 0.85) and (pct_van_dung >= 0.7):
                action = "advance"
            else:
                action = "review"
            model_version = "Smart Rules (Fallback)"
            confidence = 0.85
        else:
            # Fallback cuối cùng: Dựa trên điểm tổng
            normalized_score = normalize_score(diem, max_score=10)
            rule_rec = recommend_rule_based_topic(normalized_score, current_topic_info)
            action = rule_rec["action"]
            model_version = "Basic Score Rules"

    # 5. Quyết định Chủ đề (TOPIC ID) dựa trên Action
    suggested_topic_id = str(chu_de_id)  # Mặc định là ôn lại bài hiện tại

    if action == "advance":
        # Tìm chủ đề tiếp theo
        next_topic_id = find_next_topic(lop, tuan, mon_hoc_name)
        if next_topic_id:
            suggested_topic_id = next_topic_id
        else:
            # Nếu hết bài -> Review bài cuối
            action = "review"
            suggested_topic_id = str(chu_de_id)
            print(f"Hoàn thành lộ trình Môn '{mon_hoc_name}'.")

    elif action == "review":
        # Ôn tập -> Chính chủ đề hiện tại
        suggested_topic_id = str(chu_de_id)

    elif action == "remediate":
        # Học lại -> Tiền đề (nếu có)
        prereq_id = current_topic_info.get("prerequisite_id")
        if prereq_id:
            suggested_topic_id = str(prereq_id)
        else:
            # Nếu không có tiền đề -> Học lại bài hiện tại
            suggested_topic_id = str(chu_de_id)

    # 6. Ghi log AI (để debug và huấn luyện sau này)
    try:
        input_features_log = {
            "diem_tong": diem,
            "pct_biet": pct_biet, "pct_hieu": pct_hieu, "pct_van_dung": pct_van_dung,
            "lop": lop, "mon_hoc": mon_hoc_name
        }
        log_ai_recommendation(
            hoc_sinh_id=hoc_sinh_id,
            input_features=input_features_log,
            action=action,
            chu_de_nguon=chu_de_id,
            chu_de_de_xuat=suggested_topic_id,
            model_version=model_version,
            confidence=confidence
        )
    except Exception as log_err:
        print(f"Lỗi khi ghi log AI: {log_err}")

    # 7. Lưu Lộ trình vào CSDL
    if suggested_topic_id:
        try:
            # Sử dụng insert_learning_path (đã được sửa lỗi trả về None)
            insert_learning_path(
                hoc_sinh_id=hoc_sinh_id,
                chu_de_id=suggested_topic_id,
                bai_hoc_id=None,
                loai_goi_y=action,
                diem_truoc_goi_y=diem
            )
        except Exception as path_err:
            print(f"LỖI TRUY VẤN: Không thể tạo lộ trình học. Lỗi: {path_err}")
            return None

    return {
        "action": action,
        "suggested_topic_id": suggested_topic_id,
        "model": model_version,
        "confidence": confidence
    }