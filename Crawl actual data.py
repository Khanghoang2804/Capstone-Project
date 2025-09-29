import pandas as pd
import time
import random
import logging
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, SessionNotCreatedException, ElementClickInterceptedException
from fake_useragent import UserAgent

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def cleanup_chrome_processes():
    import os
    try:
        os.system("taskkill /im chrome.exe /f")
        os.system("taskkill /im chromedriver.exe /f")
        logging.info("Đã dọn dẹp các tiến trình Chrome và Chromedriver còn sót lại.")
    except Exception as e:
        logging.warning(f"Lỗi khi dọn dẹp tiến trình: {str(e)}")

def setup_driver(headless=False):
    chrome_options = uc.ChromeOptions()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-webgl')
    ua = UserAgent()
    chrome_options.add_argument(f'user-agent={ua.random}')
    
    try:
        driver = uc.Chrome(options=chrome_options)
        logging.info(f"Phiên bản Chrome: {driver.capabilities['browserVersion']}")
        driver.set_page_load_timeout(30)
        return driver
    except SessionNotCreatedException as e:
        logging.error(f"Lỗi tạo session ChromeDriver: {str(e)}")
        logging.error("Hãy kiểm tra phiên bản Chrome (chrome://version) và thử lại.")
        raise
    except Exception as e:
        logging.error(f"Lỗi khởi tạo driver: {str(e)}")
        raise

def save_to_csv(course_data, filename='design_data_v3.csv'):
    df = pd.DataFrame([course_data])
    try:
        with open(filename, 'a', encoding='utf-8-sig') as f:
            if not f.writable():
                raise IOError("Không thể ghi vào file CSV, kiểm tra quyền truy cập.")
            df.to_csv(f, index=False, header=not f.tell())
        logging.info(f"Đã lưu dữ liệu cho {course_data['url']} vào {filename}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu vào CSV: {str(e)}")

def scrape_course_data(url, driver, course_id, max_retries=2):
    for attempt in range(max_retries):
        try:
            logging.info(f"Đang cào dữ liệu từ: {url} (lần thử {attempt + 1}/{max_retries})")
            driver.get(url)
            
            if any(x in driver.page_source.lower() for x in ["cloudflare", "checking your browser", "ddos protection"]):
                logging.error(f"Cloudflare chặn truy cập tại {url}")
                return None
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-purpose="lead-title"]'))
            )
            
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-purpose="course-price-text"] span span'))
                )
            except TimeoutException:
                logging.warning(f"Không tìm thấy phần tử giá ngay lập tức trên {url}, có thể giá bị ẩn.")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            course_data = {'id': course_id}
            course_data['title'] = soup.select_one('h1[data-purpose="lead-title"]').text.strip() if soup.select_one('h1[data-purpose="lead-title"]') else 'N/A'
            course_data['subtitle'] = soup.select_one('div[data-purpose="lead-headline"]').text.strip() if soup.select_one('div[data-purpose="lead-headline"]') else 'N/A'
            course_data['tag'] = soup.select_one('div.clp-lead__element-item div.ribbon-module--ribbon--vVul-').text.strip() if soup.select_one('div.clp-lead__element-item div.ribbon-module--ribbon--vVul-') else 'N/A'
            
            rating_number_elem = soup.select_one('div.clp-lead__badge-ratings-enrollment')
            course_data['rating_number'] = rating_number_elem.text.strip() if rating_number_elem else 'N/A'
            logging.info(f"Rating number cho {url}: {course_data['rating_number']}")
            
            instructor_elem = soup.select_one('div[data-purpose="instructor-bio"]')
            course_data['instructor'] = instructor_elem.text.strip() if instructor_elem else 'N/A'
            logging.info(f"Instructor cho {url}: {course_data['instructor']}")
            
            max_attempts = 2
            for review_attempt in range(max_attempts):
                try:
                    show_reviews_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-purpose="show-reviews-modal-trigger-button"]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_reviews_button)
                    driver.execute_script("arguments[0].click();", show_reviews_button)
                    logging.info(f"Đã nhấn nút 'Show all reviews' trên {url} (lần thử {review_attempt + 1})")
                    time.sleep(random.uniform(3, 5))
                    break
                except TimeoutException:
                    logging.warning(f"Không tìm thấy nút 'Show all reviews' trên {url} (lần thử {review_attempt + 1})")
                    if review_attempt == max_attempts - 1:
                        logging.error(f"Không thể nhấn nút 'Show all reviews' sau {max_attempts} lần thử trên {url}")
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-purpose="ratings-and-reviews"]'))
                )
                soup = BeautifulSoup(driver.page_source, 'html.parser')
            except TimeoutException:
                logging.warning(f"Không tìm thấy phần phân bố đánh giá trên {url}")
                for i in range(1, 6):
                    course_data[f'rating_{i}_star'] = 'N/A'
            else:
                for i in range(1, 6):
                    star_level = 6 - i
                    rate_gauge = soup.select_one(f'button[data-purpose="rate-gauge-{star_level}"] span[data-purpose="percent-label"]')
                    course_data[f'rating_{i}_star'] = rate_gauge.text.strip() if rate_gauge else 'N/A'
                    logging.info(f"Rating {i} star cho {url}: {course_data[f'rating_{i}_star']}")
            
            course_data['publish_date'] = soup.select_one('div.last-update-date span').text.strip() if soup.select_one('div.last-update-date span') else 'N/A'
            course_data['discounted_price'] = soup.select_one('div[data-purpose="course-price-text"] span span').text.strip() if soup.select_one('div[data-purpose="course-price-text"] span span') else 'N/A'
            course_data['original_price'] = soup.select_one('div[data-purpose="course-old-price-text"] span s span').text.strip() if soup.select_one('div[data-purpose="course-old-price-text"] span s span') else 'N/A'
            course_data['discount_percentage'] = soup.select_one('div[data-purpose="discount-percentage"] span:not(.ud-sr-only)').text.strip() if soup.select_one('div[data-purpose="discount-percentage"] span:not(.ud-sr-only)') else 'N/A'
            
            breadcrumbs = soup.select('div.ud-breadcrumb a.ud-heading-sm')
            course_data['category'] = breadcrumbs[0].text.strip() if len(breadcrumbs) > 0 else 'N/A'
            course_data['sub_category'] = breadcrumbs[1].text.strip() if len(breadcrumbs) > 1 else 'N/A'
            course_data['sub_sub_category'] = breadcrumbs[2].text.strip() if len(breadcrumbs) > 2 else 'N/A'
            logging.info(f"Category: {course_data['category']}, Sub_category: {course_data['sub_category']}, Sub_sub_category: {course_data['sub_sub_category']} cho {url}")
            
            curriculum = soup.select_one('span.curriculum--content-length--V3vIz')
            if curriculum:
                text = curriculum.text.strip()
                parts = text.split('•')
                course_data['section_number'] = parts[0].strip() if len(parts) > 0 else 'N/A'
                course_data['lectures_number'] = parts[1].strip() if len(parts) > 1 else 'N/A'
                course_data['time_spend'] = curriculum.select_one('span span').text.strip() if curriculum.select_one('span span') else 'N/A'
            else:
                course_data['section_number'] = course_data['lectures_number'] = course_data['time_spend'] = 'N/A'
            
            course_data['level'] = 'N/A'
            course_data['language'] = soup.select_one('div.clp-lead__locale').text.strip() if soup.select_one('div.clp-lead__locale') else 'N/A'
            course_data['url'] = url
            return course_data
        
        except TimeoutException:
            logging.error(f"Timeout khi chờ phần tử trên {url} (lần thử {attempt + 1})")
            if attempt == max_retries - 1:
                logging.error(f"Bỏ qua {url} sau {max_retries} lần thử.")
                return None
            time.sleep(random.uniform(5, 10))
        except NoSuchElementException:
            logging.error(f"Không tìm thấy phần tử trên {url} (lần thử {attempt + 1})")
            if attempt == max_retries - 1:
                logging.error(f"Bỏ qua {url} sau {max_retries} lần thử.")
                return None
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            logging.error(f"Lỗi khi cào dữ liệu từ {url} (lần thử {attempt + 1}): {str(e)}")
            if attempt == max_retries - 1:
                logging.error(f"Bỏ qua {url} sau {max_retries} lần thử.")
                return None
            time.sleep(random.uniform(5, 10))

def main():
    cleanup_chrome_processes()
    
    try:
        df = pd.read_csv("design_urls.csv")
        if 'Course_URL' not in df.columns:
            logging.error("File marketing_urls phải chứa cột 'Course_URL'")
            return
        if df.empty or len(df['Course_URL']) == 0:
            logging.error("File marketing_urls không chứa URL nào.")
            return
        logging.info(f"Tổng số URL trong file: {len(df)}")
    except Exception as e:
        logging.error(f"Lỗi khi đọc file marketing_urls: {str(e)}")
        return
    
    try:
        import os
        if os.path.exists('udemy_courses.csv'):
            os.remove('udemy_courses.csv')
            logging.info("Đã xóa file udemy_courses.csv cũ.")
    except Exception as e:
        logging.error(f"Lỗi khi xóa file CSV cũ: {str(e)}")
    
    urls = df['Course_URL'].tolist()
    selected_urls = urls[2131:]  # Sử dụng toàn bộ URL
    logging.info(f"Số URL sẽ cào: {len(selected_urls)}")
    
    driver = None
    successful_urls = 0
    try:
        driver = setup_driver(headless=False)
        for idx, url in enumerate(selected_urls, start=2132):
            try:
                logging.info(f"Đang xử lý URL {idx}/{len(selected_urls)}: {url}")
                course_data = scrape_course_data(url, driver, course_id=idx)
                if course_data:
                    save_to_csv(course_data)
                    successful_urls += 1
                else:
                    logging.warning(f"Không lấy được dữ liệu từ {url}, bỏ qua...")
            except Exception as e:
                logging.error(f"Lỗi khi xử lý URL {url}: {str(e)}")
                logging.info(f"Bỏ qua URL {url} và tiếp tục với URL tiếp theo.")
            finally:
                try:
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                except Exception as e:
                    logging.warning(f"Lỗi khi làm mới trình duyệt: {str(e)}")
            time.sleep(random.uniform(5, 10))
        logging.info(f"Hoàn thành cào dữ liệu: {successful_urls}/{len(selected_urls)} URL thành công.")
    except Exception as e:
        logging.error(f"Lỗi chung trong quá trình cào dữ liệu: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Đã đóng trình duyệt.")
            except Exception as e:
                logging.warning(f"Lỗi khi đóng trình duyệt: {str(e)}")

if __name__ == "__main__":
    main()