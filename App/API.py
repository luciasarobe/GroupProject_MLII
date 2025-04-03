#Python API Wrapper for SimFin

#Import necessary libraries

import requests
import logging
import pandas as pd
import time
import re

#Exceptions

class APIError(Exception):
    #Base exception for API errors
    pass

class ResourceNotFoundError(APIError):
    #Exception raised when a resource is not found
    pass

class InvalidParameterError(APIError):
    #Exception raised when an invalid parameter is provided
    pass


#Define class AdzunaAPI - retrieve jobs (with description and locations) from different companies
#app_id = 0b31602c
#api_key = f3051eb4a97fb6f81ed113699ecde36b

class AdzunaAPI:
    def __init__(self, app_id: str, api_key: str, country: str = "us"):
        self.app_id = app_id
        self.api_key = api_key
        self.country = country
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search"

    def fetch_jobs(self, num_pages: int = 20, results_per_page: int = 50) -> list:
        """
        Fetches job listings from Adzuna API for the specified number of pages.

        Args:
            num_pages (int): Number of pages to fetch (each page = 50 jobs max).
            results_per_page (int): Number of job results per page.

        Returns:
            List of job dictionaries.
        """
        all_jobs = []

        for page in range(1, num_pages + 1):
            url = f"{self.base_url}/{page}"
            params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "results_per_page": results_per_page,
                "content-type": "application/json"
            }

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                results = response.json().get("results", [])
                all_jobs.extend(results)
                print(f"Fetched page {page}, total jobs: {len(all_jobs)}")
                time.sleep(1)  # Adzuna rate limit: ~1 request/sec

            except requests.exceptions.HTTPError as http_err:
                raise Exception(f"HTTP error while fetching page {page}: {http_err}")  # Replace with custom exception if defined

            except requests.exceptions.RequestException as req_err:
                raise Exception(f"Connection error while fetching page {page}: {req_err}")  # Replace with custom exception if defined

            except Exception as e:
                raise Exception(f"Unexpected error while fetching page {page}: {e}")  # Replace with custom exception if defined

        return all_jobs



#Define class NewsAPI - retrieve news from different companies

#API key to use when initialising the class: 9e47d5c4e7374f29a69f83554ed9c6b9

class NewsAPI:

    base_url = 'https://newsapi.org/v2/everything'

    #Initialize the API wrapper with the provided API key
    def __init__(self, api_key):
        self.api_key = api_key

        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    #Method to fetch data from the SimFin API
    def get_data(self, params: dict):

        try:
            url = f'{self.base_url}'
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTP errors, if they exist
            data = response.json()
            return data
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ResourceNotFoundError(f"Resource not found. URL = {url}?{params}")
            else:
                raise APIError(f"HTTP Error: {e}")
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request Error: {e}")
        
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")

    
    #This method will return DataFrame with all the news associated to a company from a specific date
    def get_news(self, company: str, from_date: str, sort_by: str = 'popularity') -> pd.DataFrame:

        self.logger.info(f"Fetching news for {company} from {from_date}.")
        params = {"q": company, "from": from_date, "sortBy": sort_by, "apiKey": self.api_key}
        
        df = self.get_data(params)

        # Check if DataFrame is empty and if 'articles' exist in the json response (data)
        if not df or 'articles' not in df or not df['articles']:
            self.logger.warning(f"No news available for {company} from {from_date}.")
            return pd.DataFrame()

        articles = df['articles']
        df = pd.DataFrame(articles)

        if 'source' in df.columns:
            source_df = pd.json_normalize(df['source'])
            df = pd.concat([df.drop('source', axis=1), source_df], axis=1)
        else:
            self.logger.warning("No 'source' key found in articles.")
        
        return df.head(2)