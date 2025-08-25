from place_ids import get_places
from scarper import get_place
import asyncio
import json

search_query = "restaurant in new york"
places_ids = asyncio.run(
    get_places(
        search_query, 
        place_limit = 3, 
        language = 'en')
    )

data = []
for place in places_ids:
    infos = asyncio.run(
        get_place(
            place, 
            review_limit = 10, 
            date_limit_hours = 240, 
            scrape_reviews = True, 
            scrape_open_hours = False, 
            language = 'en')
        )
    infos['place_id'] = place
    data.append(infos)

with open("results.json", "w") as json_file:
    json.dump(data, json_file)
    