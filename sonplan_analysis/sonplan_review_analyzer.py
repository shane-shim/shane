import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from collections import Counter
import re
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np

# Korean text analyzer
okt = Okt()

def scrape_sonplan_reviews(base_url, max_pages=10):
    """
    Scrape reviews from Sonplan product page
    """
    reviews_data = []
    
    # Try to find the review board URL pattern
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # First, get the main product page
    response = session.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for review section or board
    # Common patterns for Korean e-commerce sites
    review_patterns = [
        'board.html?board_no=4',  # Common cafe24 pattern
        'board/product/list.html',
        'review',
        'board_list'
    ]
    
    # Try to find review iframe or section
    iframes = soup.find_all('iframe')
    review_url = None
    
    for iframe in iframes:
        src = iframe.get('src', '')
        if any(pattern in src for pattern in review_patterns):
            review_url = src
            if not review_url.startswith('http'):
                review_url = 'https://sonplan.com' + review_url
            break
    
    if not review_url:
        # Try direct board access
        review_url = "https://sonplan.com/board/product/list.html?board_no=4&product_no=10"
    
    print(f"Attempting to scrape from: {review_url}")
    
    for page in range(1, max_pages + 1):
        print(f"Scraping page {page}...")
        
        try:
            # Construct URL with page parameter
            if '?' in review_url:
                page_url = f"{review_url}&page={page}"
            else:
                page_url = f"{review_url}?page={page}"
            
            response = session.get(page_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Multiple patterns to find reviews
            # Pattern 1: Table with class 'boardList'
            review_table = soup.find('table', class_='boardList')
            
            # Pattern 2: Any table in board area
            if not review_table:
                board_area = soup.find('div', class_='board')
                if board_area:
                    review_table = board_area.find('table')
            
            # Pattern 3: Generic table search
            if not review_table:
                tables = soup.find_all('table')
                for table in tables:
                    if table.find('tr') and len(table.find_all('tr')) > 1:
                        review_table = table
                        break
            
            if not review_table:
                print(f"No review table found on page {page}")
                continue
            
            # Extract reviews from table rows
            rows = review_table.find_all('tr')
            
            for row in rows[1:]:  # Skip header
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 3:
                    # Extract text content, handling various formats
                    subject_cell = cols[1]
                    
                    # Get the review subject/content
                    subject_link = subject_cell.find('a')
                    if subject_link:
                        subject_text = subject_link.get_text(strip=True)
                    else:
                        subject_text = subject_cell.get_text(strip=True)
                    
                    # Get rating if available
                    rating = 5  # Default rating
                    rating_imgs = row.find_all('img', src=re.compile('star|point'))
                    if rating_imgs:
                        rating = len([img for img in rating_imgs if 'star' in img.get('src', '')])
                    
                    review = {
                        'review_text': subject_text,
                        'reviewer': cols[2].get_text(strip=True) if len(cols) > 2 else 'Anonymous',
                        'date': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                        'rating': rating
                    }
                    
                    if review['review_text']:  # Only add if there's actual content
                        reviews_data.append(review)
            
            time.sleep(1)  # Be respectful to the server
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            continue
    
    return pd.DataFrame(reviews_data)

def analyze_review_keywords(df):
    """
    Analyze keywords and patterns from reviews without predefined sentiment
    """
    # Extract all meaningful words
    all_words = []
    all_nouns = []
    all_adjectives = []
    all_verbs = []
    
    # Process each review
    for review in df['review_text']:
        if pd.isna(review) or review == '':
            continue
        
        # Tokenize and POS tagging
        tokens = okt.pos(review)
        
        for word, pos in tokens:
            if len(word) > 1:  # Filter single characters
                if pos == 'Noun':
                    all_nouns.append(word)
                    all_words.append(word)
                elif pos == 'Adjective':
                    all_adjectives.append(word)
                    all_words.append(word)
                elif pos == 'Verb':
                    all_verbs.append(word)
                    all_words.append(word)
    
    # Count frequencies
    word_freq = Counter(all_words)
    noun_freq = Counter(all_nouns)
    adj_freq = Counter(all_adjectives)
    verb_freq = Counter(all_verbs)
    
    # Filter out common stop words
    stop_words = ['것', '수', '거', '저', '제', '더', '데', '때', '및', '등', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지']
    
    filtered_word_freq = {word: freq for word, freq in word_freq.items() 
                         if word not in stop_words}
    filtered_noun_freq = {word: freq for word, freq in noun_freq.items() 
                         if word not in stop_words}
    filtered_adj_freq = {word: freq for word, freq in adj_freq.items() 
                        if word not in stop_words}
    filtered_verb_freq = {word: freq for word, freq in verb_freq.items() 
                         if word not in stop_words}
    
    # Find co-occurring words (bigrams)
    bigrams = []
    for review in df['review_text']:
        if pd.isna(review):
            continue
        tokens = okt.nouns(review)
        for i in range(len(tokens)-1):
            if len(tokens[i]) > 1 and len(tokens[i+1]) > 1:
                bigrams.append(f"{tokens[i]} {tokens[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    return {
        'all_words': filtered_word_freq,
        'nouns': filtered_noun_freq,
        'adjectives': filtered_adj_freq,
        'verbs': filtered_verb_freq,
        'bigrams': dict(bigram_freq.most_common(20)),
        'total_reviews': len(df)
    }

def visualize_analysis(analysis_results, df):
    """
    Create comprehensive visualizations
    """
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'  # For Mac
    plt.rcParams['axes.unicode_minus'] = False
    
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Top Keywords (All)
    ax1 = plt.subplot(3, 3, 1)
    top_words = dict(sorted(analysis_results['all_words'].items(), 
                           key=lambda x: x[1], reverse=True)[:15])
    bars = ax1.bar(range(len(top_words)), list(top_words.values()), color='skyblue')
    ax1.set_xticks(range(len(top_words)))
    ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
    ax1.set_title('전체 상위 키워드', fontsize=14, fontweight='bold')
    ax1.set_ylabel('빈도수')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    # 2. Top Nouns
    ax2 = plt.subplot(3, 3, 2)
    top_nouns = dict(sorted(analysis_results['nouns'].items(), 
                           key=lambda x: x[1], reverse=True)[:15])
    bars = ax2.bar(range(len(top_nouns)), list(top_nouns.values()), color='lightcoral')
    ax2.set_xticks(range(len(top_nouns)))
    ax2.set_xticklabels(list(top_nouns.keys()), rotation=45, ha='right')
    ax2.set_title('상위 명사', fontsize=14, fontweight='bold')
    ax2.set_ylabel('빈도수')
    
    # 3. Top Adjectives
    ax3 = plt.subplot(3, 3, 3)
    top_adjs = dict(sorted(analysis_results['adjectives'].items(), 
                          key=lambda x: x[1], reverse=True)[:15])
    if top_adjs:
        bars = ax3.bar(range(len(top_adjs)), list(top_adjs.values()), color='lightgreen')
        ax3.set_xticks(range(len(top_adjs)))
        ax3.set_xticklabels(list(top_adjs.keys()), rotation=45, ha='right')
    ax3.set_title('상위 형용사', fontsize=14, fontweight='bold')
    ax3.set_ylabel('빈도수')
    
    # 4. Top Verbs
    ax4 = plt.subplot(3, 3, 4)
    top_verbs = dict(sorted(analysis_results['verbs'].items(), 
                           key=lambda x: x[1], reverse=True)[:15])
    if top_verbs:
        bars = ax4.bar(range(len(top_verbs)), list(top_verbs.values()), color='lightyellow')
        ax4.set_xticks(range(len(top_verbs)))
        ax4.set_xticklabels(list(top_verbs.keys()), rotation=45, ha='right')
    ax4.set_title('상위 동사', fontsize=14, fontweight='bold')
    ax4.set_ylabel('빈도수')
    
    # 5. Bigrams (Word Pairs)
    ax5 = plt.subplot(3, 3, 5)
    bigrams = analysis_results['bigrams']
    if bigrams:
        bars = ax5.barh(range(len(bigrams)), list(bigrams.values()), color='plum')
        ax5.set_yticks(range(len(bigrams)))
        ax5.set_yticklabels(list(bigrams.keys()))
        ax5.set_title('자주 함께 나타나는 단어 조합', fontsize=14, fontweight='bold')
        ax5.set_xlabel('빈도수')
    
    # 6. Rating Distribution
    ax6 = plt.subplot(3, 3, 6)
    if 'rating' in df.columns:
        rating_counts = df['rating'].value_counts().sort_index()
        bars = ax6.bar(rating_counts.index, rating_counts.values, color='gold')
        ax6.set_title('평점 분포', fontsize=14, fontweight='bold')
        ax6.set_xlabel('평점')
        ax6.set_ylabel('리뷰 수')
        ax6.set_xticks(rating_counts.index)
        
        # Add percentage labels
        total = sum(rating_counts.values)
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}\n({height/total*100:.1f}%)', 
                    ha='center', va='bottom')
    
    # 7. Review Length Distribution
    ax7 = plt.subplot(3, 3, 7)
    review_lengths = df['review_text'].str.len()
    ax7.hist(review_lengths, bins=30, color='lightsteelblue', edgecolor='black')
    ax7.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax7.set_xlabel('글자 수')
    ax7.set_ylabel('리뷰 수')
    ax7.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=1, label=f'평균: {review_lengths.mean():.0f}자')
    ax7.legend()
    
    plt.tight_layout()
    plt.savefig('sonplan_review_analysis_comprehensive.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create Word Cloud
    if analysis_results['all_words']:
        plt.figure(figsize=(12, 8))
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
            background_color='white',
            width=1200,
            height=800,
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(analysis_results['all_words'])
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('썬플랜 타임슬립 아이크림 리뷰 워드클라우드', fontsize=20, fontweight='bold', pad=20)
        plt.savefig('sonplan_wordcloud_comprehensive.png', dpi=300, bbox_inches='tight')
        plt.show()

def generate_insights(analysis_results, df):
    """
    Generate insights from the analysis
    """
    insights = []
    
    # Most common keywords
    top_5_words = list(dict(sorted(analysis_results['all_words'].items(), 
                                  key=lambda x: x[1], reverse=True)[:5]).keys())
    insights.append(f"가장 많이 언급된 키워드: {', '.join(top_5_words)}")
    
    # Most common nouns (product features)
    top_5_nouns = list(dict(sorted(analysis_results['nouns'].items(), 
                                  key=lambda x: x[1], reverse=True)[:5]).keys())
    insights.append(f"주요 제품 특성 키워드: {', '.join(top_5_nouns)}")
    
    # Most common adjectives (customer feelings)
    top_5_adjs = list(dict(sorted(analysis_results['adjectives'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]).keys())
    if top_5_adjs:
        insights.append(f"고객이 자주 사용한 형용사: {', '.join(top_5_adjs)}")
    
    # Review patterns
    avg_length = df['review_text'].str.len().mean()
    insights.append(f"평균 리뷰 길이: {avg_length:.0f}자")
    
    # Rating insights
    if 'rating' in df.columns:
        avg_rating = df['rating'].mean()
        insights.append(f"평균 평점: {avg_rating:.2f}/5.0")
    
    return insights

def main():
    base_url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    print("썬플랜 타임슬립 아이크림 리뷰 분석 시작...")
    print("고객들이 실제로 어떤 이야기를 하는지 분석합니다.\n")
    
    # Scrape reviews
    df_reviews = scrape_sonplan_reviews(base_url, max_pages=5)
    
    if df_reviews.empty:
        print("리뷰 데이터를 가져오지 못했습니다.")
        print("웹사이트 구조가 변경되었을 수 있습니다.")
        return
    
    print(f"\n총 {len(df_reviews)}개의 리뷰를 수집했습니다.")
    
    # Save raw data
    df_reviews.to_csv('sonplan_reviews_raw.csv', index=False, encoding='utf-8-sig')
    print("원본 데이터를 'sonplan_reviews_raw.csv'에 저장했습니다.")
    
    # Analyze keywords
    print("\n키워드 분석 중...")
    analysis = analyze_review_keywords(df_reviews)
    
    # Print detailed results
    print("\n=== 키워드 분석 결과 ===")
    print(f"\n1. 전체 상위 20개 키워드:")
    top_all = dict(sorted(analysis['all_words'].items(), 
                         key=lambda x: x[1], reverse=True)[:20])
    for i, (word, freq) in enumerate(top_all.items(), 1):
        print(f"   {i:2d}. {word}: {freq}회")
    
    print(f"\n2. 명사 상위 15개 (제품 특성):")
    top_nouns = dict(sorted(analysis['nouns'].items(), 
                           key=lambda x: x[1], reverse=True)[:15])
    for i, (word, freq) in enumerate(top_nouns.items(), 1):
        print(f"   {i:2d}. {word}: {freq}회")
    
    print(f"\n3. 형용사 상위 10개 (고객 감정/평가):")
    top_adjs = dict(sorted(analysis['adjectives'].items(), 
                          key=lambda x: x[1], reverse=True)[:10])
    for i, (word, freq) in enumerate(top_adjs.items(), 1):
        print(f"   {i:2d}. {word}: {freq}회")
    
    print(f"\n4. 함께 나타나는 단어 조합:")
    for i, (bigram, freq) in enumerate(analysis['bigrams'].items(), 1):
        if i > 10:
            break
        print(f"   {i:2d}. {bigram}: {freq}회")
    
    # Generate insights
    print("\n=== 주요 인사이트 ===")
    insights = generate_insights(analysis, df_reviews)
    for insight in insights:
        print(f"• {insight}")
    
    # Create visualizations
    print("\n시각화 생성 중...")
    visualize_analysis(analysis, df_reviews)
    
    # Save detailed analysis
    keyword_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '품사': '전체'} 
        for word, freq in analysis['all_words'].items()
    ])
    
    noun_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '품사': '명사'} 
        for word, freq in analysis['nouns'].items()
    ])
    
    adj_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '품사': '형용사'} 
        for word, freq in analysis['adjectives'].items()
    ])
    
    all_keywords_df = pd.concat([keyword_df, noun_df, adj_df], ignore_index=True)
    all_keywords_df = all_keywords_df.sort_values(['품사', '빈도'], ascending=[True, False])
    all_keywords_df.to_csv('sonplan_keyword_analysis_detailed.csv', index=False, encoding='utf-8-sig')
    
    print("\n상세 키워드 분석 결과를 'sonplan_keyword_analysis_detailed.csv'에 저장했습니다.")
    print("\n분석 완료!")

if __name__ == "__main__":
    main()