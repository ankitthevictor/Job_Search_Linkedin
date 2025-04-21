import os
import time
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class JobSearchAgent:
    def __init__(self, headless=True, timeout=20):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # optional: set user-agent to avoid blocks
        # options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, timeout)

    def _accept_cookies(self):
        try:
            btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(),'Accept') or contains(text(),'agree') or contains(text(),'Cookie')]"
            )
            btn.click()
            time.sleep(1)
        except Exception:
            pass

    def search_linkedin(self, job_term: str, location: str = 'Worldwide', num_results: int = 50):
        """
        Returns a list of job dicts with keys: Job Title, Company, Location, Date Posted, Link.
        """
        query = job_term.replace(' ', '%20')
        loc = location.replace(' ', '%20')
        url = f'https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}'
        self.driver.get(url)
        time.sleep(2)
        self._accept_cookies()

        # wait for any job card to load
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.base-card')))

        # scroll page to load sufficient jobs
        cards = self.driver.find_elements(By.CSS_SELECTOR, 'div.base-card')
        while len(cards) < num_results:
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(2)
            cards = self.driver.find_elements(By.CSS_SELECTOR, 'div.base-card')

        cards = cards[:num_results]
        jobs = []
        for card in cards:
            # extract basic info
            title = ''
            company = ''
            location_text = ''
            link = ''
            date_posted = None
            try:
                title = card.find_element(By.CSS_SELECTOR, 'h3.base-search-card__title').text.strip()
            except:
                pass
            try:
                company = card.find_element(By.CSS_SELECTOR, 'h4.base-search-card__subtitle').text.strip()
            except:
                pass
            try:
                location_text = card.find_element(By.CSS_SELECTOR, 'span.job-search-card__location').text.strip()
            except:
                pass
            try:
                link = card.find_element(By.CSS_SELECTOR, 'a.base-card__full-link').get_attribute('href')
            except:
                pass
            # extract date posted from time tag
            try:
                elem = card.find_element(By.TAG_NAME, 'time')
                dt = elem.get_attribute('datetime')  # ISO format date
                # parse only date portion, ignore time
                date_posted = datetime.fromisoformat(dt).date()
            except:
                pass

            jobs.append({
                'Job Title': title,
                'Company': company,
                'Location': location_text,
                'Date Posted': date_posted,
                'Link': link
            })

        return jobs

    def search(self, job_term: str, location: str = 'Worldwide', num_results: int = 50):
        job_list = self.search_linkedin(job_term, location, num_results)
        df = pd.DataFrame(job_list)
        # sort by Date Posted descending if available, ensure date only
        if 'Date Posted' in df.columns and not df['Date Posted'].isnull().all():
            df['Date Posted'] = pd.to_datetime(df['Date Posted']).dt.date  # keep only date
            df = df.sort_values(by='Date Posted', ascending=False).reset_index(drop=True)
        print(f"Collected {len(df)} jobs from LinkedIn.")
        return df

    def export_to_excel(self, df: pd.DataFrame, filename: str = 'jobs.xlsx'):
        try:
            df.to_excel(filename, index=False)
            print(f"Exported to Excel: {os.path.abspath(filename)}")
        except ImportError:
            csv_file = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_file, index=False)
            print(f"openpyxl missing, exported to CSV: {os.path.abspath(csv_file)}")

    def close(self):
        self.driver.quit()

if __name__ == '__main__':
    agent = JobSearchAgent(headless=True)
    term = input('Enter job search term: ').strip()
    loc = input('Enter location (default Worldwide): ').strip() or 'Worldwide'
    num = input('Number of results (default 50): ').strip()
    try:
        num = int(num)
    except:
        num = 50

    df = agent.search(term, loc, num)
    if not df.empty:
        agent.export_to_excel(df)
    else:
        print('No jobs found.')
    agent.close()
