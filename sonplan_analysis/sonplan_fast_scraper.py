import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter
import time
import json
from datetime import datetime

def scrape_reviews_direct():
    """
    Try to find and scrape reviews directly from API
    """
    # First, let's check the main page to find API patterns
    url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://sonplan.com/'
    }
    
    session = requests.Session()
    response = session.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Alpha Widget configuration
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string or script.get_text() or ''
            if 'alphwidget' in content.lower() or 'alpha_au' in content:
                print("Found Alpha Widget configuration")
                # Extract client_id
                client_match = re.search(r'client_id["\']?\s*[:=]\s*["\']([^"\']+)', content)
                if client_match:
                    client_id = client_match.group(1)
                    print(f"Client ID: {client_id}")
    
    # Try common review board URLs for Cafe24
    all_reviews = []
    base_urls = [
        "https://sonplan.com/board/product/list.html",
        "https://sonplan.com/board/review/list.html",
        "https://m.sonplan.com/board/product/list.html"
    ]
    
    for base_url in base_urls:
        print(f"\nTrying: {base_url}")
        page = 1
        consecutive_empty = 0
        
        while True:
            params = {
                'board_no': '4',
                'product_no': '10',
                'page': page
            }
            
            try:
                response = session.get(base_url, params=params, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find review table
                    table = soup.find('table', class_=re.compile('board|list'))
                    if not table:
                        consecutive_empty += 1
                        if consecutive_empty > 2:
                            break
                        page += 1
                        continue
                    
                    # Extract reviews
                    rows = table.find_all('tr')[1:]  # Skip header
                    page_reviews = []
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            # Extract review text (usually in 2nd column)
                            review_text = cols[1].get_text(strip=True)
                            
                            # Extract reviewer (usually in 3rd column)
                            reviewer = cols[2].get_text(strip=True) if len(cols) > 2 else "고객"
                            
                            # Extract date (usually in 4th column)
                            date = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                            
                            # Extract rating if present
                            rating = 5
                            star_elem = row.find(class_=re.compile('star|rating'))
                            if star_elem:
                                filled_stars = len(star_elem.find_all(class_=re.compile('on|full|fill')))
                                if filled_stars > 0:
                                    rating = filled_stars
                            
                            if review_text and len(review_text) > 5:
                                page_reviews.append({
                                    'review_text': review_text,
                                    'rating': rating,
                                    'reviewer': reviewer,
                                    'date': date,
                                    'page': page
                                })
                    
                    if page_reviews:
                        all_reviews.extend(page_reviews)
                        print(f"Page {page}: {len(page_reviews)} reviews found (Total: {len(all_reviews)})")
                        consecutive_empty = 0
                    else:
                        consecutive_empty += 1
                        if consecutive_empty > 2:
                            print("No more reviews found")
                            break
                    
                    page += 1
                    time.sleep(0.5)  # Be respectful
                    
                    # Stop at target
                    if len(all_reviews) >= 20000:
                        break
                        
                else:
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        if all_reviews:
            break
    
    return all_reviews

def scrape_with_simple_selenium():
    """
    Simplified Selenium approach focusing on speed
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-images')  # Don't load images for speed
    
    all_reviews = []
    
    try:
        print("Starting Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Go directly to review iframe if we know the pattern
        # Try Alpha Widget review page
        widget_url = "https://widget.alphareview.co.kr/widget/reviews?client_id=tgHZp6LCG5KuklqvIYgrtB&product_id=10"
        
        print(f"Loading: {widget_url}")
        driver.get(widget_url)
        time.sleep(3)
        
        page_count = 0
        while True:
            page_count += 1
            print(f"\nPage {page_count}")
            
            # Find all review elements
            reviews = driver.find_elements(By.CSS_SELECTOR, '.review-item, .widget_item, .review_content, [class*="review"]')
            
            page_reviews = []
            for review in reviews:
                try:
                    text = review.text.strip()
                    if text and len(text) > 10 and not any(skip in text for skip in ['번호', '제목', '작성자']):
                        page_reviews.append({
                            'review_text': text,
                            'rating': 5,
                            'reviewer': '고객',
                            'date': '',
                            'page': page_count
                        })
                except:
                    continue
            
            if page_reviews:
                all_reviews.extend(page_reviews)
                print(f"Found {len(page_reviews)} reviews (Total: {len(all_reviews)})")
            
            # Try to click next page
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, 'a.next, button.next, .pagination .next, [class*="next"]:not(.disabled)')
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
            except:
                print("No more pages")
                break
            
            if len(all_reviews) >= 20000:
                break
        
        driver.quit()
        
    except Exception as e:
        print(f"Selenium error: {e}")
        if 'driver' in locals():
            driver.quit()
    
    return all_reviews

def quick_analysis(reviews):
    """
    Quick analysis of reviews
    """
    if not reviews:
        return None
    
    df = pd.DataFrame(reviews)
    df = df.drop_duplicates(subset=['review_text'])
    
    print(f"\n=== 빠른 분석 결과 ===")
    print(f"총 리뷰 수: {len(df):,}개")
    print(f"평균 평점: {df['rating'].mean():.2f}")
    
    # Quick keyword extraction
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도']
    
    for review in df['review_text'].head(1000):  # Analyze first 1000 for speed
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    print("\n상위 20개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. {word}: {freq}회")
    
    return df

def main():
    print("썬플랜 리뷰 빠른 크롤링")
    print("=" * 50)
    
    start_time = time.time()
    
    # Try direct scraping first
    print("\n1. Direct API/Board 크롤링 시도...")
    reviews = scrape_reviews_direct()
    
    if len(reviews) < 100:
        print("\n2. Selenium 크롤링 시도...")
        reviews = scrape_with_simple_selenium()
    
    elapsed = time.time() - start_time
    print(f"\n크롤링 완료: {elapsed:.1f}초")
    print(f"수집된 리뷰: {len(reviews):,}개")
    
    if reviews:
        # Quick analysis
        df = quick_analysis(reviews)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f'sonplan_reviews_{timestamp}.csv', index=False, encoding='utf-8-sig')
        print(f"\n저장 완료: sonplan_reviews_{timestamp}.csv")

if __name__ == "__main__":
    main()