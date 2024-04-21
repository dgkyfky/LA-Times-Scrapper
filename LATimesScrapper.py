import os
import re
import time
import datetime as dt
from typing import List

import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import logging


class LatimesScraper:
    """Class to scrape articles from the Los Angeles Times website."""

    def __init__(self):
        """
        Initialize the LatimesScraper class.

        Parameters:
        - url (str): The URL of the Los Angeles Times website.
        """

        self.url = "https://www.latimes.com/"
        self.driver = self._initialize_driver()
        self.logger = self._setup_logger()

    def _initialize_driver(self):
        """Initialize Chrome WebDriver with headless mode and other options."""

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"')
        driver = webdriver.Chrome(options=options)
        #Implicit wait of 10 seconds
        driver.implicitly_wait(10)
        driver.get(self.url)
        return driver

    def _setup_logger(self):
        """Set up logging configuration."""
        
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def _search(self, search_phrase: str):
        """
        Perform a search on the Los Angeles Times website.

        Parameters:
        - search_phrase (str): The search phrase to be used for the search.

        Raises:
        - Exception: If an error occurs during the search process.
        """

        try:
            # Wait for the search button to be clickable
            search_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/ps-header/header/div[2]/button")))
            search_button.click()

            # Wait for the search box to be present
            search_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/ps-header/header/div[2]/div[2]/form/label/input')))
            search_box.send_keys(search_phrase)
            search_box.send_keys(Keys.RETURN)

            # Sort values by NEWEST 
            select_element = self.driver.find_element(By.CLASS_NAME, "select-input")
            select = Select(select_element)
            select.select_by_value("1") # 0: Relevance; 1: Newest; 2: Oldest
            time.sleep(10) # Wait for the page to load after sort values by newest
        except Exception as e:
            # Log error if an exception occurs during the search process
            self.logger.error(f'Error occurred while searching: {e}')


    def _filter_categories(self, categories: List[str]):
        """
        Filter search results by categories.

        Parameters:
        - categories (List[str]): A list of category names to filter the search results.

        Raises:
        - Exception: If an error occurs during the filtering process.
        """
        # Only when there are category values
        if categories != []:
            try:
                # Click on the filter button to open the filter options
                filter_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'filters-open-button')))
                filter_button.click()

                # Click on the "See All" button to display all available categories
                see_all_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'see-all-button')))
                see_all_button.click()

                # Get the list of all available categories
                all_categories = self.driver.find_elements(By.CLASS_NAME, 'checkbox-input-label')
                ls_categories = [i.text for i in all_categories]

                # Iterate over the specified categories and select them if they exist
                for category in categories:
                    if category not in ls_categories:
                        # Log a warning if the specified category does not exist
                        self.logger.warning(f'Category "{category}" does not exist. Available categories: {", ".join(ls_categories)}')
                    else:
                        # Click on the checkbox corresponding to the specified category
                        category_checkbox = next((label for label in all_categories if label.text == category), None)
                        category_checkbox.click()
                # Click on the apply button to apply the selected categories
                apply_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'apply-button')))
                apply_button.click()
                
                time.sleep(10) # Wait for the page to load after applying the filters
            except Exception as e:
                # Log error if an exception occurs during the filtering process
                self.logger.error(f'Error occurred while filtering categories: {e}')


    def _extract_data(self, months_back: int) -> pd.DataFrame:
        """
        Extract data from search results.

        Parameters:
        - months_back (int): Number of months back to consider for filtering the search results.

        Returns:
        - pd.DataFrame: DataFrame containing extracted data.

        Raises:
        - Exception: If an error occurs during the data extraction process.
        """
        
        try:
            today = dt.datetime.today()
            date_min = dt.datetime(today.year, today.month - months_back, 1)
            title_ls, date_ls, description_ls, picture_ls = [], [], [], []

            # Iterate over the search result pages
            # Do it for just the first 10 pages. For more you have to subscribe the website.
            for _ in range(9):
                li_elements = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-results-module-results-menu li")))
                
                # Extract data from each list element
                for li in li_elements:
                    # Extract date
                    date = li.find_element(By.CSS_SELECTOR, "p.promo-timestamp").text
                    date = date.replace('.', '')
                    if 'ago' in date:
                        date = today
                    elif type(date) == str:
                        try:
                            date = dt.datetime.strptime(date, "%B %d, %Y")
                        except ValueError:
                            date = dt.datetime.strptime(date, "%b %d, %Y")

                    # Check if the date is within the specified range
                    if date < date_min:
                        # Return DataFrame containing extracted data
                        return pd.DataFrame({'Date': date_ls, 'Title': title_ls, 'Description': description_ls, 'Picture Filename': picture_ls})
                    date_ls.append(date)

                    # Extract title
                    title = li.find_element(By.CSS_SELECTOR, "h3.promo-title").text
                    title_ls.append(title)

                    # Extract description
                    description = li.find_element(By.CSS_SELECTOR, "p.promo-description").text
                    description_ls.append(description)

                    # Extract picture
                    picture = li.find_element(By.CSS_SELECTOR, "img.image").get_attribute("src")
                    picture_ls.append(picture)

                # Click on the next page button
                next_page = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'search-results-module-next-page')))
                next_page.click()
                
                # Wait for next page to load
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-module-next-page")))
            # Return DataFrame containing extracted data
            return pd.DataFrame({'Date': date_ls, 'Title': title_ls, 'Description': description_ls, 'Picture Filename': picture_ls})
    
        except Exception as e:
            # Log error if an exception occurs during the data extraction process
            self.logger.error(f'Error occurred while extracting data: {e}')


    def _add_columns(self, data_articles: pd.DataFrame, search_phrase: str) -> pd.DataFrame:
        """
        Add additional columns to the DataFrame.

        Parameters:
        - data_articles (pd.DataFrame): DataFrame containing the extracted data.
        - search_phrase (str): The search phrase used for the search.

        Returns:
        - pd.DataFrame: DataFrame with additional columns added.

        Raises:
        - None
        """

        # Regular expression to match money-related patterns
        money_regex = r"\$\d+(?:\.\d+)?|\d+(?:,\d+)?\s?(dollars|USD)"

        # Add columns to the DataFrame
        data_articles['search_phrase'] = search_phrase
        data_articles['search_phrase_count'] = data_articles['Title'].str.lower().str.count(search_phrase.lower()) + data_articles['Description'].str.lower().str.count(search_phrase.lower())
        data_articles['has_money'] = data_articles.apply(lambda row: bool(re.search(money_regex, row['Title'] + ' ' + row['Description'])), axis=1)
        return data_articles


    def _save_results(self, df: pd.DataFrame, search_phrase: str, output_folder: str):
        """
        Save results to an Excel file.

        Parameters:
        - df (pd.DataFrame): DataFrame containing the results to be saved.
        - search_phrase (str): The search phrase used for the search.
        - output_folder (str): The path to the output folder where the file will be saved.

        Returns:
        - None

        Raises:
        - None
        """

        try:
            today = dt.datetime.today().strftime('%Y%m%d')

            # Create the output folder if it does not exist
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            # Save the DataFrame to an Excel file
            df.to_excel(f'{output_folder}/{search_phrase.replace(" ", "_")}_{today}.xlsx')
        except Exception as e:
            # Log error if an exception occurs during the saving process
            self.logger.error(f'Error occurred while saving results: {e}')

    def scrape(self, search_phrase: str, categories: List[str], months_back: int = 0, output_folder: str = 'Output'):
        """
        Main method to execute scraping.

        Parameters:
        - search_phrase (str): The search phrase to be used for the search.
        - categories (List[str]): A list of category names to filter the search results.
        - months_back (int, optional): Number of months back to consider for filtering the search results. Defaults to 0.
        - output_folder (str, optional): The path to the output folder where the file will be saved. Defaults to 'Output'.

        Returns:
        - None

        Raises:
        - None
        """

        try:
            #Perform search based on the search phrase
            self._search(search_phrase)
            
            # Filter search results based on categories
            self._filter_categories(categories)

            # Extract data from search results
            data_articles = self._extract_data(months_back)

            # Add additional columns to the extracted data
            data_articles_with_columns = self._add_columns(data_articles, search_phrase)

            # Save the results to an Excel file
            self._save_results(data_articles_with_columns, search_phrase, output_folder)
        except Exception as e:
            # Log error if an exception occurs during the scraping process
            self.logger.error(f'An error occurred: {e}')
        finally:
            # Quit the WebDriver to release resources
            self.driver.quit()


if __name__ == "__main__":
    # Example usage
    search_phrase = 'argentina'
    #url = "https://www.latimes.com/"
    categories = []
    output_folder = 'hola'
    scraper = LatimesScraper()
    scraper.scrape(search_phrase, categories, months_back=2, output_folder = output_folder)
