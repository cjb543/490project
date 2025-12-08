import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

df = pd.read_csv("repo_data_numbers.csv")
print(df.columns)

# Structural completeness
#   - header_count
#   - code_block_count
#   - inline_code_count
#   - image_count
#   - list_item_count
#   - has_description
#   - has_installation
#   - has_usage
#   - has_contributing
#   - has_license
#   - has_toc
#   - has_credits
#   - section_count
#   - completeness_score

# Sucess metrics
#   - stars
#   - log_stars
#    - stars_per_day
#    - is_highly_starred
#   - forks
#   - forks_per_day
#   - log_forks
#   - fork_to_star_ratio
#   - is_highly_forked
#   - contributors
#   - log contributors
#   - popularity_score
#   - engagement_score
#   - is_active

# NLP stuff
#  - token count
#  - noun_count
#  - verb_count
#  - adj_count

#  Other
#  - sentiment_polarity
#  - sentiment_subjectivity
#  - avg_word_length
#  - avg_sentence_length
#  -


# Correlation between completeness_score and stars
plt.scatter(df["completeness_score"], df["engagement_score"])
plt.show()
correlation_matrix = np.corrcoef(df["completeness_score"], df["popularity_score"])
pearson_r = correlation_matrix[0, 1]
print(f"Correlation score between completeness_score and stars: {pearson_r}")

# Tokens
print(df.columns)
success_cols = [
    "stars",
    "forks",
    "contributors",
    "forks_per_day",
    "is_active",
    "is_highly_starred",
    "fork_to_star_ratio",
]
print(df[["token_count"] + success_cols].corr())
sns.histplot(df["token_count"], bins=100)
plt.xlim(0, 3000)
plt.show()

# Complete correlation matrix heatmap
features = df.drop(["name", "owner", "language"], axis=1)
corr = features.corr()

plt.figure(figsize=(18, 14))

mask = np.triu(np.ones_like(corr, dtype=bool))

sns.heatmap(
    corr,
    mask=mask,
    cmap="coolwarm",
    annot=False,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8},
)

plt.title("Feature Correlation Heatmap", fontsize=18, pad=20)
plt.tight_layout()
plt.show()
