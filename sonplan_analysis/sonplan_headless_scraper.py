from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re
from collections import Counter
from datetime import datetime

def scrape_sonplan_reviews():
    """
    Scrape reviews from Sonplan using Selenium in headless mode
    """
    # Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # New headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--ignore-certificate-errors')
    
    all_reviews = []
    
    try:
        print("Chrome 드라이버 시작 (Headless 모드)...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        # Load product page
        url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
        print(f"페이지 로드 중: {url}")
        driver.get(url)
        
        # Wait for page to load completely
        time.sleep(5)
        
        # Take screenshot for debugging
        driver.save_screenshot('page_loaded.png')
        print("스크린샷 저장: page_loaded.png")
        
        # Scroll to review section
        print("리뷰 섹션으로 스크롤...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        # Click on review tab
        print("리뷰 탭 찾기...")
        review_tab_clicked = False
        
        # Try different selectors for review tab
        tab_selectors = [
            'a[href="#prdReview"]',
            'a[href*="prdReview"]',
            '.tab_review',
            '.bs_btn_prddetail_review',
            'a.alpha_review_tab',
            '[onclick*="prdReview"]'
        ]
        
        for selector in tab_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        driver.execute_script("arguments[0].click();", elem)
                        review_tab_clicked = True
                        print(f"리뷰 탭 클릭 성공: {selector}")
                        break
                
                if review_tab_clicked:
                    break
            except:
                continue
        
        # If no tab clicked, try XPath
        if not review_tab_clicked:
            try:
                elements = driver.find_elements(By.XPATH, '//a[contains(text(), "상품후기")]')
                for elem in elements:
                    driver.execute_script("arguments[0].click();", elem)
                    review_tab_clicked = True
                    print("리뷰 탭 클릭 성공 (XPath)")
                    break
            except:
                pass
        
        time.sleep(5)
        driver.save_screenshot('after_review_tab_click.png')
        
        # Find review iframe
        print("\n리뷰 iframe 찾기...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"발견된 iframe 수: {len(iframes)}")
        
        review_iframe_index = None
        
        # Check each iframe
        for i, iframe in enumerate(iframes):
            try:
                # Get iframe src
                src = iframe.get_attribute('src') or ''
                print(f"iframe {i}: {src[:100] if src else 'No src'}...")
                
                if 'alpha' in src.lower() or 'review' in src.lower() or 'widget' in src.lower():
                    review_iframe_index = i
                    break
            except:
                continue
        
        if review_iframe_index is not None:
            print(f"리뷰 iframe 발견: index {review_iframe_index}")
            driver.switch_to.frame(iframes[review_iframe_index])
            time.sleep(3)
            driver.save_screenshot('inside_iframe.png')
        else:
            print("리뷰 iframe을 찾을 수 없음, 메인 페이지에서 계속 진행")
        
        # Now scrape reviews with pagination
        page_count = 0
        consecutive_empty = 0
        
        while True:
            page_count += 1
            print(f"\n페이지 {page_count} 크롤링...")
            
            # Find review elements - try multiple selectors
            review_selectors = [
                '.widget_item_review_text',
                '.review-text',
                '.review_content',
                '.review-content',
                '.text',
                'div[class*="review"][class*="text"]',
                '.widget_item .text',
                '.widget_item_review_small .text',
                'div.text',
                'p.text'
            ]
            
            reviews_found = []
            
            for selector in review_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    reviews_found = elements
                    break
            
            if not reviews_found:
                print("CSS 셀렉터로 찾을 수 없음, XPath 시도...")
                # Try XPath
                try:
                    elements = driver.find_elements(By.XPATH, '//*[contains(@class, "review") and contains(@class, "text")]')
                    if elements:
                        print(f"Found {len(elements)} elements with XPath")
                        reviews_found = elements
                except:
                    pass
            
            if not reviews_found:
                print("리뷰 요소를 찾을 수 없음")
                consecutive_empty += 1
                if consecutive_empty > 2:
                    break
                
                # Try switching frames
                try:
                    driver.switch_to.default_content()
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    for iframe in iframes:
                        driver.switch_to.frame(iframe)
                        elements = driver.find_elements(By.CSS_SELECTOR, '.text, .review-text')
                        if elements:
                            reviews_found = elements
                            print(f"Found reviews in different iframe")
                            break
                        driver.switch_to.default_content()
                except:
                    pass
                
                if not reviews_found:
                    continue
            
            # Extract reviews
            page_reviews = []
            for idx, elem in enumerate(reviews_found):
                try:
                    # Get text
                    text = elem.text.strip()
                    if not text:
                        text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", elem)
                    
                    if text and len(text) > 10 and not any(skip in text for skip in ['번호', '제목', '작성자', '글쓴이']):
                        # Try to get additional info
                        rating = 5
                        reviewer = "고객"
                        date = ""
                        
                        try:
                            # Look for parent container
                            parent = elem.find_element(By.XPATH, '..')
                            grandparent = parent.find_element(By.XPATH, '..')
                            
                            # Rating - try multiple approaches
                            try:
                                stars = grandparent.find_elements(By.CSS_SELECTOR, '.star-on, .on, [class*="star"][class*="fill"], .star.on')
                                if stars:
                                    rating = len(stars)
                                else:
                                    # Check for rating in style
                                    star_container = grandparent.find_element(By.CSS_SELECTOR, '[class*="star"]')
                                    style = star_container.get_attribute('style')
                                    if style and 'width' in style:
                                        width_match = re.search(r'width:\s*(\d+)%', style)
                                        if width_match:
                                            rating = int(int(width_match.group(1)) / 20)
                            except:
                                pass
                            
                            # Reviewer
                            try:
                                reviewer_elem = grandparent.find_element(By.CSS_SELECTOR, '.name, .writer, .user, .reviewer')
                                reviewer = reviewer_elem.text.strip()
                            except:
                                pass
                            
                            # Date
                            try:
                                date_elem = grandparent.find_element(By.CSS_SELECTOR, '.date, .time, .created')
                                date = date_elem.text.strip()
                            except:
                                pass
                            
                        except:
                            pass
                        
                        page_reviews.append({
                            'review_text': text.strip(),
                            'rating': rating,
                            'reviewer': reviewer,
                            'date': date,
                            'page': page_count
                        })
                        
                        if idx < 3:  # Print first 3 reviews
                            print(f"  리뷰 {idx+1}: {text[:50]}...")
                        
                except Exception as e:
                    continue
            
            if page_reviews:
                all_reviews.extend(page_reviews)
                print(f"추출된 리뷰: {len(page_reviews)}개 (누적: {len(all_reviews)}개)")
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                if consecutive_empty > 2:
                    print("더 이상 리뷰가 없음")
                    break
            
            # Find next page button
            print("다음 페이지 버튼 찾기...")
            next_clicked = False
            
            # Try multiple pagination selectors
            next_selectors = [
                'a.next:not(.disabled)',
                'button.next:not(.disabled)',
                '.pagination a.next',
                'a[title="다음"]',
                '.paging a.next',
                '.widget_item_pagination a.next',
                'a[onclick*="page"]:not(.on)',
                '.pagination li:last-child a',
                'a[href*="page="]:last-child'
            ]
            
            for selector in next_selectors:
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        # Check if it's not the current page
                        classes = next_btn.get_attribute('class') or ''
                        if 'on' not in classes and 'active' not in classes and 'current' not in classes:
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", next_btn)
                            next_clicked = True
                            print(f"다음 페이지로 이동 (selector: {selector})")
                            time.sleep(3)
                            break
                except:
                    continue
            
            if not next_clicked:
                # Try page numbers
                try:
                    page_links = driver.find_elements(By.CSS_SELECTOR, '.pagination a, .paging a, .widget_item_pagination a')
                    for link in page_links:
                        link_text = link.text.strip()
                        if link_text.isdigit() and int(link_text) == page_count + 1:
                            driver.execute_script("arguments[0].click();", link)
                            next_clicked = True
                            print(f"페이지 {page_count + 1}로 이동")
                            time.sleep(3)
                            break
                except:
                    pass
            
            if not next_clicked:
                # Try XPath for next button
                try:
                    next_xpath = driver.find_element(By.XPATH, '//a[contains(text(), "다음") or contains(text(), ">")]')
                    driver.execute_script("arguments[0].click();", next_xpath)
                    next_clicked = True
                    print("다음 페이지로 이동 (XPath)")
                    time.sleep(3)
                except:
                    pass
            
            if not next_clicked:
                print("다음 페이지를 찾을 수 없음")
                break
            
            # Stop at 20000 or after 2000 pages
            if len(all_reviews) >= 20000 or page_count >= 2000:
                print(f"목표 도달 또는 최대 페이지 도달")
                break
        
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        if 'driver' in locals():
            driver.quit()
    
    return all_reviews

def analyze_reviews(reviews):
    """
    Analyze collected reviews
    """
    if not reviews:
        print("분석할 리뷰가 없습니다.")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(reviews)
    
    # Remove duplicates
    original_count = len(df)
    df = df.drop_duplicates(subset=['review_text'])
    
    print(f"\n=== 분석 결과 ===")
    print(f"수집된 리뷰 수: {original_count:,}개")
    print(f"중복 제거 후: {len(df):,}개")
    print(f"수집된 페이지 수: {df['page'].max()}페이지")
    print(f"평균 평점: {df['rating'].mean():.2f}/5.0")
    
    # Rating distribution
    print("\n평점 분포:")
    rating_dist = df['rating'].value_counts().sort_index()
    for rating, count in rating_dist.items():
        print(f"  {rating}점: {count:,}개 ({count/len(df)*100:.1f}%)")
    
    # Review length stats
    review_lengths = df['review_text'].str.len()
    print(f"\n리뷰 길이:")
    print(f"  평균: {review_lengths.mean():.0f}자")
    print(f"  최소: {review_lengths.min()}자")
    print(f"  최대: {review_lengths.max()}자")
    
    # Keyword analysis
    print("\n키워드 분석 중...")
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는']
    
    # Process in batches for efficiency
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        for review in batch['review_text']:
            words = re.findall(r'[가-힣]+', str(review))
            words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
            all_words.extend(words)
        
        if (i + batch_size) % 5000 == 0:
            print(f"  처리 중: {min(i + batch_size, len(df)):,}/{len(df):,}")
    
    word_freq = Counter(all_words)
    
    print("\n상위 30개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(30), 1):
        if i % 3 == 1 and i > 1:
            print()
        print(f"{i:2d}. {word}: {freq:,}회", end="  ")
    print()
    
    return df, word_freq

def main():
    print("썬플랜 타임슬립 아이크림 리뷰 크롤링 (Headless 모드)")
    print("=" * 60)
    
    start_time = time.time()
    
    # Scrape reviews
    reviews = scrape_sonplan_reviews()
    
    elapsed = time.time() - start_time
    print(f"\n크롤링 완료!")
    print(f"소요 시간: {elapsed/60:.1f}분")
    print(f"수집된 리뷰: {len(reviews):,}개")
    
    if reviews:
        # Analyze
        df, word_freq = analyze_reviews(reviews)
        
        if df is not None:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save reviews
            df.to_csv(f'sonplan_reviews_{timestamp}.csv', index=False, encoding='utf-8-sig')
            print(f"\n리뷰 저장: sonplan_reviews_{timestamp}.csv")
            
            # Save keywords
            keywords_df = pd.DataFrame([
                {'키워드': word, '빈도': freq, '순위': i+1}
                for i, (word, freq) in enumerate(word_freq.most_common(500))
            ])
            keywords_df.to_csv(f'sonplan_keywords_{timestamp}.csv', index=False, encoding='utf-8-sig')
            print(f"키워드 저장: sonplan_keywords_{timestamp}.csv")
            
            # Create summary
            with open(f'sonplan_summary_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write(f"썬플랜 타임슬립 아이크림 리뷰 분석 요약\n")
                f.write(f"="*50 + "\n\n")
                f.write(f"수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"총 리뷰 수: {len(df):,}개\n")
                f.write(f"평균 평점: {df['rating'].mean():.2f}/5.0\n")
                f.write(f"평균 리뷰 길이: {df['review_text'].str.len().mean():.0f}자\n\n")
                
                f.write("평점 분포:\n")
                rating_dist = df['rating'].value_counts().sort_index()
                for rating, count in rating_dist.items():
                    f.write(f"  {rating}점: {count:,}개 ({count/len(df)*100:.1f}%)\n")
                
                f.write("\n상위 50개 키워드:\n")
                for i, (word, freq) in enumerate(word_freq.most_common(50), 1):
                    f.write(f"{i:2d}. {word}: {freq:,}회\n")
            
            print(f"요약 저장: sonplan_summary_{timestamp}.txt")
    else:
        print("\n리뷰를 수집하지 못했습니다.")

if __name__ == "__main__":
    main()