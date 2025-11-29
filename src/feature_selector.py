import pandas as pd
import numpy as np
import re
from textblob import TextBlob
from datetime import datetime
import spacy
import warnings
warnings.filterwarnings('ignore')

# Load spaCy model
try:
    gpu_available = spacy.prefer_gpu()
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
except:
    nlp = None

class RepoFeatureEngineer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        
    def extract_readme_features(self):
        """Extract comprehensive README quality metrics"""
        features = []
        total = len(self.df)
        
        for idx, row in self.df.iterrows():
            if (idx + 1) % 10 == 0:
                with open('progress.txt', 'w') as f:
                    f.write(f"Processing {idx + 1}/{total}\n")
            
            readme = str(row['readme']) if pd.notna(row['readme']) else ''
            
            # Token count using spaCy (linguistic tokens, not char count)
            try:
                if nlp and readme:
                    # Clean the text to avoid encoding issues
                    clean_readme = readme[:100000].encode('utf-8', errors='ignore').decode('utf-8')
                    doc = nlp(clean_readme)
                    token_count = len(doc)
                    noun_count = sum(1 for token in doc if token.pos_ == "NOUN")
                    verb_count = sum(1 for token in doc if token.pos_ == "VERB")
                    adj_count = sum(1 for token in doc if token.pos_ == "ADJ")
                else:
                    token_count = len(readme.split())
                    noun_count = verb_count = adj_count = 0
            except Exception as e:
                token_count = len(readme.split())
                noun_count = verb_count = adj_count = 0
            
            # Structure metrics
            header_count = len(re.findall(r'^#{1,6}\s', readme, re.MULTILINE))
            code_block_count = len(re.findall(r'```[\s\S]*?```', readme))
            inline_code_count = len(re.findall(r'`[^`]+`', readme))
            image_count = len(re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', readme))
            list_item_count = len(re.findall(r'^\s*[\*\-\+]\s', readme, re.MULTILINE))
            
            # Content quality indicators
            has_installation = bool(re.search(r'install', readme, re.IGNORECASE))
            has_usage = bool(re.search(r'usage|example|quickstart', readme, re.IGNORECASE))
            has_contributing = bool(re.search(r'contribut', readme, re.IGNORECASE))
            has_license = bool(re.search(r'license', readme, re.IGNORECASE))
            has_badges = bool(re.search(r'\[!\[', readme))
            has_toc = bool(re.search(r'table of contents', readme, re.IGNORECASE))
            
            # Section detection (common sections)
            section_keywords = ['features', 'requirements', 'documentation', 'api', 
                              'testing', 'deployment', 'roadmap', 'faq', 'changelog']
            section_count = sum(1 for kw in section_keywords if kw in readme.lower())
            
            # Readability metrics (using TextBlob for sentiment/subjectivity)
            try:
                blob = TextBlob(readme[:5000])
                sentiment_polarity = blob.sentiment.polarity
                sentiment_subjectivity = blob.sentiment.subjectivity
            except:
                sentiment_polarity = 0
                sentiment_subjectivity = 0
            
            # Complexity metrics
            avg_word_length = np.mean([len(w) for w in readme.split()]) if token_count > 0 else 0
            avg_sentence_length = token_count / max(1, len(re.split(r'[.!?]+', readme)))
            
            # Documentation completeness score (0-1)
            completeness_indicators = [
                has_installation, has_usage, has_contributing, 
                has_license, header_count > 3, code_block_count > 0,
                section_count > 2
            ]
            completeness_score = sum(completeness_indicators) / len(completeness_indicators)
            
            features.append({
                'token_count': token_count,
                'noun_count': noun_count,
                'verb_count': verb_count,
                'adj_count': adj_count,
                'header_count': header_count,
                'code_block_count': code_block_count,
                'inline_code_count': inline_code_count,
                'image_count': image_count,
                'list_item_count': list_item_count,
                'has_installation': int(has_installation),
                'has_usage': int(has_usage),
                'has_contributing': int(has_contributing),
                'has_license': int(has_license),
                'has_badges': int(has_badges),
                'has_toc': int(has_toc),
                'section_count': section_count,
                'sentiment_polarity': sentiment_polarity,
                'sentiment_subjectivity': sentiment_subjectivity,
                'avg_word_length': avg_word_length,
                'avg_sentence_length': avg_sentence_length,
                'completeness_score': completeness_score
            })
        
        return pd.DataFrame(features)
    
    def extract_repo_features(self):
        """Extract repository success metrics and temporal features"""
        df = self.df.copy()
        
        # Parse creation date and remove timezone info
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
        now = pd.Timestamp.now().tz_localize(None)
        df['repo_age_days'] = (now - df['created_at']).dt.days
        df['repo_age_years'] = df['repo_age_days'] / 365.25
        
        # Activity metrics (normalized by age)
        df['stars_per_day'] = df['stars'] / df['repo_age_days'].replace(0, 1)
        df['forks_per_day'] = df['forks'] / df['repo_age_days'].replace(0, 1)
        df['commits_per_day'] = df['commits'] / df['repo_age_days'].replace(0, 1)
        
        # Engagement ratios
        df['fork_to_star_ratio'] = df['forks'] / df['stars'].replace(0, 1)
        df['commits_per_contributor'] = df['commits'] / df['contributors'].replace(0, 1)
        
        # Success metrics (composite scores)
        df['log_stars'] = np.log1p(df['stars'])
        df['log_forks'] = np.log1p(df['forks'])
        df['log_contributors'] = np.log1p(df['contributors'])
        
        # Popularity score (weighted combination)
        df['popularity_score'] = (
            0.5 * df['log_stars'] + 
            0.3 * df['log_forks'] + 
            0.2 * df['log_contributors']
        )
        
        # Engagement score (activity-based)
        df['engagement_score'] = (
            df['stars_per_day'] * 0.4 + 
            df['forks_per_day'] * 0.3 + 
            df['commits_per_day'] * 0.3
        )
        
        # Binary success indicators (upper quartile)
        df['is_highly_starred'] = (df['stars'] > df['stars'].quantile(0.75)).astype(int)
        df['is_highly_forked'] = (df['forks'] > df['forks'].quantile(0.75)).astype(int)
        df['is_active'] = (df['commits_per_day'] > df['commits_per_day'].quantile(0.75)).astype(int)
        
        return df[[
            'repo_age_days', 'repo_age_years', 'stars_per_day', 'forks_per_day',
            'commits_per_day', 'fork_to_star_ratio', 'commits_per_contributor',
            'log_stars', 'log_forks', 'log_contributors', 'popularity_score',
            'engagement_score', 'is_highly_starred', 'is_highly_forked', 'is_active'
        ]]
    
    def create_numeric_output(self):
        """Create a clean numeric-only dataframe and save to CSV"""
        readme_features = self.extract_readme_features()
        repo_features = self.extract_repo_features()
        
        result = pd.concat([
            self.df[['name', 'owner', 'language', 'stars', 'forks', 'contributors', 'commits']],
            repo_features,
            readme_features
        ], axis=1)
        
        result.to_csv('repo_data_numbers.csv', index=False)
        
        with open('progress.txt', 'w') as f:
            f.write(f"Complete! Saved repo_data_numbers.csv\n")


if __name__ == "__main__":
    engineer = RepoFeatureEngineer('repo_data.csv')
    engineer.create_numeric_output()
