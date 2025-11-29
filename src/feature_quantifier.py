import pandas as pd
import numpy as np
from scipy import stats

# Load data
df = pd.read_csv('repo_data_numbers.csv')

# Select numeric columns only
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

print("="*80)
print("GITHUB REPOSITORY STATISTICAL ANALYSIS")
print("="*80)
print(f"\nDataset: {len(df)} repositories")
print(f"Features: {len(numeric_cols)} numeric metrics\n")

# Group metrics by category
basic_metrics = ['stars', 'forks', 'contributors', 'commits']
temporal_metrics = ['repo_age_days', 'repo_age_years', 'stars_per_day', 
                    'forks_per_day', 'commits_per_day']
engagement_metrics = ['fork_to_star_ratio', 'commits_per_contributor', 
                      'popularity_score', 'engagement_score']
readme_structure = ['token_count', 'header_count', 'code_block_count', 
                    'inline_code_count', 'image_count', 'list_item_count']
readme_content = ['has_installation', 'has_usage', 'has_contributing', 
                  'has_license', 'has_badges', 'has_toc', 'section_count']
readme_quality = ['sentiment_polarity', 'sentiment_subjectivity', 
                  'avg_word_length', 'avg_sentence_length', 'completeness_score']

categories = {
    'BASIC REPOSITORY METRICS': basic_metrics,
    'TEMPORAL & GROWTH METRICS': temporal_metrics,
    'ENGAGEMENT & POPULARITY': engagement_metrics,
    'README STRUCTURE': readme_structure,
    'README CONTENT FEATURES': readme_content,
    'README QUALITY INDICATORS': readme_quality
}

def print_stats(df, columns, category_name):
    """Print comprehensive statistics for a group of columns"""
    print(f"\n{'='*80}")
    print(f"{category_name}")
    print(f"{'='*80}\n")
    
    for col in columns:
        if col not in df.columns:
            continue
            
        data = df[col].dropna()
        
        print(f"\n{col.upper()}")
        print("-" * 60)
        
        # Central tendency
        print(f"  Mean:              {data.mean():.4f}")
        print(f"  Median:            {data.median():.4f}")
        try:
            mode_result = stats.mode(data, keepdims=True)
            mode_val = mode_result.mode[0]
            mode_count = mode_result.count[0]
            print(f"  Mode:              {mode_val:.4f} (appears {mode_count} times)")
        except:
            print(f"  Mode:              No unique mode")
        
        # Dispersion
        print(f"  Std Dev:           {data.std():.4f}")
        print(f"  Variance:          {data.var():.4f}")
        print(f"  Range:             {data.max() - data.min():.4f}")
        print(f"  IQR:               {data.quantile(0.75) - data.quantile(0.25):.4f}")
        print(f"  Coef of Variation: {(data.std() / data.mean() * 100):.2f}%")
        
        # Distribution shape
        print(f"  Skewness:          {data.skew():.4f}", end="")
        if abs(data.skew()) < 0.5:
            print(" (fairly symmetric)")
        elif data.skew() > 0:
            print(" (right-skewed)")
        else:
            print(" (left-skewed)")
            
        print(f"  Kurtosis:          {data.kurtosis():.4f}", end="")
        if abs(data.kurtosis()) < 0.5:
            print(" (normal)")
        elif data.kurtosis() > 0:
            print(" (heavy-tailed)")
        else:
            print(" (light-tailed)")
        
        # Percentiles
        print(f"\n  Percentiles:")
        for p in [5, 25, 50, 75, 95]:
            print(f"    {p}th:            {data.quantile(p/100):.4f}")
        
        # Min/Max
        print(f"\n  Min:               {data.min():.4f}")
        print(f"  Max:               {data.max():.4f}")
        
        # Count stats
        print(f"  Count:             {len(data)}")
        print(f"  Missing:           {df[col].isna().sum()}")
        if data.dtype in ['int64', 'float64']:
            print(f"  Zeros:             {(data == 0).sum()}")

# Print stats for each category
for category_name, metrics in categories.items():
    print_stats(df, metrics, category_name)

# Additional derived statistics
print(f"\n\n{'='*80}")
print("DERIVED INSIGHTS")
print(f"{'='*80}\n")

print("Repository Success Distribution:")
print(f"  Highly starred repos:     {df['is_highly_starred'].sum()} ({df['is_highly_starred'].mean()*100:.1f}%)")
print(f"  Highly forked repos:      {df['is_highly_forked'].sum()} ({df['is_highly_forked'].mean()*100:.1f}%)")
print(f"  Highly active repos:      {df['is_active'].sum()} ({df['is_active'].mean()*100:.1f}%)")

print("\nREADME Completeness Breakdown:")
print(f"  Excellent (>0.8):         {(df['completeness_score'] > 0.8).sum()} ({(df['completeness_score'] > 0.8).mean()*100:.1f}%)")
print(f"  Good (0.6-0.8):           {((df['completeness_score'] >= 0.6) & (df['completeness_score'] <= 0.8)).sum()} ({((df['completeness_score'] >= 0.6) & (df['completeness_score'] <= 0.8)).mean()*100:.1f}%)")
print(f"  Fair (0.4-0.6):           {((df['completeness_score'] >= 0.4) & (df['completeness_score'] < 0.6)).sum()} ({((df['completeness_score'] >= 0.4) & (df['completeness_score'] < 0.6)).mean()*100:.1f}%)")
print(f"  Poor (<0.4):              {(df['completeness_score'] < 0.4).sum()} ({(df['completeness_score'] < 0.4).mean()*100:.1f}%)")

print("\nREADME Content Prevalence:")
for col in readme_content:
    if col in df.columns and col.startswith('has_'):
        feature = col.replace('has_', '').replace('_', ' ').title()
        print(f"  {feature:20s}: {df[col].sum()} repos ({df[col].mean()*100:.1f}%)")

print("\nGrowth Rate Insights:")
print(f"  Avg stars/day (all):      {df['stars_per_day'].mean():.4f}")
print(f"  Avg stars/day (top 25%):  {df[df['is_highly_starred']==1]['stars_per_day'].mean():.4f}")
print(f"  Avg forks/day (all):      {df['forks_per_day'].mean():.4f}")
print(f"  Avg commits/day (all):    {df['commits_per_day'].mean():.4f}")

print("\nCorrelation Highlights (top 5 absolute values):")
# Calculate correlation matrix
corr_matrix = df[numeric_cols].corr()
# Get upper triangle
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append((
            corr_matrix.columns[i],
            corr_matrix.columns[j],
            corr_matrix.iloc[i, j]
        ))
# Sort by absolute correlation
corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
for i, (col1, col2, corr) in enumerate(corr_pairs[:5], 1):
    print(f"  {i}. {col1} <-> {col2}")
    print(f"     Correlation: {corr:.4f}")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
