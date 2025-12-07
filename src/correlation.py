import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

df = pd.read_csv('repo_data_numbers.csv')
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
#   - forks_to_star_ratio
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

forks = df['forks']
stars = df['stars']
contributors = df['contributors']
engagement_score = df['engagement_score']


# Correlation between completeness_score and stars

completeness_score = df['completeness_score']
is_highly_starred = df['is_highly_starred']

plt.scatter(completeness_score, engagement_score)
plt.show()
correlation_matrix = np.corrcoef(completeness_score, df['popularity_score'])
pearson_r = correlation_matrix[0, 1]
print(f"Correlation score between completeness_score and stars: {pearson_r}")
