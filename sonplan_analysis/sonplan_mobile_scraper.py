import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time
import json

def scrape_mobile_reviews():
    """
    Scrape reviews from Sonplan mobile site
    """
    base_url = "https://m.sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    # Mobile user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session = requests.Session()
    reviews_data = []
    
    print("모바일 페이지에서 리뷰 수집 시작...")
    
    # First, get the main page
    response = session.get(base_url, headers=headers)
    print(f"메인 페이지 응답: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save debug HTML
        with open('mobile_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("디버그용 HTML 저장: mobile_page_debug.html")
        
        # Try different patterns for mobile review sections
        review_patterns = [
            # Common mobile review section IDs/classes
            soup.find('div', id='prdReview'),
            soup.find('div', class_='xans-product-review'),
            soup.find('div', class_='board-review'),
            soup.find('section', class_='review'),
            soup.find('div', class_='review-list'),
            soup.find('ul', class_='review-list'),
            soup.find('div', class_='board-list-review')
        ]
        
        review_section = None
        for pattern in review_patterns:
            if pattern:
                review_section = pattern
                print(f"리뷰 섹션 발견: {pattern.name} with class/id: {pattern.get('class', pattern.get('id'))}")
                break
        
        # If review section found, extract reviews
        if review_section:
            # Look for individual review items
            review_items = review_section.find_all(['li', 'div', 'article'], class_=re.compile('review|item|board'))
            
            if not review_items:
                # Try without class filter
                review_items = review_section.find_all(['li', 'div', 'tr'])
            
            print(f"발견된 리뷰 아이템 수: {len(review_items)}")
            
            for item in review_items:
                review_data = extract_review_from_element(item)
                if review_data and review_data['review_text']:
                    reviews_data.append(review_data)
        
        # Check for iframe with reviews
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'review' in src or 'board' in src:
                print(f"리뷰 iframe 발견: {src}")
                if not src.startswith('http'):
                    src = 'https://m.sonplan.com' + src
                
                # Get iframe content
                iframe_response = session.get(src, headers=headers)
                if iframe_response.status_code == 200:
                    iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')
                    iframe_reviews = extract_reviews_from_soup(iframe_soup)
                    reviews_data.extend(iframe_reviews)
        
        # Check for AJAX endpoints in scripts
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string or ''
            
            # Look for API endpoints
            api_matches = re.findall(r'["\']([^"\']*(?:review|board)[^"\']*)["\']', content)
            for match in api_matches:
                if match.startswith('/') and 'api' in match:
                    print(f"발견된 API 엔드포인트: {match}")
        
        # Try common mobile board URLs
        if not reviews_data:
            print("\n일반적인 모바일 리뷰 URL 시도 중...")
            
            mobile_review_urls = [
                f"https://m.sonplan.com/board/product/list.html?board_no=4&product_no=10",
                f"https://m.sonplan.com/board/review/list.html?product_no=10",
                f"https://m.sonplan.com/board/free/list.html?board_no=4"
            ]
            
            for review_url in mobile_review_urls:
                print(f"시도: {review_url}")
                try:
                    review_response = session.get(review_url, headers=headers)
                    if review_response.status_code == 200:
                        review_soup = BeautifulSoup(review_response.content, 'html.parser')
                        
                        # Extract reviews
                        page_reviews = extract_reviews_from_soup(review_soup)
                        if page_reviews:
                            reviews_data.extend(page_reviews)
                            print(f"추출된 리뷰 수: {len(page_reviews)}")
                            
                            # Try to get more pages
                            for page in range(2, 6):
                                page_url = f"{review_url}&page={page}"
                                try:
                                    page_response = session.get(page_url, headers=headers)
                                    if page_response.status_code == 200:
                                        page_soup = BeautifulSoup(page_response.content, 'html.parser')
                                        more_reviews = extract_reviews_from_soup(page_soup)
                                        if more_reviews:
                                            reviews_data.extend(more_reviews)
                                        else:
                                            break
                                    time.sleep(0.5)
                                except:
                                    break
                            break
                except Exception as e:
                    print(f"에러: {e}")
                    continue
    
    return reviews_data

def extract_review_from_element(element):
    """
    Extract review data from an HTML element
    """
    review_text = ""
    rating = 5
    reviewer = "고객"
    date = ""
    
    # Extract text content
    # Look for specific content containers
    content_containers = element.find_all(class_=re.compile('content|text|comment|description|subject'))
    if content_containers:
        review_text = ' '.join([c.get_text(strip=True) for c in content_containers])
    else:
        # Get all text but filter out metadata
        all_text = element.get_text(separator=' ', strip=True)
        # Remove common metadata patterns
        review_text = re.sub(r'(번호|작성자|날짜|평점|조회수)[\s:]\S+', '', all_text)
        review_text = review_text.strip()
    
    # Extract rating
    rating_elem = element.find(class_=re.compile('star|rating|score'))
    if rating_elem:
        # Count star images
        stars = rating_elem.find_all('img', src=re.compile('star'))
        if stars:
            rating = len([s for s in stars if 'full' in s.get('src', '') or 'on' in s.get('src', '')])
        else:
            # Try to extract from text
            rating_text = rating_elem.get_text()
            rating_match = re.search(r'(\d+)점|★+|(\d+)/5', rating_text)
            if rating_match:
                if rating_match.group(1):
                    rating = int(rating_match.group(1))
                elif '★' in rating_match.group(0):
                    rating = len(rating_match.group(0))
    
    # Extract reviewer
    reviewer_elem = element.find(class_=re.compile('writer|name|user|author'))
    if reviewer_elem:
        reviewer = reviewer_elem.get_text(strip=True)
        # Anonymize if needed
        if len(reviewer) > 2:
            reviewer = reviewer[:2] + '*' * (len(reviewer) - 2)
    
    # Extract date
    date_elem = element.find(class_=re.compile('date|time|created'))
    if date_elem:
        date = date_elem.get_text(strip=True)
    
    # Clean up review text
    if review_text:
        # Remove excessive whitespace
        review_text = ' '.join(review_text.split())
        # Remove navigation text
        nav_patterns = ['이전글', '다음글', '목록', '글쓰기', '답변', '수정', '삭제']
        for pattern in nav_patterns:
            review_text = review_text.replace(pattern, '')
        review_text = review_text.strip()
    
    return {
        'review_text': review_text,
        'rating': rating,
        'reviewer': reviewer,
        'date': date
    }

def extract_reviews_from_soup(soup):
    """
    Extract all reviews from a BeautifulSoup object
    """
    reviews = []
    
    # Look for review table
    tables = soup.find_all('table', class_=re.compile('board|list'))
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 2:
                review_data = {
                    'review_text': '',
                    'rating': 5,
                    'reviewer': '고객',
                    'date': ''
                }
                
                # Usually: number, subject, writer, date, views
                if len(cols) >= 2:
                    # Subject is usually the second column
                    subject_cell = cols[1]
                    link = subject_cell.find('a')
                    if link:
                        review_data['review_text'] = link.get_text(strip=True)
                    else:
                        review_data['review_text'] = subject_cell.get_text(strip=True)
                
                if len(cols) >= 3:
                    review_data['reviewer'] = cols[2].get_text(strip=True)
                
                if len(cols) >= 4:
                    review_data['date'] = cols[3].get_text(strip=True)
                
                # Extract rating if present
                rating_elem = row.find(class_=re.compile('star|rating'))
                if rating_elem:
                    stars = len(rating_elem.find_all(class_=re.compile('on|full')))
                    if stars > 0:
                        review_data['rating'] = stars
                
                if review_data['review_text'] and len(review_data['review_text']) > 5:
                    reviews.append(review_data)
    
    # Look for review lists (ul/ol)
    review_lists = soup.find_all(['ul', 'ol'], class_=re.compile('review|board'))
    for review_list in review_lists:
        items = review_list.find_all('li')
        for item in items:
            review_data = extract_review_from_element(item)
            if review_data['review_text']:
                reviews.append(review_data)
    
    # Look for review divs
    review_divs = soup.find_all('div', class_=re.compile('review-item|board-item|list-item'))
    for div in review_divs:
        review_data = extract_review_from_element(div)
        if review_data['review_text']:
            reviews.append(review_data)
    
    return reviews

def analyze_reviews(reviews_data):
    """
    Analyze collected reviews
    """
    if not reviews_data:
        return None, None, None
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews_data)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['review_text'])
    
    # Keyword analysis
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', '되어', '됩니다', '합니다', '있고', '없고', '같은', '이런', '그런', '저런', '모든', '각각', '번호', '작성자', '날짜', '조회수']
    
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

def visualize_results(df, word_freq, bigram_freq):
    """
    Create visualizations
    """
    if df is None or df.empty:
        return
    
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
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
    
    # 3. Review Length Distribution
    ax3 = axes[1, 0]
    review_lengths = df['review_text'].str.len()
    ax3.hist(review_lengths, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
    ax3.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax3.set_xlabel('글자 수')
    ax3.set_ylabel('리뷰 수')
    mean_length = review_lengths.mean()
    ax3.axvline(mean_length, color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {mean_length:.0f}자')
    ax3.legend()
    
    # 4. Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    total_reviews = len(df)
    unique_keywords = len(word_freq)
    avg_rating = df['rating'].mean()
    
    summary_text = f"""
    📊 썬플랜 타임슬립 아이크림 리뷰 분석 요약
    
    총 리뷰 수: {total_reviews}개
    평균 평점: {avg_rating:.2f}/5.0
    평균 리뷰 길이: {mean_length:.0f}자
    추출된 고유 키워드: {unique_keywords}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 키워드:
      {', '.join(list(top_words.keys())[:5])}
    
    • 고객들이 함께 언급하는 표현:
      {', '.join(list(top_bigrams.keys())[:3]) if top_bigrams else '없음'}
    """
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
             fontsize=12, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_mobile_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Word Cloud
    if word_freq:
        plt.figure(figsize=(10, 6))
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
            background_color='white',
            width=1000,
            height=600,
            max_words=50,
            colormap='viridis'
        ).generate_from_frequencies(dict(word_freq))
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('썬플랜 타임슬립 아이크림 리뷰 워드클라우드', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.savefig('sonplan_mobile_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 - 모바일 페이지 리뷰 분석")
    print("=" * 50)
    
    # Scrape reviews from mobile site
    reviews_data = scrape_mobile_reviews()
    
    if not reviews_data:
        print("\n리뷰를 찾을 수 없습니다.")
        print("모바일 페이지도 동적 로딩을 사용하거나 인증이 필요할 수 있습니다.")
        return
    
    print(f"\n✅ 총 {len(reviews_data)}개의 리뷰를 수집했습니다!")
    
    # Analyze reviews
    df, word_freq, bigram_freq = analyze_reviews(reviews_data)
    
    if df is None or df.empty:
        print("분석할 데이터가 없습니다.")
        return
    
    # Save data
    df.to_csv('sonplan_mobile_reviews.csv', index=False, encoding='utf-8-sig')
    print("\n💾 리뷰 데이터를 'sonplan_mobile_reviews.csv'에 저장했습니다.")
    
    # Display samples
    print("\n📝 리뷰 샘플:")
    for i, row in df.head(5).iterrows():
        print(f"\n{i+1}. {row['review_text'][:80]}...")
        print(f"   평점: {'⭐' * int(row['rating'])}")
        print(f"   작성자: {row['reviewer']}")
    
    # Print analysis
    print("\n📊 상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_results(df, word_freq, bigram_freq)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()