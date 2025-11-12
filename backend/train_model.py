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
    # Lấy tất cả dữ liệu
    res = supabase.table('ket_qua_test').select('*').execute()
    data = res.data
    if not data:
        print("Không có dữ liệu trong bảng 'ket_qua_test'.")
        return None

    df = pd.DataFrame(data)

    # --- SỬA LỖI KEYERROR: Lấy cột 'tuan_kiem_tra' và đổi tên thành 'tuan' ---
    # Đảm bảo cột cần thiết tồn tại trước khi xử lý
    if 'tuan_kiem_tra' not in df.columns:
        print("Lỗi: Thiếu cột 'tuan_kiem_tra' trong dữ liệu tải về. Vui lòng kiểm tra schema CSDL.")
        return None

    # Đổi tên cột để logic phía dưới có thể sử dụng tên feature 'tuan'
    df = df.rename(columns={'tuan_kiem_tra': 'tuan'})
    # -------------------------------------------------------------------------

    # Xử lý kiểu dữ liệu an toàn hơn
    df['diem'] = pd.to_numeric(df['diem'], errors='coerce')
    df = df.dropna(subset=['diem'])
    if df.empty:
        print("Không có dữ liệu 'diem' hợp lệ sau khi làm sạch.")
        return None

    # Chuẩn hóa điểm
    df['score_norm'] = df['diem'].astype(float) / 10.0

    # Áp dụng hàm map_action để tạo biến y mới
    y = df['score_norm'].apply(map_action)

    # Lấy features X
    # Kiểm tra cột 'tuan' (đã được đổi tên)
    if 'tuan' not in df.columns:
        # Trường hợp này không thể xảy ra nếu đổi tên thành công ở trên
        print("Lỗi: Cột 'tuan' bị thiếu sau khi đổi tên.")
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