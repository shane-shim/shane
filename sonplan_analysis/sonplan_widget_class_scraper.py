import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time
import json

def scrape_reviews_by_widget_class():
    """
    Scrape reviews using widget_item review small class
    """
    # Both desktop and mobile URLs
    urls = [
        "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/",
        "https://m.sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session = requests.Session()
    all_reviews = []
    
    for url in urls:
        print(f"\n크롤링 시도: {url}")
        
        try:
            response = session.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all elements with class "widget_item review small"
                widget_items = soup.find_all(class_='widget_item review small')
                print(f"Found {len(widget_items)} widget items")
                
                # Also try variations
                if not widget_items:
                    widget_items = soup.find_all('div', class_=re.compile('widget_item.*review'))
                    print(f"Found {len(widget_items)} widget items with regex")
                
                # Extract reviews from widget items
                for item in widget_items:
                    review_data = extract_review_from_widget(item)
                    if review_data and review_data['review_text']:
                        all_reviews.append(review_data)
                
                # Also look for iframe with widget class
                iframes = soup.find_all('iframe')
                for iframe in iframes:
                    src = iframe.get('src', '')
                    if 'widget' in src or 'review' in src:
                        print(f"Widget iframe found: {src}")
                        
                        if not src.startswith('http'):
                            base_domain = url.split('/product')[0]
                            src = base_domain + src if src.startswith('/') else base_domain + '/' + src
                        
                        # Get iframe content
                        try:
                            iframe_response = session.get(src, headers=headers)
                            if iframe_response.status_code == 200:
                                iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')
                                
                                # Look for widget items in iframe
                                iframe_widgets = iframe_soup.find_all(class_='widget_item review small')
                                print(f"Found {len(iframe_widgets)} widget items in iframe")
                                
                                for widget in iframe_widgets:
                                    review_data = extract_review_from_widget(widget)
                                    if review_data and review_data['review_text']:
                                        all_reviews.append(review_data)
                                
                                # Save iframe content for debugging
                                with open('widget_iframe_debug.html', 'w', encoding='utf-8') as f:
                                    f.write(iframe_soup.prettify())
                        except Exception as e:
                            print(f"Iframe error: {e}")
                
                # Look for dynamic content loading scripts
                scripts = soup.find_all('script')
                for script in scripts:
                    content = script.string or ''
                    if 'widget' in content and 'review' in content:
                        # Extract widget configuration
                        widget_config = re.search(r'widget[_-]?config\s*=\s*({[^}]+})', content)
                        if widget_config:
                            print(f"Widget config found: {widget_config.group(1)[:100]}...")
                        
                        # Look for API endpoints
                        api_matches = re.findall(r'["\']([^"\']*widget[^"\']*review[^"\']*)["\']', content)
                        for match in api_matches:
                            if match.startswith('http') or match.startswith('/'):
                                print(f"Widget API endpoint: {match}")
                
                # Save page for debugging
                with open(f'widget_page_debug_{len(all_reviews)}.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify()[:50000])  # Save first 50KB
                
                time.sleep(1)  # Be respectful
                
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # If no reviews found, try to get widget content directly
    if not all_reviews:
        print("\n직접 위젯 URL 접근 시도...")
        
        # Common widget URLs for Alpha Review
        widget_urls = [
            "https://widget.alphareview.co.kr/widget/review",
            "https://review.alphwidget.com/widget/index",
            "https://static.alphwidget.com/widget/review"
        ]
        
        widget_params = {
            'client_id': 'tgHZp6LCG5KuklqvIYgrtB',
            'shop_domain': 'sonplan.com',
            'product_id': '10',
            'product_code': '10'
        }
        
        for widget_url in widget_urls:
            try:
                print(f"Trying widget URL: {widget_url}")
                widget_response = session.get(widget_url, params=widget_params, headers=headers)
                
                if widget_response.status_code == 200:
                    widget_soup = BeautifulSoup(widget_response.content, 'html.parser')
                    
                    # Find widget items
                    widgets = widget_soup.find_all(class_=re.compile('widget_item|review.*small'))
                    print(f"Found {len(widgets)} widgets")
                    
                    for widget in widgets:
                        review_data = extract_review_from_widget(widget)
                        if review_data and review_data['review_text']:
                            all_reviews.append(review_data)
                    
                    if all_reviews:
                        break
                        
            except Exception as e:
                print(f"Widget URL error: {e}")
                continue
    
    return all_reviews

def extract_review_from_widget(widget_element):
    """
    Extract review data from widget_item element
    """
    review_data = {
        'review_text': '',
        'rating': 5,
        'reviewer': '고객',
        'date': '',
        'product': '썬플랜 타임슬립 아이크림'
    }
    
    # Extract review text
    # Look for review content in various possible containers
    content_selectors = [
        widget_element.find(class_='review-content'),
        widget_element.find(class_='content'),
        widget_element.find(class_='text'),
        widget_element.find(class_='comment'),
        widget_element.find(class_='description'),
        widget_element.find('p'),
        widget_element.find('div', class_=re.compile('content|text'))
    ]
    
    for selector in content_selectors:
        if selector:
            review_data['review_text'] = selector.get_text(strip=True)
            break
    
    # If no specific content container, get all text
    if not review_data['review_text']:
        review_data['review_text'] = widget_element.get_text(separator=' ', strip=True)
    
    # Extract rating
    rating_element = widget_element.find(class_=re.compile('star|rating|score'))
    if rating_element:
        # Count filled stars
        filled_stars = len(rating_element.find_all(class_=re.compile('fill|full|on|active')))
        if filled_stars > 0:
            review_data['rating'] = filled_stars
        else:
            # Try to extract from style width (e.g., width: 80% = 4 stars)
            style = rating_element.get('style', '')
            width_match = re.search(r'width:\s*(\d+)%', style)
            if width_match:
                review_data['rating'] = int(int(width_match.group(1)) / 20)
            else:
                # Try to find rating in text
                rating_text = rating_element.get_text()
                if '★' in rating_text:
                    review_data['rating'] = rating_text.count('★')
                elif '점' in rating_text:
                    rating_match = re.search(r'(\d+)점', rating_text)
                    if rating_match:
                        review_data['rating'] = int(rating_match.group(1))
    
    # Extract reviewer name
    reviewer_selectors = [
        widget_element.find(class_='reviewer'),
        widget_element.find(class_='writer'),
        widget_element.find(class_='name'),
        widget_element.find(class_='user'),
        widget_element.find(class_='author')
    ]
    
    for selector in reviewer_selectors:
        if selector:
            review_data['reviewer'] = selector.get_text(strip=True)
            break
    
    # Extract date
    date_selectors = [
        widget_element.find(class_='date'),
        widget_element.find(class_='time'),
        widget_element.find(class_='created'),
        widget_element.find('time')
    ]
    
    for selector in date_selectors:
        if selector:
            review_data['date'] = selector.get_text(strip=True)
            break
    
    # Clean review text
    if review_data['review_text']:
        # Remove metadata that might be included
        metadata_patterns = ['작성자', '날짜', '평점', '별점', '구매확정']
        for pattern in metadata_patterns:
            review_data['review_text'] = re.sub(f'{pattern}[:\s]*\S+\s*', '', review_data['review_text'])
        
        # Clean up
        review_data['review_text'] = ' '.join(review_data['review_text'].split())
    
    return review_data

def analyze_reviews(reviews_data):
    """
    Analyze review data
    """
    if not reviews_data:
        return None, None, None, None
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews_data)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['review_text'])
    
    # Remove too short reviews
    df = df[df['review_text'].str.len() > 10]
    
    print(f"\n유효한 리뷰 수: {len(df)}")
    
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
    
    # Sentiment keywords
    positive_keywords = {}
    negative_keywords = {}
    
    # Simple sentiment analysis based on common patterns
    positive_patterns = ['좋', '좋아', '좋은', '최고', '추천', '만족', '부드러', '촉촉', '효과', '개선', '탄력', '쫀쫀']
    negative_patterns = ['별로', '아쉬', '비싸', '끈적', '건조', '자극', '트러블', '실망']
    
    for word, freq in word_freq.items():
        for pos_pattern in positive_patterns:
            if pos_pattern in word:
                positive_keywords[word] = freq
                break
        
        for neg_pattern in negative_patterns:
            if neg_pattern in word:
                negative_keywords[word] = freq
                break
    
    return df, word_freq, bigram_freq, {'positive': positive_keywords, 'negative': negative_keywords}

def visualize_analysis(df, word_freq, bigram_freq, sentiment_keywords):
    """
    Create comprehensive visualizations
    """
    if df is None or df.empty:
        return
    
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1. Top Keywords
    ax1 = plt.subplot(2, 3, 1)
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
    ax2 = plt.subplot(2, 3, 2)
    top_bigrams = dict(bigram_freq.most_common(10))
    if top_bigrams:
        y_pos = range(len(top_bigrams))
        ax2.barh(y_pos, list(top_bigrams.values()), color='lightcoral')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(list(top_bigrams.keys()))
        ax2.set_title('함께 나타나는 단어 조합 TOP 10', fontsize=14, fontweight='bold')
        ax2.set_xlabel('빈도수')
    
    # 3. Positive Keywords
    ax3 = plt.subplot(2, 3, 3)
    if sentiment_keywords['positive']:
        pos_words = dict(sorted(sentiment_keywords['positive'].items(), 
                               key=lambda x: x[1], reverse=True)[:10])
        bars = ax3.bar(range(len(pos_words)), list(pos_words.values()), color='lightgreen')
        ax3.set_xticks(range(len(pos_words)))
        ax3.set_xticklabels(list(pos_words.keys()), rotation=45, ha='right')
        ax3.set_title('긍정적 키워드', fontsize=14, fontweight='bold')
        ax3.set_ylabel('빈도수')
    
    # 4. Rating Distribution
    ax4 = plt.subplot(2, 3, 4)
    if 'rating' in df.columns:
        rating_counts = df['rating'].value_counts().sort_index()
        colors = ['#ff4444', '#ff7744', '#ffaa44', '#44ff44', '#00ff00']
        bars = ax4.bar(rating_counts.index, rating_counts.values, 
                       color=[colors[min(int(r)-1, 4)] for r in rating_counts.index])
        ax4.set_title('평점 분포', fontsize=14, fontweight='bold')
        ax4.set_xlabel('평점')
        ax4.set_ylabel('리뷰 수')
        ax4.set_xticks(rating_counts.index)
        
        total = sum(rating_counts.values)
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}\n({height/total*100:.1f}%)', 
                    ha='center', va='bottom', fontsize=9)
    
    # 5. Review Length Distribution
    ax5 = plt.subplot(2, 3, 5)
    review_lengths = df['review_text'].str.len()
    ax5.hist(review_lengths, bins=30, color='lightblue', edgecolor='black', alpha=0.7)
    ax5.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax5.set_xlabel('글자 수')
    ax5.set_ylabel('리뷰 수')
    mean_length = review_lengths.mean()
    ax5.axvline(mean_length, color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {mean_length:.0f}자')
    ax5.legend()
    
    # 6. Summary
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    total_reviews = len(df)
    unique_keywords = len(word_freq)
    avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
    
    summary_text = f"""
    📊 썬플랜 타임슬립 아이크림 리뷰 분석 요약
    
    총 리뷰 수: {total_reviews}개
    평균 평점: {avg_rating:.2f}/5.0
    평균 리뷰 길이: {mean_length:.0f}자
    추출된 고유 키워드: {unique_keywords}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 키워드:
      {', '.join(list(top_words.keys())[:5])}
    
    • 긍정적 표현:
      {', '.join(list(sentiment_keywords['positive'].keys())[:3]) if sentiment_keywords['positive'] else '없음'}
    
    • 부정적 표현:
      {', '.join(list(sentiment_keywords['negative'].keys())[:3]) if sentiment_keywords['negative'] else '없음'}
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, 
             fontsize=11, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_widget_analysis.png', dpi=300, bbox_inches='tight')
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
        plt.savefig('sonplan_widget_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 - Widget Class 기반 리뷰 분석")
    print("=" * 50)
    
    # Scrape reviews using widget class
    print("\n'widget_item review small' 클래스로 리뷰 수집 중...")
    reviews_data = scrape_reviews_by_widget_class()
    
    if not reviews_data:
        print("\n리뷰를 찾을 수 없습니다.")
        print("페이지가 JavaScript로 동적 렌더링되거나 다른 클래스명을 사용할 수 있습니다.")
        print("\n확인 사항:")
        print("1. 브라우저 개발자 도구에서 실제 클래스명 확인")
        print("2. 리뷰가 iframe 내부에 있는지 확인")
        print("3. JavaScript 렌더링 후 생성되는 요소인지 확인")
        return
    
    print(f"\n✅ 총 {len(reviews_data)}개의 리뷰를 수집했습니다!")
    
    # Analyze reviews
    print("\n🔍 리뷰 분석 중...")
    df, word_freq, bigram_freq, sentiment_keywords = analyze_reviews(reviews_data)
    
    if df is None or df.empty:
        print("분석할 데이터가 없습니다.")
        return
    
    # Save data
    df.to_csv('sonplan_widget_reviews.csv', index=False, encoding='utf-8-sig')
    print("\n💾 리뷰 데이터를 'sonplan_widget_reviews.csv'에 저장했습니다.")
    
    # Display samples
    print("\n📝 리뷰 샘플 (처음 5개):")
    for i, row in df.head(5).iterrows():
        print(f"\n{i+1}. {row['review_text'][:100]}...")
        print(f"   평점: {'⭐' * int(row['rating'])}")
        print(f"   작성자: {row['reviewer']}")
        if row['date']:
            print(f"   날짜: {row['date']}")
    
    # Print analysis
    print("\n📊 상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    print("\n🔗 함께 자주 나타나는 단어 조합:")
    for i, (bigram, freq) in enumerate(bigram_freq.most_common(10), 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    print("\n😊 긍정적 키워드:")
    for word, freq in sorted(sentiment_keywords['positive'].items(), 
                            key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {word}: {freq}회")
    
    if sentiment_keywords['negative']:
        print("\n😞 부정적 키워드:")
        for word, freq in sorted(sentiment_keywords['negative'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {word}: {freq}회")
    
    # Save detailed analysis
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(100))
    ])
    keywords_df.to_csv('sonplan_widget_keywords.csv', index=False, encoding='utf-8-sig')
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_analysis(df, word_freq, bigram_freq, sentiment_keywords)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()