import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MODEL_PATH = 'backend/model_recommender.pkl'


# --- THÊM HÀM ÁNH XẠ ---
def map_action(score_norm):
    """Ánh xạ điểm chuẩn hóa sang hành động (0, 1, 2)."""
    if score_norm < 0.6:
        return 0  # remediate
    elif score_norm < 0.8:
        return 1  # review
    else:
        return 2  # advance


# --- KẾT THÚC HÀM ÁNH XẠ ---

def load_data_from_supabase():
    """Tải dữ liệu từ Supabase và chuẩn bị features (X) và target (y)."""
    res = supabase.table('ket_qua_test').select('*').execute()
    data = res.data
    if not data:
        print("Không có dữ liệu trong bảng 'ket_qua_test'.")
        return None

    df = pd.DataFrame(data)

    # --- Xử lý kiểu dữ liệu an toàn hơn ---
    # Chuyển đổi 'diem' sang số, lỗi sẽ thành NaN
    df['diem'] = pd.to_numeric(df['diem'], errors='coerce')
    # Loại bỏ các dòng có điểm không hợp lệ
    df = df.dropna(subset=['diem'])
    if df.empty:
        print("Không có dữ liệu 'diem' hợp lệ sau khi làm sạch.")
        return None

    # Chuẩn hóa điểm
    df['score_norm'] = df['diem'].astype(float) / 10.0

    # --- SỬA LOGIC TẠO BIẾN MỤC TIÊU (y) ---
    # Bỏ dòng y = df['is_pass']
    # y = df['is_pass'] = (df['diem'].astype(float) >= 7).astype(int)

    # Áp dụng hàm map_action để tạo biến y mới
    y = df['score_norm'].apply(map_action)
    # --- KẾT THÚC SỬA LOGIC ---

    # Giữ nguyên features X (có thể thêm features khác sau này)
    X = df[['score_norm', 'tuan']]  # Đảm bảo cột 'tuan' cũng tồn tại và hợp lệ
    # Kiểm tra cột 'tuan'
    if 'tuan' not in df.columns:
        print("Lỗi: Thiếu cột 'tuan' trong dữ liệu tải về.")
        return None
    # Chuyển đổi 'tuan' sang số nếu cần, xử lý lỗi
    df['tuan'] = pd.to_numeric(df['tuan'], errors='coerce')
    df = df.dropna(subset=['tuan'])  # Loại bỏ dòng nếu 'tuan' không hợp lệ
    if df.empty:
        print("Không có dữ liệu hợp lệ sau khi kiểm tra cột 'tuan'.")
        return None
    X = df[['score_norm', 'tuan']].astype(float)  # Đảm bảo X là kiểu float
    y = y.loc[X.index]  # Đảm bảo y khớp với X sau khi lọc NaN

    # Kiểm tra lại kích thước
    if X.empty or y.empty or len(X) != len(y):
        print("Lỗi: Dữ liệu X hoặc y rỗng hoặc không khớp kích thước sau khi xử lý.")
        return None

    print(f"Dữ liệu sẵn sàng: {len(X)} mẫu.")
    print("Phân phối các hành động (y):")
    print(y.value_counts(normalize=True))

    return X, y


def train():
    """Huấn luyện model Decision Tree và lưu lại."""
    print("Bắt đầu quá trình huấn luyện model...")
    data = load_data_from_supabase()

    if data is None:
        print('Không có dữ liệu hợp lệ để huấn luyện. Vui lòng kiểm tra bảng "ket_qua_test".')
        return

    X, y = data

    # Khởi tạo model (có thể điều chỉnh tham số)
    # class_weight='balanced' giúp xử lý nếu số lượng các hành động không đều
    model = DecisionTreeClassifier(max_depth=5, random_state=42, class_weight='balanced')

    print(f"Huấn luyện model DecisionTreeClassifier với {len(X)} mẫu...")
    model.fit(X, y)

    # Lưu model
    try:
        joblib.dump(model, MODEL_PATH)
        print(f"Đã lưu model huấn luyện vào: {MODEL_PATH}")
    except Exception as e:
        print(f"Lỗi khi lưu model: {e}")


if __name__ == '__main__':
    train()  # Chạy trực tiếp để huấn luyện