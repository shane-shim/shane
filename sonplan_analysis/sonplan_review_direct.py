import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time

def find_review_iframe_url():
    """
    Find the actual review iframe URL from the product page
    """
    url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find iframe sources
    iframes = soup.find_all('iframe')
    review_iframe_url = None
    
    for iframe in iframes:
        src = iframe.get('src', '')
        if 'board' in src or 'review' in src:
            print(f"Found potential review iframe: {src}")
            if not src.startswith('http'):
                src = 'https://sonplan.com' + src
            review_iframe_url = src
            break
    
    # Also check for board URLs in scripts
    scripts = soup.find_all('script')
    for script in scripts:
        content = script.string or ''
        if 'board' in content:
            # Look for board URLs
            board_matches = re.findall(r'/board[^"\']*', content)
            for match in board_matches:
                if 'list' in match:
                    print(f"Found board URL in script: {match}")
    
    return review_iframe_url

def scrape_reviews_from_board():
    """
    Try common Cafe24 board patterns
    """
    base_url = "https://sonplan.com"
    product_no = "10"
    
    # Common Cafe24 review board patterns
    board_urls = [
        f"{base_url}/board/product/list.html?board_no=4&product_no={product_no}",
        f"{base_url}/board/free/list.html?board_no=4&product_no={product_no}",
        f"{base_url}/board/review/list.html?product_no={product_no}",
        f"{base_url}/board/board.html?board_no=4&product_no={product_no}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://sonplan.com/'
    }
    
    reviews_data = []
    
    for board_url in board_urls:
        print(f"\nTrying: {board_url}")
        
        try:
            response = requests.get(board_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Debug: print page title
                title = soup.find('title')
                if title:
                    print(f"Page title: {title.text}")
                
                # Look for board table
                tables = soup.find_all('table')
                for table in tables:
                    # Check if this is a board table
                    ths = table.find_all('th')
                    if any('번호' in th.text for th in ths):
                        print("Found board table!")
                        
                        # Extract reviews from rows
                        rows = table.find_all('tr')[1:]  # Skip header
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 3:
                                # Extract review data
                                subject_cell = cols[1]
                                subject_link = subject_cell.find('a')
                                
                                if subject_link:
                                    review_text = subject_link.get_text(strip=True)
                                else:
                                    review_text = subject_cell.get_text(strip=True)
                                
                                if review_text and len(review_text) > 5:
                                    reviewer = cols[2].get_text(strip=True) if len(cols) > 2 else 'Customer'
                                    date = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                                    
                                    reviews_data.append({
                                        'review_text': review_text,
                                        'reviewer': reviewer,
                                        'date': date,
                                        'rating': 5
                                    })
                        
                        if reviews_data:
                            print(f"Successfully extracted {len(reviews_data)} reviews!")
                            
                            # Try to get more pages
                            for page in range(2, 6):  # Get pages 2-5
                                page_url = f"{board_url}&page={page}"
                                try:
                                    page_response = requests.get(page_url, headers=headers)
                                    page_soup = BeautifulSoup(page_response.content, 'html.parser')
                                    
                                    page_table = page_soup.find('table')
                                    if page_table:
                                        page_rows = page_table.find_all('tr')[1:]
                                        for row in page_rows:
                                            cols = row.find_all('td')
                                            if len(cols) >= 3:
                                                subject_cell = cols[1]
                                                review_text = subject_cell.get_text(strip=True)
                                                
                                                if review_text and len(review_text) > 5:
                                                    reviewer = cols[2].get_text(strip=True) if len(cols) > 2 else 'Customer'
                                                    date = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                                                    
                                                    reviews_data.append({
                                                        'review_text': review_text,
                                                        'reviewer': reviewer,
                                                        'date': date,
                                                        'rating': 5
                                                    })
                                    
                                    time.sleep(0.5)  # Be respectful
                                except:
                                    break
                            
                            return pd.DataFrame(reviews_data)
                
                # If no board table found, look for review divs
                review_divs = soup.find_all('div', class_=re.compile('review|board'))
                for div in review_divs:
                    text = div.get_text(strip=True)
                    if len(text) > 20 and len(text) < 500:
                        reviews_data.append({
                            'review_text': text,
                            'reviewer': 'Customer',
                            'date': '',
                            'rating': 5
                        })
                
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    return pd.DataFrame(reviews_data)

def analyze_keywords(df):
    """
    Simple keyword analysis
    """
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요']
    
    for review in df['review_text']:
        if pd.isna(review):
            continue
        
        # Extract Korean words
        words = re.findall(r'[가-힣]+', review)
        words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    # Get bigrams
    bigrams = []
    for review in df['review_text']:
        if pd.isna(review):
            continue
        words = re.findall(r'[가-힣]+', review)
        words = [word for word in words if 2 <= len(word) <= 6]
        for i in range(len(words)-1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    return word_freq, bigram_freq

def visualize_analysis(word_freq, bigram_freq, df):
    """
    Create visualizations
    """
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Top Keywords
    top_words = dict(word_freq.most_common(15))
    ax1 = axes[0, 0]
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
    top_bigrams = dict(bigram_freq.most_common(10))
    ax2 = axes[0, 1]
    if top_bigrams:
        y_pos = range(len(top_bigrams))
        ax2.barh(y_pos, list(top_bigrams.values()), color='lightcoral')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(list(top_bigrams.keys()))
        ax2.set_title('함께 나타나는 단어 조합 TOP 10', fontsize=14, fontweight='bold')
        ax2.set_xlabel('빈도수')
    
    # 3. Review stats
    ax3 = axes[1, 0]
    review_lengths = df['review_text'].str.len()
    ax3.hist(review_lengths, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
    ax3.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax3.set_xlabel('글자 수')
    ax3.set_ylabel('리뷰 수')
    ax3.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {review_lengths.mean():.0f}자')
    ax3.legend()
    
    # 4. Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    summary_text = f"""
    📊 분석 요약
    
    총 리뷰 수: {len(df)}개
    평균 리뷰 길이: {review_lengths.mean():.0f}자
    추출된 고유 키워드: {len(word_freq)}개
    
    🔍 주요 발견사항:
    • 가장 많이 언급된 3개 키워드:
      {', '.join(list(top_words.keys())[:3])}
    
    • 고객들이 자주 함께 언급하는 표현:
      {', '.join(list(top_bigrams.keys())[:3])}
    """
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
             fontsize=12, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_review_analysis.png', dpi=300, bbox_inches='tight')
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
        plt.savefig('sonplan_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 리뷰 분석")
    print("=" * 50)
    
    # First try to find iframe URL
    print("\n1. 리뷰 iframe URL 찾기...")
    iframe_url = find_review_iframe_url()
    
    # Try to scrape reviews
    print("\n2. 리뷰 데이터 수집 시도...")
    df_reviews = scrape_reviews_from_board()
    
    if df_reviews.empty:
        print("\n리뷰를 가져올 수 없습니다.")
        print("\n가능한 해결 방법:")
        print("1. 브라우저에서 개발자 도구(F12)를 열고 Network 탭 확인")
        print("2. 리뷰 탭을 클릭할 때 발생하는 요청 확인")
        print("3. 'board' 또는 'review'가 포함된 요청 찾기")
        print("4. 해당 URL과 필요한 파라미터 확인")
        return
    
    print(f"\n✅ 총 {len(df_reviews)}개의 리뷰를 수집했습니다!")
    
    # Save raw data
    df_reviews.to_csv('sonplan_reviews_raw.csv', index=False, encoding='utf-8-sig')
    print("원본 데이터를 'sonplan_reviews_raw.csv'에 저장했습니다.")
    
    # Display sample reviews
    print("\n📝 리뷰 샘플 (처음 5개):")
    for i, row in df_reviews.head().iterrows():
        print(f"\n{i+1}. {row['review_text'][:50]}...")
        print(f"   작성자: {row['reviewer']}, 날짜: {row['date']}")
    
    # Analyze keywords
    print("\n🔍 키워드 분석 중...")
    word_freq, bigram_freq = analyze_keywords(df_reviews)
    
    # Print top keywords
    print("\n📊 가장 많이 언급된 키워드 TOP 20:")
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
    keywords_df.to_csv('sonplan_keywords_analysis.csv', index=False, encoding='utf-8-sig')
    
    bigrams_df = pd.DataFrame([
        {'단어조합': bigram, '빈도': freq, '순위': i+1}
        for i, (bigram, freq) in enumerate(bigram_freq.most_common(50))
    ])
    bigrams_df.to_csv('sonplan_bigrams_analysis.csv', index=False, encoding='utf-8-sig')
    
    print("\n💾 분석 결과 저장:")
    print("- 키워드 분석: sonplan_keywords_analysis.csv")
    print("- 단어 조합 분석: sonplan_bigrams_analysis.csv")
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_analysis(word_freq, bigram_freq, df_reviews)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()