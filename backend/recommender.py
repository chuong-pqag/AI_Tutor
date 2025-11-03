# Simple rule-based recommender and placeholder to plug ML model later
import joblib
MODEL_PATH = 'backend/model_recommender.pkl'

def recommend_rule_based(diem_normalized, chu_de_row):
    # diem_normalized: 0..1
    if diem_normalized < 0.6:
        # recommend prerequisite if available
        prereq = chu_de_row.get('prerequisite_id') if isinstance(chu_de_row, dict) else None
        return {'action':'remediate', 'chu_de_id': prereq or chu_de_row.get('id')}
    elif diem_normalized < 0.8:
        return {'action':'review', 'chu_de_id': chu_de_row.get('id')}
    else:
        return {'action':'advance', 'chu_de_id': None}

def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None

def recommend_ml(features_df):
    model = load_model()
    if model is None:
        return None
    preds = model.predict(features_df)
    return preds
