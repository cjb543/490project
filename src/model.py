import datetime
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
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

best_f1, best_p = 0, 0
for p in np.linspace(0.5, 0.90, 10):
    print(f"testing percentile: {p}")
    target = df["stars"].quantile(p)

    y = df["stars"] > target
    counter = Counter(y.to_numpy())

    print("Records with label 1: ", counter[1])
    print("Records with label 0: ", counter[0])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    param_grid = {
        "n_estimators": np.arange(100, 300, 20),
        "max_features": ["log2", "sqrt", None],
        "max_depth": list(np.arange(5, 25, 5)) + [None],
        "min_samples_split": np.arange(2, 6, 1),
        "min_samples_leaf": [1, 2],
        "bootstrap": [True, False],
        "class_weight": ["balanced", None],
    }

    before = datetime.datetime.now().astimezone()

    model = RandomForestClassifier()
    clf = RandomizedSearchCV(
        model, param_grid, n_iter=45, cv=5, scoring="f1", random_state=42, n_jobs=6
    )

    # model = RandomForestClassifier(
    #     # bootstrap=False,
    #     class_weight="balanced",
    #     n_estimators=120,
    #     max_depth=15,
    #     random_state=42,
    #     # max_features=None,
    #     # min_samples_leaf=2,
    #     # min_samples_split=3,
    #
    # )

    clf.fit(X_train, y_train)

    after = datetime.datetime.now().astimezone()
    elapsed = after - before
    print("model selection time: ", elapsed)

    print("Best Model: ", clf.best_estimator_)
    model = clf.best_estimator_

    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred)

    if f1 > best_f1:
        best_p = p
        best_f1 = f1

    print(f1_score(y_test, y_pred))
    # print(accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))
