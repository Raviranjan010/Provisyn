"""Training script for tabular supply chain risk models.
Evaluates models on train/test split and records authentic metrics in MODEL_VERSIONS.
"""
import json
import pickle
from pathlib import Path
from datetime import datetime
import pandas as pd

from backend.core.logging import get_logger
from backend.data.repository import BaseRepository, get_repository
from ml.risk.model import extract_vendor_features, TabularRiskPipeline

logger = get_logger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def train_and_register_risk_models(repo: BaseRepository) -> TabularRiskPipeline:
    """Train risk regressor and classifier, calculate genuine metrics, and save to MODEL_VERSIONS."""
    logger.info("Extracting vendor operational and graph features for ML training...")
    df_feats, y_reg, y_clf = extract_vendor_features(repo)

    pipeline = TabularRiskPipeline()
    metrics = pipeline.train(df_feats, y_reg, y_clf)
    logger.info(f"Model training complete. Regressor RMSE: {metrics['regressor']['RMSE']}, Classifier PR-AUC: {metrics['classifier']['PR_AUC']}")

    # Save model artifacts locally
    model_path = ARTIFACTS_DIR / "risk_pipeline.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info(f"Saved model pipeline to {model_path}")

    # Register authentic models in MODEL_VERSIONS
    now = datetime.now()
    reg_metrics_json = json.dumps({
        "RMSE": metrics["regressor"]["RMSE"],
        "MAE": metrics["regressor"]["MAE"],
        "R2": metrics["regressor"]["R2"],
        "feature_importances": metrics["feature_importances"],
    })
    clf_metrics_json = json.dumps({
        "Accuracy": metrics["classifier"]["Accuracy"],
        "F1": metrics["classifier"]["F1"],
        "PR_AUC": metrics["classifier"]["PR_AUC"],
        "ROC_AUC": metrics["classifier"]["ROC_AUC"],
    })

    model_records = [
        {
            "MODEL_NAME": "RiskScoreRegressor",
            "VERSION": "v1.2.0-tabular",
            "TRAINING_DATE": now,
            "DATASET_VERSION": "seed_42_synthetic",
            "METRICS_JSON": reg_metrics_json,
            "STATUS": "TRAINED_ACTIVE",
            "NOTE": "Supervised GradientBoostingRegressor with 80/20 train/test split on operational and NetworkX centrality features"
        },
        {
            "MODEL_NAME": "FailureProbabilityClassifier",
            "VERSION": "v1.0.0-tabular",
            "TRAINING_DATE": now,
            "DATASET_VERSION": "seed_42_synthetic",
            "METRICS_JSON": clf_metrics_json,
            "STATUS": "TRAINED_ACTIVE",
            "NOTE": "RandomForestClassifier predicting supply chain disruption probability with balanced class weights"
        }
    ]

    # Fetch existing model versions, append or update
    existing_models = repo.get_model_versions()
    df_new = pd.DataFrame(model_records)
    
    if not existing_models.empty:
        # Keep any non-conflicting models or replace synthetic rows
        filtered_existing = existing_models[~existing_models["MODEL_NAME"].isin(["RiskScoreRegressor", "FailureProbabilityClassifier"])]
        combined = pd.concat([filtered_existing, df_new], ignore_index=True)
    else:
        combined = df_new

    repo.write_table(combined, "MODEL_VERSIONS", overwrite=True)
    logger.info("Successfully registered authentic trained models into MODEL_VERSIONS repository table.")
    return pipeline

if __name__ == "__main__":
    repo = get_repository()
    train_and_register_risk_models(repo)
