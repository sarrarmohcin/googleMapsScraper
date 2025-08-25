import streamlit as st
from place_ids import get_places
from scarper import get_place
import asyncio
import json
import pandas as pd

def main(search_query, place_limit = 1, language = 'en', scrape_open_hours = False, scrape_reviews = False, review_limit = 10, date_limit_hours = 24):
    places_ids = asyncio.run(get_places(search_query, place_limit = place_limit, language = language))

    data = []
    for place in places_ids:
        infos = asyncio.run(
            get_place(
                place, 
                review_limit = review_limit, 
                date_limit_hours = date_limit_hours, 
                scrape_reviews = scrape_reviews, 
                scrape_open_hours = scrape_open_hours, 
                language = language)
            )
        infos['place_id'] = place
        data.append(infos)
    

    return data

# --- SIDEBAR ---
with st.sidebar:

    st.markdown("### Query Settings")

    # Inputs at the bottom (you can customize these)
    search_query = st.text_input("Your Search Query")
    place_limit = st.number_input("Limit number of Places", min_value=1)
    language = st.selectbox(
        "Select your favorite language",
        options=["en", "fr"]
    )
    scrape_open_hours = st.checkbox("Enable opening hours")
    st.markdown("---")
    st.markdown("### Reviews Settings")
    scrape_reviews = st.checkbox("Enable reviews")
    review_limit = st.number_input("Limit number of reviews", min_value=1)
    date_limit_hours = st.number_input("Limit date of reviews ( in hours )", min_value=0)

    submitted = st.button("Submit")    

# --- MAIN CONTENT ---
st.image("logo-bg.png", use_container_width=False, width=300)
st.write("This is a Google Maps scraper that allows you to search for places and scrape their information. choose your settings in the sidebar to get started.")


st.markdown("### Search Results")
if submitted:
    if not search_query:
        st.error("Please choose your search query.")
    else:
        with st.spinner("Search query started. Results will be displayed here.... Please wait."):
            data = main(
                search_query, 
                place_limit = place_limit, 
                language = language, 
                scrape_open_hours = scrape_open_hours, 
                scrape_reviews = scrape_reviews, 
                review_limit = review_limit, 
                date_limit_hours = date_limit_hours
            )

        df = pd.DataFrame(data)[["place_id", "name", "rating","reviews_number","address","phone","website"]]
        st.dataframe(df , use_container_width=True)