import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json

def scrape_with_selenium():
    """
    Use Selenium to scrape dynamically loaded reviews
    """
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    reviews_data = []
    
    try:
        print("Selenium으로 페이지 로드 중...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the page
        url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
        driver.get(url)
        
        # Wait for the page to load
        print("페이지 로딩 대기 중...")
        time.sleep(5)
        
        # Scroll to review section to trigger loading
        print("리뷰 섹션으로 스크롤...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        # Try to find review tab and click it
        try:
            review_tab = driver.find_element(By.CSS_SELECTOR, 'a[href*="#prdReview"], a[href*="#review"], .tab-review, .review-tab')
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
            print("리뷰 탭 클릭 완료")
        except:
            print("리뷰 탭을 찾을 수 없음, 계속 진행...")
        
        # Find all review text elements
        print("\n'.widget_item_review_text' 클래스 요소 찾는 중...")
        review_texts = driver.find_elements(By.CLASS_NAME, 'widget_item_review_text')
        
        if not review_texts:
            # Try other possible selectors
            print("다른 셀렉터 시도 중...")
            selectors = [
                '.widget_item.review .text',
                '.widget_item_review_text',
                '.review-text',
                '.review-content',
                '[class*="review"][class*="text"]',
                '.widget_item_review_small .text'
            ]
            
            for selector in selectors:
                review_texts = driver.find_elements(By.CSS_SELECTOR, selector)
                if review_texts:
                    print(f"Found {len(review_texts)} reviews with selector: {selector}")
                    break
        
        print(f"발견된 리뷰 텍스트: {len(review_texts)}개")
        
        # Extract review data
        for i, review_element in enumerate(review_texts):
            try:
                review_text = review_element.text.strip()
                
                if review_text and len(review_text) > 10:
                    # Try to find associated rating
                    rating = 5  # Default
                    try:
                        # Look for rating in parent element
                        parent = review_element.find_element(By.XPATH, '..')
                        rating_elements = parent.find_elements(By.CSS_SELECTOR, '.star-on, .star-full, [class*="star"][class*="fill"]')
                        if rating_elements:
                            rating = len(rating_elements)
                    except:
                        pass
                    
                    # Try to find reviewer name
                    reviewer = "고객"
                    try:
                        parent = review_element.find_element(By.XPATH, '../..')
                        reviewer_elem = parent.find_element(By.CSS_SELECTOR, '.reviewer, .writer, .name, .user')
                        reviewer = reviewer_elem.text.strip()
                    except:
                        pass
                    
                    # Try to find date
                    date = ""
                    try:
                        parent = review_element.find_element(By.XPATH, '../..')
                        date_elem = parent.find_element(By.CSS_SELECTOR, '.date, .time, .created')
                        date = date_elem.text.strip()
                    except:
                        pass
                    
                    reviews_data.append({
                        'review_text': review_text,
                        'rating': rating,
                        'reviewer': reviewer,
                        'date': date
                    })
                    
                    print(f"리뷰 {i+1}: {review_text[:50]}...")
                    
            except Exception as e:
                print(f"Error extracting review {i}: {e}")
                continue
        
        # Check if reviews are in iframe
        if not reviews_data:
            print("\niframe 내부 확인 중...")
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            
            for iframe_idx, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    print(f"iframe {iframe_idx+1} 진입")
                    
                    # Look for review texts in iframe
                    iframe_reviews = driver.find_elements(By.CLASS_NAME, 'widget_item_review_text')
                    
                    if not iframe_reviews:
                        iframe_reviews = driver.find_elements(By.CSS_SELECTOR, '.review-text, .review-content, [class*="review"][class*="text"]')
                    
                    print(f"iframe 내부에서 {len(iframe_reviews)}개 리뷰 발견")
                    
                    for idx, review_elem in enumerate(iframe_reviews):
                        try:
                            review_text = review_elem.text.strip()
                            if not review_text:
                                # Try getting text with JavaScript
                                review_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", review_elem)
                            
                            if review_text and len(review_text) > 10:
                                reviews_data.append({
                                    'review_text': review_text.strip(),
                                    'rating': 5,
                                    'reviewer': '고객',
                                    'date': ''
                                })
                                print(f"  리뷰 {idx+1}: {review_text[:50]}...")
                        except Exception as e:
                            print(f"  리뷰 추출 오류 {idx}: {e}")
                    
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"iframe error: {e}")
                    driver.switch_to.default_content()
                    continue
        
        # Save page source for debugging
        with open('selenium_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\n디버그용 페이지 소스 저장: selenium_page_source.html")
        
        driver.quit()
        
    except Exception as e:
        print(f"Selenium error: {e}")
        return []
    
    return reviews_data

def scrape_with_requests():
    """
    Try to scrape with requests first (faster if it works)
    """
    url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
    }
    
    print("Requests로 페이지 가져오기 시도...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find review text elements
        review_elements = soup.find_all(class_='widget_item_review_text')
        print(f"Found {len(review_elements)} elements with class 'widget_item_review_text'")
        
        if not review_elements:
            # Try to find any element containing the class
            all_elements = soup.find_all(class_=re.compile('widget.*review.*text'))
            print(f"Found {len(all_elements)} elements with similar class names")
            
            # Also check in scripts for dynamic content
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'widget_item_review_text' in script.string:
                    print("Found 'widget_item_review_text' in script - content is dynamically loaded")
                    return None
        
        reviews_data = []
        for elem in review_elements:
            review_text = elem.get_text(strip=True)
            if review_text and len(review_text) > 10:
                reviews_data.append({
                    'review_text': review_text,
                    'rating': 5,
                    'reviewer': '고객',
                    'date': ''
                })
        
        return reviews_data
    
    return None

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
    
    print(f"\n중복 제거 후 리뷰 수: {len(df)}")
    
    # Keyword analysis
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요']
    
    for review in df['review_text']:
        # Extract Korean words
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    # Get bigrams
    bigrams = []
    for review in df['review_text']:
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
                    f'{int(height)}', ha='center', va='bottom')
    
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
    ax3.hist(review_lengths, bins=20, color='lightgreen', edgecolor='black')
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
    📊 리뷰 분석 요약
    
    총 리뷰 수: {len(df)}개
    평균 리뷰 길이: {review_lengths.mean():.0f}자
    추출된 고유 키워드: {len(word_freq)}개
    
    🔍 가장 많이 언급된 키워드:
    {', '.join(list(top_words.keys())[:5])}
    
    🔗 자주 함께 나타나는 표현:
    {', '.join(list(top_bigrams.keys())[:3]) if top_bigrams else '없음'}
    """
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
             fontsize=12, verticalalignment='top', fontfamily='AppleGothic')
    
    plt.tight_layout()
    plt.savefig('sonplan_final_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Word Cloud
    if word_freq:
        plt.figure(figsize=(10, 6))
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
            background_color='white',
            width=1000,
            height=600,
            max_words=50
        ).generate_from_frequencies(dict(word_freq))
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('리뷰 키워드 워드클라우드', fontsize=16, fontweight='bold', pad=20)
        plt.savefig('sonplan_final_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    print("썬플랜 타임슬립 아이크림 리뷰 분석")
    print("=" * 50)
    print("'.widget_item_review_text' 클래스로 리뷰 수집")
    
    # First try with requests
    reviews_data = scrape_with_requests()
    
    # If requests doesn't work, use Selenium
    if not reviews_data:
        print("\n정적 크롤링 실패, Selenium 사용...")
        reviews_data = scrape_with_selenium()
    
    if not reviews_data:
        print("\n리뷰를 찾을 수 없습니다.")
        print("가능한 원인:")
        print("1. 클래스명이 다를 수 있음")
        print("2. JavaScript 렌더링 타이밍 문제")
        print("3. 인증이 필요할 수 있음")
        return
    
    print(f"\n✅ 총 {len(reviews_data)}개의 리뷰를 수집했습니다!")
    
    # Analyze
    df, word_freq, bigram_freq = analyze_reviews(reviews_data)
    
    if df is None:
        print("분석할 데이터가 없습니다.")
        return
    
    # Save data
    df.to_csv('sonplan_final_reviews.csv', index=False, encoding='utf-8-sig')
    print("\n💾 'sonplan_final_reviews.csv'에 저장 완료")
    
    # Display samples
    print("\n📝 리뷰 샘플:")
    for i, row in df.head(5).iterrows():
        print(f"\n{i+1}. {row['review_text'][:100]}...")
        print(f"   평점: {'⭐' * int(row['rating'])}")
    
    # Analysis results
    print("\n📊 상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    print("\n🔗 단어 조합 TOP 10:")
    for i, (bigram, freq) in enumerate(bigram_freq.most_common(10), 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    # Visualize
    print("\n📈 시각화 생성 중...")
    visualize_results(df, word_freq, bigram_freq)
    
    print("\n✨ 분석 완료!")

if __name__ == "__main__":
    main()