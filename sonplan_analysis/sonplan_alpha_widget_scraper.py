import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time

def get_alpha_widget_reviews():
    """
    Get reviews from Alpha Widget API
    """
    base_url = 'https://review.alphwidget.com'
    client_id = 'tgHZp6LCG5KuklqvIYgrtB'
    
    # Session to maintain cookies
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Origin': 'https://sonplan.com',
        'Referer': 'https://sonplan.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # First, create session
    session_url = f"{base_url}/api_widget/module/session"
    session_data = {
        'client_id': client_id,
        'shop_domain': 'sonplan.com',
        'product_id': '10',
        'product_code': '10'
    }
    
    try:
        print(f"Creating session at: {session_url}")
        session_response = session.post(session_url, json=session_data, headers=headers)
        print(f"Session response status: {session_response.status_code}")
        
        if session_response.status_code == 200:
            session_info = session_response.json()
            print(f"Session created: {json.dumps(session_info, indent=2, ensure_ascii=False)[:200]}...")
    except Exception as e:
        print(f"Session error: {e}")
    
    # Try different API endpoints for reviews
    review_endpoints = [
        f"{base_url}/api_widget/reviews/list",
        f"{base_url}/api_widget/module/reviews",
        f"{base_url}/api_widget/product/reviews",
        f"{base_url}/api/reviews/list",
        f"{base_url}/widget/reviews"
    ]
    
    reviews_data = []
    
    for endpoint in review_endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        
        # Common parameters for Alpha Widget
        params = {
            'client_id': client_id,
            'shop_domain': 'sonplan.com',
            'product_id': '10',
            'product_code': '10',
            'page': 1,
            'limit': 100,
            'sort': 'recent'
        }
        
        try:
            response = session.get(endpoint, params=params, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response preview: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")
                    
                    # Extract reviews from various possible structures
                    if 'reviews' in data:
                        reviews_data = data['reviews']
                        break
                    elif 'data' in data:
                        if isinstance(data['data'], list):
                            reviews_data = data['data']
                            break
                        elif isinstance(data['data'], dict) and 'list' in data['data']:
                            reviews_data = data['data']['list']
                            break
                        elif isinstance(data['data'], dict) and 'reviews' in data['data']:
                            reviews_data = data['data']['reviews']
                            break
                    elif 'list' in data:
                        reviews_data = data['list']
                        break
                    elif 'items' in data:
                        reviews_data = data['items']
                        break
                except json.JSONDecodeError:
                    # Try HTML parsing if not JSON
                    soup = BeautifulSoup(response.content, 'html.parser')
                    review_elements = soup.find_all(['div', 'li'], class_=re.compile('review'))
                    
                    for elem in review_elements:
                        review_text = elem.get_text(strip=True)
                        if len(review_text) > 10:
                            reviews_data.append({
                                'content': review_text,
                                'rating': 5,
                                'writer': 'Customer',
                                'created_at': ''
                            })
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # If still no data, try widget HTML endpoint
    if not reviews_data:
        print("\nTrying widget HTML endpoint...")
        widget_url = f"{base_url}/widget/index"
        
        params = {
            'client_id': client_id,
            'product_id': '10',
            'shop_domain': 'sonplan.com'
        }
        
        try:
            response = session.get(widget_url, params=params, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for review containers
                review_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile('review|item'))
                
                for container in review_containers:
                    # Extract review content
                    content_elem = container.find(class_=re.compile('content|text|comment|description'))
                    if content_elem:
                        content = content_elem.get_text(strip=True)
                    else:
                        content = container.get_text(strip=True)
                    
                    # Extract rating
                    rating = 5
                    star_elem = container.find(class_=re.compile('star|rating'))
                    if star_elem:
                        # Try to find filled stars
                        filled_stars = len(star_elem.find_all(class_=re.compile('fill|active|on')))
                        if filled_stars > 0:
                            rating = filled_stars
                        else:
                            # Try to extract from style or data attribute
                            rating_match = re.search(r'(\d+)점|rating["\']?\s*[:=]\s*(\d+)', str(star_elem))
                            if rating_match:
                                rating = int(rating_match.group(1) or rating_match.group(2))
                    
                    # Extract writer
                    writer = 'Customer'
                    writer_elem = container.find(class_=re.compile('writer|name|user|author'))
                    if writer_elem:
                        writer = writer_elem.get_text(strip=True)
                    
                    # Extract date
                    date = ''
                    date_elem = container.find(class_=re.compile('date|time|created'))
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                    
                    if content and len(content) > 10:
                        reviews_data.append({
                            'content': content,
                            'rating': rating,
                            'writer': writer,
                            'created_at': date
                        })
                
                print(f"Found {len(reviews_data)} reviews from widget HTML")
        except Exception as e:
            print(f"Widget HTML error: {e}")
    
    return reviews_data

def analyze_reviews(reviews_data):
    """
    Analyze review data
    """
    if not reviews_data:
        return None, None, None
    
    # Convert to DataFrame
    df_data = []
    for review in reviews_data:
        if isinstance(review, dict):
            df_data.append({
                'review_text': review.get('content', review.get('comment', review.get('text', review.get('review_content', '')))),
                'rating': int(review.get('rating', review.get('score', review.get('star', 5)))),
                'reviewer': review.get('writer', review.get('name', review.get('user_name', review.get('reviewer', 'Customer')))),
                'date': review.get('created_at', review.get('date', review.get('write_date', '')))
            })
        else:
            df_data.append({
                'review_text': str(review),
                'rating': 5,
                'reviewer': 'Customer',
                'date': ''
            })
    
    df = pd.DataFrame(df_data)
    
    # Clean empty reviews
    df = df[df['review_text'].str.len() > 0]
    
    # Keyword analysis
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', '되어', '됩니다', '합니다', '있고', '없고', '같은', '이런', '그런', '저런', '모든', '각각']
    
    for review in df['review_text']:
        if pd.isna(review):
            continue
        
        # Extract Korean words
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    # Get bigrams
    bigrams = []
    for review in df['review_text']:
        if pd.isna(review):
            continue
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6]
        for i in range(len(words)-1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    # Categorize keywords
    categories = {
        '피부/효과': ['피부', '주름', '눈가', '탄력', '개선', '효과', '좋아', '좋은', '만족', '추천'],
        '텍스처/사용감': ['촉촉', '부드러', '흡수', '발림', '끈적', '가벼', '쫀쫀', '무거', '산뜻'],
        '성분/향': ['성분', '향', '냄새', '자극', '순한', '민감', '알러지', '트러블'],
        '가격/구매': ['가격', '가성비', '비싸', '저렴', '구매', '재구매', '세일', '할인']
    }
    
    category_keywords = {}
    for category, keywords in categories.items():
        category_words = {}
        for word, freq in word_freq.items():
            if any(keyword in word for keyword in keywords):
                category_words[word] = freq
        category_keywords[category] = category_words
    
    return df, word_freq, bigram_freq, category_keywords

def visualize_analysis(df, word_freq, bigram_freq, category_keywords):
    """
    Create comprehensive visualizations
    """
    if df is None or df.empty:
        print("No data to visualize")
        return
    
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Top Keywords
    ax1 = plt.subplot(3, 3, 1)
    top_words = dict(word_freq.most_common(15))
    if top_words:
        bars = ax1.bar(range(len(top_words)), list(top_words.values()), color='skyblue')
        ax1.set_xticks(range(len(top_words)))
        ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
        ax1.set_title('가장 많이 언급된 키워드 TOP 15', fontsize=14, fontweight='bold')
        ax1.set_ylabel('빈도수')
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    # 2. Bigrams
    ax2 = plt.subplot(3, 3, 2)
    top_bigrams = dict(bigram_freq.most_common(10))
    if top_bigrams:
        y_pos = range(len(top_bigrams))
        ax2.barh(y_pos, list(top_bigrams.values()), color='lightcoral')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(list(top_bigrams.keys()))
        ax2.set_title('함께 나타나는 단어 조합 TOP 10', fontsize=14, fontweight='bold')
        ax2.set_xlabel('빈도수')
    
    # 3. Rating Distribution
    ax3 = plt.subplot(3, 3, 3)
    if 'rating' in df.columns:
        rating_counts = df['rating'].value_counts().sort_index()
        colors = ['#ff4444', '#ff7744', '#ffaa44', '#44ff44', '#00ff00']
        bars = ax3.bar(rating_counts.index, rating_counts.values, 
                       color=[colors[min(int(r)-1, 4)] for r in rating_counts.index])
        ax3.set_title('평점 분포', fontsize=14, fontweight='bold')
        ax3.set_xlabel('평점')
        ax3.set_ylabel('리뷰 수')
        ax3.set_xticks(rating_counts.index)
        
        total = sum(rating_counts.values)
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}\n({height/total*100:.1f}%)', 
                    ha='center', va='bottom', fontsize=9)
    
    # 4-7. Category Keywords
    for idx, (category, keywords) in enumerate(category_keywords.items()):
        ax = plt.subplot(3, 3, 4 + idx)
        if keywords:
            top_category = dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10])
            bars = ax.bar(range(len(top_category)), list(top_category.values()), 
                          color=plt.cm.Set3(idx))
            ax.set_xticks(range(len(top_category)))
            ax.set_xticklabels(list(top_category.keys()), rotation=45, ha='right')
            ax.set_title(f'{category} 관련 키워드', fontsize=12, fontweight='bold')
            ax.set_ylabel('빈도수')
    
    # 8. Review Length Distribution
    ax8 = plt.subplot(3, 3, 8)
    review_lengths = df['review_text'].str.len()
    ax8.hist(review_lengths, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
    ax8.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax8.set_xlabel('글자 수')
    ax8.set_ylabel('리뷰 수')
    ax8.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {review_lengths.mean():.0f}자')
    ax8.legend()
    
    # 9. Summary Stats
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
    total_reviews = len(df)
    unique_keywords = len(word_freq)
    
    # Find most positive and negative keywords (based on rating correlation)
    positive_keywords = []
    negative_keywords = []
    
    for word in list(word_freq.keys())[:50]:
        word_reviews = df[df['review_text'].str.contains(word, na=False)]
        if len(word_reviews) >= 3:  # Only consider words that appear in at least 3 reviews
            avg_word_rating = word_reviews['rating'].mean()
            if avg_word_rating >= 4.5:
                positive_keywords.append((word, avg_word_rating))
            elif avg_word_rating <= 3.5:
                negative_keywords.append((word, avg_word_rating))
    
    positive_keywords.sort(key=lambda x: x[1], reverse=True)
    negative_keywords.sort(key=lambda x: x[1])
    
    summary_text = f"""
    📊 썬플랜 타임슬립 아이크림 리뷰 분석 요약
    
    총 리뷰 수: {total_reviews:,}개
    평균 평점: {avg_rating:.2f}/5.0
    평균 리뷰 길이: {review_lengths.mean():.0f}자
    추출된 고유 키워드: {unique_keywords:,}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 키워드:
      {', '.join(list(top_words.keys())[:5])}
    
    • 긍정적 평가와 연관된 키워드:
      {', '.join([kw[0] for kw in positive_keywords[:3]])}
    
    • 주요 카테고리별 언급:
      - 피부/효과: {sum(category_keywords.get('피부/효과', {}).values())}회
      - 텍스처/사용감: {sum(category_keywords.get('텍스처/사용감', {}).values())}회
    """
    
    ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, 
             fontsize=11, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_alpha_widget_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Word Cloud
    if word_freq:
        plt.figure(figsize=(12, 8))
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
            background_color='white',
            width=1200,
            height=800,
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10,
            colormap='viridis'
        ).generate_from_frequencies(dict(word_freq))
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('썬플랜 타임슬립 아이크림 리뷰 워드클라우드', 
                 fontsize=18, fontweight='bold', pad=20)
        plt.savefig('sonplan_alpha_widget_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 - 알파위젯 리뷰 분석")
    print("=" * 50)
    
    # Get reviews from Alpha Widget
    print("\n알파위젯 API에서 리뷰 데이터 수집 중...")
    reviews_data = get_alpha_widget_reviews()
    
    if not reviews_data:
        print("\n리뷰 데이터를 가져올 수 없습니다.")
        print("\n브라우저 개발자 도구에서 다음을 확인해주세요:")
        print("1. Network 탭에서 'review.alphwidget.com' 도메인 요청 찾기")
        print("2. 실제 리뷰 데이터가 포함된 요청의 URL 확인")
        print("3. Request Headers와 Parameters 확인")
        return
    
    print(f"\n✅ 총 {len(reviews_data)}개의 리뷰를 수집했습니다!")
    
    # Analyze reviews
    print("\n🔍 리뷰 분석 중...")
    df, word_freq, bigram_freq, category_keywords = analyze_reviews(reviews_data)
    
    if df is None or df.empty:
        print("분석할 리뷰 데이터가 없습니다.")
        return
    
    # Save raw data
    df.to_csv('sonplan_alpha_widget_reviews.csv', index=False, encoding='utf-8-sig')
    print("\n💾 리뷰 데이터를 'sonplan_alpha_widget_reviews.csv'에 저장했습니다.")
    
    # Display sample reviews
    print("\n📝 리뷰 샘플 (처음 5개):")
    for i, row in df.head().iterrows():
        print(f"\n{i+1}. {row['review_text'][:100]}...")
        print(f"   평점: {'⭐' * int(row.get('rating', 5))}")
        print(f"   작성자: {row.get('reviewer', 'Unknown')}")
        if row.get('date'):
            print(f"   날짜: {row['date']}")
    
    # Print analysis results
    print("\n📊 키워드 분석 결과:")
    print("\n상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    print("\n🔗 함께 자주 나타나는 단어 조합 TOP 10:")
    for i, (bigram, freq) in enumerate(bigram_freq.most_common(10), 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    print("\n📑 카테고리별 주요 키워드:")
    for category, keywords in category_keywords.items():
        if keywords:
            top_5 = dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5])
            print(f"\n[{category}]")
            for word, freq in top_5.items():
                print(f"  - {word}: {freq}회")
    
    # Save analysis results
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(100))
    ])
    keywords_df.to_csv('sonplan_alpha_widget_keywords.csv', index=False, encoding='utf-8-sig')
    
    bigrams_df = pd.DataFrame([
        {'단어조합': bigram, '빈도': freq, '순위': i+1}
        for i, (bigram, freq) in enumerate(bigram_freq.most_common(50))
    ])
    bigrams_df.to_csv('sonplan_alpha_widget_bigrams.csv', index=False, encoding='utf-8-sig')
    
    # Save category analysis
    category_analysis = []
    for category, keywords in category_keywords.items():
        for word, freq in keywords.items():
            category_analysis.append({
                '카테고리': category,
                '키워드': word,
                '빈도': freq
            })
    
    category_df = pd.DataFrame(category_analysis)
    category_df = category_df.sort_values(['카테고리', '빈도'], ascending=[True, False])
    category_df.to_csv('sonplan_alpha_widget_categories.csv', index=False, encoding='utf-8-sig')
    
    print("\n💾 분석 결과 저장:")
    print("- 전체 키워드: sonplan_alpha_widget_keywords.csv")
    print("- 단어 조합: sonplan_alpha_widget_bigrams.csv")
    print("- 카테고리별: sonplan_alpha_widget_categories.csv")
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_analysis(df, word_freq, bigram_freq, category_keywords)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()