import asyncio
from playwright.async_api import async_playwright
import json
import re

final_place_ids = []
HEADLESS = True


async def get_places_response(response,part_url):

    if part_url in response.url:
        text = await response.text()
        parse_place_ids(text)

def parse_place_ids(text):
    # remove no-json chars
    text = text.replace('/*""*/','')
    data = json.loads(text)
    places = json.loads(data['d'].replace(')]}\'\n',''))

    pattern = r'placeid=([^&]+)'
    place_ids = re.findall(pattern, str(places))

    final_place_ids.extend(place_ids)

async def get_places(query, place_limit = 0, language = 'en'):
    
    async with async_playwright() as p:
        # init language map
        language_locale = {
            'en' : 'en-UK',
            'fr' : 'fr-FR'
        }
        # Launch the browser
        browser = await p.chromium.launch(headless=HEADLESS)  # Set to True to run headless
        context = await browser.new_context(
            locale = language_locale[language],
            timezone_id='Europe/Berlin',
            viewport={ 'width': 1100, 'height': 1024 },
            geolocation={"latitude": 48.8566, "longitude": 2.3522},
            permissions=["geolocation"]
            )
        page = await context.new_page()
        
        base_url = "https://www.google.com/maps"
        part_url = "https://www.google.com/search?tbm=map"
        # Subscribe to "response" events.
        page.on("response", lambda response: get_places_response(response,part_url))

        # Navigate to a website
        await page.goto("https://www.google.com/maps/@35.5748652,-36.8814465,3z?entry=ttu&g_ep=EgoyMDI0MTEyNC4xIKXMDSoASAFQAw%3D%3D")
        await page.wait_for_load_state("domcontentloaded")

        # wait for locators
        await page.wait_for_selector('input#searchboxinput[name="q"]')
        await page.wait_for_selector('button#searchbox-searchbutton')

        # get searchbox input
        searchbox = page.locator('input#searchboxinput[name="q"]')
        await searchbox.fill(query)

        # click on search button
        searchbutton = page.locator('button#searchbox-searchbutton')
        await searchbutton.click()   
        await asyncio.sleep(2)

        # wait for page to load
        await page.wait_for_load_state("domcontentloaded")

        # get main div
        await page.wait_for_selector('div[role="feed"]')
        main = page.locator('div[role="feed"]').first

        # scroll to the bottom while number of place not changed
        old_place_numbers = 0
        new_place_numbers = 0
        exist_while = False

        while True:
            scroll_number = 0

            # scroll until the number of place change
            while old_place_numbers == new_place_numbers:
                await main.evaluate("el => el.scrollTop = el.scrollHeight")
                scroll_number = scroll_number + 1
                await asyncio.sleep(3)
                new_place_numbers = len(final_place_ids)

                # if scroll 10 times without update exist while loop
                if scroll_number > 10:
                    exist_while = True
                    break
            await asyncio.sleep(5)
            # update old number of places for next scrolls
            old_place_numbers = new_place_numbers

            # if no place exist end the while loop
            if exist_while == True:
                break

            # exist while loop if limit number reached
            if place_limit > 0:
                if new_place_numbers >= place_limit:
                    break

        
        # Close the browser
        await context.close()
        await browser.close()
    
    if place_limit > 0:
        unique_list = list(set(final_place_ids[:place_limit]))
    else:
        unique_list = list(set(final_place_ids))

    
    return unique_list