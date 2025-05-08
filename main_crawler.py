import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from pdf_downloader import PDFDownloader


class GuidanceCrawler:
    def __init__(self, base_url, download_dir='downloads', headless=True):
        """Initialize the crawler."""
        self.base_url = base_url
        self.current_page = 1
        self.total_pages = None
        self.download_dir = download_dir

        # Create download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")

        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)

    def start(self):
        """Start the crawling process."""
        try:
            print(f"Starting crawler on {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(8)  # Longer wait for initial page load

            # Get total pages
            total_pages = self._get_total_pages()
            self.total_pages = total_pages
            print(f"Total pages found: {total_pages}")

            # If we need to start from a page other than 1, navigate to that page first
            if self.current_page > 1:
                print(f"Navigating to start page {self.current_page}...")
                if not self._navigate_to_specific_page(self.current_page):
                    print(f"Failed to navigate to start page {self.current_page}. Exiting.")
                    return

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
            # Find the element that shows the total number of pages
            page_info_element = self.driver.find_element(By.CSS_SELECTOR, ".pageTagLiInfo.info.gong")
            page_info_text = page_info_element.text

            # Extract the number using regex
            match = re.search(r'\d+', page_info_text)
            if match:
                return int(match.group())
            else:
                # Default fallback
                print("Could not determine total pages, assuming 1")
                return 1
        except NoSuchElementException:
            print("Pagination element not found, assuming 1 page")
            return 1
        except Exception as e:
            print(f"Error getting total pages: {e}")
            return 1

    def _process_current_page(self):
        """Process all links on the current page."""
        print(f"\nProcessing page {self.current_page}...")

        try:
            # Wait for the content to load with a longer timeout
            WebDriverWait(self.driver, 15).until(
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

            # Debug info
            print("Page source preview:")
            print(self.driver.page_source[:500] + "...")

            # Try refreshing the page
            print("Attempting to refresh the page...")
            self.driver.refresh()
            time.sleep(8)  # Wait longer after refresh

            # Try again after refresh
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, "#topdownlist li.listp a")
                print(f"After refresh: Found {len(links)} links")

                # Process each link
                for i, link in enumerate(links):
                    title = link.text
                    url = link.get_attribute("href")
                    print(f"\nLink {i + 1}/{len(links)}: {title}")
                    self._process_link(url, title)
            except Exception as e:
                print(f"Error after refresh: {e}")

        except Exception as e:
            print(f"Error processing page {self.current_page}: {e}")

    def _process_link(self, url, title, max_retries=3, retry_delay=5):
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
                time.sleep(5)  # Longer wait for page to load

                # Look for PDF download buttons and download the PDF
                pdf_downloader = PDFDownloader(self.driver, self.download_dir)
                pdf_downloader.find_and_download_pdf(title)
                break  # Success, exit the retry loop

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

    def _goto_next_page(self, max_retries=4, retry_delay=5):
        """Navigate to the next page with retry mechanism."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Find and click the "Next Page" button
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.clickpage.next"))
                )
                next_button.click()

                # Wait longer for the page to refresh
                time.sleep(8)

                # Wait for new content to load
                WebDriverWait(self.driver, 15).until(
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

        return False

    def _navigate_to_specific_page(self, target_page, max_retries=3, retry_delay=5):
        """Navigate to a specific page using direct JavaScript execution."""
        retry_count = 0

        while retry_count < max_retries:
            try:
                print(f"Attempting to jump directly to page {target_page} using JavaScript...")

                # Direct JavaScript execution to jump to the target page
                self.driver.execute_script(f"gotopage({target_page});")

                # Wait a long time for the page to load completely
                time.sleep(10)

                # Verify we're on the correct page by checking the "current" page button
                try:
                    current_page_element = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.clickpage.current"))
                    )

                    current_page_text = current_page_element.text.strip()
                    if current_page_text.isdigit() and int(current_page_text) == target_page:
                        print(f"Successfully jumped to page {target_page}")
                        self.current_page = target_page

                        # Make sure the content is loaded
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.ID, "topdownlist"))
                        )

                        return True
                    else:
                        print(f"Page verification failed. Current page shows: {current_page_text}")

                        # Try refreshing and navigating again
                        if retry_count < max_retries - 1:
                            print("Refreshing the page before retry...")
                            self.driver.refresh()
                            time.sleep(8)
                            retry_count += 1
                            continue
                        else:
                            print("Maximum retries reached. Using fallback navigation...")
                            return self._navigate_by_first_last_buttons(target_page)

                except TimeoutException:
                    print("Could not verify current page after navigation")
                    if retry_count < max_retries - 1:
                        print("Refreshing the page before retry...")
                        self.driver.refresh()
                        time.sleep(8)
                        retry_count += 1
                        continue
                    else:
                        print("Maximum retries reached. Using fallback navigation...")
                        return self._navigate_by_first_last_buttons(target_page)

            except Exception as e:
                print(f"Error using JavaScript navigation to page {target_page}: {e}")
                if retry_count < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    print("Maximum retries reached. Using fallback navigation...")
                    return self._navigate_by_first_last_buttons(target_page)

        return False

    def _navigate_by_first_last_buttons(self, target_page, max_retries=3, retry_delay=5):
        """Fallback method to navigate using first, last, next, and previous buttons."""
        print(f"Using fallback navigation method to reach page {target_page}...")

        try:
            # If target is page 1, use "首页" (first page) button
            if target_page == 1:
                first_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.clickpage.first"))
                )
                first_button.click()
                time.sleep(8)
                self.current_page = 1
                return True

            # If target is the last page, use "末页" (last page) button
            if target_page == self.total_pages:
                last_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.clickpage.last"))
                )
                last_button.click()
                time.sleep(8)
                self.current_page = self.total_pages
                return True

            # For other pages, start from page 1 and use next button repeatedly
            first_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.clickpage.first"))
            )
            first_button.click()
            time.sleep(8)
            self.current_page = 1

            # Click next button until we reach target page
            while self.current_page < target_page:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.clickpage.next"))
                )
                next_button.click()
                time.sleep(8)
                self.current_page += 1
                print(f"Navigated to page {self.current_page}")

            return True

        except Exception as e:
            print(f"Error in fallback navigation: {e}")
            return False