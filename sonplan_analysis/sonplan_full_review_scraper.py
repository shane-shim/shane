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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime

def scrape_all_reviews_selenium():
    """
    Scrape all reviews using Selenium with pagination
    """
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    all_reviews = []
    page_count = 0
    
    try:
        print("Selenium으로 페이지 로드 중...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the page
        url = "https://sonplan.com/product/%EC%8D%AC%ED%94%8C%EB%9E%9C-%ED%83%80%EC%9E%84%EC%8A%AC%EB%A6%BD-%EC%95%84%EC%9D%B4-%ED%81%AC%EB%A6%BC-220g/10/category/23/display/1/"
        driver.get(url)
        
        # Wait for the page to load
        print("페이지 로딩 대기 중...")
        time.sleep(5)
        
        # Scroll to review section
        print("리뷰 섹션으로 스크롤...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        # Click review tab if exists
        try:
            review_tab = driver.find_element(By.CSS_SELECTOR, 'a[href*="#prdReview"], a[href*="#review"], .tab-review, .review-tab, .bs_btn_prddetail_review')
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(3)
            print("리뷰 탭 클릭 완료")
        except:
            print("리뷰 탭을 찾을 수 없음, 계속 진행...")
        
        # Find the iframe containing reviews
        print("\n리뷰가 포함된 iframe 찾는 중...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        review_iframe = None
        
        for idx, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                
                # Check if this iframe contains reviews
                review_elements = driver.find_elements(By.CSS_SELECTOR, '.widget_item_review_text, .review-text, .review-content, [class*="review"][class*="text"]')
                
                if review_elements:
                    print(f"iframe {idx+1}에서 리뷰 발견!")
                    review_iframe = idx
                    driver.switch_to.default_content()
                    break
                
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue
        
        if review_iframe is None:
            print("리뷰 iframe을 찾을 수 없습니다.")
            driver.quit()
            return []
        
        # Switch to review iframe
        driver.switch_to.frame(driver.find_elements(By.TAG_NAME, 'iframe')[review_iframe])
        time.sleep(2)
        
        # Start pagination
        while True:
            page_count += 1
            print(f"\n페이지 {page_count} 크롤링 중...")
            
            # Find all reviews on current page
            review_elements = driver.find_elements(By.CSS_SELECTOR, '.widget_item_review_text, .review-text, .review-content, .review_content, .text')
            
            if not review_elements:
                print("리뷰 요소를 찾을 수 없습니다.")
                break
            
            # Extract reviews from current page
            page_reviews = []
            for idx, review_elem in enumerate(review_elements):
                try:
                    # Get review text
                    review_text = review_elem.text.strip()
                    if not review_text:
                        review_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", review_elem)
                    
                    if review_text and len(review_text) > 10:
                        # Try to get parent element for additional info
                        try:
                            parent = review_elem.find_element(By.XPATH, '../..')
                            
                            # Extract rating
                            rating = 5
                            try:
                                star_elements = parent.find_elements(By.CSS_SELECTOR, '.star-on, .star-full, [class*="star"][class*="fill"], .on')
                                if star_elements:
                                    rating = len(star_elements)
                                else:
                                    # Check for rating in style
                                    star_container = parent.find_element(By.CSS_SELECTOR, '[class*="star"], [class*="rating"]')
                                    style = star_container.get_attribute('style')
                                    if style and 'width' in style:
                                        width_match = re.search(r'width:\s*(\d+)%', style)
                                        if width_match:
                                            rating = int(int(width_match.group(1)) / 20)
                            except:
                                pass
                            
                            # Extract reviewer
                            reviewer = "고객"
                            try:
                                reviewer_elem = parent.find_element(By.CSS_SELECTOR, '.reviewer, .writer, .name, .user, .nickname')
                                reviewer = reviewer_elem.text.strip()
                            except:
                                pass
                            
                            # Extract date
                            date = ""
                            try:
                                date_elem = parent.find_element(By.CSS_SELECTOR, '.date, .time, .created, .write_date')
                                date = date_elem.text.strip()
                            except:
                                pass
                            
                        except:
                            parent = None
                            rating = 5
                            reviewer = "고객"
                            date = ""
                        
                        review_data = {
                            'review_text': review_text.strip(),
                            'rating': rating,
                            'reviewer': reviewer,
                            'date': date,
                            'page': page_count
                        }
                        
                        page_reviews.append(review_data)
                        
                except Exception as e:
                    continue
            
            print(f"  현재 페이지에서 {len(page_reviews)}개 리뷰 추출")
            all_reviews.extend(page_reviews)
            print(f"  누적 리뷰 수: {len(all_reviews)}개")
            
            # Find and click next page button
            try:
                # Common pagination selectors
                next_selectors = [
                    'a.next',
                    'button.next',
                    '.pagination .next',
                    'a[class*="next"]',
                    'button[class*="next"]',
                    '.paging a.next',
                    'a[title="다음"]',
                    'a:contains("다음")',
                    '.widget_item_pagination a.next',
                    '.pagination li:last-child a',
                    'a[onclick*="page"]'
                ]
                
                next_button = None
                for selector in next_selectors:
                    try:
                        if ':contains' in selector:
                            # Use XPath for text content
                            next_button = driver.find_element(By.XPATH, '//a[contains(text(), "다음")]')
                        else:
                            next_button = driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if next_button and next_button.is_displayed() and next_button.is_enabled():
                            break
                        else:
                            next_button = None
                    except:
                        continue
                
                if not next_button:
                    # Try to find page numbers
                    page_links = driver.find_elements(By.CSS_SELECTOR, '.pagination a, .paging a, .widget_item_pagination a')
                    current_page_num = page_count
                    next_page_found = False
                    
                    for link in page_links:
                        try:
                            link_text = link.text.strip()
                            if link_text.isdigit() and int(link_text) == current_page_num + 1:
                                next_button = link
                                next_page_found = True
                                break
                        except:
                            continue
                    
                    if not next_page_found:
                        print("다음 페이지 버튼을 찾을 수 없습니다.")
                        break
                
                # Check if next button is disabled
                if next_button:
                    classes = next_button.get_attribute('class') or ''
                    if 'disabled' in classes or 'inactive' in classes:
                        print("마지막 페이지에 도달했습니다.")
                        break
                    
                    # Click next page
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Wait for page to load
                    
                else:
                    print("다음 페이지로 이동할 수 없습니다.")
                    break
                    
            except TimeoutException:
                print("페이지 로딩 시간 초과")
                break
            except Exception as e:
                print(f"페이지네이션 오류: {e}")
                break
            
            # Stop if we have enough reviews or no new reviews
            if len(all_reviews) >= 20000:
                print(f"\n목표 리뷰 수(20,000개)에 도달했습니다.")
                break
            
            # Safety check: stop if we're stuck on the same page
            if len(page_reviews) == 0:
                print("현재 페이지에서 리뷰를 찾을 수 없습니다.")
                break
        
        driver.quit()
        
    except Exception as e:
        print(f"Selenium error: {e}")
        if 'driver' in locals():
            driver.quit()
        return all_reviews
    
    return all_reviews

def analyze_large_dataset(reviews_data):
    """
    Analyze large review dataset
    """
    if not reviews_data:
        return None, None, None, None
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews_data)
    
    # Remove exact duplicates
    original_count = len(df)
    df = df.drop_duplicates(subset=['review_text'])
    print(f"\n중복 제거: {original_count}개 → {len(df)}개")
    
    # Basic statistics
    print(f"\n=== 기본 통계 ===")
    print(f"총 리뷰 수: {len(df):,}개")
    print(f"평균 평점: {df['rating'].mean():.2f}")
    print(f"평점 분포:")
    rating_dist = df['rating'].value_counts().sort_index()
    for rating, count in rating_dist.items():
        print(f"  {rating}점: {count:,}개 ({count/len(df)*100:.1f}%)")
    
    # Date analysis if available
    if df['date'].notna().any():
        try:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
            valid_dates = df[df['date_parsed'].notna()]
            if len(valid_dates) > 0:
                print(f"\n날짜 범위: {valid_dates['date_parsed'].min()} ~ {valid_dates['date_parsed'].max()}")
        except:
            pass
    
    # Keyword analysis
    print("\n키워드 분석 중...")
    all_words = []
    stop_words = ['있어요', '있습니다', '같아요', '것', '수', '저', '제', '더', '데', '때', '등', '및', '이', '그', '을', '를', '에', '의', '가', '은', '는', '도', '로', '으로', '만', '까지', '해요', '하고', '했어요', '입니다', '에요', '예요', '있는', '하는', '되는', '되어', '됩니다', '합니다', '있고', '없고', '같은', '이런', '그런', '저런', '모든', '각각', '그리고', '하지만', '그러나', '그래서', '따라서', '때문에', '위해', '통해', '대해', '관해', '또한', '역시', '아주', '매우', '너무', '정말', '진짜']
    
    for idx, review in enumerate(df['review_text']):
        if idx % 1000 == 0:
            print(f"  {idx:,}/{len(df):,} 리뷰 처리 중...")
        
        # Extract Korean words
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6 and word not in stop_words]
        all_words.extend(words)
    
    word_freq = Counter(all_words)
    
    # Get bigrams (limited for performance)
    print("\n단어 조합 분석 중...")
    bigrams = []
    sample_size = min(5000, len(df))  # Analyze sample for bigrams
    sample_df = df.sample(n=sample_size, random_state=42)
    
    for review in sample_df['review_text']:
        words = re.findall(r'[가-힣]+', str(review))
        words = [word for word in words if 2 <= len(word) <= 6]
        for i in range(len(words)-1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
    
    bigram_freq = Counter(bigrams)
    
    # Categorize keywords
    categories = {
        '피부/효과': ['피부', '주름', '눈가', '탄력', '개선', '효과', '좋아', '좋은', '만족', '추천', '변화', '느낌'],
        '텍스처/사용감': ['촉촉', '부드러', '흡수', '발림', '끈적', '가벼', '쫀쫀', '무거', '산뜻', '텍스처', '제형'],
        '성분/안전성': ['성분', '향', '냄새', '자극', '순한', '민감', '알러지', '트러블', '안전', '천연'],
        '가격/가치': ['가격', '가성비', '비싸', '저렴', '구매', '재구매', '세일', '할인', '돈', '가치']
    }
    
    category_analysis = {}
    for category, keywords in categories.items():
        category_words = {}
        for word, freq in word_freq.items():
            if any(keyword in word for keyword in keywords):
                category_words[word] = freq
        category_analysis[category] = {
            'keywords': category_words,
            'total_mentions': sum(category_words.values())
        }
    
    return df, word_freq, bigram_freq, category_analysis

def visualize_large_dataset(df, word_freq, bigram_freq, category_analysis):
    """
    Create comprehensive visualizations for large dataset
    """
    plt.style.use('seaborn-v0_8-white')
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    # Create a comprehensive figure
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Top Keywords
    ax1 = plt.subplot(3, 3, 1)
    top_words = dict(word_freq.most_common(20))
    bars = ax1.bar(range(len(top_words)), list(top_words.values()), color='skyblue')
    ax1.set_xticks(range(len(top_words)))
    ax1.set_xticklabels(list(top_words.keys()), rotation=45, ha='right')
    ax1.set_title('가장 많이 언급된 키워드 TOP 20', fontsize=14, fontweight='bold')
    ax1.set_ylabel('빈도수')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}', ha='center', va='bottom', fontsize=8)
    
    # 2. Rating Distribution
    ax2 = plt.subplot(3, 3, 2)
    rating_counts = df['rating'].value_counts().sort_index()
    colors = ['#ff4444', '#ff7744', '#ffaa44', '#44ff44', '#00ff00']
    bars = ax2.bar(rating_counts.index, rating_counts.values, 
                   color=[colors[min(int(r)-1, 4)] for r in rating_counts.index])
    ax2.set_title(f'평점 분포 (총 {len(df):,}개 리뷰)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('평점')
    ax2.set_ylabel('리뷰 수')
    ax2.set_xticks(rating_counts.index)
    
    total = sum(rating_counts.values)
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}\n({height/total*100:.1f}%)', 
                ha='center', va='bottom', fontsize=9)
    
    # 3. Category Analysis
    ax3 = plt.subplot(3, 3, 3)
    categories = list(category_analysis.keys())
    mentions = [category_analysis[cat]['total_mentions'] for cat in categories]
    colors_cat = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    
    bars = ax3.bar(categories, mentions, color=colors_cat)
    ax3.set_title('카테고리별 언급 빈도', fontsize=14, fontweight='bold')
    ax3.set_ylabel('총 언급 횟수')
    ax3.set_xticklabels(categories, rotation=15, ha='right')
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}', ha='center', va='bottom')
    
    # 4. Bigrams
    ax4 = plt.subplot(3, 3, 4)
    top_bigrams = dict(bigram_freq.most_common(15))
    if top_bigrams:
        y_pos = range(len(top_bigrams))
        ax4.barh(y_pos, list(top_bigrams.values()), color='lightcoral')
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(list(top_bigrams.keys()))
        ax4.set_title('함께 나타나는 단어 조합 TOP 15', fontsize=14, fontweight='bold')
        ax4.set_xlabel('빈도수')
    
    # 5. Review Length Distribution
    ax5 = plt.subplot(3, 3, 5)
    review_lengths = df['review_text'].str.len()
    ax5.hist(review_lengths, bins=50, color='lightgreen', edgecolor='black', alpha=0.7)
    ax5.set_title('리뷰 길이 분포', fontsize=14, fontweight='bold')
    ax5.set_xlabel('글자 수')
    ax5.set_ylabel('리뷰 수')
    mean_length = review_lengths.mean()
    median_length = review_lengths.median()
    ax5.axvline(mean_length, color='red', linestyle='dashed', linewidth=2, 
                label=f'평균: {mean_length:.0f}자')
    ax5.axvline(median_length, color='blue', linestyle='dashed', linewidth=2, 
                label=f'중앙값: {median_length:.0f}자')
    ax5.legend()
    
    # 6-9. Category-specific keywords
    for idx, (category, data) in enumerate(category_analysis.items()):
        ax = plt.subplot(3, 3, 6 + idx)
        top_cat_words = dict(sorted(data['keywords'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10])
        if top_cat_words:
            bars = ax.bar(range(len(top_cat_words)), list(top_cat_words.values()), 
                         color=colors_cat[idx])
            ax.set_xticks(range(len(top_cat_words)))
            ax.set_xticklabels(list(top_cat_words.keys()), rotation=45, ha='right')
            ax.set_title(f'{category} 관련 키워드', fontsize=12, fontweight='bold')
            ax.set_ylabel('빈도수')
    
    plt.tight_layout()
    plt.savefig('sonplan_full_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create Word Cloud
    print("\n워드클라우드 생성 중...")
    plt.figure(figsize=(14, 8))
    
    # Limit words for performance
    top_500_words = dict(word_freq.most_common(500))
    
    wordcloud = WordCloud(
        font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
        background_color='white',
        width=1400,
        height=800,
        max_words=200,
        relative_scaling=0.5,
        min_font_size=10,
        colormap='viridis'
    ).generate_from_frequencies(top_500_words)
    
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'썬플랜 타임슬립 아이크림 리뷰 워드클라우드 ({len(df):,}개 리뷰 기반)', 
             fontsize=20, fontweight='bold', pad=20)
    plt.savefig('sonplan_full_wordcloud.png', dpi=300, bbox_inches='tight')
    plt.show()

def save_analysis_report(df, word_freq, bigram_freq, category_analysis):
    """
    Save comprehensive analysis report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw reviews
    print(f"\n리뷰 데이터 저장 중...")
    df.to_csv(f'sonplan_all_reviews_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Save keyword analysis
    keywords_df = pd.DataFrame([
        {'키워드': word, '빈도': freq, '순위': i+1}
        for i, (word, freq) in enumerate(word_freq.most_common(1000))
    ])
    keywords_df.to_csv(f'sonplan_keywords_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Save bigram analysis
    bigrams_df = pd.DataFrame([
        {'단어조합': bigram, '빈도': freq, '순위': i+1}
        for i, (bigram, freq) in enumerate(bigram_freq.most_common(500))
    ])
    bigrams_df.to_csv(f'sonplan_bigrams_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Save category analysis
    category_data = []
    for category, data in category_analysis.items():
        for word, freq in data['keywords'].items():
            category_data.append({
                '카테고리': category,
                '키워드': word,
                '빈도': freq
            })
    category_df = pd.DataFrame(category_data)
    category_df = category_df.sort_values(['카테고리', '빈도'], ascending=[True, False])
    category_df.to_csv(f'sonplan_categories_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Create summary report
    with open(f'sonplan_analysis_report_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write("썬플랜 타임슬립 아이크림 리뷰 분석 보고서\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"분석 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}\n")
        f.write(f"총 리뷰 수: {len(df):,}개\n")
        f.write(f"평균 평점: {df['rating'].mean():.2f}/5.0\n")
        f.write(f"평균 리뷰 길이: {df['review_text'].str.len().mean():.0f}자\n\n")
        
        f.write("평점 분포:\n")
        rating_dist = df['rating'].value_counts().sort_index()
        for rating, count in rating_dist.items():
            f.write(f"  {rating}점: {count:,}개 ({count/len(df)*100:.1f}%)\n")
        
        f.write("\n상위 50개 키워드:\n")
        for i, (word, freq) in enumerate(word_freq.most_common(50), 1):
            f.write(f"  {i:2d}. {word}: {freq:,}회\n")
        
        f.write("\n카테고리별 분석:\n")
        for category, data in category_analysis.items():
            f.write(f"\n[{category}] - 총 {data['total_mentions']:,}회 언급\n")
            top_10 = dict(sorted(data['keywords'].items(), 
                                key=lambda x: x[1], reverse=True)[:10])
            for word, freq in top_10.items():
                f.write(f"  - {word}: {freq:,}회\n")
    
    print(f"\n분석 결과 저장 완료:")
    print(f"  - 전체 리뷰: sonplan_all_reviews_{timestamp}.csv")
    print(f"  - 키워드 분석: sonplan_keywords_{timestamp}.csv")
    print(f"  - 단어 조합: sonplan_bigrams_{timestamp}.csv")
    print(f"  - 카테고리 분석: sonplan_categories_{timestamp}.csv")
    print(f"  - 종합 보고서: sonplan_analysis_report_{timestamp}.txt")

def main():
    print("썬플랜 타임슬립 아이크림 - 전체 리뷰 크롤링 및 분석")
    print("=" * 60)
    print("목표: 약 20,000개 리뷰 수집\n")
    
    # Scrape all reviews
    start_time = time.time()
    all_reviews = scrape_all_reviews_selenium()
    
    if not all_reviews:
        print("\n리뷰를 수집할 수 없습니다.")
        return
    
    elapsed_time = time.time() - start_time
    print(f"\n크롤링 완료!")
    print(f"소요 시간: {elapsed_time/60:.1f}분")
    print(f"수집된 리뷰 수: {len(all_reviews):,}개")
    
    # Analyze reviews
    print("\n대용량 데이터 분석 시작...")
    df, word_freq, bigram_freq, category_analysis = analyze_large_dataset(all_reviews)
    
    if df is None:
        print("분석할 데이터가 없습니다.")
        return
    
    # Save analysis results
    save_analysis_report(df, word_freq, bigram_freq, category_analysis)
    
    # Display top results
    print("\n=== 주요 분석 결과 ===")
    print(f"\n📊 상위 30개 키워드:")
    for i, (word, freq) in enumerate(word_freq.most_common(30), 1):
        if i % 3 == 1:
            print()
        print(f"{i:2d}. {word}: {freq:,}회", end="  ")
    
    print(f"\n\n🔗 주요 단어 조합:")
    for i, (bigram, freq) in enumerate(bigram_freq.most_common(15), 1):
        print(f"{i:2d}. {bigram}: {freq}회")
    
    print("\n📈 카테고리별 주요 인사이트:")
    for category, data in category_analysis.items():
        print(f"\n[{category}] - 총 {data['total_mentions']:,}회 언급")
        top_5 = dict(sorted(data['keywords'].items(), 
                           key=lambda x: x[1], reverse=True)[:5])
        keywords = ', '.join([f"{w}({f:,})" for w, f in top_5.items()])
        print(f"  주요 키워드: {keywords}")
    
    # Visualize
    print("\n📊 시각화 생성 중...")
    visualize_large_dataset(df, word_freq, bigram_freq, category_analysis)
    
    print("\n✨ 전체 분석 완료!")

if __name__ == "__main__":
    main()