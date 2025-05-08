import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import the PDF downloader class
from pdf_downloader import PDFDownloader


class GuidanceCrawler:
    def __init__(self, base_url="https://example.com"):
        """Initialize the crawler with the target website URL."""
        self.base_url = base_url
        self.chrome_options = Options()
        # Run in headless mode (browser won't be visible)
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.current_page = 1
        self.total_pages = None

    def start(self):
        """Start the crawling process."""
        try:
            print(f"Starting crawler on {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(8)  # Wait for page to load

            # Get total pages
            self.total_pages = self._get_total_pages()
            print(f"Total pages found: {self.total_pages}")

            # Process current page
            self._process_current_page()

            # Go through all remaining pages
            while self.current_page < self.total_pages:
                if self._goto_next_page():
                    self._process_current_page()
                else:
                    print(f"Failed to navigate to page {self.current_page + 1}")
                    break
        finally:
            print("Closing browser...")
            self.driver.quit()

    def _get_total_pages(self):
        """Get the total number of pages."""
        try:
            page_info = self.driver.find_element(By.CLASS_NAME, "pageTagLiInfo.info.gong").text
            # Extract the number from "共:63页"
            return int(page_info.strip("共:页"))
        except (NoSuchElementException, ValueError) as e:
            print(f"Error getting total pages: {e}")
            return 1  # Default to 1 if we can't determine

    def _process_current_page(self):
        """Process all links on the current page."""
        print(f"\nProcessing page {self.current_page}...")

        try:
            # Wait for the content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "topdownlist"))
            )

            # Get all article links
            links = self.driver.find_elements(By.CSS_SELECTOR, "#topdownlist li.listp a")
            print(f"Found {len(links)} links on page {self.current_page}")

            # Process each link
            for i, link in enumerate(links):
                title = link.text
                url = link.get_attribute("href")
                print(f"\nLink {i + 1}/{len(links)}: {title}")
                self._process_link(url, title)

        except TimeoutException:
            print(f"Timeout waiting for content on page {self.current_page}")
        except Exception as e:
            print(f"Error processing page {self.current_page}: {e}")

    def _process_link(self, url, title, max_retries=5, retry_delay=10):
        """Process a single link to a guidance page with retry mechanism."""
        retry_count = 0
        while retry_count < max_retries:
            original_window = self.driver.current_window_handle

            try:
                # Open the link in a new tab
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])

                # Navigate to the URL
                print(f"Accessing: {url} (Attempt {retry_count + 1}/{max_retries})")
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load

                # Confirm we've reached the guidance page
                try:
                    # Look for typical elements on guidance pages
                    content_element = self.driver.find_element(By.CLASS_NAME, "content")
                    print(f"✓ Successfully accessed guidance page: {title}")

                    # Look for PDF download buttons and download the PDF
                    pdf_downloader = PDFDownloader(self.driver)
                    pdf_downloader.find_and_download_pdf(title)
                    break  # Success, exit the retry loop

                except NoSuchElementException:
                    print(f"× This doesn't appear to be a guidance page: {title}")
                    break  # Not a guidance page, no need to retry

            except TimeoutException:
                print(f"Timeout accessing page")
                if retry_count < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    retry_count += 1
                    # Close the tab if it was opened before the timeout
                    try:
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                    except:
                        pass
                    time.sleep(wait_time)
                    continue
                else:
                    print("Maximum retries reached. Timeout persists.")
                    break

            except Exception as e:
                print(f"Error processing link: {e}")
                if retry_count < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    retry_count += 1
                    # Close the tab if it was opened before the error
                    try:
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                    except:
                        pass
                    time.sleep(wait_time)
                    continue
                else:
                    print("Maximum retries reached. Error persists.")
                    break

            finally:
                # Make sure we close the tab and switch back to the main window
                try:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                except Exception as e:
                    print(f"Error while closing tab: {e}")
                    # If we can't close the tab, try to at least get back to the original window
                    try:
                        if len(self.driver.window_handles) > 0:
                            self.driver.switch_to.window(self.driver.window_handles[0])
                    except:
                        pass

    def _goto_next_page(self, max_retries=3, retry_delay=5):
        """Navigate to the next page with retry mechanism."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Find and click the "Next Page" button
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "clickpage.next"))
                )
                next_button.click()

                # Wait for the page to refresh
                WebDriverWait(self.driver, 10).until(
                    EC.staleness_of(next_button)
                )

                # Wait for new content to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "topdownlist"))
                )

                # Update current page counter
                self.current_page += 1
                print(f"Navigated to page {self.current_page}")
                return True

            except TimeoutException:
                print(f"Timeout navigating to next page")
                if retry_count < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    print("Maximum retries reached. Could not navigate to next page.")
                    return False

            except NoSuchElementException:
                print("Next page button not found")
                return False

            except Exception as e:
                print(f"Error navigating to next page: {e}")
                if retry_count < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    print("Maximum retries reached. Error persists.")
                    return False

        return False  # Should not reach here, but just in case