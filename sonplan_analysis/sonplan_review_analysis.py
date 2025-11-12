import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set Korean font
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def load_and_combine_data():
    """
    Load both CSV files and combine them
    """
    print("CSV 파일 로드 및 결합 중...")
    
    # Load both files
    df1 = pd.read_csv('/Users/jaewansim/Documents/nerdlab/sonplancos_20250718_3321_review1.csv')
    df2 = pd.read_csv('/Users/jaewansim/Documents/nerdlab/sonplancos_20250718_3321_review2.csv')
    
    # Combine dataframes
    df_combined = pd.concat([df1, df2], ignore_index=True)
    
    print(f"파일 1: {len(df1):,}개 리뷰")
    print(f"파일 2: {len(df2):,}개 리뷰")
    print(f"전체: {len(df_combined):,}개 리뷰")
    
    return df_combined

def preprocess_text(df):
    """
    Preprocess review text for analysis
    """
    print("\n텍스트 전처리 중...")
    
    # Remove empty content
    df = df.dropna(subset=['내용'])
    df = df[df['내용'].str.len() > 0]
    
    # Clean text data
    df['cleaned_content'] = df['내용'].apply(lambda x: str(x))
    
    # Remove duplicate reviews
    original_count = len(df)
    df = df.drop_duplicates(subset=['내용'])
    print(f"중복 제거: {original_count:,}개 → {len(df):,}개")
    
    # Parse dates
    df['작성일시'] = pd.to_datetime(df['게시물 작성일시'], errors='coerce')
    
    return df

def extract_keywords(text_series):
    """
    Extract Korean keywords from text
    """
    print("키워드 추출 중...")
    
    # Combine all text
    all_text = ' '.join(text_series.astype(str))
    
    # Extract Korean words (2-6 characters)
    korean_words = re.findall(r'[가-힣]{2,6}', all_text)
    
    # Stop words for cosmetics reviews
    stop_words = {
        '있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', 
        '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', 
        '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', 
        '되어', '됩니다', '합니다', '있고', '없고', '같은', '이런', '그런', '저런', '모든', 
        '각각', '그리고', '하지만', '그러나', '그래서', '따라서', '때문에', '위해', '통해', 
        '대해', '관해', '또한', '역시', '아주', '매우', '너무', '정말', '진짜', '아마', 
        '언제', '어디', '무엇', '누구', '어떻게', '왜', '어느', '얼마', '몇', '게시물', 
        '제목', '내용', '작성자', '이름', '아이디', '작성일시', '카테고리', '감사', '감사합니다'
    }
    
    # Filter stop words
    filtered_words = [word for word in korean_words if word not in stop_words]
    
    # Count frequency
    word_freq = Counter(filtered_words)
    
    return word_freq

def analyze_sentiment_keywords(word_freq):
    """
    Categorize keywords by sentiment and themes
    """
    # Define keyword categories for cosmetics
    categories = {
        '긍정적 감정': ['좋아', '좋은', '좋네', '만족', '추천', '최고', '완벽', '훌륭', '대박', '짱', '굿'],
        '제품 특성': ['촉촉', '부드러', '쫀쫀', '가벼운', '산뜻', '끈적', '무거운', '텍스처', '제형'],
        '효과': ['효과', '개선', '좋아졌', '변화', '달라', '느낌', '탄력', '주름', '보습', '수분'],
        '사용성': ['발림', '흡수', '사용', '발라', '바르기', '펴발', '스며', '발림성'],
        '구매/재구매': ['구매', '재구매', '리피', '또', '다시', '계속', '주문', '샀어', '살게'],
        '추천/공유': ['추천', '소개', '입소문', '엄마', '친구', '가족', '주변', '같이'],
        '부정적': ['별로', '아쉬워', '실망', '안좋', '그저그래', '보통', '흠']
    }
    
    category_analysis = {}
    
    for category, keywords in categories.items():
        category_words = {}
        for word, freq in word_freq.items():
            for keyword in keywords:
                if keyword in word:
                    category_words[word] = freq
                    break
        category_analysis[category] = category_words
    
    return category_analysis

def create_wordcloud(word_freq, title="워드클라우드"):
    """
    Create word cloud visualization
    """
    print(f"{title} 생성 중...")
    
    # Create word cloud
    wordcloud = WordCloud(
        font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
        background_color='white',
        width=1200,
        height=800,
        max_words=150,
        relative_scaling=0.5,
        min_font_size=10,
        colormap='viridis'
    ).generate_from_frequencies(dict(word_freq))
    
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title, fontsize=20, fontweight='bold', pad=20)
    
    # Save
    filename = f'sonplan_{title.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    return filename

def create_comprehensive_analysis(df, word_freq, category_analysis):
    """
    Create comprehensive analysis visualizations
    """
    print("\n종합 분석 시각화 생성 중...")
    
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Top Keywords
    ax1 = plt.subplot(3, 3, 1)
    top_words = dict(word_freq.most_common(20))
    bars = ax1.bar(range(len(top_words)), list(top_words.values()), color='skyblue')
    ax1.set_xticks(range(len(top_words)))
    ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
    ax1.set_title('가장 많이 언급된 키워드 TOP 20', fontsize=14, fontweight='bold')
    ax1.set_ylabel('빈도수')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # 2. Review Length Distribution
    ax2 = plt.subplot(3, 3, 2)
    review_lengths = df['내용'].str.len()
    ax2.hist(review_lengths, bins=50, color='lightgreen', edgecolor='black', alpha=0.7)
    ax2.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax2.set_xlabel('글자 수')
    ax2.set_ylabel('리뷰 수')
    ax2.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=2,
                label=f'평균: {review_lengths.mean():.0f}자')
    ax2.legend()
    
    # 3. Monthly Review Trend
    ax3 = plt.subplot(3, 3, 3)
    if df['작성일시'].notna().any():
        df['월'] = df['작성일시'].dt.to_period('M')
        monthly_counts = df.groupby('월').size()
        monthly_counts.plot(ax=ax3, kind='line', marker='o', linewidth=2, markersize=6)
        ax3.set_title('월별 리뷰 추이', fontsize=14, fontweight='bold')
        ax3.set_xlabel('월')
        ax3.set_ylabel('리뷰 수')
        ax3.tick_params(axis='x', rotation=45)
    
    # 4-8. Category Analysis
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
    
    for idx, (category, words) in enumerate(list(category_analysis.items())[:5]):
        ax = plt.subplot(3, 3, 4 + idx)
        if words:
            top_category_words = dict(sorted(words.items(), key=lambda x: x[1], reverse=True)[:10])
            if top_category_words:
                bars = ax.bar(range(len(top_category_words)), list(top_category_words.values()),
                             color=colors[idx % len(colors)])
                ax.set_xticks(range(len(top_category_words)))
                ax.set_xticklabels(list(top_category_words.keys()), rotation=45, ha='right')
                ax.set_title(f'{category} 관련 키워드', fontsize=12, fontweight='bold')
                ax.set_ylabel('빈도수')
    
    # 9. Summary Statistics
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    total_reviews = len(df)
    unique_keywords = len(word_freq)
    avg_length = review_lengths.mean()
    
    # Calculate sentiment ratio
    positive_words = len(category_analysis.get('긍정적 감정', {}))
    negative_words = len(category_analysis.get('부정적', {}))
    
    summary_text = f"""
    📊 썬플랜 리뷰 분석 요약
    
    총 리뷰 수: {total_reviews:,}개
    평균 리뷰 길이: {avg_length:.0f}자
    추출된 고유 키워드: {unique_keywords:,}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 키워드:
      {', '.join(list(top_words.keys())[:5])}
    
    • 긍정 키워드: {positive_words}개
    • 부정 키워드: {negative_words}개
    
    • 리뷰 기간: {df['작성일시'].min().strftime('%Y-%m') if df['작성일시'].notna().any() else 'N/A'} ~ 
      {df['작성일시'].max().strftime('%Y-%m') if df['작성일시'].notna().any() else 'N/A'}
    """
    
    ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_detailed_report(df, word_freq, category_analysis):
    """
    Create detailed text report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f'sonplan_analysis_report_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write("썬플랜 제품 리뷰 분석 보고서\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"분석 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}\n")
        f.write(f"총 리뷰 수: {len(df):,}개\n\n")
        
        # Basic statistics
        f.write("=== 기본 통계 ===\n")
        f.write(f"평균 리뷰 길이: {df['내용'].str.len().mean():.0f}자\n")
        f.write(f"최대 리뷰 길이: {df['내용'].str.len().max()}자\n")
        f.write(f"최소 리뷰 길이: {df['내용'].str.len().min()}자\n\n")
        
        # Top keywords
        f.write("=== 상위 50개 키워드 ===\n")
        for i, (word, freq) in enumerate(word_freq.most_common(50), 1):
            f.write(f"{i:2d}. {word}: {freq:,}회\n")
        
        # Category analysis
        f.write("\n=== 카테고리별 분석 ===\n")
        for category, words in category_analysis.items():
            f.write(f"\n[{category}] - 총 {sum(words.values()):,}회 언급\n")
            top_words = dict(sorted(words.items(), key=lambda x: x[1], reverse=True)[:10])
            for word, freq in top_words.items():
                f.write(f"  - {word}: {freq:,}회\n")
        
        # Sample reviews
        f.write("\n=== 리뷰 샘플 ===\n")
        sample_reviews = df.sample(n=min(20, len(df)), random_state=42)
        for i, (_, row) in enumerate(sample_reviews.iterrows(), 1):
            f.write(f"\n{i}. [{row['작성자 이름']}] {row['게시물 작성일시']}\n")
            f.write(f"   {row['내용'][:100]}{'...' if len(row['내용']) > 100 else ''}\n")
    
    return f'sonplan_analysis_report_{timestamp}.txt'

def main():
    print("썬플랜 리뷰 데이터 분석 시작")
    print("=" * 50)
    
    # Load and preprocess data
    df = load_and_combine_data()
    df = preprocess_text(df)
    
    # Extract keywords
    word_freq = extract_keywords(df['내용'])
    
    # Analyze categories
    category_analysis = analyze_sentiment_keywords(word_freq)
    
    # Create visualizations
    print("\n=== 시각화 생성 ===")
    
    # 1. Main word cloud
    create_wordcloud(word_freq, "썬플랜 리뷰 워드클라우드")
    
    # 2. Positive keywords word cloud
    positive_words = category_analysis.get('긍정적 감정', {})
    if positive_words:
        create_wordcloud(positive_words, "긍정적 키워드 워드클라우드")
    
    # 3. Product characteristics word cloud
    product_words = category_analysis.get('제품 특성', {})
    if product_words:
        create_wordcloud(product_words, "제품 특성 키워드 워드클라우드")
    
    # 4. Comprehensive analysis
    create_comprehensive_analysis(df, word_freq, category_analysis)
    
    # Print results
    print("\n=== 주요 분석 결과 ===")
    print(f"\n📊 전체 통계:")
    print(f"- 총 리뷰 수: {len(df):,}개")
    print(f"- 평균 리뷰 길이: {df['내용'].str.len().mean():.0f}자")
    print(f"- 추출된 키워드: {len(word_freq):,}개")
    
    print(f"\n🔥 상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        if i % 4 == 1 and i > 1:
            print()
        print(f"{i:2d}.{word}({freq:,})", end="  ")
    
    print(f"\n\n📈 카테고리별 주요 인사이트:")
    for category, words in category_analysis.items():
        if words:
            total_mentions = sum(words.values())
            top_word = max(words.items(), key=lambda x: x[1])
            print(f"- {category}: {total_mentions:,}회 (주요: {top_word[0]})")
    
    # Save detailed report
    report_file = create_detailed_report(df, word_freq, category_analysis)
    print(f"\n📝 상세 보고서 저장: {report_file}")
    
    # Save processed data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Keywords CSV
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(200))
    ])
    keywords_df.to_csv(f'sonplan_keywords_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Category analysis CSV
    category_data = []
    for category, words in category_analysis.items():
        for word, freq in words.items():
            category_data.append({
                '카테고리': category,
                '키워드': word,
                '빈도': freq
            })
    
    if category_data:
        category_df = pd.DataFrame(category_data)
        category_df = category_df.sort_values(['카테고리', '빈도'], ascending=[True, False])
        category_df.to_csv(f'sonplan_categories_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    print(f"\n💾 결과 파일:")
    print(f"- 키워드 분석: sonplan_keywords_{timestamp}.csv")
    print(f"- 카테고리 분석: sonplan_categories_{timestamp}.csv")
    print(f"- 워드클라우드: sonplan_*워드클라우드*.png")
    print(f"- 종합 분석: sonplan_comprehensive_analysis.png")
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()