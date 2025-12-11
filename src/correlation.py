import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import pointbiserialr

SUCCESS_METRICS = [
    "stars",
    "forks",
    "contributors",
]

BINARY_FEATURES = [
    "has_description",
    "has_installation",
    "has_usage",
    "has_contributing",
    "has_license",
    "has_toc",
    "has_credits",
]

CONTINUOUS_FEATURES = [
    "token_count",
    "noun_count",
    "verb_count",
    "adj_count",
    "section_count",
    "total_sections",
    "header_count",
    "code_block_count",
    "inline_code_count",
    "image_count",
    "list_item_count",
    "completeness_score",
    "avg_word_length",
    "avg_sentence_length",
    "flesch_kincade",
    "flesch_reading_ease",
    "gunning_fog",
    "dale_chall",
    "difficult_words",
    "sentiment_polarity",
    "sentiment_subjectivity",
]

BINARY_SUCCESS_LABEL = "successful"


def compute_spearman_correlations(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in CONTINUOUS_FEATURES + SUCCESS_METRICS if c in df.columns]
    corr = df[cols].corr(method="spearman")

    rows = [c for c in CONTINUOUS_FEATURES if c in corr.index]
    cols = [c for c in SUCCESS_METRICS if c in corr.columns]

    return corr.loc[rows, cols]


def compute_pointbiserial_correlations(df: pd.DataFrame) -> pd.DataFrame:
    res = []

    row_names = []
    col_names = [m for m in SUCCESS_METRICS if m in df.columns]

    for feature in BINARY_FEATURES:
        if feature not in df.columns:
            continue

        row = []
        for metric in col_names:
            x = df[feature]
            y = df[metric]

            mask = x.notna() & y.notna()
            x_valid = x[mask]
            y_valid = y[mask]

            if x_valid.nunique() <= 1:
                corr_val = np.nan
            else:
                try:
                    corr_val, _ = pointbiserialr(x_valid, y_valid)
                except Exception:
                    corr_val = np.nan
            row.append(corr_val)

        res.append(row)
        row_names.append(feature)

    if not res:
        return pd.DataFrame()

    return pd.DataFrame(res, index=row_names, columns=col_names)

def plot_binary_feature_boxplots(df):

    star_col = "stars"
    section_cols = [
        "has_contributing",
        "has_license",
        "has_installation",
        "has_credits",
        "has_usage",
        "has_toc",
        "has_description",
    ]

    section_labels = {
        "has_contributing": "Contributing",
        "has_license": "License",
        "has_installation": "Installation",
        "has_credits": "Credit",
        "has_usage": "Usage",
        "has_toc": "Table of Content",
        "has_description": "Description",
    }

    p80 = df[star_col].quantile(0.5)
    df_sub = df[df[star_col] <= p80].copy()

    cols = [star_col] + section_cols
    df_long = df_sub[cols].melt(
        id_vars=star_col,
        value_vars=section_cols,

        var_name="section",
        value_name="included",
    )

    df_long["section"] = df_long["section"].map(section_labels)
    df_long["included_label"] = df_long["included"].map({0: "Not Included", 1: "Included"})

    plt.figure(figsize=(8, 5))

    sns.boxplot(
        data=df_long,
        x="section",
        y=star_col,
        hue="included_label",
    )

    plt.xlabel("")
    plt.ylabel("Stars")
    plt.title("Stars by Section Presence")

    plt.xticks(rotation=45, ha="right")
    plt.legend(title="", loc="upper right")

    plt.tight_layout()
    plt.savefig("../figures/section_boxplot_50th.png", dpi=300)
    plt.show()


def plot_heatmap(corr_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr_df.values, aspect="auto")

    ax.set_xticks(np.arange(len(corr_df.columns)))
    ax.set_yticks(np.arange(len(corr_df.index)))
    ax.set_xticklabels(corr_df.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr_df.index)

    ax.set_title("Correlation matrix heatmap")
    fig.colorbar(im, ax=ax, label="Spearman correlation")

    fig.savefig("../figures/heatmap.png")
    fig.tight_layout()
    plt.show()


def print_top_correlations(corr_df: pd.DataFrame, top_k: int = 10) -> None:

    stacked = (
        corr_df.stack()
        .rename("corr")
        .reset_index()
        .rename(columns={"level_0": "feature", "level_1": "metric"})
    )
    stacked["abs_corr"] = stacked["corr"].abs()
    top = stacked.sort_values("abs_corr", ascending=False).head(top_k)

    print("\nTop correlations (by |r|) ")
    for _, row in top.iterrows():
        print(f"{row['feature']:25s} vs {row['metric']:15s} => r = {row['corr']:.3f}")


if __name__ == "__main__":
    df = pd.read_csv("../data/repo_data_numbers.csv")
    pearson_corr = compute_spearman_correlations(df)
    print_top_correlations(pearson_corr, top_k=15)
    pb_corr = compute_pointbiserial_correlations(df)
    plot_heatmap(pearson_corr)
    plot_binary_feature_boxplots(df)
