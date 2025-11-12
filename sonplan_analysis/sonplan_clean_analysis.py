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

def load_and_clean_data():
    """
    Load both CSV files, combine them, and remove NaverPay reviews
    """
    print("CSV 파일 로드 및 정제 중...")
    
    # Load both files
    df1 = pd.read_csv('/Users/jaewansim/Documents/nerdlab/sonplancos_20250718_3321_review1.csv')
    df2 = pd.read_csv('/Users/jaewansim/Documents/nerdlab/sonplancos_20250718_3321_review2.csv')
    
    print(f"파일 1 원본: {len(df1):,}개 리뷰")
    print(f"파일 2 원본: {len(df2):,}개 리뷰")
    
    # Combine dataframes
    df_combined = pd.concat([df1, df2], ignore_index=True)
    print(f"전체 원본: {len(df_combined):,}개 리뷰")
    
    # Remove NaverPay reviews
    # Look for patterns indicating NaverPay automated reviews
    naverpay_patterns = [
        '네이버페이 구매평',
        '네이버 페이 구매평',
        '네이버페이',
        '네이버 페이',
        '구매평 등록',
        '자동 등록',
        '네이버쇼핑',
        'NAVER',
        '네이버',
        '스마트스토어'
    ]
    
    # Check for NaverPay patterns in content
    original_count = len(df_combined)
    
    for pattern in naverpay_patterns:
        df_combined = df_combined[~df_combined['내용'].str.contains(pattern, na=False)]
    
    # Also check for very short generic reviews (likely automated)
    df_combined = df_combined[df_combined['내용'].str.len() > 5]
    
    # Remove reviews with only emojis or very repetitive content
    df_combined = df_combined[~df_combined['내용'].str.match(r'^[^\w가-힣]*$', na=False)]
    
    # Check for duplicate content (common in automated reviews)
    df_combined = df_combined.drop_duplicates(subset=['내용'])
    
    print(f"정제 후: {len(df_combined):,}개 리뷰")
    print(f"제거된 리뷰: {original_count - len(df_combined):,}개")
    
    # Clean and preprocess
    df_combined = df_combined.dropna(subset=['내용'])
    df_combined['작성일시'] = pd.to_datetime(df_combined['게시물 작성일시'], errors='coerce')
    
    return df_combined

def extract_meaningful_keywords(text_series):
    """
    Extract meaningful Korean keywords from text
    """
    print("의미있는 키워드 추출 중...")
    
    # Combine all text
    all_text = ' '.join(text_series.astype(str))
    
    # Extract Korean words (2-8 characters for more meaningful words)
    korean_words = re.findall(r'[가-힣]{2,8}', all_text)
    
    # Comprehensive stop words
    stop_words = {
        # Common words
        '있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', 
        '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', 
        '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', 
        '되어', '됩니다', '합니다', '있고', '없고', '같은', '이런', '그런', '저런', '모든', 
        '각각', '그리고', '하지만', '그러나', '그래서', '따라서', '때문에', '위해', '통해', 
        '대해', '관해', '또한', '역시', '아주', '매우', '너무', '정말', '진짜', '아마', 
        '언제', '어디', '무엇', '누구', '어떻게', '왜', '어느', '얼마', '몇',
        # Meta words
        '게시물', '제목', '내용', '작성자', '이름', '아이디', '작성일시', '카테고리', 
        '감사', '감사합니다', '고맙습니다', '안녕하세요', '안녕히', '여러분', '모두', '다들',
        # Generic phrases
        '생각', '마음', '기분', '느낌', '정도', '상태', '경우', '방법', '시간', '다음', 
        '이번', '지금', '그때', '요즘', '오늘', '내일', '어제', '처음', '마지막', '계속',
        # Filler words
        '그냥', '조금', '약간', '살짝', '좀', '많이', '완전', '진짜', '정말', '엄청', 
        '되게', '꽤', '상당히', '보통', '일반', '평소', '항상', '늘', '자주', '가끔'
    }
    
    # Filter stop words and short words
    filtered_words = [word for word in korean_words if word not in stop_words and len(word) >= 2]
    
    # Count frequency
    word_freq = Counter(filtered_words)
    
    # Remove words that appear only once (likely typos or very specific terms)
    word_freq = Counter({word: freq for word, freq in word_freq.items() if freq > 1})
    
    return word_freq

def analyze_product_themes(word_freq):
    """
    Categorize keywords by product themes and sentiment
    """
    print("제품 테마별 키워드 분석 중...")
    
    # Define detailed categories for cosmetics analysis
    theme_categories = {
        '만족도': {
            '긍정': ['좋아', '좋은', '좋네', '좋다', '만족', '추천', '최고', '완벽', '훌륭', '대박', '짱', '굿', '베스트', '완전'],
            '부정': ['별로', '아쉬워', '실망', '안좋', '그저그래', '보통', '흠', '별로네', '아쉽']
        },
        '제품특성': {
            '텍스처': ['촉촉', '부드러', '쫀쫀', '가벼운', '산뜻', '끈적', '무거운', '텍스처', '제형', '발림', '흡수'],
            '향': ['향', '냄새', '향기', '시카향', '무향', '향이'],
            '용량': ['용량', '많이', '적당', '크기']
        },
        '효과': {
            '보습': ['보습', '수분', '촉촉', '건조', '당김'],
            '개선': ['효과', '개선', '좋아졌', '변화', '달라', '탄력', '주름'],
            '안전성': ['자극', '순한', '민감', '알러지', '트러블', '따가움']
        },
        '사용경험': {
            '사용성': ['사용', '발라', '바르기', '펴발', '스며', '발림성', '세수', '씻고'],
            '지속성': ['지속', '오래', '계속', '하루', '이틀', '며칠']
        },
        '구매행동': {
            '구매': ['구매', '샀어', '사러', '주문', '구입'],
            '재구매': ['재구매', '리피', '또', '다시', '계속', '몇번째'],
            '추천': ['추천', '소개', '입소문', '엄마', '친구', '가족', '주변', '같이', '이모']
        }
    }
    
    # Analyze themes
    theme_analysis = {}
    
    for main_theme, sub_themes in theme_categories.items():
        theme_analysis[main_theme] = {}
        
        for sub_theme, keywords in sub_themes.items():
            matched_words = {}
            
            for word, freq in word_freq.items():
                for keyword in keywords:
                    if keyword in word:
                        matched_words[word] = freq
                        break
            
            if matched_words:
                theme_analysis[main_theme][sub_theme] = matched_words
    
    return theme_analysis

def create_enhanced_wordcloud(word_freq, title="워드클라우드", colormap='viridis'):
    """
    Create enhanced word cloud visualization
    """
    print(f"{title} 생성 중...")
    
    if not word_freq:
        print(f"No words found for {title}")
        return None
    
    # Create word cloud with better settings
    wordcloud = WordCloud(
        font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
        background_color='white',
        width=1400,
        height=900,
        max_words=100,
        relative_scaling=0.5,
        min_font_size=12,
        max_font_size=80,
        colormap=colormap,
        prefer_horizontal=0.7
    ).generate_from_frequencies(dict(word_freq))
    
    plt.figure(figsize=(14, 9))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title, fontsize=22, fontweight='bold', pad=30)
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'sonplan_{title.replace(" ", "_")}_{timestamp}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    return filename

def create_comprehensive_dashboard(df, word_freq, theme_analysis):
    """
    Create comprehensive analysis dashboard
    """
    print("종합 분석 대시보드 생성 중...")
    
    fig = plt.figure(figsize=(24, 18))
    
    # 1. Top Keywords (larger)
    ax1 = plt.subplot(3, 4, (1, 2))
    top_words = dict(word_freq.most_common(25))
    bars = ax1.bar(range(len(top_words)), list(top_words.values()), 
                   color=plt.cm.Set3(np.linspace(0, 1, len(top_words))))
    ax1.set_xticks(range(len(top_words)))
    ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
    ax1.set_title('가장 많이 언급된 키워드 TOP 25', fontsize=16, fontweight='bold')
    ax1.set_ylabel('빈도수')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    # 2. Review Length Distribution
    ax2 = plt.subplot(3, 4, 3)
    review_lengths = df['내용'].str.len()
    ax2.hist(review_lengths, bins=30, color='lightblue', edgecolor='black', alpha=0.7)
    ax2.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax2.set_xlabel('글자 수')
    ax2.set_ylabel('리뷰 수')
    ax2.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=2)
    
    # 3. Monthly Review Trend
    ax3 = plt.subplot(3, 4, 4)
    if df['작성일시'].notna().any():
        df['년월'] = df['작성일시'].dt.to_period('M')
        monthly_counts = df.groupby('년월').size()
        monthly_counts.plot(ax=ax3, kind='line', marker='o', linewidth=2, markersize=6, color='green')
        ax3.set_title('월별 리뷰 추이', fontsize=14, fontweight='bold')
        ax3.set_xlabel('월')
        ax3.set_ylabel('리뷰 수')
        ax3.tick_params(axis='x', rotation=45)
    
    # 4-8. Theme Analysis
    theme_colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']
    plot_idx = 5
    
    for theme_idx, (main_theme, sub_themes) in enumerate(theme_analysis.items()):
        if plot_idx > 12:  # Limit to available subplot spaces
            break
            
        ax = plt.subplot(3, 4, plot_idx)
        
        # Aggregate all words from sub-themes
        all_theme_words = {}
        for sub_theme, words in sub_themes.items():
            all_theme_words.update(words)
        
        if all_theme_words:
            top_theme_words = dict(sorted(all_theme_words.items(), 
                                         key=lambda x: x[1], reverse=True)[:10])
            
            bars = ax.bar(range(len(top_theme_words)), list(top_theme_words.values()),
                         color=theme_colors[theme_idx % len(theme_colors)])
            ax.set_xticks(range(len(top_theme_words)))
            ax.set_xticklabels(list(top_theme_words.keys()), rotation=45, ha='right')
            ax.set_title(f'{main_theme} 관련 키워드', fontsize=12, fontweight='bold')
            ax.set_ylabel('빈도수')
        
        plot_idx += 1
    
    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f'sonplan_comprehensive_dashboard_{timestamp}.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_insights(df, word_freq, theme_analysis):
    """
    Generate actionable insights from the analysis
    """
    print("\n🔍 인사이트 분석 중...")
    
    insights = []
    
    # 1. Overall sentiment analysis
    positive_themes = theme_analysis.get('만족도', {}).get('긍정', {})
    negative_themes = theme_analysis.get('만족도', {}).get('부정', {})
    
    positive_count = sum(positive_themes.values()) if positive_themes else 0
    negative_count = sum(negative_themes.values()) if negative_themes else 0
    
    sentiment_ratio = positive_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0
    
    insights.append({
        'category': '고객 만족도',
        'finding': f'긍정적 언급이 {sentiment_ratio:.1%}로 압도적으로 많음',
        'implication': '전반적인 고객 만족도가 매우 높음',
        'action': '현재 제품 품질 유지 및 마케팅 포인트로 활용'
    })
    
    # 2. Top keywords analysis
    top_5_keywords = list(word_freq.most_common(5))
    most_mentioned = top_5_keywords[0][0] if top_5_keywords else "없음"
    
    insights.append({
        'category': '핵심 키워드',
        'finding': f'가장 많이 언급된 키워드는 "{most_mentioned}"',
        'implication': '이 키워드가 고객들의 주요 관심사',
        'action': '해당 키워드를 중심으로 한 마케팅 메시지 강화'
    })
    
    # 3. Product characteristics analysis
    texture_words = theme_analysis.get('제품특성', {}).get('텍스처', {})
    if texture_words:
        top_texture = max(texture_words.items(), key=lambda x: x[1])
        insights.append({
            'category': '제품 특성',
            'finding': f'텍스처 관련해서는 "{top_texture[0]}"이 가장 많이 언급됨',
            'implication': '고객들이 인식하는 주요 제품 특성',
            'action': '제품 설명 및 광고에서 해당 특성 부각'
        })
    
    # 4. Purchase behavior analysis
    repurchase_words = theme_analysis.get('구매행동', {}).get('재구매', {})
    if repurchase_words:
        repurchase_mentions = sum(repurchase_words.values())
        insights.append({
            'category': '재구매 의도',
            'finding': f'재구매 관련 언급이 {repurchase_mentions}회 나타남',
            'implication': '고객 충성도가 높고 재구매 의도가 강함',
            'action': '리피터 고객 대상 특별 혜택 및 프로모션 기획'
        })
    
    # 5. Word-of-mouth analysis
    recommendation_words = theme_analysis.get('구매행동', {}).get('추천', {})
    if recommendation_words:
        wom_mentions = sum(recommendation_words.values())
        insights.append({
            'category': '입소문 효과',
            'finding': f'추천/입소문 관련 언급이 {wom_mentions}회 나타남',
            'implication': '자연스러운 입소문이 활발히 일어나고 있음',
            'action': '리뷰 이벤트 및 추천 리워드 프로그램 운영'
        })
    
    # 6. Usage experience analysis
    usage_words = theme_analysis.get('사용경험', {}).get('사용성', {})
    if usage_words:
        top_usage = max(usage_words.items(), key=lambda x: x[1])
        insights.append({
            'category': '사용 경험',
            'finding': f'사용 관련해서는 "{top_usage[0]}"이 주요 키워드',
            'implication': '고객들의 실제 사용 경험에서 중요한 포인트',
            'action': '사용법 가이드 및 사용 팁 콘텐츠 제작'
        })
    
    # 7. Review volume analysis
    total_reviews = len(df)
    if df['작성일시'].notna().any():
        review_period = (df['작성일시'].max() - df['작성일시'].min()).days
        daily_avg = total_reviews / review_period if review_period > 0 else 0
        
        insights.append({
            'category': '리뷰 활동량',
            'finding': f'일평균 {daily_avg:.1f}개의 리뷰가 작성됨',
            'implication': '활발한 고객 참여도',
            'action': '지속적인 고객 소통 및 피드백 관리 필요'
        })
    
    return insights

def create_insight_report(insights, df, word_freq, theme_analysis):
    """
    Create comprehensive insight report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'sonplan_insights_report_{timestamp}.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("썬플랜 제품 리뷰 인사이트 분석 보고서\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"분석 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}\n")
        f.write(f"분석 대상: 정제된 리뷰 {len(df):,}개\n\n")
        
        # Executive Summary
        f.write("📈 EXECUTIVE SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"• 총 리뷰 수: {len(df):,}개\n")
        f.write(f"• 평균 리뷰 길이: {df['내용'].str.len().mean():.0f}자\n")
        f.write(f"• 추출된 키워드: {len(word_freq):,}개\n")
        f.write(f"• 주요 키워드: {', '.join([word for word, _ in word_freq.most_common(5)])}\n\n")
        
        # Key Insights
        f.write("🔍 KEY INSIGHTS\n")
        f.write("-" * 30 + "\n")
        for i, insight in enumerate(insights, 1):
            f.write(f"{i}. {insight['category']}\n")
            f.write(f"   발견사항: {insight['finding']}\n")
            f.write(f"   시사점: {insight['implication']}\n")
            f.write(f"   액션 아이템: {insight['action']}\n\n")
        
        # Detailed Analysis
        f.write("📊 DETAILED ANALYSIS\n")
        f.write("-" * 30 + "\n\n")
        
        # Top Keywords
        f.write("상위 30개 키워드:\n")
        for i, (word, freq) in enumerate(word_freq.most_common(30), 1):
            f.write(f"{i:2d}. {word}: {freq:,}회\n")
        
        # Theme Analysis
        f.write("\n테마별 분석:\n")
        for main_theme, sub_themes in theme_analysis.items():
            f.write(f"\n[{main_theme}]\n")
            for sub_theme, words in sub_themes.items():
                if words:
                    f.write(f"  {sub_theme}: {sum(words.values()):,}회 언급\n")
                    top_words = dict(sorted(words.items(), key=lambda x: x[1], reverse=True)[:5])
                    f.write(f"    주요 키워드: {', '.join([f'{w}({c})' for w, c in top_words.items()])}\n")
        
        # Recommendations
        f.write("\n🎯 RECOMMENDATIONS\n")
        f.write("-" * 30 + "\n")
        f.write("1. 마케팅 전략:\n")
        f.write("   - 고객 만족도가 높으므로 testimonial 마케팅 활용\n")
        f.write("   - 주요 키워드를 활용한 SEO 최적화\n\n")
        
        f.write("2. 제품 개발:\n")
        f.write("   - 현재 제품 품질 유지가 최우선\n")
        f.write("   - 고객이 언급하는 주요 특성 강화\n\n")
        
        f.write("3. 고객 관리:\n")
        f.write("   - 리뷰 작성 고객 대상 리워드 프로그램\n")
        f.write("   - 재구매 고객 대상 특별 혜택\n\n")
        
        f.write("4. 콘텐츠 전략:\n")
        f.write("   - 고객 리뷰 기반 사용법 가이드 제작\n")
        f.write("   - 입소문 효과를 활용한 소셜 마케팅\n")
    
    return filename

def main():
    print("썬플랜 리뷰 데이터 정제 및 분석 시작")
    print("=" * 60)
    
    # 1. Load and clean data
    df = load_and_clean_data()
    
    # 2. Extract meaningful keywords
    word_freq = extract_meaningful_keywords(df['내용'])
    
    # 3. Analyze themes
    theme_analysis = analyze_product_themes(word_freq)
    
    # 4. Create visualizations
    print("\n=== 시각화 생성 ===")
    
    # Main word cloud
    create_enhanced_wordcloud(word_freq, "썬플랜 리뷰 전체 워드클라우드", 'viridis')
    
    # Positive sentiment word cloud
    positive_words = theme_analysis.get('만족도', {}).get('긍정', {})
    if positive_words:
        create_enhanced_wordcloud(positive_words, "긍정적 키워드 워드클라우드", 'Greens')
    
    # Product characteristics word cloud
    product_words = {}
    for sub_theme, words in theme_analysis.get('제품특성', {}).items():
        product_words.update(words)
    if product_words:
        create_enhanced_wordcloud(product_words, "제품 특성 키워드 워드클라우드", 'Blues')
    
    # Comprehensive dashboard
    create_comprehensive_dashboard(df, word_freq, theme_analysis)
    
    # 5. Generate insights
    insights = generate_insights(df, word_freq, theme_analysis)
    
    # 6. Create insight report
    report_filename = create_insight_report(insights, df, word_freq, theme_analysis)
    
    # 7. Print results
    print("\n" + "=" * 60)
    print("🎯 주요 인사이트 요약")
    print("=" * 60)
    
    for i, insight in enumerate(insights, 1):
        print(f"\n{i}. {insight['category']}")
        print(f"   💡 {insight['finding']}")
        print(f"   📈 {insight['implication']}")
        print(f"   🎬 {insight['action']}")
    
    print(f"\n" + "=" * 60)
    print("📊 분석 결과 요약")
    print("=" * 60)
    print(f"• 분석된 리뷰 수: {len(df):,}개")
    print(f"• 추출된 키워드: {len(word_freq):,}개")
    print(f"• 평균 리뷰 길이: {df['내용'].str.len().mean():.0f}자")
    
    print(f"\n🔥 TOP 10 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(10), 1):
        print(f"{i:2d}. {word}: {freq:,}회")
    
    print(f"\n📝 생성된 파일:")
    print(f"• 인사이트 보고서: {report_filename}")
    print(f"• 워드클라우드: sonplan_*워드클라우드*.png")
    print(f"• 종합 대시보드: sonplan_comprehensive_dashboard*.png")
    
    # Save processed data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f'sonplan_cleaned_reviews_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(100))
    ])
    keywords_df.to_csv(f'sonplan_keywords_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    print(f"• 정제된 리뷰 데이터: sonplan_cleaned_reviews_{timestamp}.csv")
    print(f"• 키워드 데이터: sonplan_keywords_{timestamp}.csv")
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()