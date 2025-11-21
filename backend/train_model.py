# File: backend/train_model.py
# (BẢN HOÀN CHỈNH - Đã sửa lỗi import joblib và đường dẫn)

import joblib
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from supabase import create_client
from dotenv import load_dotenv
import os

# --- CẤU HÌNH ĐƯỜNG DẪN TUYỆT ĐỐI ---
# Lấy thư mục chứa file script hiện tại (tức là thư mục 'backend')
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Xác định đường dẫn file .env (nằm ở thư mục gốc, tức là cha của backend)
BASE_DIR = os.path.dirname(CURRENT_DIR)
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load .env từ đường dẫn tuyệt đối
load_dotenv(ENV_PATH)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Đường dẫn tuyệt đối để lưu model (lưu ngay trong thư mục backend)
MODEL_PATH = os.path.join(CURRENT_DIR, 'model_recommender.pkl')


# --- HÀM TẠO TARGET (Y) MỚI ---
def map_action_smart(row):
    """
    Tạo nhãn (Y) dựa trên TỶ LỆ % sư phạm chi tiết.
    """
    pct_biet = row.get('pct_biet', 0)
    pct_hieu = row.get('pct_hieu', 0)
    pct_van_dung = row.get('pct_van_dung', 0)
    pct_tong = row.get('pct_tong', 0)  # Điểm tổng thang 10

    # 1. 🟥 HỌC LẠI (Remediate): Nếu hổng kiến thức nền tảng
    if (pct_biet < 0.5) or (pct_hieu < 0.5):
        return 0  # Remediate

    # 2. 🟩 HỌC TIẾP (Advance): Nếu làm chủ cả kiến thức nâng cao
    if (pct_tong >= 0.85) and (pct_van_dung >= 0.7):
        return 2  # Advance

    # 3. 🟨 ÔN TẬP (Review): Các trường hợp còn lại
    return 1  # Review


def calculate_percentages(df):
    """Hàm helper để tính toán các cột tỷ lệ % một cách an toàn."""
    df['pct_biet'] = df.apply(lambda row: row['diem_biet'] / row['tong_diem_biet'] if row['tong_diem_biet'] > 0 else 0,
                              axis=1)
    df['pct_hieu'] = df.apply(lambda row: row['diem_hieu'] / row['tong_diem_hieu'] if row['tong_diem_hieu'] > 0 else 0,
                              axis=1)
    df['pct_van_dung'] = df.apply(
        lambda row: row['diem_van_dung'] / row['tong_diem_van_dung'] if row['tong_diem_van_dung'] > 0 else 0, axis=1)
    df['pct_tong'] = df['diem'] / 10.0
    return df


def load_data_from_supabase():
    """Tải dữ liệu HUẤN LUYỆN ĐÃ ĐƯỢC LỌC SẠCH (Lần 2)."""

    # 1. Lấy dữ liệu kết quả (6 cột điểm VÀ loai_bai_tap)
    res_kq = supabase.table('ket_qua_test').select(
        'diem, lop, chu_de_id, bai_tap(loai_bai_tap),'
        'diem_biet, diem_hieu, diem_van_dung,'
        'tong_diem_biet, tong_diem_hieu, tong_diem_van_dung'
    ).execute()

    df_kq = pd.DataFrame(res_kq.data)
    if df_kq.empty:
        print("Không có dữ liệu trong bảng 'ket_qua_test'.")
        return None

    # 2. Lấy dữ liệu chủ đề
    res_cd = supabase.table('chu_de').select('id, mon_hoc').execute()
    df_cd = pd.DataFrame(res_cd.data)
    if df_cd.empty:
        print("Không có dữ liệu trong bảng 'chu_de'.")
        return None

    # 3. Merge
    df_cd = df_cd.rename(columns={'id': 'chu_de_id'})
    df_kq['chu_de_id'] = df_kq['chu_de_id'].astype(str)
    df_cd['chu_de_id'] = df_cd['chu_de_id'].astype(str)

    df = pd.merge(df_kq, df_cd, on='chu_de_id', how='left')

    # 4. Xử lý Dữ liệu
    df['loai_bai_tap'] = df['bai_tap'].apply(lambda x: x.get('loai_bai_tap') if isinstance(x, dict) else None)

    numeric_cols = [
        'diem', 'lop',
        'diem_biet', 'diem_hieu', 'diem_van_dung',
        'tong_diem_biet', 'tong_diem_hieu', 'tong_diem_van_dung'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=numeric_cols + ['mon_hoc', 'loai_bai_tap'])
    if df.empty:
        print("Không có dữ liệu hợp lệ sau khi làm sạch.")
        return None

    # 5. LỌC DỮ LIỆU HUẤN LUYỆN
    # Chỉ lấy Bài Kiểm tra Chủ đề
    df_train = df[df['loai_bai_tap'] == 'kiem_tra_chu_de'].copy()

    if df_train.empty:
        print("Không tìm thấy dữ liệu 'kiem_tra_chu_de' nào.")
        return None

    # Chỉ lấy dữ liệu MỚI (có tổng điểm > 0)
    df_train['tong_cac_muc_do'] = df_train['tong_diem_biet'] + df_train['tong_diem_hieu'] + df_train[
        'tong_diem_van_dung']
    df_train = df_train[df_train['tong_cac_muc_do'] > 0].copy()

    if df_train.empty:
        print("Không tìm thấy dữ liệu huấn luyện MỚI (chưa có điểm Hiểu/Vận dụng).")
        return None

    # 6. Tạo Features & Target
    df_train = calculate_percentages(df_train)
    y = df_train.apply(map_action_smart, axis=1)

    feature_cols = ['pct_biet', 'pct_hieu', 'pct_van_dung', 'lop', 'mon_hoc']
    X = df_train[feature_cols]

    print(f"Dữ liệu huấn luyện đã lọc: {len(X)} mẫu.")
    print("Phân phối các hành động (y) mới:")
    print(y.value_counts(normalize=True))

    return X, y


def train():
    """Huấn luyện model (Pipeline) và lưu lại."""
    print("Bắt đầu quá trình huấn luyện Lõi AI Mới (Lần 2 - Tỷ lệ %)...")
    data = load_data_from_supabase()

    if data is None:
        print('Không có dữ liệu huấn luyện hợp lệ.')
        return

    X, y = data

    if len(X) < 5:  # Giảm ngưỡng kiểm tra để test nhanh
        print(f"Lỗi: Chỉ có {len(X)} mẫu dữ liệu. Cần nhiều hơn.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- Pipeline ---
    numeric_features = ['pct_biet', 'pct_hieu', 'pct_van_dung']
    numeric_transformer = StandardScaler()
    categorical_features = ['lop', 'mon_hoc']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    model = DecisionTreeClassifier(max_depth=10, random_state=42, class_weight='balanced')

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

    print(f"Huấn luyện Pipeline với {len(X_train)} mẫu...")
    pipeline.fit(X_train, y_train)

    print("\n--- Đánh giá Model trên tập Test ---")
    if len(X_test) > 0:
        y_pred = pipeline.predict(X_test)
        # target_names cần khớp với số lượng class thực tế trong y
        unique_classes = sorted(y.unique())
        target_names = []
        if 0 in unique_classes: target_names.append('Remediate (0)')
        if 1 in unique_classes: target_names.append('Review (1)')
        if 2 in unique_classes: target_names.append('Advance (2)')

        print(classification_report(y_test, y_pred, target_names=target_names))
    else:
        print("Tập test quá nhỏ để đánh giá.")

    # --- Lưu Model ---
    try:
        joblib.dump(pipeline, MODEL_PATH)
        print(f"\n✅ Đã lưu Pipeline (Model Mới) thành công vào: {MODEL_PATH}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu model: {e}")


if __name__ == '__main__':
    train()