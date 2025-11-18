import json
import re
import emoji
from collections import Counter

def strip_markdown(text):
    """Remove markdown syntax and non-essential characters"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Remove links but keep text [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove headers (#, ##, etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
    
    # Remove excess whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def count_emojis(text):
    """Count emoji occurrences"""
    if not text:
        return 0
    return len([c for c in text if c in emoji.EMOJI_DATA])

def count_words(text):
    """Count actual words (excluding special characters)"""
    if not text:
        return 0
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    return len(words)

def count_sentences(text):
    """Count sentences for readability metrics"""
    if not text:
        return 0
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def count_syllables(word):
    """Estimate syllable count for a word"""
    word = word.lower()
    syllables = 0
    vowels = "aeiouy"
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllables += 1
        previous_was_vowel = is_vowel
    
    # Adjust for silent e
    if word.endswith('e'):
        syllables -= 1
    
    # Ensure at least 1 syllable
    return max(1, syllables)

def flesch_kincaid_grade(text):
    """Calculate Flesch-Kincaid Grade Level"""
    if not text:
        return 0
    
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    word_count = len(words)
    sentence_count = count_sentences(text)
    
    if word_count == 0 or sentence_count == 0:
        return 0
    
    syllable_count = sum(count_syllables(word) for word in words)
    
    # Flesch-Kincaid Grade Level formula
    grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    return max(0, round(grade, 2))

def flesch_reading_ease(text):
    """Calculate Flesch Reading Ease score (0-100, higher = easier)"""
    if not text:
        return 0
    
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    word_count = len(words)
    sentence_count = count_sentences(text)
    
    if word_count == 0 or sentence_count == 0:
        return 0
    
    syllable_count = sum(count_syllables(word) for word in words)
    
    # Flesch Reading Ease formula
    score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    return max(0, min(100, round(score, 2)))

def has_sections(text):
    """Check if README has common sections"""
    if not text:
        return {}
    
    text_lower = text.lower()
    sections = {
        'installation': any(word in text_lower for word in ['install', 'setup', 'getting started']),
        'usage': 'usage' in text_lower or 'example' in text_lower,
        'contributing': 'contribut' in text_lower,
        'license': 'license' in text_lower,
        'features': 'feature' in text_lower,
    }
    return sections

def calculate_quality_score(metrics):
    """Calculate overall quality score (0-100)"""
    score = 0
    
    # Word count (0-25 points)
    if metrics['word_count'] >= 500:
        score += 25
    elif metrics['word_count'] >= 300:
        score += 20
    elif metrics['word_count'] >= 150:
        score += 15
    elif metrics['word_count'] >= 50:
        score += 10
    
    # Reading ease (0-20 points) - prefer 60-80 range (conversational)
    ease = metrics['flesch_reading_ease']
    if 60 <= ease <= 80:
        score += 20
    elif 50 <= ease < 60 or 80 < ease <= 90:
        score += 15
    elif 40 <= ease < 50 or 90 < ease <= 100:
        score += 10
    
    # Grade level (0-15 points) - prefer 8-12 (accessible but detailed)
    grade = metrics['flesch_kincaid_grade']
    if 8 <= grade <= 12:
        score += 15
    elif 6 <= grade < 8 or 12 < grade <= 14:
        score += 10
    elif grade < 6 or grade > 14:
        score += 5
    
    # Sections present (0-25 points)
    section_count = sum(metrics['sections'].values())
    score += min(25, section_count * 5)
    
    # Emoji usage (0-10 points) - moderate use is good
    emoji_count = metrics['emoji_count']
    if 1 <= emoji_count <= 10:
        score += 10
    elif 11 <= emoji_count <= 20:
        score += 5
    
    # Sentence structure (0-5 points)
    if metrics['sentence_count'] >= 10:
        score += 5
    
    return min(100, score)

def analyze_readme(readme_text):
    """Analyze a single README and return metrics"""
    # Strip markdown first
    clean_text = strip_markdown(readme_text)
    
    # Calculate metrics
    metrics = {
        'original_length': len(readme_text) if readme_text else 0,
        'clean_text': clean_text,
        'word_count': count_words(clean_text),
        'sentence_count': count_sentences(clean_text),
        'emoji_count': count_emojis(readme_text),
        'flesch_kincaid_grade': flesch_kincaid_grade(clean_text),
        'flesch_reading_ease': flesch_reading_ease(clean_text),
        'sections': has_sections(readme_text),
    }
    
    # Calculate quality score
    metrics['quality_score'] = calculate_quality_score(metrics)
    
    return metrics

def analyze_all_readmes(input_file='github_repos_data.json', output_file='readme_analysis.json'):
    """Analyze all READMEs from scraped data"""
    print("Loading repository data...")
    with open(input_file, 'r', encoding='utf-8') as f:
        repos = json.load(f)
    
    print(f"Analyzing {len(repos)} READMEs...")
    results = []
    
    for i, repo in enumerate(repos):
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(repos)}")
        
        readme = repo.get('readme')
        metrics = analyze_readme(readme)
        
        result = {
            'repo_name': repo.get('name'),
            'stars': repo.get('stars'),
            'forks': repo.get('forks'),
            'commits': repo.get('commits'),
            'has_readme': readme is not None,
            **metrics
        }
        
        results.append(result)
    
    # Sort by quality score
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis complete! Results saved to {output_file}")
    
    # Print summary statistics
    print_summary(results)
    
    return results

def print_summary(results):
    """Print summary statistics"""
    valid_readmes = [r for r in results if r['has_readme']]
    
    print("\n=== Summary Statistics ===")
    print(f"Total repositories: {len(results)}")
    print(f"With README: {len(valid_readmes)}")
    print(f"Without README: {len(results) - len(valid_readmes)}")
    
    if valid_readmes:
        avg_score = sum(r['quality_score'] for r in valid_readmes) / len(valid_readmes)
        avg_words = sum(r['word_count'] for r in valid_readmes) / len(valid_readmes)
        avg_grade = sum(r['flesch_kincaid_grade'] for r in valid_readmes) / len(valid_readmes)
        
        print(f"\nAverage quality score: {avg_score:.2f}/100")
        print(f"Average word count: {avg_words:.0f}")
        print(f"Average grade level: {avg_grade:.1f}")
        
        print("\n=== Top 5 Quality READMEs ===")
        for i, repo in enumerate(valid_readmes[:5], 1):
            print(f"{i}. {repo['repo_name']} - Score: {repo['quality_score']}/100")
            print(f"   Words: {repo['word_count']}, Grade: {repo['flesch_kincaid_grade']}, Stars: {repo['stars']}")

if __name__ == "__main__":
    # Install required: pip install emoji
    analyze_all_readmes()
