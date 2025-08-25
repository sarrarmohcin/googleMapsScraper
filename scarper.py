import asyncio
from playwright.async_api import async_playwright
import json
import re
from bs4 import BeautifulSoup
import dateparser
from datetime import datetime,timedelta
import string

final_place_ids = []
HEADLESS = True

def date_limit(hours=24):
    now = datetime.now()
    # Subtract 24 hours
    minus_24h = now - timedelta(hours=hours)
    # Convert to Unix timestamp
    timestamp_minus_24h = minus_24h.timestamp()

    return int(timestamp_minus_24h)
    
    
def string_date_to_timestamp(date_str):
    parsed_time = dateparser.parse(date_str)
    return int(parsed_time.timestamp())

def parse_reviews(html, review_limit = 0):
    data = []
    soup = BeautifulSoup(html,'lxml')
    reviews = soup.select('div[data-review-id]')
    if review_limit > 0:
        reviews = reviews[:review_limit]
    for rev in reviews:
        revId = None
        try:
            revId = rev['data-review-id']
        except:
            revId = None

        author = None
        try:
            author = rev.select('div.WNxzHc.qLhwHc button div')[0].text
        except:
            author = None

        author_type = None
        try:
            author_type = rev.select('div.WNxzHc.qLhwHc button div')[1].text.split('.')
        except:
            author_type = None
        
        content = None
        try:
            content = rev.select_one('div.MyEned span').text
        except:
            content = None
        
        tags_data = None
        try:
            tags = rev.select('div.MyEned div.PBK6be')
            tags_data = []
            for tag in tags:
                tag_name = tag.select('div')[0].text
                tag_value = tag.select('div')[1].text
                tags_data.append({
                    "tag name" : tag_name,
                    "tag value" : tag_value
                })
        except:
            tags_data = None
        
        rating = None
        try:
            rating = rev.select_one('span.kvMYJc')['aria-label']
        except:
            rating = None
        
        timestamp = None
        try:
            date_str = rev.select_one('span.rsqaWe').text
            timestamp = string_date_to_timestamp(date_str)
        except:
            timestamp = None

        data.append({
            'revId' : revId,
            'author' : author,
            'author_type' : author_type,
            'content' : content,
            'tags' : tags_data,
            'rating' : rating,
            'timestamp' : timestamp
        })
    
    return data
    
def clean_text(text):
    return ''.join(c for c in text if c.isalnum() or c.isspace() or c in string.punctuation)

def parse_infos(html):
    data = dict()
    soup = BeautifulSoup(html,'lxml')
    
    img = None
    try:
        img = soup.select_one('img')['src']
    except:
        img = None

    name = None
    try:
        name = soup.select_one('div.lMbq3e h1').text
        name = clean_text(name)
    except:
        name = None
    
    rating = None
    try:
        rating = soup.select_one('div.lMbq3e span[role="img"]')['aria-label'].strip().split('\xa0')[0]
        rating = clean_text(rating)
    except:
        rating = None
    
    reviews = None
    try:
        reviews = soup.select_one('div.lMbq3e span[role="img"]').parent.find_next_sibling().get_text()
        reviews = reviews.replace('(','').replace(')','').strip()
        reviews = clean_text(reviews)
    except:
        reviews = None
    
    place_type = None
    try:
        place_type = soup.select_one("button.DkEaL").text
        place_type = clean_text(place_type)
    except:
        place_type = None
    
    accessible = None
    try:
        accessible = soup.select_one("span.wmQCje")['aria-label']
        accessible = True
    except:
        accessible = None
    
    description = None
    try:
        description = soup.select_one('div.PYvSYb').text
        description = clean_text(description)
    except:
        description = None
    
    services = None
    try:
        services = [clean_text(div.text.strip()) for div in soup.select('div.E0DTEd > div')]
    except:
        services = None
    
    address = None
    try:
        address = soup.select_one('button[data-item-id="address"]').text
        address = clean_text(address)
    except:
        address = None
    
    menu = None
    try:
        menu = soup.select_one('a[data-item-id="menu"]')['href']
        menu = clean_text(menu)
    except:
        menu = None
    
    website = None
    try:
        website = soup.select_one('a[data-item-id="authority"]')['href']
        website = clean_text(website)
    except:
        website = None
    
    phone = None
    try:
        phone = soup.select_one('button[data-item-id*="phone"]').text
        phone = clean_text(phone)
    except:
        phone = None
    
    
    data = {
        'img' : img,
        'name' : name,
        'rating' : rating,
        'reviews_number' : reviews,
        'place_type' : place_type,
        'accessible' : accessible,
        'description' : description,
        'services' : services,
        'address' : address,
        'menu' : menu,
        'website' : website,
        'phone' : phone,
    }

    return data


def parse_horaires(html):
    data = []
    soup = BeautifulSoup(html,"lxml")
    ho = soup.select('table')[0]
    trs = ho.select('tr')
    for tr in trs:
        tds = tr.select('td')
        data.append({
            'day' : clean_text(tds[0].text),
            'horaires' : clean_text(tds[1]['aria-label'])
        })

    return data

async def get_reviews(page, language = 'en', date_limit_hours = 0, review_limit = 0):
    sort_language = {
        'en' : 'Sort',
        'fr' : 'Trier'
    }
    # click on tri button
    tri_btn = page.locator(f'button[data-value="{sort_language[language]}"]').first
    await tri_btn.click()
    await asyncio.sleep(2)

    # click on recent btn to tri reviwes by date
    recent_btn = page.locator('div#action-menu div[data-index="1"]').first
    await recent_btn.click()
    await asyncio.sleep(2)

    # get the div to scroll the reviews
    scroll_rev_div = page.locator('div[role="main"] > :nth-child(2)').first

    # init params
    old_number_reviews = 0
    new_number_reviews = 0
    date_limit_rev = date_limit(date_limit_hours)
    exist_while = False

    # iterate until end of reviews
    while True:

        scroll_number = 0
        reviews_div = []

        # scroll while the number of reviews not changed
        while new_number_reviews == old_number_reviews:
            # scroll to bottom
            await scroll_rev_div.evaluate("el => el.scrollTop = el.scrollHeight")
            scroll_number = scroll_number + 1
            await asyncio.sleep(3)

            # get the number of reviews
            rev_div = page.locator('div[role="main"]').first
            reviews_div = await rev_div.locator('div[data-review-id][aria-label]').all()

            # update the new reviews number
            new_number_reviews = len(reviews_div)

            # if scroll 10 times without the number of reviews change, its the end
            if scroll_number > 10:
                exist_while = True
                break
        
        # update the old reviews number for next scrolls
        old_number_reviews = new_number_reviews

        # if no reviews exist end the while loop
        if exist_while == True:
            break
        
        # exist while loop if limit date reached
        if date_limit_hours > 0:
            date_str = await reviews_div[-1].locator('span.rsqaWe').first.text_content()
            parsed_time = string_date_to_timestamp(date_str)
            if parsed_time<date_limit_rev:
                break

        # exist while loop if limit number reached
        if review_limit > 0:
            if new_number_reviews >= review_limit:
                break
    
    # iterate over all reviews and click on plus button to show all review text
    rev_div = page.locator('div[role="main"]').first
    reviews_div = await rev_div.locator('div[data-review-id][aria-label]').all()
    for review in reviews_div:
        try:
            plus_button = review.locator('div.MyEned button[data-review-id]').first
            await plus_button.click(timeout=1000)
        except:
            pass
    
    # get html code for all reviews
    reviews_html = await page.locator('div[role="main"]').first.inner_html()
    data = parse_reviews(reviews_html, review_limit)

    return data

async def click_tab(page, index, language):
    language_tabs = [
        {
            'en' : 'Overview',
            'fr' : 'Présentation'
        },
        {
            'en' : 'Reviews',
            'fr' : 'Avis'
        }
    ]

    try:
        rev = page.locator(f'button[role="tab"][data-tab-index][aria-label*="{language_tabs[index][language]}"]').first
        await rev.click()
        await asyncio.sleep(3)
        return True
    except:
        return False

async def get_open_hours(page):
    try:
        ho_button = page.locator('button[data-item-id="oh"]').first
        await ho_button.click(timeout=1000)
        await asyncio.sleep(3)
        ho_div = page.locator('div[role="main"]').first
        ho_div_html = await ho_div.inner_html()
    except:
        try:
            ho_table = page.locator('table.eK4R0e').first
            ho_div_html = await ho_table.inner_html()
            ho_div_html = f"<div><table>{ho_div_html}</table></div>"
        except:
            return None
    
    data = parse_horaires(ho_div_html)
    return data

async def close_browser(browser,context):
    try:
        await context.close()
        await browser.close()
    except:
        print('cant close browser')

async def get_place_id(page_content):
    pattern = r"placeid\\\\u003d([^\\\\]+)\\\\"

    match = re.search(pattern, page_content)
    if match:
        placeid_value = match.group(1)
        return placeid_value
    else:
        print('not found')
        return None

async def get_place(place_id,review_limit = 0,date_limit_hours = 0, scrape_reviews = False, scrape_open_hours = False, language = 'en'):
    async with async_playwright() as p:
        # init language map
        language_locale = {
            'en' : 'en-UK',
            'fr' : 'fr-FR'
        }
        infos = dict()

        # Launch the browser
        browser = await p.chromium.launch(headless=HEADLESS)  # Set to True to run headless
        context = await browser.new_context(
            locale = language_locale[language],
            viewport={ 'width': 1100, 'height': 1024 },
            
        )
        page = await context.new_page()


        url=f"https://www.google.com/maps/search/?api=1&query=11111&query_place_id={place_id}"


        # Navigate to a website

        await page.goto(url)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)

        # get place id 
        page_content = await page.content()
        place_id = await get_place_id(page_content)

        # get reviews
        reviews = None
        if scrape_reviews == True:
            if not await click_tab(page, 1, language):
                await close_browser(browser,context)
            reviews = await get_reviews(page, language, date_limit_hours , review_limit )
        
        # get infos
        ## get main div html
        
        if not await click_tab(page, 0, language):
            await close_browser(browser,context)
        infos_html = await page.locator('div[role="main"]').first.inner_html()
        infos = parse_infos(infos_html)

        
        ## get open hours
        if scrape_open_hours == True:
            open_hours = await get_open_hours(page) 
            infos['open_hours'] = open_hours   

        # Close the browser
        await close_browser(browser,context)

        # return data
        if scrape_reviews == True:
            infos['reviews'] = reviews

        return infos


# Run the async function
'''
rest1 = "ChIJQ7aZhzNv5kcR2ukcRnOizeQ"
rest2 = "ChIJOVTwFt5t5kcRvIpKiXQKGi8"
rest3 = "ChIJH-CzO7Nrpw0RTbXZa8AgjTo"
hotel1 = "ChIJ9T4c2ldn5kcRf54VT2VGdgY"
url3 = f"https://www.google.com/maps/search/?api=1&query=11111&query_place_id={rest3}"
url = "https://www.google.com/maps/search/?api=1&query=11111&query_place_id=ChIJQ7aZhzNv5kcR2ukcRnOizeQ"
url2 = "https://www.google.com/maps/place/JO%26JOE+Paris+Gentilly/@48.8163491,2.3382857,17z/data=!4m10!3m9!1s0x47e671cfed9cfa55:0x196cc051f6af8d4b!5m2!4m1!1i2!8m2!3d48.8163491!4d2.3382857!10e7!16s%2Fg%2F11gy1twcgz?authuser=0&hl=fr&entry=ttu&g_ep=EgoyMDI0MTEyNC4xIKXMDSoASAFQAw%3D%3D"
asyncio.run(get_place("ChIJk7ZmSJtrpw0RzePFgzeoD4w",reviews=True))
'''
#+33142596931
