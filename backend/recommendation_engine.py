# File: backend/recommendation_engine.py
# (NÂNG CẤP LÕI AI LẦN 2 - CẬP NHẬT "CHÌA KHÓA" ĐẦU VÀO)

import joblib
import pandas as pd
from backend.data_service import (
    get_topic_by_id,
    insert_learning_path,
    log_ai_recommendation,
    get_student_all_results # <-- THÊM MỚI (Để lấy kết quả mới nhất)
)
from backend.utils import normalize_score
from backend.supabase_client import supabase

# --- Cấu hình ---
MODEL_PATH = "backend/model_recommender.pkl" 

# =========================================================
# 1️⃣ (KHÔNG THAY ĐỔI) RULE-BASED ENGINE (Dùng làm Fallback)
# =========================================================
def recommend_rule_based_topic(diem_normalized: float, current_topic_info: dict):
    # ... (Giữ nguyên logic rule-based)
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
# 2️⃣ (ĐÃ CẬP NHẬT) ML ENGINE (Sử dụng Pipeline mới)
# =========================================================

def load_model():
    """Tải mô hình (Pipeline) nếu tồn tại."""
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception:
        return None

def recommend_ml_topic(student_features_df: pd.DataFrame):
    """
    Dự đoán gợi ý CHỦ ĐỀ bằng mô hình ML (Pipeline) mới.
    Args:
        student_features_df (pd.DataFrame): DataFrame chứa 5 cột features
                                            ['pct_biet', 'pct_hieu', 'pct_van_dung', 'lop', 'mon_hoc']
    """
    model = load_model()
    if not model:
        return None # Trả về None nếu không có model

    try:
        # Pipeline (model) đã bao gồm preprocessor (OneHotEncoder, StandardScaler)
        # nên chúng ta chỉ cần truyền DataFrame thô vào
        pred = model.predict(student_features_df)
        
        mapping = {0: "remediate", 1: "review", 2: "advance"}
        predicted_action = mapping.get(int(pred[0]), "review") 
        
        confidence = 0.9
        if hasattr(model, "predict_proba"):
            try:
                confidence = model.predict_proba(student_features_df)[0].max()
            except: pass

        return {"action": predicted_action, "confidence": confidence}

    except Exception as e:
        print(f"Lỗi khi dự đoán ML (Lần 2): {e}")
        return None


# =========================================================
# 3️⃣ (GIỮ NGUYÊN) HÀM HỖ TRỢ TÌM CHỦ ĐỀ TIẾP THEO
# =========================================================

def find_next_topic(lop: int, current_tuan: int, mon_hoc_name: str):
    # ... (Giữ nguyên logic find_next_topic)
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
# 4️⃣ (ĐÃ CẬP NHẬT) WRAPPER — SINH GỢI Ý (LÕI AI LẦN 2)
# =========================================================

def generate_recommendation(hoc_sinh_id: str, chu_de_id: str, diem: float, lop: int, tuan: int, mon_hoc_name: str):
    """
    (NÂNG CẤP LẦN 2) Sinh gợi ý dựa trên 6 cột điểm %.
    """
    
    # 1. Lấy thông tin chủ đề hiện tại (cần prerequisite_id)
    current_topic_info = get_topic_by_id(chu_de_id)
    if not current_topic_info:
        print(f"Lỗi: Không tìm thấy thông tin chủ đề ID {chu_de_id}")
        return None
    
    # 2. (MỚI) Lấy bản ghi ket_qua_test MỚI NHẤT (để lấy 6 cột điểm)
    # Lưu ý: Hàm này giả định ui_quiz_engine.py đã LƯU KẾT QUẢ XONG
    latest_result = None
    try:
        # Lấy 1 kết quả mới nhất của học sinh này (giả định đó là bài vừa nộp)
        res_data = get_student_all_results(hoc_sinh_id) 
        if res_data:
            latest_result = res_data[0] # Lấy bản ghi mới nhất
    except Exception as e:
        print(f"Lỗi khi lấy kết quả test mới nhất: {e}")
        latest_result = None

    # 3. Chuẩn bị Features (X) cho Model Mới
    student_features_df = None
    if latest_result:
        try:
            # Lấy điểm đạt được
            diem_biet = float(latest_result.get('diem_biet', 0))
            diem_hieu = float(latest_result.get('diem_hieu', 0))
            diem_van_dung = float(latest_result.get('diem_van_dung', 0))
            # Lấy điểm tối đa
            tong_biet = float(latest_result.get('tong_diem_biet', 0))
            tong_hieu = float(latest_result.get('tong_diem_hieu', 0))
            tong_van_dung = float(latest_result.get('tong_diem_van_dung', 0))

            # Tính toán Tỷ lệ %
            pct_biet = (diem_biet / tong_biet) if tong_biet > 0 else 0
            pct_hieu = (diem_hieu / tong_hieu) if tong_hieu > 0 else 0
            pct_van_dung = (diem_van_dung / tong_van_dung) if tong_van_dung > 0 else 0

            # Tạo DataFrame (1 dòng) cho pipeline
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

    # 4. Gọi Model và Fallback
    action = "review" # Mặc định
    confidence = 0.5
    model_version = "Rule-based (Default)"
    suggested_topic_id = str(chu_de_id) 

    ml_rec = None
    if student_features_df is not None:
        ml_rec = recommend_ml_topic(student_features_df)
        
    if ml_rec:
        action = ml_rec["action"]
        confidence = ml_rec.get("confidence", 0.9)
        model_version = "AI Model (Lần 2 - Tỷ lệ %)"
    else:
        # Fallback sang rule-based (dùng điểm tổng)
        normalized_score_fallback = normalize_score(diem, max_score=10)
        rule_rec = recommend_rule_based_topic(normalized_score_fallback, current_topic_info)
        action = rule_rec["action"]
        suggested_topic_id = rule_rec["suggested_topic_id"]
        confidence = rule_rec["confidence"]
        model_version = "Rule-based (Fallback)"

    # 5. Xác định suggested_topic_id cuối cùng
    if action == "advance":
        next_topic_id = find_next_topic(lop, tuan, mon_hoc_name)
        if next_topic_id:
            suggested_topic_id = next_topic_id
        else:
            action = "review"
            suggested_topic_id = str(chu_de_id)
            print(f"Hoàn thành lộ trình Môn '{mon_hoc_name}' cho lớp {lop}.")
    elif action == "remediate" or action == "review":
         # Nếu ML gợi ý (hoặc Fallback), chúng ta cần lấy ID từ Rule-based gốc
         normalized_score_fallback = normalize_score(diem, max_score=10)
         rule_rec_fallback = recommend_rule_based_topic(normalized_score_fallback, current_topic_info)
         suggested_topic_id = rule_rec_fallback["suggested_topic_id"]
    else:
        action = "review"
        suggested_topic_id = str(chu_de_id)


    # 6. Ghi log AI
    try:
        # Log input features (cả cũ và mới)
        input_features_log = {
            "diem_tong_thang_10": diem,
            "lop": lop,
            "tuan": tuan,
            "mon_hoc": mon_hoc_name,
            "features_df_v2": student_features_df.to_dict('records')[0] if student_features_df is not None else None
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

    # 7. Tạo bản ghi lộ trình học (Giữ nguyên)
    if suggested_topic_id:
        try:
            # (SỬA LỖI): Đảm bảo gọi hàm insert_learning_path đã được sửa lỗi (trả về None thay vì raise e)
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