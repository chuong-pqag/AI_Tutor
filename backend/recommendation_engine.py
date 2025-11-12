"""
AI Tutor — Recommendation Engine (Đã cập nhật lọc theo Môn học)
--------------------------------
Gợi ý lộ trình học CHỦ ĐỀ cá nhân hóa dựa trên kết quả BÀI KIỂM TRA CUỐI CHỦ ĐỀ.
Hỗ trợ hai chế độ: Rule-based (mặc định), ML (nếu có model).

Trigger: Chỉ gọi sau khi học sinh hoàn thành bài kiểm tra loại 'kiem_tra_chu_de'.
"""

import joblib
import pandas as pd
# Import các hàm data_service đã cập nhật
from backend.data_service import (
    get_topic_by_id,
    insert_learning_path,
    log_ai_recommendation,
)
from backend.utils import normalize_score
from backend.supabase_client import supabase

# --- Cấu hình ---
MODEL_PATH = "backend/model_recommender.pkl" # Đường dẫn tới model ML (nếu có)


# =========================================================
# 1️⃣ RULE-BASED ENGINE (Cho gợi ý Chủ đề)
# =========================================================

def recommend_rule_based_topic(diem_normalized: float, current_topic_info: dict):
    """
    Logic rule-based đơn giản cho Chủ đề dựa trên điểm KIỂM TRA CHỦ ĐỀ:
    - < 0.6: Học lại tiền đề hoặc ôn lại chủ đề hiện tại
    - 0.6–0.8: Ôn tập chủ đề hiện tại
    - >= 0.8: Tiến sang chủ đề mới
    """
    if not current_topic_info:
        # Trường hợp không tìm thấy thông tin chủ đề -> Mặc định ôn tập
        return {"action": "review", "suggested_topic_id": None, "confidence": 0.5}

    current_topic_id = str(current_topic_info.get("id")) # Đảm bảo là string
    prerequisite_id = current_topic_info.get("prerequisite_id")
    # Đảm bảo prerequisite_id cũng là string nếu không None
    if prerequisite_id is not None:
        prerequisite_id = str(prerequisite_id)

    if diem_normalized < 0.6:
        if prerequisite_id:
            # Gợi ý học lại chủ đề tiền đề
            return {
                "action": "remediate",
                "suggested_topic_id": prerequisite_id,
                "confidence": 0.9
            }
        else:
            # Không có tiền đề -> Gợi ý học lại/ôn tập chủ đề hiện tại
            return {
                "action": "remediate",
                "suggested_topic_id": current_topic_id,
                "confidence": 0.85
            }
    elif diem_normalized < 0.8:
        # Gợi ý ôn tập chủ đề hiện tại
        return {
            "action": "review",
            "suggested_topic_id": current_topic_id,
            "confidence": 0.7
        }
    else:
        # Gợi ý học chủ đề tiếp theo (ID sẽ được tìm bởi find_next_topic)
        return {
            "action": "advance",
            "suggested_topic_id": None, # Sẽ tìm sau
            "confidence": 0.8
        }

# =========================================================
# 2️⃣ ML ENGINE (DecisionTree - Giữ nguyên)
# =========================================================

def load_model():
    """Tải mô hình DecisionTree nếu tồn tại."""
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception:
        return None

def recommend_ml_topic(student_features: dict):
    """Dự đoán gợi ý CHỦ ĐỀ bằng mô hình ML (nếu có)."""
    model = load_model()
    if not model:
        return None # Trả về None nếu không có model

    try:
        # Lấy các feature cần thiết từ student_features
        features_for_model = {
            'score_norm': student_features.get('normalized_score'), # Đổi tên key nếu cần
            'tuan': student_features.get('tuan')
        }
        # Kiểm tra None
        if features_for_model['score_norm'] is None or features_for_model['tuan'] is None:
             print("Cảnh báo ML: Thiếu score_norm hoặc tuan.")
             return None

        X = pd.DataFrame([features_for_model])
        pred = model.predict(X)
        # Giả sử mô hình trả về giá trị 0–2 tương ứng với hành động
        mapping = {0: "remediate", 1: "review", 2: "advance"}
        predicted_action = mapping.get(int(pred[0]), "review") # Mặc định là review nếu lỗi

        # Lấy xác suất nếu có (tùy thuộc model)
        confidence = 0.9 # Giả định độ tin cậy cao cho ML
        if hasattr(model, "predict_proba"):
            try:
                confidence = model.predict_proba(X)[0].max()
            except: pass # Bỏ qua nếu lỗi lấy proba

        return {"action": predicted_action, "confidence": confidence}

    except Exception as e:
        print(f"Lỗi khi dự đoán ML: {e}")
        return None


# =========================================================
# 3️⃣ HÀM HỖ TRỢ TÌM CHỦ ĐỀ TIẾP THEO (ĐÃ THÊM LỌC MÔN HỌC)
# =========================================================

def find_next_topic(lop: int, current_tuan: int, mon_hoc_name: str): # <--- THAM SỐ MỚI
    """
    Xác định ID (UUID string) của chủ đề kế tiếp dựa theo lớp, tuần hiện tại VÀ MÔN HỌC.
    Giả định: chủ đề tiếp theo có tuan > hiện tại, cùng lớp và cùng môn học.
    """
    if lop is None or current_tuan is None or not mon_hoc_name:
        return None
    try:
        res = (
            supabase.table("chu_de")
            .select("id") # Chỉ cần lấy ID
            .eq("lop", lop)
            .eq("mon_hoc", mon_hoc_name) # <--- LỌC THEO MÔN HỌC
            .gt("tuan", current_tuan)
            .order("tuan", desc=False) # Sắp xếp tăng dần theo tuần
            .limit(1) # Lấy chủ đề đầu tiên tìm thấy
            .execute()
        )
        if res.data and len(res.data) > 0:
            return str(res.data[0]["id"]) # Trả về UUID dạng string
        return None # Không tìm thấy chủ đề tiếp theo
    except Exception as e:
        print(f"Lỗi khi tìm chủ đề tiếp theo: {e}")
        return None

# =========================================================
# 4️⃣ WRAPPER — SINH GỢI Ý CHỦ ĐỀ (ĐÃ THÊM THAM SỐ VÀ LOGGING)
# =========================================================

def generate_recommendation(hoc_sinh_id: str, chu_de_id: str, diem: float, lop: int, tuan: int, mon_hoc_name: str): # <--- THAM SỐ MỚI
    """
    Sinh gợi ý học tập cho CHỦ ĐỀ tiếp theo dựa trên điểm BÀI KIỂM TRA CUỐI CHỦ ĐỀ.
    Args:
        hoc_sinh_id (str): UUID của học sinh.
        chu_de_id (str): UUID của chủ đề vừa hoàn thành kiểm tra.
        diem (float): Điểm bài kiểm tra cuối chủ đề (thang 10).
        lop (int): Khối lớp của học sinh.
        tuan (int): Tuần học của chủ đề vừa hoàn thành.
        mon_hoc_name (str): Tên môn học của chủ đề vừa hoàn thành. <--- THAM SỐ MỚI
    Returns:
        dict: Chứa thông tin gợi ý ('action', 'suggested_topic_id', 'model', 'confidence')
              hoặc None nếu có lỗi.
    """
    # Lấy thông tin chủ đề hiện tại (cần prerequisite_id)
    current_topic_info = get_topic_by_id(chu_de_id)
    if not current_topic_info:
        print(f"Lỗi: Không tìm thấy thông tin chủ đề ID {chu_de_id}")
        return None

    normalized_score = normalize_score(diem, max_score=10)

    # Chuẩn bị feature input cho AI (cả Rule-based và ML)
    student_features = {
        "lop": lop,
        "tuan": tuan,
        "diem_raw": diem,
        "normalized_score": normalized_score,
        "mon_hoc": mon_hoc_name
    }

    action = "review" # Hành động mặc định
    confidence = 0.5
    model_version = "Rule-based (Default)"
    suggested_topic_id = str(chu_de_id) # Mặc định gợi ý ôn lại chủ đề hiện tại

    # 1️⃣ Thử mô hình ML nếu có
    ml_rec = recommend_ml_topic(student_features)
    if ml_rec:
        action = ml_rec["action"]
        confidence = ml_rec.get("confidence", 0.9)
        model_version = "ML DecisionTree"
    else:
        # 2️⃣ Fallback sang rule-based
        rule_rec = recommend_rule_based_topic(normalized_score, current_topic_info)
        action = rule_rec["action"]
        suggested_topic_id = rule_rec["suggested_topic_id"]
        confidence = rule_rec["confidence"]
        model_version = "Rule-based"

    # 3️⃣ Xác định suggested_topic_id cuối cùng
    if action == "advance":
        # Tìm chủ đề tiếp theo nếu hành động là advance (từ cả ML và Rule-based)
        next_topic_id = find_next_topic(lop, tuan, mon_hoc_name) # <--- TRUYỀN THAM SỐ MỚI
        if next_topic_id:
            suggested_topic_id = next_topic_id
        else:
            # Không tìm thấy chủ đề mới (Hoàn thành lộ trình môn học) -> Gợi ý ôn lại chủ đề hiện tại
            action = "review"
            suggested_topic_id = str(chu_de_id)
            print(f"Hoàn thành lộ trình Môn '{mon_hoc_name}' cho lớp {lop}. Gợi ý ôn tập.")
    elif action == "remediate" or action == "review":
         # Nếu ML gợi ý remediate/review, cần lấy ID từ rule-based
         if ml_rec:
             rule_rec_fallback = recommend_rule_based_topic(normalized_score, current_topic_info)
             suggested_topic_id = rule_rec_fallback["suggested_topic_id"]
         # Nếu dùng rule-based thì suggested_topic_id đã có sẵn
    else: # Trường hợp action không hợp lệ
        action = "review"
        suggested_topic_id = str(chu_de_id)


    # 4️⃣ Ghi log AI
    try:
        log_ai_recommendation(
            hoc_sinh_id=hoc_sinh_id,
            input_features=student_features,
            action=action,
            chu_de_nguon=chu_de_id, # UUID string
            chu_de_de_xuat=suggested_topic_id, # UUID string or None
            bai_hoc_de_xuat=None, # Gợi ý cấp độ Chủ đề
            model_version=model_version,
            confidence=confidence
        )
    except Exception as log_err:
        print(f"Lỗi khi ghi log AI: {log_err}")

    # 5️⃣ Tạo bản ghi lộ trình học (Thêm logging rõ ràng)
    if suggested_topic_id:
        try:
            insert_learning_path(
                hoc_sinh_id=hoc_sinh_id,
                chu_de_id=suggested_topic_id, # UUID string
                bai_hoc_id=None, # Gợi ý cấp độ Chủ đề
                loai_goi_y=action,
                muc_do_de_xuat="biết", # Có thể dựa vào current_topic_info['muc_do']
                diem_truoc_goi_y=diem
            )
            print(f"✅ Đã chèn thành công gợi ý '{action}' cho Chủ đề ID: {suggested_topic_id}")
        except Exception as path_err:
             print(f"❌ LỖI TRUY VẤN: Không thể tạo lộ trình học cho Chủ đề {suggested_topic_id}. Lỗi: {path_err}")
             return None # Trả về None nếu insert thất bại


    return {
        "action": action,
        "suggested_topic_id": suggested_topic_id, # UUID string or None
        "model": model_version,
        "confidence": confidence
    }
