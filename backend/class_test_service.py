# ===============================================
# ⚙️ backend/class_test_service.py (Cập nhật logic sinh bài tập)
# ===============================================

import random
from backend.supabase_client import supabase
from datetime import datetime


def generate_class_test(
        lop_id: str, giao_vien_id: str, ten_bai: str, chu_de_id: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int  # <-- THAM SỐ MỚI
):
    """
    Sinh bài KIỂM TRA CHỦ ĐỀ cho lớp.
    Logic MỚI: Lấy câu hỏi theo 3 mức độ từ chu_de_id.
    """
    selected_question_ids = []

    try:
        # 1. Lấy câu "Biết"
        if so_cau_biet > 0:
            questions_biet = (supabase.table("cau_hoi").select("id")
                              .eq("chu_de_id", chu_de_id)
                              .eq("muc_do", "biết")
                              .execute().data or [])
            if len(questions_biet) < so_cau_biet:
                print(
                    f"Lỗi (KT): Không đủ {so_cau_biet} câu 'biết' cho chủ đề {chu_de_id}. Chỉ có {len(questions_biet)}.")
                return False  # Dừng lại nếu không đủ
            selected_question_ids.extend([q["id"] for q in random.sample(questions_biet, so_cau_biet)])

        # 2. Lấy câu "Hiểu"
        if so_cau_hieu > 0:
            questions_hieu = (supabase.table("cau_hoi").select("id")
                              .eq("chu_de_id", chu_de_id)
                              .eq("muc_do", "hiểu")
                              .execute().data or [])
            if len(questions_hieu) < so_cau_hieu:
                print(
                    f"Lỗi (KT): Không đủ {so_cau_hieu} câu 'hiểu' cho chủ đề {chu_de_id}. Chỉ có {len(questions_hieu)}.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_hieu, so_cau_hieu)])

        # 3. Lấy câu "Vận dụng"
        if so_cau_van_dung > 0:
            questions_van_dung = (supabase.table("cau_hoi").select("id")
                                  .eq("chu_de_id", chu_de_id)
                                  .eq("muc_do", "vận dụng")
                                  .execute().data or [])
            if len(questions_van_dung) < so_cau_van_dung:
                print(
                    f"Lỗi (KT): Không đủ {so_cau_van_dung} câu 'vận dụng' cho chủ đề {chu_de_id}. Chỉ có {len(questions_van_dung)}.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_van_dung, so_cau_van_dung)])

    except Exception as e:
        print(f"Lỗi khi truy vấn câu hỏi (KT): {e}")
        return False

    # Xáo trộn thứ tự các câu hỏi đã chọn
    random.shuffle(selected_question_ids)

    # Tạo bản ghi bai_tap (KIỂM TRA CHỦ ĐỀ)
    res_bai_tap = supabase.table("bai_tap").insert({
        "chu_de_id": chu_de_id,
        "bai_hoc_id": None,
        "tieu_de": ten_bai,
        "mo_ta": f"Bài kiểm tra chủ đề do GV ({giao_vien_id}) giao. (B:{so_cau_biet}, H:{so_cau_hieu}, VD:{so_cau_van_dung})",
        # Thêm mô tả
        "loai_bai_tap": "kiem_tra_chu_de",
        # Có thể thêm mức độ chung cho bài tập (ví dụ: 'tổng hợp') nếu cột bai_tap.muc_do cho phép
    }).execute()

    if not res_bai_tap.data:
        print("Lỗi khi tạo bản ghi bai_tap cho bài kiểm tra chủ đề.")
        return False

    bai_tap_id = res_bai_tap.data[0]["id"]
    links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
    supabase.table("bai_tap_cau_hoi").insert(links).execute()
    return True


def generate_practice_exercise(
        bai_hoc_id: str, giao_vien_id: str, ten_bai: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int  # <-- THAM SỐ MỚI
):
    """
    Sinh bài LUYỆN TẬP cho một BÀI HỌC cụ thể.
    Logic MỚI: Lấy câu hỏi theo 3 mức độ từ bai_hoc_id.
    """
    lesson_info = supabase.table("bai_hoc").select("chu_de_id").eq("id", bai_hoc_id).maybe_single().execute().data
    if not lesson_info or not lesson_info.get("chu_de_id"):
        print(f"Lỗi: Không tìm thấy thông tin chủ đề cho bài học {bai_hoc_id}")
        return False
    chu_de_id_of_lesson = lesson_info["chu_de_id"]

    selected_question_ids = []

    try:
        # 1. Lấy câu "Biết"
        if so_cau_biet > 0:
            questions_biet = (supabase.table("cau_hoi").select("id")
                              .eq("bai_hoc_id", bai_hoc_id)  # Lọc theo bai_hoc_id
                              .eq("muc_do", "biết")
                              .execute().data or [])
            if len(questions_biet) < so_cau_biet:
                print(
                    f"Lỗi (LT): Không đủ {so_cau_biet} câu 'biết' cho bài học {bai_hoc_id}. Chỉ có {len(questions_biet)}.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_biet, so_cau_biet)])

        # 2. Lấy câu "Hiểu"
        if so_cau_hieu > 0:
            questions_hieu = (supabase.table("cau_hoi").select("id")
                              .eq("bai_hoc_id", bai_hoc_id)
                              .eq("muc_do", "hiểu")
                              .execute().data or [])
            if len(questions_hieu) < so_cau_hieu:
                print(
                    f"Lỗi (LT): Không đủ {so_cau_hieu} câu 'hiểu' cho bài học {bai_hoc_id}. Chỉ có {len(questions_hieu)}.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_hieu, so_cau_hieu)])

        # 3. Lấy câu "Vận dụng"
        if so_cau_van_dung > 0:
            questions_van_dung = (supabase.table("cau_hoi").select("id")
                                  .eq("bai_hoc_id", bai_hoc_id)
                                  .eq("muc_do", "vận dụng")
                                  .execute().data or [])
            if len(questions_van_dung) < so_cau_van_dung:
                print(
                    f"Lỗi (LT): Không đủ {so_cau_van_dung} câu 'vận dụng' cho bài học {bai_hoc_id}. Chỉ có {len(questions_van_dung)}.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_van_dung, so_cau_van_dung)])

    except Exception as e:
        print(f"Lỗi khi truy vấn câu hỏi (LT): {e}")
        return False

    # Xáo trộn thứ tự các câu hỏi đã chọn
    random.shuffle(selected_question_ids)

    # Tạo bản ghi bai_tap (LUYỆN TẬP)
    res_bai_tap = supabase.table("bai_tap").insert({
        "chu_de_id": chu_de_id_of_lesson,
        "bai_hoc_id": bai_hoc_id,
        "tieu_de": ten_bai,
        "mo_ta": f"Bài luyện tập do GV ({giao_vien_id}) giao. (B:{so_cau_biet}, H:{so_cau_hieu}, VD:{so_cau_van_dung})",
        # Thêm mô tả
        "loai_bai_tap": "luyen_tap"
    }).execute()

    if not res_bai_tap.data:
        print("Lỗi khi tạo bản ghi bai_tap cho bài luyện tập.")
        return False

    bai_tap_id = res_bai_tap.data[0]["id"]
    links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
    supabase.table("bai_tap_cau_hoi").insert(links).execute()
    return True