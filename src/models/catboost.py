import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split

df = pd.read_csv("repo_data_numbers.csv")
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
model = CatBoostClassifier(
    loss_function="Logloss",
    eval_metric="F1",
    iterations=1000,
    depth=6,
    verbose=False,
    thread_count=6,
    random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
pos_weight = (y_train.to_numpy() == 0).sum() / (y_train.to_numpy() == 1).sum()
param_grid_cat = {
    "depth": [4, 6, 8, 10],
    "learning_rate": [0.01, 0.03, 0.1],
    "iterations": [300, 600, 1000],
    "l2_leaf_reg": [1, 3, 5, 10],
    "bagging_temperature": [0.0, 0.25, 0.5, 1.0],
    "border_count": [64, 128, 254],
    "scale_pos_weight": [1.0, pos_weight],
}
clf_cat = RandomizedSearchCV(
    model,
    param_distributions=param_grid_cat,
    n_iter=50,
    cv=5,
    scoring="f1",
    random_state=42,
    n_jobs=1,
)
clf_cat.fit(X_train, y_train)
best_cat = clf_cat.best_estimator_
y_pred = best_cat.predict(X_test)
print("CatBoost F1:", f1_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
