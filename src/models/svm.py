import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

df = pd.read_csv("../../data/repo_data_numbers.csv")
X = df[
    [
        "token_count",
        "noun_count",
        "verb_count",
        "adj_count",
        "header_count",
        "code_block_count",
        "inline_code_count",
        "image_count",
        "list_item_count",
        "has_description",
        "has_installation",
        "has_usage",
        "has_contributing",
        "has_license",
        "has_toc",
        "has_credits",
        "section_count",
        "sentiment_polarity",
        "sentiment_subjectivity",
        "avg_word_length",
        "avg_sentence_length",
        "flesch_kincade",
        "flesch_reading_ease",
        "gunning_fog",
        "dale_chall",
        "difficult_words",
        "completeness_score",
        "total_sections",
    ]
]
y = df["is_highly_starred"]
binary_features = [
    "has_description", "has_installation", "has_usage", "has_contributing",
    "has_license", "has_toc", "has_credits"
]
numeric_features = [col for col in X.columns if col not in binary_features]
preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("bin", "passthrough", binary_features)
    ]
)
model = Pipeline([
    ("preprocess", preprocess),
    ("svm", LinearSVC())
])
param_grid_svm = {
    "svm__C": np.logspace(-3, 3, 20),
    "svm__class_weight": [None, "balanced"],
}
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
clf_svm = GridSearchCV(
    model,
    param_grid=param_grid_svm,
    cv=5,
    scoring="f1",
)
clf_svm.fit(X_train, y_train)
best_svm = clf_svm.best_estimator_
y_pred_svm = best_svm.predict(X_test)
print("Linear SVM F1:", f1_score(y_test, y_pred_svm))
print(classification_report(y_test, y_pred_svm))
