<div id="top"></div>
<div align="center">
  <h1 align="center">Google Maps Scraper</h1>
  <img src="./images/gmapscraper.png">
</div>

This Google Maps Scraper will enable you to get data from Google Places, the scraper built with Python and library <a href="https://www.selenium.dev">Selenium</a>
  <br>
This scraper enables you to extract all of the following data from Google Maps:
- place title and image
- Address
- Phone and website if available
- Average rating and review count
- Opening hours
- Popular times 

The scraper also supports the scraping of all detailed information about reviews:
- Review text
- Stars
- Published date
- Reviewer name
- Reviewer number of reviews
- Reviewer is Local Guide


<!-- GETTING STARTED -->
## Installation

1. Clone the repo
   ```sh
   git clone https://github.com/mohcinsarrar/googleMaps-scraper.git
   ```
2. Install requirements
   ```sh
   pip install -r requirements.txt
   ```

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### Scrape places
you can scrape places for a specific search query, Example : "restaurant in new york", to start scraping execute this command in the directory of the file main.py :
python main.py -q "rest in new york" -l 2 -pf "dd.csv" -r -rf "ff.csv" -rl 2
  ```sh
     python main.py -r -q "search query" -l maxPlaces -rl maxReviews -pf "outputFile.csv" -rf "outputFile.csv"
  ```

- -r : option to activate scraping reviews (Default : deactivate)
- -q "search query" : Example : -q "restaurant in new york"
- -l maxPlaces : max places to be scraped
- -rl maxReviews : max reviews to be scraped
- -pf "outputFile.csv" : path to output file to save places data
- -rf "outputFile.csv" : path to output file to save reviews data

<p align="right">(<a href="#top">back to top</a>)</p>
