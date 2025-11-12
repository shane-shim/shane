from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime

def test_widget_scraping():
    """
    Test scraping using .widget_item_review_text class for 5 pages
    """
    chrome_options = Options()
    # Remove headless for debugging
    # chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    all_reviews = []
    
    try:
        print("브라우저 시작...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # Load product page
        url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
        print(f"페이지 로드: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Scroll down to review section
        print("리뷰 섹션으로 스크롤...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(3)
        
        # Click review tab
        print("리뷰 탭 클릭 시도...")
        try:
            # Try multiple selectors
            review_tab_selectors = [
                'a[href="#prdReview"]',
                '.bs_btn_prddetail_review',
                'a[onclick*="prdReview"]',
                '.tab-link.review',
                'a:contains("상품후기")'
            ]
            
            clicked = False
            for selector in review_tab_selectors:
                try:
                    if ':contains' in selector:
                        # Use JavaScript for text search
                        driver.execute_script("""
                            var links = document.querySelectorAll('a');
                            for (var i = 0; i < links.length; i++) {
                                if (links[i].textContent.includes('상품후기')) {
                                    links[i].click();
                                    break;
                                }
                            }
                        """)
                    else:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].click();", elem)
                    clicked = True
                    print(f"리뷰 탭 클릭 성공: {selector}")
                    break
                except:
                    continue
            
            if not clicked:
                print("리뷰 탭을 찾을 수 없음, 계속 진행...")
        except Exception as e:
            print(f"리뷰 탭 클릭 실패: {e}")
        
        time.sleep(5)
        
        # Find and switch to review iframe
        print("\n리뷰 iframe 찾기...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"총 {len(iframes)}개 iframe 발견")
        
        review_iframe_found = False
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src') or ''
                if 'alpha' in src.lower() or 'review' in src.lower() or 'widget' in src.lower():
                    print(f"리뷰 iframe 발견 (index {i}): {src[:100]}...")
                    driver.switch_to.frame(iframe)
                    review_iframe_found = True
                    time.sleep(3)
                    break
            except:
                continue
        
        if not review_iframe_found:
            print("리뷰 iframe을 찾을 수 없음, 메인 페이지에서 계속...")
        
        # Now scrape reviews for 5 pages
        for page_num in range(1, 6):
            print(f"\n=== 페이지 {page_num} ===")
            
            # Wait for reviews to load
            time.sleep(2)
            
            # Find all elements with class .widget_item_review_text
            print("'.widget_item_review_text' 클래스 요소 찾기...")
            review_elements = driver.find_elements(By.CSS_SELECTOR, '.widget_item_review_text')
            
            if not review_elements:
                print("  클래스를 찾을 수 없음, 다른 방법 시도...")
                # Try variations
                alternative_selectors = [
                    'div.widget_item_review_text',
                    'span.widget_item_review_text',
                    'p.widget_item_review_text',
                    '.widget_item .review_text',
                    '.widget_item_review_small .text',
                    '[class*="widget_item_review_text"]'
                ]
                
                for alt_selector in alternative_selectors:
                    review_elements = driver.find_elements(By.CSS_SELECTOR, alt_selector)
                    if review_elements:
                        print(f"  '{alt_selector}'로 {len(review_elements)}개 요소 발견")
                        break
            else:
                print(f"  {len(review_elements)}개 리뷰 요소 발견")
            
            # Extract text from each review element
            page_reviews = []
            for idx, element in enumerate(review_elements):
                try:
                    # Try different methods to get text
                    text = element.text.strip()
                    
                    if not text:
                        # Try JavaScript if .text doesn't work
                        text = driver.execute_script("return arguments[0].innerText;", element)
                    
                    if not text:
                        # Try textContent
                        text = driver.execute_script("return arguments[0].textContent;", element)
                    
                    if text and len(text) > 10:  # Filter out too short texts
                        review_data = {
                            'page': page_num,
                            'review_index': idx + 1,
                            'review_text': text.strip(),
                            'text_length': len(text)
                        }
                        page_reviews.append(review_data)
                        
                        # Print first 3 reviews of each page
                        if idx < 3:
                            print(f"  리뷰 {idx + 1}: {text[:80]}...")
                
                except Exception as e:
                    print(f"  리뷰 {idx + 1} 추출 실패: {e}")
            
            print(f"  페이지 {page_num}에서 {len(page_reviews)}개 리뷰 추출")
            all_reviews.extend(page_reviews)
            
            # Go to next page
            if page_num < 5:
                print(f"\n다음 페이지({page_num + 1})로 이동 시도...")
                next_clicked = False
                
                # Try to find and click next button
                next_selectors = [
                    'a.next:not(.disabled)',
                    '.pagination a.next',
                    '.widget_item_pagination a.next',
                    'a[title="다음"]',
                    '.paging .next',
                    f'a:contains("{page_num + 1}")'  # Try page number
                ]
                
                for selector in next_selectors:
                    try:
                        if ':contains' in selector:
                            # Click page number
                            driver.execute_script(f"""
                                var links = document.querySelectorAll('a');
                                for (var i = 0; i < links.length; i++) {{
                                    if (links[i].textContent.trim() === '{page_num + 1}') {{
                                        links[i].click();
                                        break;
                                    }}
                                }}
                            """)
                        else:
                            next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", next_btn)
                        
                        next_clicked = True
                        print(f"  다음 페이지 클릭 성공: {selector}")
                        time.sleep(3)  # Wait for page to load
                        break
                    except:
                        continue
                
                if not next_clicked:
                    # Try finding page number directly
                    try:
                        page_link = driver.find_element(By.LINK_TEXT, str(page_num + 1))
                        driver.execute_script("arguments[0].click();", page_link)
                        print(f"  페이지 번호 {page_num + 1} 클릭")
                        time.sleep(3)
                    except:
                        print("  다음 페이지로 이동 실패")
                        break
        
        # Take final screenshot
        driver.save_screenshot('widget_test_final.png')
        print("\n최종 스크린샷 저장: widget_test_final.png")
        
        driver.quit()
        
    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback
        traceback.print_exc()
        if 'driver' in locals():
            driver.quit()
    
    return all_reviews

def analyze_results(reviews):
    """
    Analyze the collected reviews
    """
    if not reviews:
        print("\n분석할 리뷰가 없습니다.")
        return
    
    df = pd.DataFrame(reviews)
    
    print("\n=== 수집 결과 분석 ===")
    print(f"총 리뷰 수: {len(df)}개")
    print(f"수집된 페이지: {df['page'].unique()}")
    print(f"페이지별 리뷰 수:")
    
    page_counts = df.groupby('page').size()
    for page, count in page_counts.items():
        print(f"  페이지 {page}: {count}개")
    
    print(f"\n리뷰 길이 통계:")
    print(f"  평균: {df['text_length'].mean():.0f}자")
    print(f"  최소: {df['text_length'].min()}자")
    print(f"  최대: {df['text_length'].max()}자")
    
    # Show sample reviews
    print("\n=== 리뷰 샘플 (각 페이지별 첫 번째) ===")
    for page in sorted(df['page'].unique()):
        first_review = df[df['page'] == page].iloc[0]
        print(f"\n페이지 {page}:")
        print(f"  {first_review['review_text'][:150]}...")
    
    return df

def main():
    print("썬플랜 리뷰 - widget_item_review_text 클래스 테스트")
    print("=" * 60)
    print("목표: 5페이지의 리뷰를 .widget_item_review_text 클래스로 추출\n")
    
    start_time = time.time()
    
    # Collect reviews
    reviews = test_widget_scraping()
    
    elapsed = time.time() - start_time
    print(f"\n크롤링 완료! 소요 시간: {elapsed:.1f}초")
    
    # Analyze and save results
    df = analyze_results(reviews)
    
    if df is not None and len(df) > 0:
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'sonplan_widget_test_{timestamp}.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n결과 저장: {filename}")
        
        # Estimate time for full scraping
        if len(df) > 0:
            avg_reviews_per_page = len(df) / df['page'].nunique()
            time_per_page = elapsed / 5
            total_pages_needed = 20000 / avg_reviews_per_page
            estimated_total_time = total_pages_needed * time_per_page
            
            print(f"\n=== 전체 크롤링 예상 시간 ===")
            print(f"페이지당 평균 리뷰: {avg_reviews_per_page:.0f}개")
            print(f"페이지당 소요 시간: {time_per_page:.1f}초")
            print(f"20,000개 리뷰를 위한 페이지 수: {total_pages_needed:.0f}페이지")
            print(f"예상 총 소요 시간: {estimated_total_time/60:.0f}분 ({estimated_total_time/3600:.1f}시간)")

if __name__ == "__main__":
    main()