from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re
from datetime import datetime

def scrape_iframe_directly():
    """
    Access the iframe URL directly
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    all_reviews = []
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Go directly to the iframe URL
        iframe_url = "https://review.alphwidget.com/api_widget/widget?code=0dae6c62&value=10&idx=0&mall_id=tgHZp6LCG5KuklqvIYgrtB"
        print(f"iframe URL 직접 접속...")
        driver.get(iframe_url)
        time.sleep(5)
        
        # Save screenshot
        driver.save_screenshot('iframe_direct.png')
        print("스크린샷 저장: iframe_direct.png")
        
        # Try to find reviews with various selectors
        selectors = [
            '.widget_item_review_text',
            '.review_text',
            '.text',
            '.review-content',
            '.review_content',
            '.widget_item .text',
            'div.text',
            'p.text',
            '.widget_item_review_small .text',
            '[class*="review"][class*="text"]'
        ]
        
        for selector in selectors:
            reviews = driver.find_elements(By.CSS_SELECTOR, selector)
            if reviews:
                print(f"\n'{selector}' 셀렉터로 {len(reviews)}개 요소 발견")
                
                # Print first few for debugging
                for i, review in enumerate(reviews[:3]):
                    text = review.text.strip()
                    if not text:
                        text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", review)
                    print(f"  리뷰 {i+1}: {text[:100] if text else 'Empty'}...")
                
                # Collect all reviews
                for review in reviews:
                    text = review.text.strip()
                    if not text:
                        text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", review)
                    
                    if text and len(text) > 10:
                        all_reviews.append({'review_text': text})
                
                if all_reviews:
                    break
        
        # If no reviews found, print page source sample
        if not all_reviews:
            print("\n리뷰를 찾을 수 없음. 페이지 소스 확인:")
            page_source = driver.page_source
            print(f"Page source length: {len(page_source)}")
            
            # Look for review-like content in source
            review_patterns = [
                r'<div[^>]*class="[^"]*text[^"]*"[^>]*>(.*?)</div>',
                r'<p[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</p>',
                r'class="widget_item_review_text"[^>]*>(.*?)<',
            ]
            
            for pattern in review_patterns:
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    print(f"\nPattern '{pattern}' found {len(matches)} matches")
                    for i, match in enumerate(matches[:3]):
                        print(f"  Match {i+1}: {match[:100]}...")
        
        # Try pagination
        print("\n페이지네이션 확인...")
        pagination = driver.find_elements(By.CSS_SELECTOR, '.pagination a, .paging a, .widget_item_pagination a')
        print(f"페이지네이션 링크: {len(pagination)}개")
        
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        if 'driver' in locals():
            driver.quit()
    
    return all_reviews

def main():
    print("썬플랜 리뷰 iframe 직접 접속 테스트")
    print("=" * 50)
    
    reviews = scrape_iframe_directly()
    
    print(f"\n결과:")
    print(f"수집된 리뷰: {len(reviews)}개")
    
    if reviews:
        # Show samples
        print("\n리뷰 샘플:")
        for i, review in enumerate(reviews[:5]):
            print(f"{i+1}. {review['review_text'][:100]}...")
        
        # Save
        df = pd.DataFrame(reviews)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f'sonplan_iframe_test_{timestamp}.csv', index=False, encoding='utf-8-sig')
        print(f"\n저장: sonplan_iframe_test_{timestamp}.csv")

if __name__ == "__main__":
    main()