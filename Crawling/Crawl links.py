
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

class UdemyScraper:
    def __init__(self):
        try:
            self.driver = self._setup_driver()
            self.course_urls = []
            self.category_urls = {}  # Dictionary để lưu URL theo danh mục
            print("Khởi tạo trình duyệt thành công!")
        except Exception as e:
            self._handle_error("Lỗi khi khởi tạo trình duyệt", e)
            raise

    def _setup_driver(self):
        try:
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")

            service = Service("C:/Users/khang/OneDrive/Desktop/Capstone/chromedriver-win64/chromedriver-win64/chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)

            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)

            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self._handle_error("Lỗi khi cấu hình trình duyệt", e)
            raise

    def _pause_and_resume_driver(self, wait_time=4):
        print(f"⏳ Đang tạm dừng trình duyệt trong {wait_time} giây...")
        self.driver.quit()
        time.sleep(wait_time)
        self.driver = self._setup_driver()
        print("🔄 Đã bật lại trình duyệt.")

    def _handle_error(self, message, error):
        error_msg = f"{message}: {type(error).__name__} - {str(error)}"
        print(f"\n❌ LỖI: {error_msg}")
        with open("scraper_errors.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")

    def _human_like_scroll(self, scroll_pause_time=1):
        try:
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_step = random.randint(200, 500)

            while current_position < scroll_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                pause_time = random.uniform(scroll_pause_time * 0.5, scroll_pause_time * 1.5)
                time.sleep(pause_time)
                self._random_mouse_movement()
                current_position += scroll_step
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")

            self.driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(0.5)
        except WebDriverException as e:
            self._handle_error("Lỗi khi cuộn trang", e)

    def _random_mouse_movement(self):
        try:
            actions = ActionChains(self.driver)
            x_offset = random.randint(-50, 50)
            y_offset = random.randint(-50, 50)
            actions.move_by_offset(x_offset, y_offset).perform()
        except WebDriverException:
            pass

    def _accept_cookies(self):
        try:
            cookie_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Accept']"))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(cookie_btn).pause(0.5).click().perform()
            time.sleep(1)
        except TimeoutException:
            pass
        except Exception as e:
            self._handle_error("Lỗi khi xử lý cookie", e)

    def _get_course_links(self):
        try:
            container_selectors = [
                "div.course-list_container__yXli8",
                "div.course-list--container--3zXPS",
                "div[data-purpose='course-card-list']",
                "div.ud-main-content",
                "div.course-directory--container--5ZPhr"
            ]

            container = None
            for selector in container_selectors:
                try:
                    container = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Đã tìm thấy container với selector: {selector}")
                    break
                except TimeoutException:
                    print(f"⚠️ Không tìm thấy container với selector: {selector}")
                    continue

            if not container:
                print("⚠️ Không tìm thấy container khóa học, bỏ qua trang này.")
                return []

            course_selectors = [
                "a[href*='/course/']:not([href*='/subscribe'])",
                "a.course-card-link",
                "a[data-purpose='course-card-url']",
                "a.course-card--course-card--1nL1G",
                "div.course-card--main-content--2XqiX a"
            ]

            links = []
            for selector in course_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Tìm thấy {len(elements)} khóa học với selector: {selector}")
                        for el in elements:
                            try:
                                url = el.get_attribute("href")
                                if url and "/course/" in url and url not in links:
                                    links.append(url)
                            except StaleElementReferenceException:
                                continue
                        break
                    else:
                        print(f"⚠️ Không tìm thấy khóa học với selector: {selector}")
                except Exception as e:
                    print(f"⚠️ Lỗi khi tìm khóa học với selector {selector}: {str(e)}")
                    continue

            if not links:
                print("⚠️ Không tìm thấy liên kết khóa học, bỏ qua trang này.")
                return []

            return links

        except Exception as e:
            print("\n⚠️ THÔNG TIN DEBUG:")
            print("URL hiện tại:", self.driver.current_url)
            print("Tiêu đề trang:", self.driver.title)
            self._handle_error("Lỗi khi thu thập liên kết khóa học", e)
            return []

    def scrape(self, categories=None, max_urls=10000, max_pages_per_category=625, start_page=1, output_file_override=False):
        try:
            print("\n🟢 Bắt đầu quá trình scraping...")

            if categories is None:
                categories = [
                    "development", "it-and-software", "business", "design", "marketing",
                    "personal-development", "photography-and-video", "health-and-fitness", "music", "teaching-and-academics"
                ]

            for category in categories:
                self.category_urls[category] = []

            total_urls = 0
            for category in categories:
                if total_urls >= max_urls:
                    print(f"✅ Đã đạt {max_urls} URL, dừng scraping.")
                    break

                print(f"\n📚 Đang cào danh mục: {category}")
                current_page = start_page

                while current_page <= max_pages_per_category:
                    if total_urls >= max_urls:
                        print(f"✅ Đã đạt {max_urls} URL, dừng scraping.")
                        break

                    print(f"\n📖 Đang xử lý trang {current_page} của danh mục {category}...")
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            self.driver.get(f"https://www.udemy.com/courses/{category}/?p={current_page}")
                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_element_located((By.TAG_NAME, "body"))
                            )
                            time.sleep(random.uniform(2, 4))
                            self._accept_cookies()
                            self._human_like_scroll()
                            new_links = self._get_course_links()
                            if not new_links:
                                print(f"⚠️ Không tìm thấy khóa học mới trong danh mục {category}, chuyển sang danh mục tiếp theo.")
                                break

                            initial_count = len(self.category_urls[category])
                            for link in new_links:
                                if link not in self.category_urls[category]:
                                    self.category_urls[category].append(link)
                            new_added = len(self.category_urls[category]) - initial_count
                            total_urls = sum(len(urls) for urls in self.category_urls.values())

                            print(f"✅ Trang {current_page} (danh mục {category}): Thêm {new_added} URL | Tổng (danh mục): {len(self.category_urls[category])} | Tổng (tất cả): {total_urls}")
                            filename_override = f"{category}_data_v2.csv" if output_file_override else None
                            self._save_results(category, filename_override=filename_override)
                            break
                        except Exception as e:
                            self._handle_error(f"Lỗi khi xử lý trang {current_page} của danh mục {category} (thử {attempt + 1}/{max_retries})", e)
                            if attempt < max_retries - 1:
                                print(f"🔄 Thử lại sau 5 giây...")
                                self.driver.quit()
                                time.sleep(5)
                                self.driver = self._setup_driver()
                            else:
                                print(f"⚠️ Bỏ qua trang {current_page} sau {max_retries} lần thử.")
                                break

                    self.driver.quit()
                    print("🛑 Đã đóng trình duyệt.")
                    time.sleep(random.uniform(6, 8))
                    self.driver = self._setup_driver()
                    print(f"🔄 Mở lại trang {current_page + 1} của danh mục {category}...")
                    current_page += 1
                    time.sleep(random.uniform(2, 5))

            print("\n✅ Hoàn thành!")
            return self.category_urls

        except Exception as e:
            self._handle_error("Lỗi nghiêm trọng trong quá trình scraping", e)
            return self.category_urls

        finally:
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit()
                    print("🛑 Đã đóng trình duyệt.")
            except Exception as e:
                print(f"⚠️ Lỗi khi đóng trình duyệt: {str(e)}")
            for category in self.category_urls:
                filename_override = f"{category}_data_v2.csv" if category == 'design' else None
                self._save_results(category, filename_override=filename_override)

    def _save_results(self, category, filename_override=None):
        try:
            if self.category_urls[category]:
                df = pd.DataFrame(self.category_urls[category], columns=["Course_URL"])
                df.drop_duplicates(inplace=True)
                filename = filename_override or f"{category}_urls.csv"
                df.to_csv(filename, index=False)
                print(f"📂 Đã lưu kết quả danh mục {category} vào file {filename}.")
        except Exception as e:
            print(f"⚠️ Lỗi khi lưu kết quả danh mục {category}: {str(e)}")

if __name__ == "__main__":
    try:
        scraper = UdemyScraper()
        result = scraper.scrape(
            categories=["design"],
            max_urls=10000,
            max_pages_per_category=625,
            start_page=1888,
            output_file_override=True
        )
        total_urls = sum(len(urls) for urls in result.values())
        print(f"\n📊 Tổng số URL đã thu thập: {total_urls}")
        print("📂 Kết quả đã được lưu vào file: design_data_v2.csv")
    except Exception as e:
        print(f"\n❌ KHÔNG THỂ BẮT ĐẦU SCRAPER: {str(e)}")
