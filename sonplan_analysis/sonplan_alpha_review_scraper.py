import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time

def get_alpha_review_data():
    """
    Get reviews from Alpha Review service
    """
    # Alpha Review API endpoints
    client_id = 'tgHZp6LCG5KuklqvIYgrtB'
    
    # Common Alpha Review API patterns
    api_endpoints = [
        f"https://api.alphareview.co.kr/v1/reviews?client_id={client_id}&product_id=10",
        f"https://alphwidget.com/api/reviews?client_id={client_id}&product_id=10",
        f"https://static.alphwidget.com/api/reviews/{client_id}/10",
        f"https://alphareview.co.kr/widget/reviews?client_id={client_id}&product_id=10"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Origin': 'https://sonplan.com',
        'Referer': 'https://sonplan.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    reviews_data = []
    
    # Try different API endpoints
    for endpoint in api_endpoints:
        print(f"Trying: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'reviews' in data:
                        reviews_data = data['reviews']
                        break
                    elif 'data' in data:
                        reviews_data = data['data']
                        break
                    elif isinstance(data, list):
                        reviews_data = data
                        break
                except:
                    pass
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # If API fails, try to get iframe content
    if not reviews_data:
        print("\nTrying to get iframe content...")
        iframe_url = f"https://alphwidget.com/widget/review?client_id={client_id}&product_id=10"
        
        try:
            response = requests.get(iframe_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for review elements in Alpha Review widget
                review_elements = soup.find_all(['div', 'li'], class_=re.compile('review|item'))
                
                for element in review_elements:
                    review_text = ""
                    rating = 5
                    reviewer = "Customer"
                    date = ""
                    
                    # Extract review content
                    content_elem = element.find(class_=re.compile('content|text|comment'))
                    if content_elem:
                        review_text = content_elem.get_text(strip=True)
                    
                    # Extract rating
                    rating_elem = element.find(class_=re.compile('star|rating'))
                    if rating_elem:
                        # Count filled stars
                        filled_stars = len(rating_elem.find_all(class_=re.compile('fill|active')))
                        if filled_stars > 0:
                            rating = filled_stars
                    
                    # Extract reviewer
                    reviewer_elem = element.find(class_=re.compile('name|writer|user'))
                    if reviewer_elem:
                        reviewer = reviewer_elem.get_text(strip=True)
                    
                    # Extract date
                    date_elem = element.find(class_=re.compile('date|time'))
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                    
                    if review_text:
                        reviews_data.append({
                            'review_text': review_text,
                            'rating': rating,
                            'reviewer': reviewer,
                            'date': date
                        })
        except Exception as e:
            print(f"Iframe error: {e}")
    
    return reviews_data

def scrape_alpha_review_directly():
    """
    Try to scrape Alpha Review widget directly from the product page
    """
    product_url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    # Get the main page
    response = requests.get(product_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for Alpha Review script configuration
    scripts = soup.find_all('script')
    product_code = None
    shop_domain = None
    
    for script in scripts:
        content = script.string or ''
        if 'alpha_au' in content or 'alphareview' in content:
            # Extract product code
            product_match = re.search(r'product[_-]?(?:code|id|no)["\']?\s*[:=]\s*["\']?(\d+)', content)
            if product_match:
                product_code = product_match.group(1)
            
            # Extract shop domain
            domain_match = re.search(r'shop[_-]?domain["\']?\s*[:=]\s*["\']([^"\']+)', content)
            if domain_match:
                shop_domain = domain_match.group(1)
    
    print(f"Found product code: {product_code}")
    print(f"Found shop domain: {shop_domain}")
    
    # Try Alpha Review API with extracted parameters
    if product_code:
        alpha_api_url = f"https://api.alphareview.co.kr/shop/reviews/list"
        
        params = {
            'shop_domain': shop_domain or 'sonplan.com',
            'product_code': product_code,
            'page': 1,
            'limit': 100,
            'sort': 'recent'
        }
        
        try:
            response = requests.get(alpha_api_url, params=params, headers={
                **headers,
                'Origin': 'https://sonplan.com',
                'Referer': product_url
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'reviews' in data:
                    return data['reviews']
                elif 'data' in data and 'list' in data['data']:
                    return data['data']['list']
        except Exception as e:
            print(f"Alpha API error: {e}")
    
    return []

def analyze_reviews(reviews_data):
    """
    Analyze review data
    """
    if not reviews_data:
        print("No reviews to analyze")
        return None, None, None
    
    # Convert to DataFrame
    if isinstance(reviews_data[0], dict):
        df = pd.DataFrame(reviews_data)
    else:
        # If reviews are in different format, try to extract
        df_data = []
        for review in reviews_data:
            if isinstance(review, str):
                df_data.append({'review_text': review, 'rating': 5, 'reviewer': 'Customer', 'date': ''})
            else:
                df_data.append({
                    'review_text': str(review.get('content', review.get('comment', review.get('text', '')))),
                    'rating': review.get('rating', review.get('score', 5)),
                    'reviewer': review.get('writer', review.get('name', 'Customer')),
                    'date': review.get('date', review.get('created_at', ''))
                })
        df = pd.DataFrame(df_data)
    
    # Clean empty reviews
    df = df[df['review_text'].str.len() > 0]
    
    # Keyword analysis
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', '되어', '됩니다', '합니다']
    
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
    
    return df, word_freq, bigram_freq

def visualize_analysis(df, word_freq, bigram_freq):
    """
    Create visualizations
    """
    if df is None or df.empty:
        print("No data to visualize")
        return
    
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Top Keywords
    ax1 = axes[0, 0]
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
    ax2 = axes[0, 1]
    top_bigrams = dict(bigram_freq.most_common(10))
    if top_bigrams:
        y_pos = range(len(top_bigrams))
        ax2.barh(y_pos, list(top_bigrams.values()), color='lightcoral')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(list(top_bigrams.keys()))
        ax2.set_title('함께 나타나는 단어 조합 TOP 10', fontsize=14, fontweight='bold')
        ax2.set_xlabel('빈도수')
    
    # 3. Rating Distribution
    ax3 = axes[0, 2]
    if 'rating' in df.columns:
        rating_counts = df['rating'].value_counts().sort_index()
        colors = ['#ff4444', '#ff7744', '#ffaa44', '#44ff44', '#00ff00']
        bars = ax3.bar(rating_counts.index, rating_counts.values, 
                       color=[colors[int(r)-1] for r in rating_counts.index])
        ax3.set_title('평점 분포', fontsize=14, fontweight='bold')
        ax3.set_xlabel('평점')
        ax3.set_ylabel('리뷰 수')
        ax3.set_xticks(rating_counts.index)
        
        # Add percentage labels
        total = sum(rating_counts.values)
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}\n({height/total*100:.1f}%)', 
                    ha='center', va='bottom', fontsize=9)
    
    # 4. Review Length Distribution
    ax4 = axes[1, 0]
    review_lengths = df['review_text'].str.len()
    ax4.hist(review_lengths, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
    ax4.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax4.set_xlabel('글자 수')
    ax4.set_ylabel('리뷰 수')
    ax4.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {review_lengths.mean():.0f}자')
    ax4.legend()
    
    # 5. Monthly Review Trend (if date available)
    ax5 = axes[1, 1]
    if 'date' in df.columns and df['date'].notna().any():
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df_with_date = df[df['date'].notna()]
            if not df_with_date.empty:
                monthly = df_with_date.groupby(df_with_date['date'].dt.to_period('M')).size()
                monthly.plot(ax=ax5, kind='line', marker='o', linewidth=2, markersize=8)
                ax5.set_title('월별 리뷰 추이', fontsize=14, fontweight='bold')
                ax5.set_xlabel('기간')
                ax5.set_ylabel('리뷰 수')
                ax5.grid(True, alpha=0.3)
        except:
            ax5.text(0.5, 0.5, '날짜 데이터 없음', transform=ax5.transAxes, 
                    ha='center', va='center', fontsize=12)
            ax5.axis('off')
    else:
        ax5.axis('off')
    
    # 6. Summary Stats
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
    total_reviews = len(df)
    unique_keywords = len(word_freq)
    
    summary_text = f"""
    📊 썬플랜 타임슬립 아이크림 리뷰 분석 요약
    
    총 리뷰 수: {total_reviews:,}개
    평균 평점: {avg_rating:.2f}/5.0
    평균 리뷰 길이: {review_lengths.mean():.0f}자
    추출된 고유 키워드: {unique_keywords:,}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 키워드:
      {', '.join(list(top_words.keys())[:5])}
    
    • 고객들이 함께 언급하는 표현:
      {', '.join(list(top_bigrams.keys())[:3])}
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, 
             fontsize=11, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_alpha_review_analysis.png', dpi=300, bbox_inches='tight')
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
        plt.savefig('sonplan_alpha_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 - 알파리뷰 데이터 분석")
    print("=" * 50)
    
    # Try to get reviews from Alpha Review
    print("\n1. 알파리뷰 API에서 리뷰 데이터 수집 시도...")
    reviews_data = get_alpha_review_data()
    
    if not reviews_data:
        print("\n2. 제품 페이지에서 직접 수집 시도...")
        reviews_data = scrape_alpha_review_directly()
    
    if not reviews_data:
        print("\n알파리뷰 데이터를 가져올 수 없습니다.")
        print("\n가능한 원인:")
        print("- API 키나 인증이 필요함")
        print("- CORS 정책으로 인한 접근 제한")
        print("- 동적 로딩으로 인한 데이터 접근 불가")
        
        print("\n해결 방법:")
        print("1. 브라우저 개발자 도구에서 Network 탭 확인")
        print("2. 'alpha' 또는 'review'가 포함된 요청 찾기")
        print("3. 실제 API 엔드포인트와 필요한 파라미터 확인")
        return
    
    print(f"\n✅ 총 {len(reviews_data)}개의 리뷰를 수집했습니다!")
    
    # Analyze reviews
    print("\n🔍 리뷰 분석 중...")
    df, word_freq, bigram_freq = analyze_reviews(reviews_data)
    
    if df is None or df.empty:
        print("분석할 리뷰 데이터가 없습니다.")
        return
    
    # Save raw data
    df.to_csv('sonplan_alpha_reviews.csv', index=False, encoding='utf-8-sig')
    print("\n💾 리뷰 데이터를 'sonplan_alpha_reviews.csv'에 저장했습니다.")
    
    # Display sample reviews
    print("\n📝 리뷰 샘플 (처음 5개):")
    for i, row in df.head().iterrows():
        print(f"\n{i+1}. {row['review_text'][:100]}...")
        print(f"   평점: {'⭐' * int(row.get('rating', 5))}")
        print(f"   작성자: {row.get('reviewer', 'Unknown')}")
    
    # Print analysis results
    print("\n📊 키워드 분석 결과:")
    print("\n상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    print("\n🔗 함께 자주 나타나는 단어 조합 TOP 10:")
    for i, (bigram, freq) in enumerate(bigram_freq.most_common(10), 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    # Save analysis results
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(100))
    ])
    keywords_df.to_csv('sonplan_alpha_keywords.csv', index=False, encoding='utf-8-sig')
    
    bigrams_df = pd.DataFrame([
        {'단어조합': bigram, '빈도': freq, '순위': i+1}
        for i, (bigram, freq) in enumerate(bigram_freq.most_common(50))
    ])
    bigrams_df.to_csv('sonplan_alpha_bigrams.csv', index=False, encoding='utf-8-sig')
    
    print("\n💾 분석 결과 저장:")
    print("- 키워드 분석: sonplan_alpha_keywords.csv")
    print("- 단어 조합 분석: sonplan_alpha_bigrams.csv")
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_analysis(df, word_freq, bigram_freq)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()