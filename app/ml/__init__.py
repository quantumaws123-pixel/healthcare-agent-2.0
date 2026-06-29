"""
Machine learning models, inference engine, and explainability
"""

from app.ml.feature_engineer import (  # noqa: F401
    FeatureEngineer,
    CATEGORICAL_COLUMNS,
    NUMERICAL_COLUMNS,
    DERIVED_COLUMNS,
    HEALTH_TREND_ENCODING,
    impute_missing_values,
    one_hot_encode,
    minmax_normalize,
    zscore_normalize,
    create_derived_features,
)

from app.ml.model_trainer import (  # noqa: F401
    EvaluationMetrics,
    TrainingResult,
    TARGET_COLUMN,
    train_logistic_regression,
    train_random_forest,
    train_xgboost,
    train_lstm,
    train_all_models,
)

from app.ml.model_registry import (  # noqa: F401
    ModelRegistry,
    DEFAULT_MODEL_DIR,
    VERSION_LATEST,
)

from app.ml.inference_engine import (  # noqa: F401
    InferenceEngine,
    SHAPExplainer,
    classify_risk_level,
    INFERENCE_TIMEOUT_SECONDS,
    SHAP_TIMEOUT_SECONDS,
    TOP_N_SHAP_FEATURES,
    SHAP_BACKGROUND_SAMPLES,
)

from app.ml.shap_explainer import initialize_explainer  # noqa: F401
