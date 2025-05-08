import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class PDFDownloader:
    def __init__(self, driver, download_dir="downloads"):
        """Initialize the PDF downloader."""
        self.driver = driver
        self.download_dir = download_dir

        # Create download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def find_and_download_pdf(self, title):
        """Find PDF elements and attempt to download them."""
        try:
            # Look for elements with PDF-related text
            elements = self.driver.find_elements(By.XPATH,
                                                 "//*[contains(text(), 'PDF') or contains(text(), 'pdf') or contains(text(), '下载') or contains(text(), 'Download')]")

            if not elements:
                print("No PDF download elements found on this page")
                return False

            print(f"Found {len(elements)} potential PDF elements by text content")

            # Try to get the file URL prefix from hidden input field
            try:
                file_url_prefix = self.driver.find_element(By.ID, "fileurls").get_attribute('value')
                print(f"Found file URL prefix: {file_url_prefix}")
            except:
                file_url_prefix = "/fileLCGDBZZ/"  # Default fallback if not found
                print(f"Using default file URL prefix: {file_url_prefix}")

            for i, element in enumerate(elements):
                tag_name = element.tag_name
                text = element.text
                href = element.get_attribute('href')
                onclick = element.get_attribute('onclick')

                print(f"  Element {i + 1} tag: {tag_name}")
                print(f"  Element {i + 1} text: '{text}'")
                print(f"  Element {i + 1} href: '{href}'")
                print(f"  Element {i + 1} onclick: '{onclick}'")

                # Look for JavaScript onclick attribute that calls downpdfbyname
                if onclick and 'downpdfbyname' in onclick:
                    # Extract the PDF path from the function call
                    try:
                        # Example: downpdfbyname('cms/news/info/052e1f33-a08a-4877-ac79-f08b7cfa1b35.pdf','2025 ESGAR共识声明：原发性硬化性胆管炎的MR成像)
                        import re
                        pdf_path_match = re.search(r"downpdfbyname\('([^']+)'", onclick)

                        if pdf_path_match:
                            pdf_path = pdf_path_match.group(1)
                            base_url = self.driver.current_url.split('/custom/')[0]  # Get base domain
                            pdf_url = f"{base_url}{file_url_prefix}{pdf_path}"

                            print(f"Constructed PDF URL: {pdf_url}")
                            sanitized_title = self._sanitize_filename(title)
                            self._download_pdf_from_url(pdf_url, sanitized_title)
                            return True
                    except Exception as e:
                        print(f"Error extracting PDF path from onclick: {e}")

                # Check if element is a direct link to PDF
                elif href and href.lower().endswith('.pdf'):
                    sanitized_title = self._sanitize_filename(title)
                    self._download_pdf_from_url(href, sanitized_title)
                    return True

            # If we get here, we found elements but couldn't download the PDF
            print("Found potential PDF elements but couldn't determine how to download")
            return False

        except Exception as e:
            print(f"Error finding and downloading PDF: {e}")
            return False

    def _sanitize_filename(self, filename):
        """Remove invalid characters from filename."""
        import re
        # Replace invalid filename characters with underscores
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def _download_pdf_from_url(self, url, title):
        """Download a PDF from a URL using requests."""
        import requests
        from urllib.parse import urlparse

        try:
            print(f"Attempting to download PDF from: {url}")

            # Make the GET request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            response = requests.get(url, headers=headers, stream=True)

            # Check if the response is valid
            if response.status_code == 200:
                # If the URL doesn't end with .pdf, get filename from parsed URL
                if not url.lower().endswith('.pdf'):
                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.split('/')
                    filename = next((part for part in reversed(path_parts) if part.lower().endswith('.pdf')), None)
                    if not filename:
                        filename = f"{title}.pdf"
                else:
                    filename = f"{title}.pdf"

                # Save the file
                filepath = os.path.join(self.download_dir, filename)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                print(f"Successfully downloaded PDF to: {filepath}")
                return True
            else:
                print(f"Failed to download PDF. Status code: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return False