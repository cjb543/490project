import pandas as pd
from langdetect import detect, LangDetectException

def is_english(text):
    """Check if text is in English"""
    if not text or pd.isna(text) or len(str(text).strip()) < 50:
        return False
    
    try:
        # Take first 1000 chars for detection
        sample = str(text)[:1000]
        lang = detect(sample)
        return lang == 'en'
    except LangDetectException:
        return False

# Load the CSV
print("Loading CSV...")
df = pd.read_csv('github_repos_final.csv')
print(f"Original count: {len(df)}")

# Filter for English READMEs
print("\nFiltering for English READMEs...")
df['is_english'] = df['readme'].apply(is_english)
df_english = df[df['is_english']].copy()
df_english = df_english.drop(columns=['is_english'])

# Save filtered data
df_english.to_csv('github_repos_english_only.csv', index=False, encoding='utf-8')

print(f"\nFiltered count: {len(df_english)}")
print(f"Removed: {len(df) - len(df_english)} non-English repos")
print(f"\nSaved to: github_repos_english_only.csv")

# Show language distribution
print(f"\nRepositories per programming language:")
print(df_english['language'].value_counts())
