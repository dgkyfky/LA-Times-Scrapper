# LAtimes Scraper
The Latimes Scraper is a Python script designed to scrape articles from the Los Angeles Times website. It allows users to specify a search phrase, filter articles by categories, and extract relevant information from the search results.

## Features
- Perform searches on the Los Angeles Times website using a specified search phrase.
- Filter search results by categories to narrow down the articles of interest.
- Extract data such as title, description, date, and picture filename from the search results.
- Add additional columns to the extracted data, such as the count of occurrences of the search phrase and whether the article contains mentions of money.
- Save the extracted data to an Excel file for further analysis.


## Dependencies
- Python 3.8+
- Selenium
- Pandas

## Parameters
- search_phrase: The search phrase to be used for the search.
- categories (optional): A list of category names to filter the search results.
- months_back (optional): Number of months back to consider for filtering the search results. Defaults to 0.
- output_folder (optional): The path to the output folder where the file will be saved. Defaults to 'Output'.
