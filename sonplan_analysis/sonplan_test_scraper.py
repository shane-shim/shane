from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re
from datetime import datetime

def test_scrape_few_pages():
    """
    Test scraping with just a few pages to verify it works
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    all_reviews = []
    
    try:
        print("테스트: 처음 5페이지만 크롤링")
        print("=" * 50)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        
        # Load product page
        url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
        print(f"페이지 로드 중...")
        driver.get(url)
        time.sleep(3)
        
        # Click review tab
        print("리뷰 탭 클릭 시도...")
        try:
            # Try multiple ways to click review tab
            review_tab = driver.find_element(By.CSS_SELECTOR, 'a[href="#prdReview"], .bs_btn_prddetail_review')
            driver.execute_script("arguments[0].click();", review_tab)
            print("리뷰 탭 클릭 성공")
        except:
            print("리뷰 탭을 찾을 수 없음")
        
        time.sleep(3)
        
        # Find iframe
        print("\niframe 찾기...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute('src') or ''
            if 'alpha' in src.lower() or 'review' in src.lower():
                print(f"리뷰 iframe 발견: {src[:80]}...")
                driver.switch_to.frame(iframe)
                break
        
        # Scrape only 5 pages
        for page in range(1, 6):
            print(f"\n페이지 {page} 크롤링...")
            
            # Find reviews
            reviews = driver.find_elements(By.CSS_SELECTOR, '.widget_item_review_text, .review-text, .text')
            
            page_reviews = 0
            for review in reviews:
                text = review.text.strip()
                if text and len(text) > 10:
                    all_reviews.append({
                        'review_text': text,
                        'page': page
                    })
                    page_reviews += 1
            
            print(f"  {page_reviews}개 리뷰 추출 (누적: {len(all_reviews)}개)")
            
            if page_reviews == 0:
                print("  리뷰를 찾을 수 없음")
                break
            
            # Next page
            if page < 5:
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, 'a.next, .pagination a:contains("다음")')
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2)
                except:
                    # Try page number
                    try:
                        page_link = driver.find_element(By.LINK_TEXT, str(page + 1))
                        driver.execute_script("arguments[0].click();", page_link)
                        time.sleep(2)
                    except:
                        print("  다음 페이지로 이동 실패")
                        break
        
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        if 'driver' in locals():
            driver.quit()
    
    return all_reviews

def estimate_total_time(reviews_per_page=10, seconds_per_page=3):
    """
    Estimate time to scrape all reviews
    """
    total_reviews = 20000
    total_pages = total_reviews / reviews_per_page
    total_seconds = total_pages * seconds_per_page
    
    print(f"\n예상 소요 시간:")
    print(f"- 총 리뷰: {total_reviews:,}개")
    print(f"- 페이지당 리뷰: {reviews_per_page}개")
    print(f"- 총 페이지: {int(total_pages):,}페이지")
    print(f"- 페이지당 소요시간: {seconds_per_page}초")
    print(f"- 예상 총 소요시간: {total_seconds/60:.1f}분 ({total_seconds/3600:.1f}시간)")

def main():
    print("썬플랜 리뷰 크롤링 테스트")
    print("=" * 50)
    
    # First test with few pages
    start_time = time.time()
    reviews = test_scrape_few_pages()
    elapsed = time.time() - start_time
    
    print(f"\n테스트 결과:")
    print(f"- 수집된 리뷰: {len(reviews)}개")
    print(f"- 소요 시간: {elapsed:.1f}초")
    
    if reviews:
        df = pd.DataFrame(reviews)
        print(f"- 평균 리뷰 길이: {df['review_text'].str.len().mean():.0f}자")
        
        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f'sonplan_test_{timestamp}.csv', index=False, encoding='utf-8-sig')
        print(f"- 저장: sonplan_test_{timestamp}.csv")
        
        # Estimate time for full scraping
        if len(reviews) > 0:
            pages_scraped = df['page'].max()
            reviews_per_page = len(reviews) / pages_scraped
            seconds_per_page = elapsed / pages_scraped
            
            estimate_total_time(reviews_per_page, seconds_per_page)
    
    print("\n제안:")
    print("1. API 엔드포인트를 찾아 직접 호출하는 것이 가장 빠름")
    print("2. 병렬 처리로 여러 페이지를 동시에 크롤링")
    print("3. 필요한 정보만 추출하여 처리 시간 단축")

if __name__ == "__main__":
    main()