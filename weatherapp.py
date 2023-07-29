import streamlit as st
import requests
import json
from datetime import date
import pandas as pd
import numpy as np
import datetime
import pytz

# AccuWeather API key
api_key = '51faa15c80a628a998085d49f0faf3a0'

def home_page():
    st.title('Free Weather App for Florida Skydivers')
    st.subheader('Use the sidebar to view present and forecasted weather conditions near various dropzones throughout the state.')
    st.image('http://panoviewimaging.com/tumblr/clouds3_1024.gif')

    st.write('Made by Cameron Haley for Intro to HCI w/Professor Greg Reis')

    email = st.text_input('Enter your email to get daily skydiving weather updates') # Requirement widget (1/5)
    if email:
        st.success('Subscribed!') # Requirement Successbox (1/2)

#########################################################################################################

# Defining your page rendering functions
def current_weather_page():
    
    st.title('Compare Current Weather')
    # st.subheader('current weather conditions in Florida')

    # Pre-defined cities with prominent dropzones
    cities = ['Sebastian, Florida', 'Deland, Florida', 'Clewiston, Florida', 'Zephyrhills, Florida', 'Homestead, Florida', 'Lake Wales, Florida']
    
    # REQUIREMENT: Widget (2/5) multiselect
    selected_cities = st.multiselect("Select and compare the current weather conditions and see which dropzone is the best choice for jumping today.", cities)

    if selected_cities:
        columns = st.columns(len(selected_cities))  # Create the required number of columns

        for i, city in enumerate(selected_cities):
            base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
            response = requests.get(base_url)
            data = response.json()

            if data["cod"] != "404":
                if 'main' in data:
                    main = data['main']
                    weather_desc = data['weather'][0]['description']
                    temp_kelvin = main['temp']
                    temp_fahrenheit = (temp_kelvin - 273.15) * 9/5 + 32 # Convert temperature to Fahrenheit

                    # Simple approximation of the chance of rain
                    if "rain" in weather_desc or "drizzle" in weather_desc:
                        chance_of_rain = "High"
                    elif "cloud" in weather_desc:
                        chance_of_rain = "Medium"
                    else:
                        chance_of_rain = "Low"

                    # Display the weather data
                    columns[i].write(f"**City**: {city}")
                    columns[i].write(f"**Weather**: {weather_desc}")
                    columns[i].write(f"**Temperature**: {temp_fahrenheit:.1f} °F")
                    columns[i].write(f"**Chance of Rain**: {chance_of_rain}")
                elif 'message' in data:
                    columns[i].error(f"Error: {data['message']}")   # REQUIREMENT: Error Box (2/2)
            else: 
                columns[i].error(f"Invalid city: {city}. Please enter a valid city name.") 

######################################################################################################

def get_weather_data(lat, lon, api_key):
    response = requests.get(
        f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}')
    print(response.json())  # print the response
    return response.json()

def twelve_hour_forecasts_page():
    cities_coords = {
        'Sebastian': (27.8164, -80.4706),
        'Lake Wales': (27.9014, -81.5855),
        'Deland': (29.0283, -81.3031),
        'Homestead': (25.4687, -80.4776),
        'Zephyrhills': (28.2336, -82.1812)
    }

    st.title("24 Hour Rain and Wind Speed Forecast in Florida Cities")

    selected_city = st.radio("Select a city", list(cities_coords.keys())) # Requirement Widget (3/5) 

    lat, lon = cities_coords[selected_city]

    data = get_weather_data(lat, lon, api_key)

    df = pd.DataFrame(data['list'])
    df['dt'] = pd.to_datetime(df['dt'], unit='s')

    # Convert 'dt' to local timezone and format datetime values
    df['dt'] = df['dt'].dt.tz_localize('UTC').dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d %I:%M %p')

    # Get the current local time + 24 hours
    now_plus_24h = (pd.Timestamp.now(tz='US/Eastern') + pd.DateOffset(hours=24)).strftime('%Y-%m-%d %I:%M %p')

    # Filter data to the next 24 hours
    df = df[df['dt'] < now_plus_24h]

    # Calculate the likelihood of rain and rename the column
    df['Chance of precipitation'] = df.apply(lambda row: row['pop'] if 'pop' in row else 0, axis=1)
    
    # Extract wind speed data from the json response and convert it to mph
    df['Wind Speed (mph)'] = df['wind'].apply(lambda x: x['speed']*2.23694) # Assuming the speed is in meter/sec 

    # Add other required data to the dataframe and convert units as needed
    df['Wind Gust'] = df['wind'].apply(lambda x: x.get('gust', 0)*2.23694) # Assuming the speed is in meter/sec
    df['Temperature (F)'] = df['main'].apply(lambda x: (x['temp'] - 273.15) * 9/5 + 32) # Convert temperature to Fahrenheit
    df['Feels Like (F)'] = df['main'].apply(lambda x: (x['feels_like'] - 273.15) * 9/5 + 32) # Convert temperature to Fahrenheit
    df['Humidity (%)'] = df['main'].apply(lambda x: x['humidity'])
    df['Visibility (miles)'] = df.apply(lambda x: x['visibility']/1609.34 if 'visibility' in x else np.nan, axis=1) # Convert visibility to miles
    df['Clouds (%)'] = df['clouds'].apply(lambda x: x['all'])

    st.write('Likelihood of rain over the next 24 hours in', selected_city)
    # Create the line chart for rain
    st.line_chart(df['Chance of precipitation']) # Requirement Line Chart (1/2)

    st.write('Probability of Precipitation over the next twelve hours. (1.0 = 100 percent chance)')

    st.write('Wind speed (mph) over the next 24 hours in', selected_city)
    # Create the bar chart for wind speed
    st.bar_chart(df['Wind Speed (mph)']) # Requirement bar Chart (2/2)

    # Checkbox and Multi-select widget
    detailed_forecast = st.button('Detailed Forecast Table') # Requirement : Button Widget
    if detailed_forecast:
        options = ['Wind Speed (mph)', 'Wind Gust', 'Temperature (F)', 'Feels Like (F)', 'Humidity (%)', 'Visibility (miles)', 'Clouds (%)'] # Requirement : Interactive Table 
        selected_options = st.multiselect("Select categories for detailed forecast", options, default=options)
        # Filter the dataframe to include only the selected columns and display as a table
        st.table(df[['dt'] + selected_options])

###############################################################################################

def render_weather_maps():
    
    st.title('Weather Maps')
    # st.header('Dropzones Locations:')
    st.header('Current GOES-16 cloud cover')
    st.image('https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/se/GEOCOLOR/20232091401-20232091806-GOES16-ABI-SE-GEOCOLOR-600x600.gif')

    # REQUIREMENT : Checkbox widget (1/1)
    display_DZ_map = st.checkbox('Display a map of all Florida Skydiving Dropzones')

    if display_DZ_map:
        map_data = pd.DataFrame(
            np.array([
                [27.8164, -80.4706],    #sebastian
                [29.0283, -81.3031],    #deland
                [26.7542, -80.9337],    #clewiston
                [28.2336, -82.1812],    #z-hills
                [25.4687, -80.4776],    #homestead
                [27.9014, -81.5856]     #Lake Wales
            ]),
    columns= ['lat', 'lon'])

        st.map(map_data)
        st.write('All DZs locations above are denoted in red.')

    st.title('Florida NEXRAD Radar')
    st.image('https://s.w-x.co/staticmaps/wu/wu/wxtype1200_cur/uspie/current.png')

##########################################################################################

# Define the options for the sidebar
options = ['Home', 'Compare Current Weather', 'Twelve Hour Forecasts', 'Weather Maps']

# Render a selectbox in the sidebar and get the current selection
selected_option = st.sidebar.selectbox('Choose a page:', options)  # REQUIREMENT Selectbox widget (5/5)

# Depending on the selection, render the appropriate page
if selected_option == options[0]:  
    home_page()
elif selected_option == options[1]:  
    current_weather_page()
elif selected_option == options[2]:  
    twelve_hour_forecasts_page()  # Corrected this line
elif selected_option == options[3]:  
    render_weather_maps()
