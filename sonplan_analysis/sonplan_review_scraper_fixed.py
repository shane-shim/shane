import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from collections import Counter
import re
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json

def scrape_with_selenium(url, max_pages=5):
    """
    Use Selenium to scrape reviews from dynamically loaded content
    """
    reviews_data = []
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Click on review tab if exists
        try:
            review_tab = driver.find_element(By.CSS_SELECTOR, '.bs_btn_prddetail_review')
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
        except:
            print("리뷰 탭을 찾을 수 없음, 계속 진행...")
        
        # Try to find review section
        review_selectors = [
            '#tabProduct',
            '#prdReview',
            '.xans-product-review',
            '.board-list-review',
            '.review-list',
            'iframe[name*="review"]',
            'iframe[src*="board"]'
        ]
        
        reviews_found = False
        
        for selector in review_selectors:
            try:
                # Check for iframe
                if 'iframe' in selector:
                    iframe = driver.find_element(By.CSS_SELECTOR, selector)
                    driver.switch_to.frame(iframe)
                    time.sleep(1)
                
                # Find review elements
                review_elements = driver.find_elements(By.CSS_SELECTOR, 'tr, .review-item, .board-item')
                
                if review_elements:
                    print(f"Found {len(review_elements)} review elements with selector: {selector}")
                    reviews_found = True
                    
                    for element in review_elements:
                        try:
                            text = element.text.strip()
                            if len(text) > 10 and not any(skip in text for skip in ['번호', '제목', '작성자', 'No.']):
                                # Extract review details
                                lines = text.split('\n')
                                review_text = ''
                                reviewer = 'Customer'
                                date = ''
                                
                                for line in lines:
                                    if len(line) > 20:  # Likely the review content
                                        review_text = line
                                    elif '****' in line or '님' in line:  # Likely reviewer
                                        reviewer = line
                                    elif re.match(r'\d{4}-\d{2}-\d{2}', line):  # Date
                                        date = line
                                
                                if review_text:
                                    reviews_data.append({
                                        'review_text': review_text,
                                        'reviewer': reviewer,
                                        'date': date,
                                        'rating': 5  # Default
                                    })
                        except:
                            continue
                    
                    if reviews_found:
                        break
                        
                # Switch back from iframe
                if 'iframe' in selector:
                    driver.switch_to.default_content()
                    
            except Exception as e:
                print(f"Error with selector {selector}: {str(e)}")
                continue
        
        # If no reviews found, try to get review count and URL from the button
        if not reviews_data:
            try:
                review_count_elem = driver.find_element(By.CSS_SELECTOR, '.alpha_review_count')
                review_count = review_count_elem.text.replace(',', '')
                print(f"리뷰 총 개수: {review_count}")
                
                # Try to find review board URL
                scripts = driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    content = script.get_attribute('innerHTML')
                    if 'board' in content and 'review' in content:
                        print("Found review-related script")
                        # Extract board URL patterns
                        board_matches = re.findall(r'board[^"\']*review[^"\']*', content)
                        if board_matches:
                            print(f"Possible review URLs: {board_matches}")
            except:
                pass
        
        driver.quit()
        
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return pd.DataFrame()
    
    return pd.DataFrame(reviews_data)

def scrape_direct_api(product_id='10'):
    """
    Try direct API approach for Cafe24 platform
    """
    reviews_data = []
    
    # Common Cafe24 review API endpoints
    api_endpoints = [
        f"https://sonplan.com/exec/front/board/product/4?product_no={product_id}&board_no=4",
        f"https://sonplan.com/api/v2/products/{product_id}/reviews",
        f"https://sonplan.com/board/product/list.html?board_no=4&product_no={product_id}",
        f"https://sonplan.com/board/free/list.html?board_no=4"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
        'Referer': 'https://sonplan.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    session = requests.Session()
    
    for endpoint in api_endpoints:
        try:
            print(f"Trying endpoint: {endpoint}")
            response = session.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                # Try JSON parsing
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'reviews' in data:
                        for review in data['reviews']:
                            reviews_data.append({
                                'review_text': review.get('content', ''),
                                'reviewer': review.get('writer', 'Customer'),
                                'date': review.get('created_at', ''),
                                'rating': review.get('rating', 5)
                            })
                except:
                    # Try HTML parsing
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find review table or list
                    review_containers = soup.find_all(['tr', 'li', 'div'], class_=re.compile('review|board'))
                    
                    for container in review_containers:
                        text = container.get_text(strip=True)
                        if len(text) > 20 and not any(skip in text for skip in ['번호', '제목', '작성자']):
                            reviews_data.append({
                                'review_text': text[:200],  # Limit length
                                'reviewer': 'Customer',
                                'date': '',
                                'rating': 5
                            })
                
                if reviews_data:
                    print(f"Successfully extracted {len(reviews_data)} reviews")
                    break
                    
        except Exception as e:
            print(f"Error with endpoint {endpoint}: {str(e)}")
            continue
    
    return pd.DataFrame(reviews_data)

def simple_keyword_analysis(df):
    """
    Analyze keywords from reviews
    """
    all_words = []
    
    # Korean stop words
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도']
    
    for review in df['review_text']:
        if pd.isna(review):
            continue
        
        # Simple tokenization
        words = re.findall(r'[가-힣]+', review)
        words = [word for word in words if 2 <= len(word) <= 4 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    # Get bigrams
    bigrams = []
    for review in df['review_text']:
        if pd.isna(review):
            continue
        words = re.findall(r'[가-힣]+', review)
        words = [word for word in words if 2 <= len(word) <= 4]
        for i in range(len(words)-1):
            bigrams.append(f"{words[i]} {words[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    return {
        'words': dict(word_freq.most_common(50)),
        'bigrams': dict(bigram_freq.most_common(20)),
        'total_reviews': len(df)
    }

def visualize_results(analysis, df):
    """
    Create visualizations
    """
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Top Keywords
    ax1 = axes[0, 0]
    top_words = dict(list(analysis['words'].items())[:15])
    if top_words:
        bars = ax1.bar(range(len(top_words)), list(top_words.values()), color='skyblue')
        ax1.set_xticks(range(len(top_words)))
        ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
        ax1.set_title('가장 많이 언급된 키워드', fontsize=14, fontweight='bold')
        ax1.set_ylabel('빈도수')
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
    
    # 2. Bigrams
    ax2 = axes[0, 1]
    bigrams = dict(list(analysis['bigrams'].items())[:10])
    if bigrams:
        y_pos = range(len(bigrams))
        ax2.barh(y_pos, list(bigrams.values()), color='lightcoral')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(list(bigrams.keys()))
        ax2.set_title('함께 나타나는 단어 조합', fontsize=14, fontweight='bold')
        ax2.set_xlabel('빈도수')
    
    # 3. Review Length Distribution
    ax3 = axes[1, 0]
    if not df.empty and 'review_text' in df.columns:
        review_lengths = df['review_text'].str.len()
        if len(review_lengths) > 0:
            ax3.hist(review_lengths, bins=20, color='lightgreen', edgecolor='black')
            ax3.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
            ax3.set_xlabel('글자 수')
            ax3.set_ylabel('리뷰 수')
            ax3.axvline(review_lengths.mean(), color='red', linestyle='dashed', linewidth=1)
    
    # 4. Summary Stats
    ax4 = axes[1, 1]
    ax4.axis('off')
    summary_text = f"""
    분석 요약
    
    총 리뷰 수: {analysis['total_reviews']}
    추출된 고유 키워드: {len(analysis['words'])}
    단어 조합 수: {len(analysis['bigrams'])}
    
    상위 5개 키워드:
    """
    
    for i, (word, freq) in enumerate(list(analysis['words'].items())[:5], 1):
        summary_text += f"\n{i}. {word} ({freq}회)"
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
             fontsize=12, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_analysis_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Word Cloud
    if analysis['words']:
        plt.figure(figsize=(10, 6))
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
            background_color='white',
            width=1000,
            height=600,
            max_words=50
        ).generate_from_frequencies(analysis['words'])
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('리뷰 키워드 워드클라우드', fontsize=16, fontweight='bold', pad=20)
        plt.savefig('sonplan_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 리뷰 분석")
    print("=" * 50)
    
    url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    # Try Selenium first
    print("\n1. Selenium으로 리뷰 수집 시도...")
    df_reviews = scrape_with_selenium(url)
    
    # If Selenium fails, try direct API
    if df_reviews.empty:
        print("\n2. Direct API 접근 시도...")
        df_reviews = scrape_direct_api('10')
    
    if df_reviews.empty:
        print("\n리뷰를 가져올 수 없습니다. 가능한 원인:")
        print("- 리뷰가 로그인 후에만 보일 수 있음")
        print("- 리뷰가 별도의 보안 API를 통해 로드됨")
        print("- 웹사이트가 봇 접근을 차단함")
        print("\n브라우저에서 직접 리뷰를 확인하고 개발자 도구의 Network 탭에서")
        print("리뷰 로드 시 호출되는 정확한 API 엔드포인트를 찾아보세요.")
        return
    
    print(f"\n총 {len(df_reviews)}개의 리뷰를 수집했습니다.")
    
    # Save data
    df_reviews.to_csv('sonplan_reviews.csv', index=False, encoding='utf-8-sig')
    print("리뷰 데이터를 'sonplan_reviews.csv'에 저장했습니다.")
    
    # Analyze
    print("\n키워드 분석 중...")
    analysis = simple_keyword_analysis(df_reviews)
    
    # Print results
    print("\n=== 분석 결과 ===")
    print(f"\n상위 20개 키워드:")
    for i, (word, freq) in enumerate(list(analysis['words'].items())[:20], 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    print(f"\n함께 나타나는 단어 조합 TOP 10:")
    for i, (bigram, freq) in enumerate(list(analysis['bigrams'].items())[:10], 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    # Visualize
    print("\n시각화 생성 중...")
    visualize_results(analysis, df_reviews)
    
    print("\n분석 완료!")

if __name__ == "__main__":
    main()