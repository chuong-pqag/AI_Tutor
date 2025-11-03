# ===============================================
# 💾 Backend Data Service Layer (Sửa lỗi đếm cuối cùng)
# ===============================================
from backend.supabase_client import supabase
from datetime import datetime
import json
import pandas as pd


# =========================================================
# 1️⃣ HỌC SINH (Giữ nguyên)
# =========================================================
def get_student(student_id: str):
    try:
        res = supabase.table("hoc_sinh").select("*").eq("id", student_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy thông tin học sinh {student_id}: {e}"); return None


def get_all_students(lop_id: str = None):
    try:
        query = supabase.table("hoc_sinh").select("*")
        if lop_id: query = query.eq("lop_id", lop_id)
        res = query.order("ho_ten").execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy danh sách học sinh: {e}"); return []


def insert_student(ho_ten: str, lop_id: str, ma_hoc_sinh: str, mat_khau: str, email: str = None, gioi_tinh: str = None,
                   ngay_sinh: str = None):
    data = {"ho_ten": ho_ten, "lop_id": lop_id, "ma_hoc_sinh": ma_hoc_sinh, "mat_khau": mat_khau, "email": email,
            "gioi_tinh": gioi_tinh, "ngay_sinh": ngay_sinh}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("hoc_sinh").insert(data).execute()
    except Exception as e:
        print(f"Lỗi khi thêm học sinh {ma_hoc_sinh}: {e}"); raise e


# =========================================================
# 2️⃣ MÔN HỌC & CHỦ ĐỀ (Giữ nguyên)
# =========================================================
def get_subjects_by_grade(lop: int):
    if lop is None: return []
    try:
        lop_int = int(lop)
    except (ValueError, TypeError):
        return []
    try:
        filter_value = f'[{lop_int}]'
        query = supabase.table("mon_hoc").select("id, ten_mon").filter("khoi_ap_dung", "cs", filter_value)
        res = query.execute()
        if hasattr(res, 'data'):
            if res.data is None: return []
            return res.data
        else:
            return []
    except Exception as e:
        print(f"Lỗi Exception khi truy vấn Supabase (get_subjects_by_grade): {e}"); return []


def get_topics_by_subject_and_class(mon_hoc_ten: str, lop: int):
    if lop is None or not mon_hoc_ten: return []
    try:
        res = supabase.table("chu_de").select("id, ten_chu_de, tuan, mon_hoc").eq("mon_hoc", mon_hoc_ten).eq("lop",
                                                                                                             lop).order(
            "tuan", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy chủ đề theo môn '{mon_hoc_ten}', lớp {lop}: {e}"); return []


def get_all_topics(mon_hoc: str, lop: int):
    return get_topics_by_subject_and_class(mon_hoc, lop)


def get_topic_by_id(chu_de_id: str):
    try:
        res = supabase.table("chu_de").select("*").eq("id", chu_de_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy chủ đề ID {chu_de_id}: {e}"); return None


# =========================================================
# 📝 BÀI HỌC (Giữ nguyên)
# =========================================================
def get_lessons_by_topic(chu_de_id: str):
    try:
        res = supabase.table("bai_hoc").select("*").eq("chu_de_id", chu_de_id).order("thu_tu", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài học cho chủ đề {chu_de_id}: {e}"); return []


def get_lesson_by_id(bai_hoc_id: str):
    try:
        res = supabase.table("bai_hoc").select("*").eq("id", bai_hoc_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài học ID {bai_hoc_id}: {e}"); return None


def insert_lesson(chu_de_id: str, ten_bai_hoc: str, thu_tu: int = 0, mo_ta: str = None, noi_dung_pdf_url: str = None):
    data = {"chu_de_id": chu_de_id, "ten_bai_hoc": ten_bai_hoc, "thu_tu": thu_tu, "mo_ta": mo_ta,
            "noi_dung_pdf_url": noi_dung_pdf_url}
    data = {k: v for k, v in data.items() if v is not None};
    try:
        return supabase.table("bai_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm bài học: {e}"); raise e


def update_lesson(bai_hoc_id: str, update_data: dict):
    allowed_keys = {"chu_de_id", "ten_bai_hoc", "thu_tu", "mo_ta", "noi_dung_pdf_url"};
    data_to_update = {k: v for k, v in update_data.items() if k in allowed_keys}
    if not data_to_update: return None;
    try:
        return supabase.table("bai_hoc").update(data_to_update).eq("id", bai_hoc_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật bài học: {e}"); raise e


def delete_lesson(bai_hoc_id: str):
    try:
        return supabase.table("bai_hoc").delete().eq("id", bai_hoc_id).execute()
    except Exception as e:
        print(f"Lỗi xóa bài học: {e}"); raise e


# =========================================================
# 🎥 VIDEO BÀI GIẢNG (Giữ nguyên)
# =========================================================
def get_videos_by_lesson(bai_hoc_id: str):
    try:
        res = supabase.table("video_bai_giang").select("*").eq("bai_hoc_id", bai_hoc_id).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy video cho bài học {bai_hoc_id}: {e}"); return []


def insert_video(bai_hoc_id: str, tieu_de: str, url: str, mo_ta: str = None):
    data = {"bai_hoc_id": bai_hoc_id, "tieu_de": tieu_de, "url": url, "mo_ta": mo_ta};
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("video_bai_giang").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm video: {e}"); raise e


def update_video(video_id: str, update_data: dict):
    allowed_keys = {"bai_hoc_id", "tieu_de", "url", "mo_ta"};
    data_to_update = {k: v for k, v in update_data.items() if k in allowed_keys}
    if not data_to_update: return None;
    try:
        return supabase.table("video_bai_giang").update(data_to_update).eq("id", video_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật video: {e}"); raise e


def delete_video(video_id: str):
    try:
        return supabase.table("video_bai_giang").delete().eq("id", video_id).execute()
    except Exception as e:
        print(f"Lỗi xóa video: {e}"); raise e


# =========================================================
# 🧩 BÀI TẬP (Giữ nguyên)
# =========================================================
def get_practice_exercises_by_lesson(bai_hoc_id: str):
    try:
        res = supabase.table("bai_tap").select("*").eq("bai_hoc_id", bai_hoc_id).eq("loai_bai_tap", "luyen_tap").order(
            "created_at", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài luyện tập cho bài học {bai_hoc_id}: {e}"); return []


def get_topic_test_by_topic(chu_de_id: str):
    try:
        res = supabase.table("bai_tap").select("*").eq("chu_de_id", chu_de_id).eq("loai_bai_tap",
                                                                                  "kiem_tra_chu_de").limit(
            1).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài kiểm tra chủ đề {chu_de_id}: {e}"); return None


def get_exercise_by_id(bai_tap_id: str):
    try:
        res = supabase.table("bai_tap").select("*").eq("id", bai_tap_id).maybe_single().execute(); return res.data
    except Exception as e:
        print(f"Lỗi lấy bài tập ID {bai_tap_id}: {e}"); return None


def insert_exercise(tieu_de: str, loai_bai_tap: str, chu_de_id: str = None, bai_hoc_id: str = None, mo_ta: str = None,
                    muc_do: str = 'biết'):
    if loai_bai_tap == 'luyen_tap' and not bai_hoc_id: raise ValueError("Bài luyện tập phải có bai_hoc_id.");
    if loai_bai_tap == 'kiem_tra_chu_de' and not chu_de_id: raise ValueError("Bài kiểm tra chủ đề phải có chu_de_id.");
    data = {"tieu_de": tieu_de, "loai_bai_tap": loai_bai_tap, "chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id,
            "mo_ta": mo_ta, "muc_do": muc_do};
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("bai_tap").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm bài tập: {e}"); raise e


def add_questions_to_exercise(bai_tap_id: str, cau_hoi_ids: list):
    if not cau_hoi_ids: return None; links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in cau_hoi_ids];
    try:
        return supabase.table("bai_tap_cau_hoi").insert(links, upsert=False).execute()
    except Exception as e:
        print(f"Lỗi thêm câu hỏi vào bài tập: {e}"); raise e


# =========================================================
# ❓ CÂU HỎI (ĐÃ CẬP NHẬT)
# =========================================================
def get_questions_by_topic_for_admin(chu_de_id: str):
    try:
        res = supabase.table("cau_hoi").select("*").eq("chu_de_id", chu_de_id).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi cho chủ đề {chu_de_id}: {e}"); return []


# ===============================================
# ---- HÀM get_question_counts (ĐÃ SỬA LỖI) ----
# ===============================================
# ===============================================
# ---- HÀM get_question_counts (ĐÃ SỬA LỖI) ----
# ===============================================
def get_question_counts(chu_de_id: str = None, bai_hoc_id: str = None):
    """
    Đếm số lượng câu hỏi theo từng mức độ (biết, hiểu, vận dụng)
    cho một chủ đề hoặc một bài học cụ thể.
    SỬ DỤNG 3 TRUY VẤN RIÊNG BIỆT ĐỂ ĐẢM BẢO ĐỘ CHÍNH XÁC.
    """
    counts = {'biết': 0, 'hiểu': 0, 'vận dụng': 0}  # Khởi tạo dict đếm

    if not chu_de_id and not bai_hoc_id:
        print("DEBUG (get_question_counts): Không có ID, trả về 0")
        return counts  # Trả về 0 nếu không có ID

    # Xác định cột và giá trị để lọc
    filter_col = "bai_hoc_id" if bai_hoc_id else "chu_de_id"
    filter_val = bai_hoc_id if bai_hoc_id else chu_de_id

    try:
        # ---- SỬA LỖI LOGIC: Xây dựng 3 truy vấn đầy đủ ----

        # 1. Đếm 'biết'
        res_biet = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "biết") \
            .execute()
        counts['biết'] = res_biet.count

        # 2. Đếm 'hiểu'
        res_hieu = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "hiểu") \
            .execute()
        counts['hiểu'] = res_hieu.count

        # 3. Đếm 'vận dụng'
        res_van_dung = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "vận dụng") \
            .execute()
        counts['vận dụng'] = res_van_dung.count

        print(f"DEBUG (get_question_counts): Lọc theo {filter_col}={filter_val}. Counts={counts}")
        return counts

    except Exception as e:
        print(f"Lỗi khi đếm câu hỏi (get_question_counts): {e}")
        return counts  # Trả về 0 nếu có lỗi


# ===============================================
# ---- KẾT THÚC HÀM get_question_counts ----
# ===============================================
# ===============================================
# ---- KẾT THÚC HÀM get_question_counts ----
# ===============================================

def get_questions_for_exercise(bai_tap_id: str):
    """Lấy danh sách câu hỏi cho một BÀI TẬP cụ thể."""
    try:
        res_links = supabase.table("bai_tap_cau_hoi").select("cau_hoi_id").eq("bai_tap_id", bai_tap_id).execute()
        if not res_links.data: return []
        question_ids = [link['cau_hoi_id'] for link in res_links.data]
        if not question_ids: return []

        res_questions = supabase.table("cau_hoi").select(
            "id, noi_dung, dap_an_dung, dap_an_khac, muc_do, diem_so, loai_cau_hoi").in_("id", question_ids).execute()
        if not res_questions.data: return []

        questions_data = res_questions.data
        questions = []
        for q in questions_data:
            lua_chon_raw = q.get("dap_an_khac") or []
            lua_chon = [str(opt) for opt in lua_chon_raw]
            dap_an_dung_raw = q.get("dap_an_dung") if isinstance(q.get("dap_an_dung"), list) else []
            dap_an_dung = [str(ans) for ans in dap_an_dung_raw]
            loai_cau_hoi = q.get("loai_cau_hoi", "mot_lua_chon")
            questions.append({
                "id": str(q["id"]),
                "noi_dung": q["noi_dung"],
                "loai_cau_hoi": loai_cau_hoi,
                "lua_chon": lua_chon,
                "dap_an_dung": dap_an_dung,
                "muc_do": q.get("muc_do", "biết"),
                "diem_so": q.get("diem_so", 1)
            })
        return questions
    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi cho bài tập {bai_tap_id}: {e}")
        return []


def insert_question(chu_de_id: str, loai_cau_hoi: str, noi_dung: str, dap_an_dung: list, dap_an_khac: list = None,
                    muc_do: str = 'biết', diem_so: int = 1, bai_hoc_id: str = None):
    data = {"chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id, "loai_cau_hoi": loai_cau_hoi, "noi_dung": noi_dung,
            "dap_an_dung": dap_an_dung, "dap_an_khac": dap_an_khac or [], "muc_do": muc_do, "diem_so": diem_so}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("cau_hoi").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm câu hỏi: {e}")
        raise e


# ... (Giữ nguyên tất cả các hàm còn lại: save_test_result, get_student_results_by_topic, v.v...)
def save_test_result(hoc_sinh_id: str, bai_tap_id: str, chu_de_id: str, diem: float, so_cau_dung: int, tong_cau: int,
                     tuan_kiem_tra: int, lop: int):
    data = {"hoc_sinh_id": hoc_sinh_id, "bai_tap_id": bai_tap_id, "chu_de_id": chu_de_id, "diem": diem,
            "so_cau_dung": so_cau_dung, "tong_cau": tong_cau, "tuan_kiem_tra": tuan_kiem_tra, "lop": lop,
            "ngay_kiem_tra": datetime.now().isoformat()}
    try:
        return supabase.table("ket_qua_test").insert(data).execute()
    except Exception as e:
        print(f"Lỗi lưu kết quả test: {e}"); return None


def get_student_results_by_topic(hoc_sinh_id: str, chu_de_id: str):
    test_exercise = get_topic_test_by_topic(chu_de_id)
    if not test_exercise: return []
    try:
        res = supabase.table("ket_qua_test").select("*").eq("hoc_sinh_id", hoc_sinh_id).eq("bai_tap_id",
                                                                                           test_exercise['id']).order(
            "ngay_kiem_tra", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy KQ theo chủ đề: {e}"); return []


def get_student_all_results(hoc_sinh_id: str):
    try:
        res = supabase.table("ket_qua_test").select("*, bai_tap(tieu_de, loai_bai_tap), chu_de(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("ngay_kiem_tra", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy tất cả KQ: {e}"); return []


def insert_learning_path(hoc_sinh_id: str, loai_goi_y: str, chu_de_id: str = None, bai_hoc_id: str = None,
                         muc_do_de_xuat: str = "biết", diem_truoc_goi_y: float = None):
    data = {"hoc_sinh_id": hoc_sinh_id, "loai_goi_y": loai_goi_y, "chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id,
            "muc_do_de_xuat": muc_do_de_xuat, "diem_truoc_goi_y": diem_truoc_goi_y}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("lo_trinh_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm lộ trình: {e}"); raise e


def update_learning_status(lo_trinh_id: str, trang_thai: str):
    try:
        return supabase.table("lo_trinh_hoc").update({"trang_thai": trang_thai}).eq("id", lo_trinh_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật trạng thái lộ trình: {e}"); raise e


def get_learning_paths(hoc_sinh_id: str):
    try:
        res = supabase.table("lo_trinh_hoc").select(
            "*, suggested_lesson:bai_hoc_id(ten_bai_hoc), suggested_topic:chu_de_id(ten_chu_de)").eq("hoc_sinh_id",
                                                                                                     hoc_sinh_id).order(
            "ngay_goi_y", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy lộ trình: {e}"); return []


def log_learning_activity(hoc_sinh_id: str, hanh_dong: str, noi_dung: str, chu_de_id: str = None,
                          bai_hoc_id: str = None):
    data = {"hoc_sinh_id": hoc_sinh_id, "chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id, "hanh_dong": hanh_dong,
            "noi_dung": noi_dung, "thoi_gian": datetime.now().isoformat()}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("lich_su_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi ghi lịch sử học: {e}")


def get_learning_history(hoc_sinh_id: str):
    try:
        res = supabase.table("lich_su_hoc").select("*, lesson:bai_hoc_id(ten_bai_hoc), topic:chu_de_id(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("thoi_gian", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy lịch sử học: {e}"); return []


def log_ai_recommendation(hoc_sinh_id: str, input_features: dict, action: str, chu_de_nguon: str,
                          chu_de_de_xuat: str = None, bai_hoc_de_xuat: str = None, model_version: str = "rule-based",
                          confidence: float = None):
    data = {"hoc_sinh_id": hoc_sinh_id, "input_features": input_features, "action": action,
            "chu_de_nguon": chu_de_nguon, "chu_de_de_xuat": chu_de_de_xuat, "bai_hoc_de_xuat": bai_hoc_de_xuat,
            "model_version": model_version, "confidence": confidence}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("ai_recommendation_log").insert(data).execute()
    except Exception as e:
        print(f"Lỗi ghi log AI: {e}"); return None


def get_ai_logs(hoc_sinh_id: str):
    try:
        res = supabase.table("ai_recommendation_log").select(
            "*, suggested_lesson:bai_hoc_de_xuat(ten_bai_hoc), suggested_topic:chu_de_de_xuat(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy log AI: {e}"); return []