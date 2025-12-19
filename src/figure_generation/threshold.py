import matplotlib.pyplot as plt

# Percentiles that we tested
percentiles = [
    0.5,
    0.5444444444444444,
    0.5888888888888889,
    0.6333333333333333,
    0.6777777777777778,

    0.7222222222222222,
    0.7666666666666666,
    0.8111111111111111,
    0.8555555555555556,

    0.9,
]

# Scores from the model
f1_scores = [
    0.48491497531541417,
    0.5665773011617515,
    0.45232273838630804,
    0.3979125896934116,
    0.33278688524590166,
    0.41130298273155413,
    0.3507853403141361,
    0.3059388122375525,
    0.20676328502415459,
    0.16219751471550034,
]

plt.figure(figsize=(8, 5))
plt.plot(percentiles, f1_scores, marker="o")
plt.xlabel("Success Threshold (Stars Percentile)")
plt.ylabel("F1 Score (positive class)")
plt.title("F1 Score vs. Popularity Percentile Threshold")
plt.grid(True)
best_idx = max(range(len(f1_scores)), key=lambda i: f1_scores[i])
plt.scatter(percentiles[best_idx], f1_scores[best_idx], color="red")
plt.text(
    percentiles[best_idx],
    f1_scores[best_idx] + 0.01,
    f"max F1={f1_scores[best_idx]:.3f}\n@ p={percentiles[best_idx]:.3f}",
    ha="center",
)
plt.tight_layout()
plt.show()
