import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler

class ReadmeCorrelationAnalysis:
    def __init__(self, csv_path='repo_data_numbers.csv'):
        self.df = pd.read_csv(csv_path)
        self._clean_data()
        
    def _clean_data(self):
        """Basic filtering - remove junk data"""
        initial = len(self.df)
        self.df = self.df[
            (self.df['token_count'] >= 50) &
            (self.df['repo_age_days'] >= 90) &
            (self.df['commits'] >= 10) &
            (self.df['stars'] > 0)
        ].copy()
        print(f"Filtered {initial - len(self.df)} low-quality repos. Remaining: {len(self.df)}")
        
    def define_feature_groups(self):
        """Group README quality metrics by category"""
        
        quality_features = {
            'Structure': [
                'header_count', 'section_count', 'code_block_count',
                'inline_code_count', 'list_item_count', 'image_count'
            ],
            'Completeness': [
                'has_installation', 'has_usage', 'has_contributing',
                'has_license', 'has_badges', 'has_toc', 'completeness_score'
            ],
            'Readability': [
                'avg_word_length', 'avg_sentence_length', 'token_count',
                'sentiment_polarity', 'sentiment_subjectivity'
            ],
            'Linguistic': [
                'noun_count', 'verb_count', 'adj_count'
            ]
        }
        
        success_metrics = {
            'Raw Popularity': ['stars', 'forks', 'contributors'],
            'Age-Adjusted': ['stars_per_day', 'forks_per_day'],
            'Engagement': ['fork_to_star_ratio', 'commits_per_contributor']
        }
        
        return quality_features, success_metrics
    
    def compute_correlations(self):
        """Compute Pearson and Spearman correlations"""
        
        quality_features, success_metrics = self.define_feature_groups()
        
        # Flatten feature lists
        all_quality = [f for group in quality_features.values() for f in group]
        all_success = [f for group in success_metrics.values() for f in group]
        
        # Filter to existing columns
        all_quality = [f for f in all_quality if f in self.df.columns]
        all_success = [f for f in all_success if f in self.df.columns]
        
        results = []
        
        for quality_feat in all_quality:
            for success_feat in all_success:
                # Remove NaN pairs
                mask = self.df[[quality_feat, success_feat]].notna().all(axis=1)
                x = self.df.loc[mask, quality_feat]
                y = self.df.loc[mask, success_feat]
                
                if len(x) < 10:
                    continue
                
                # Pearson (linear correlation)
                pearson_r, pearson_p = pearsonr(x, y)
                
                # Spearman (rank/monotonic correlation)
                spearman_r, spearman_p = spearmanr(x, y)
                
                results.append({
                    'quality_metric': quality_feat,
                    'success_metric': success_feat,
                    'pearson_r': pearson_r,
                    'pearson_p': pearson_p,
                    'spearman_r': spearman_r,
                    'spearman_p': spearman_p,
                    'n_samples': len(x)
                })
        
        return pd.DataFrame(results)
    
    def aggregate_correlation_score(self, corr_df, alpha=0.05):
        """Create overall README quality → success correlation score"""
        
        # Filter significant correlations (p < 0.05)
        significant = corr_df[
            (corr_df['pearson_p'] < alpha) | (corr_df['spearman_p'] < alpha)
        ].copy()
        
        # Use Spearman (better for non-linear relationships)
        significant['abs_correlation'] = significant['spearman_r'].abs()
        
        # Aggregate by success metric
        summary = significant.groupby('success_metric').agg({
            'abs_correlation': ['mean', 'max', 'count'],
            'spearman_r': 'mean'
        }).round(3)
        
        summary.columns = ['avg_correlation', 'max_correlation', 'n_significant', 'avg_direction']
        summary = summary.sort_values('avg_correlation', ascending=False)
        
        return summary
    
    def composite_quality_score(self):
        """Create single composite README quality score"""
        
        # Normalize all quality metrics to 0-1
        quality_features, _ = self.define_feature_groups()
        all_quality = [f for group in quality_features.values() for f in group]
        all_quality = [f for f in all_quality if f in self.df.columns]
        
        scaler = StandardScaler()
        scaled = pd.DataFrame(
            scaler.fit_transform(self.df[all_quality]),
            columns=all_quality
        )
        
        # Composite score (average of all normalized metrics)
        self.df['readme_quality_composite'] = scaled.mean(axis=1)
        
        return 'readme_quality_composite'
    
    def final_verdict(self):
        """Answer: Does README quality correlate with repo success?"""
        
        print("=" * 70)
        print("README QUALITY ↔ REPO SUCCESS CORRELATION ANALYSIS")
        print("=" * 70)
        
        # Compute all correlations
        print("\n1. Computing pairwise correlations...")
        corr_df = self.compute_correlations()
        
        # Statistical significance threshold
        alpha = 0.05
        significant = corr_df[
            (corr_df['pearson_p'] < alpha) | (corr_df['spearman_p'] < alpha)
        ]
        
        print(f"   Total tests: {len(corr_df)}")
        print(f"   Significant (p<{alpha}): {len(significant)} ({100*len(significant)/len(corr_df):.1f}%)")
        
        # Aggregate results
        print("\n2. Aggregating by success metric...")
        summary = self.aggregate_correlation_score(corr_df, alpha)
        print(summary)
        
        # Composite score correlation
        print("\n3. Testing composite README quality score...")
        composite_feat = self.composite_quality_score()
        
        composite_results = []
        for success in ['stars', 'forks', 'contributors']:
            if success in self.df.columns:
                r, p = spearmanr(self.df[composite_feat], self.df[success])
                composite_results.append({
                    'success_metric': success,
                    'correlation': r,
                    'p_value': p,
                    'significant': 'YES' if p < alpha else 'NO'
                })
        
        composite_df = pd.DataFrame(composite_results)
        print("\nComposite Quality Score Correlations:")
        print(composite_df.to_string(index=False))
        
        # Final verdict
        print("\n" + "=" * 70)
        print("FINAL VERDICT")
        print("=" * 70)
        
        avg_correlation = composite_df['correlation'].mean()
        all_significant = all(composite_df['significant'] == 'YES')
        
        print(f"\nAverage correlation (README quality → success): {avg_correlation:.3f}")
        print(f"Statistical significance: {'ALL METRICS' if all_significant else 'PARTIAL'}")
        
        if avg_correlation > 0.3 and all_significant:
            verdict = "✓ YES - STRONG POSITIVE CORRELATION"
            explanation = "README quality shows moderate-to-strong positive correlation with repo success."
        elif avg_correlation > 0.15 and len(significant) > len(corr_df) * 0.3:
            verdict = "✓ YES - MODERATE POSITIVE CORRELATION"
            explanation = "README quality shows consistent moderate correlation with repo success."
        elif avg_correlation > 0.05 and len(significant) > 0:
            verdict = "~ WEAK POSITIVE CORRELATION"
            explanation = "README quality shows weak but statistically significant correlation."
        else:
            verdict = "✗ NO - INSUFFICIENT CORRELATION"
            explanation = "README quality does not show meaningful correlation with repo success."
        
        print(f"\n{verdict}")
        print(f"{explanation}")
        
        # Effect size interpretation
        print(f"\nEffect Size Interpretation:")
        if avg_correlation > 0.5:
            print("  → Large effect: README quality is a major predictor of success")
        elif avg_correlation > 0.3:
            print("  → Medium effect: README quality is a meaningful predictor")
        elif avg_correlation > 0.1:
            print("  → Small effect: README quality has modest predictive value")
        else:
            print("  → Negligible effect: Other factors dominate repo success")
        
        # Top correlated features
        print(f"\nTop 10 README features correlated with stars:")
        top_features = corr_df[corr_df['success_metric'] == 'stars'].nlargest(10, 'spearman_r')
        for _, row in top_features.iterrows():
            print(f"  {row['quality_metric']}: r={row['spearman_r']:.3f} (p={row['spearman_p']:.4f})")
        
        # Save detailed results
        corr_df.to_csv('correlation_results_detailed.csv', index=False)
        summary.to_csv('correlation_results_summary.csv')
        
        print(f"\nDetailed results saved to:")
        print(f"  - correlation_results_detailed.csv")
        print(f"  - correlation_results_summary.csv")
        
        return verdict, avg_correlation, composite_df
    
    def visualize_results(self, top_n=15):
        """Create correlation heatmap"""
        
        quality_features, _ = self.define_feature_groups()
        all_quality = [f for group in quality_features.values() for f in group]
        all_quality = [f for f in all_quality if f in self.df.columns]
        
        success_cols = ['stars', 'forks', 'contributors']
        success_cols = [c for c in success_cols if c in self.df.columns]
        
        # Compute correlation matrix
        corr_matrix = self.df[all_quality + success_cols].corr().loc[all_quality, success_cols]
        
        # Select top N most correlated features
        max_corr = corr_matrix.abs().max(axis=1).nlargest(top_n)
        top_features = max_corr.index.tolist()
        
        # Plot
        plt.figure(figsize=(8, 10))
        sns.heatmap(
            corr_matrix.loc[top_features],
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0,
            vmin=-0.5,
            vmax=0.5,
            cbar_kws={'label': 'Spearman Correlation'}
        )
        plt.title(f'Top {top_n} README Quality Metrics vs. Success', fontsize=14, pad=20)
        plt.xlabel('Success Metrics', fontsize=12)
        plt.ylabel('README Quality Metrics', fontsize=12)
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
        print("\nVisualization saved: correlation_heatmap.png")
        plt.close()


if __name__ == "__main__":
    analyzer = ReadmeCorrelationAnalysis('repo_data_numbers.csv')
    verdict, avg_corr, results = analyzer.final_verdict()
    analyzer.visualize_results()
