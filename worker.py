# ===============================================
# 🤖 TTS Worker (Giải pháp Giả lập)
# Chạy độc lập: python worker.py
# (ĐÃ SỬA LỖI: Unresolved reference 'datetime')
# ===============================================
import time
import json
from datetime import datetime  # <-- THÊM DÒNG NÀY ĐỂ SỬA LỖI
from backend.supabase_client import supabase
from backend.tts_service import generate_and_upload_tts

# Cấu hình
POLL_INTERVAL = 10  # Kiểm tra CSDL mỗi 10 giây


def process_pending_tasks():
    """Lấy và xử lý các tác vụ TTS đang chờ."""
    try:
        # 1. Lấy các task "pending"
        res = supabase.table("task_queue").select("*").eq("status", "pending").eq("task_type", "tts_generation").limit(
            5).execute()
        tasks = res.data or []

        if not tasks:
            return False  # Không có task nào

        print(f"--- {time.ctime()} ---")
        print(f"Phát hiện {len(tasks)} nhiệm vụ TTS mới...")

        for task in tasks:
            task_id = task['id']
            payload = task.get('payload', {})
            question_id = payload.get('question_id')
            noi_dung = payload.get('noi_dung')

            if not question_id or not noi_dung:
                print(f"  [Lỗi Task {task_id}]: Payload không hợp lệ. Đánh dấu 'failed'.")
                supabase.table("task_queue").update({
                    "status": "failed",
                    "error_message": "Payload thiếu question_id hoặc noi_dung.",
                    "processed_at": datetime.now().isoformat()  # <-- SỬ DỤNG datetime
                }).eq("id", task_id).execute()
                continue

            print(f"  Đang xử lý Task {task_id} cho Câu hỏi {question_id}...")

            try:
                # 2. Gọi hàm tạo TTS (đây là tác vụ chậm)
                audio_url = generate_and_upload_tts(noi_dung, question_id)

                if audio_url:
                    # 3. Cập nhật bảng cau_hoi
                    supabase.table("cau_hoi").update({"audio_url": audio_url}).eq("id", question_id).execute()

                    # 4. Cập nhật task_queue -> 'completed'
                    supabase.table("task_queue").update({
                        "status": "completed",
                        "processed_at": datetime.now().isoformat()  # <-- SỬ DỤNG datetime
                    }).eq("id", task_id).execute()
                    print(f"  ✅ [Task {task_id}]: Hoàn thành!")
                else:
                    raise Exception("Hàm generate_and_upload_tts trả về None.")

            except Exception as e:
                # 5. Xử lý lỗi
                print(f"  ❌ [Task {task_id}]: Thất bại! Lỗi: {e}")
                supabase.table("task_queue").update({
                    "status": "failed",
                    "error_message": str(e),
                    "processed_at": datetime.now().isoformat()  # <-- SỬ DỤNG datetime
                }).eq("id", task_id).execute()

        return True  # Đã xử lý tasks

    except Exception as e:
        print(f"Lỗi nghiêm trọng trong vòng lặp worker: {e}")
        return False


# --- Vòng lặp chính của Worker ---
if __name__ == "__main__":
    print("====================================")
    print("🚀 AI TUTOR - TTS WORKER (Giả lập)")
    print("Đang khởi động...")
    print(f"Kiểm tra tác vụ mới mỗi {POLL_INTERVAL} giây.")
    print("Nhấn CTRL+C để dừng.")
    print("====================================")

    while True:
        try:
            processed = process_pending_tasks()
            if not processed:
                # Nếu không có task, nghỉ 10 giây
                time.sleep(POLL_INTERVAL)
            else:
                # Nếu có task, chỉ nghỉ 1 giây để xử lý nhanh
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nĐã nhận lệnh dừng. Tạm biệt!")
            break
        except Exception as e:
            print(f"Lỗi không xác định, nghỉ 30 giây: {e}")
            time.sleep(30)