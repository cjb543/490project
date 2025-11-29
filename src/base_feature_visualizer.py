import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load data
df = pd.read_csv('repo_data_numbers.csv')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 12)

# Create 3x3 subplot grid
fig, axes = plt.subplots(3, 3, figsize=(18, 15))
fig.suptitle('GitHub Repository Feature Analysis', fontsize=16, y=0.995)

# 1. Stars vs README Completeness (does good docs = more stars?)
ax1 = axes[0, 0]
scatter1 = ax1.scatter(df['completeness_score'], df['log_stars'], 
                       c=df['repo_age_years'], cmap='viridis', alpha=0.6, s=50)
ax1.set_xlabel('README Completeness Score')
ax1.set_ylabel('Log(Stars)')
ax1.set_title('Documentation Quality vs Popularity')
plt.colorbar(scatter1, ax=ax1, label='Repo Age (years)')

# 2. Engagement vs Popularity (are popular repos actually active?)
ax2 = axes[0, 1]
ax2.scatter(df['popularity_score'], df['engagement_score'], 
           c=df['fork_to_star_ratio'], cmap='coolwarm', alpha=0.6, s=50)
ax2.set_xlabel('Popularity Score')
ax2.set_ylabel('Engagement Score')
ax2.set_title('Popularity vs Activity Level')
ax2.set_yscale('log')

# 3. Commits per Contributor vs Forks (team dynamics)
ax3 = axes[0, 2]
ax3.scatter(df['commits_per_contributor'], df['log_forks'], 
           c=df['log_contributors'], cmap='plasma', alpha=0.6, s=50)
ax3.set_xlabel('Commits per Contributor')
ax3.set_ylabel('Log(Forks)')
ax3.set_title('Team Dynamics vs Fork Activity')
ax3.set_xlim(0, df['commits_per_contributor'].quantile(0.95))

# 4. README Token Count vs Stars (does length matter?)
ax4 = axes[1, 0]
ax4.scatter(df['token_count'], df['stars'], 
           c=df['code_block_count'], cmap='YlOrRd', alpha=0.6, s=50)
ax4.set_xlabel('README Token Count')
ax4.set_ylabel('Stars')
ax4.set_title('README Length vs Popularity')
ax4.set_xscale('log')
ax4.set_yscale('log')

# 5. Repo Age vs Stars per Day (growth rate over time)
ax5 = axes[1, 1]
ax5.scatter(df['repo_age_days'], df['stars_per_day'], 
           c=df['is_highly_starred'], cmap='RdYlGn', alpha=0.6, s=50)
ax5.set_xlabel('Repo Age (days)')
ax5.set_ylabel('Stars per Day')
ax5.set_title('Growth Rate vs Maturity')
ax5.set_yscale('log')

# 6. Code Blocks vs Sentiment (technical vs friendly tone)
ax6 = axes[1, 2]
ax6.scatter(df['code_block_count'], df['sentiment_polarity'], 
           c=df['has_usage'], cmap='bwr', alpha=0.6, s=50)
ax6.set_xlabel('Code Block Count')
ax6.set_ylabel('Sentiment Polarity')
ax6.set_title('Technical Content vs Tone')
ax6.axhline(y=0, color='gray', linestyle='--', alpha=0.3)

# 7. Section Count vs Completeness (structure quality)
ax7 = axes[2, 0]
ax7.scatter(df['section_count'], df['header_count'], 
           c=df['completeness_score'], cmap='Greens', alpha=0.6, s=50)
ax7.set_xlabel('Section Count')
ax7.set_ylabel('Header Count')
ax7.set_title('README Structure Metrics')

# 8. Fork/Star Ratio vs Contributors (utility vs popularity)
ax8 = axes[2, 1]
ax8.scatter(df['fork_to_star_ratio'], df['log_contributors'], 
           c=df['commits_per_day'], cmap='magma', alpha=0.6, s=50)
ax8.set_xlabel('Fork to Star Ratio')
ax8.set_ylabel('Log(Contributors)')
ax8.set_title('Utility vs Community Size')
ax8.set_xlim(0, df['fork_to_star_ratio'].quantile(0.95))

# 9. Image Count vs Stars (visual appeal impact)
ax9 = axes[2, 2]
ax9.scatter(df['image_count'], df['log_stars'], 
           c=df['has_badges'], cmap='twilight', alpha=0.6, s=50)
ax9.set_xlabel('Image Count in README')
ax9.set_ylabel('Log(Stars)')
ax9.set_title('Visual Content vs Popularity')
ax9.set_xlim(0, df['image_count'].quantile(0.95))

plt.tight_layout()
plt.savefig('repo_features_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Print correlation insights
print("\n=== Key Correlations ===")
correlations = {
    'Stars vs Completeness': df[['log_stars', 'completeness_score']].corr().iloc[0,1],
    'Stars vs Token Count': df[['log_stars', 'token_count']].corr().iloc[0,1],
    'Stars vs Code Blocks': df[['log_stars', 'code_block_count']].corr().iloc[0,1],
    'Engagement vs Popularity': df[['engagement_score', 'popularity_score']].corr().iloc[0,1],
    'Fork Ratio vs Contributors': df[['fork_to_star_ratio', 'log_contributors']].corr().iloc[0,1]
}

for name, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
    print(f"{name}: {corr:.3f}")
