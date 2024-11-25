import streamlit as st
import requests
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import math 

st.title("Where.com")
st.text("where are you going today?")

api_key = 'AIzaSyDwGOdRil8IydOWPUs7FDBhmMLUMgaR4kw'  # Replace with your actual Google Maps API key
api_keyw = 'a9f8bd68c3c0c5ccc934a6f6e725b575'

with st.form("nlpForm"):
    location = st.text_area("Enter the name of the location:")
    submit_button = st.form_submit_button(label='enter')

place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={location}&inputtype=textquery&fields=place_id,geometry&key={api_key}" 

# Get the place data
response = requests.get(place_url)
place_data = json.loads(response.content)

if place_data.get('candidates'):
    place_id = place_data['candidates'][0]['place_id']

    # --- Data fetching and processing ---
    if api_key and place_id:
        reviews_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,review&key={api_key}"
        response = requests.get(reviews_url)
        reviews_data = json.loads(response.content)

        if 'result' in reviews_data and 'reviews' in reviews_data['result']:
            reviews = reviews_data['result']['reviews']

            # --- Sentiment Analysis ---
            def analyze_sentiment(text):
                analysis = TextBlob(text)
                return analysis.sentiment.polarity  # Return polarity score

            sentiments = [analyze_sentiment(review.get('text', '')) for review in reviews]

            # --- weather ---
            def get_weather(api_keyw, lat, lon):
                """Mendapatkan data cuaca menggunakan latitude dan longitude."""
                url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_keyw}"
                response = requests.get(url).json()
    
                temp = response['main']['temp']
                temp = math.floor((temp * 1.8) - 459.67)  
    
                feels_like = response['main']['feels_like']
                feels_like = math.floor((feels_like * 1.8) - 459.67)  
    
                humidity = response['main']['humidity']
    
                weather_description = response['weather'][0]['description'] 
    
                weather_icon = response['weather'][0]['icon']
    
                return temp, feels_like, humidity, weather_description, weather_icon 
            
            # --- Get latitude and longitude ---

            latitude = place_data["candidates"][0]["geometry"]["location"]["lat"]
            longitude = place_data["candidates"][0]["geometry"]["location"]["lng"]

            # --- get the weather data ---
            temp, feels_like, humidity, weather_description, weather_icon = get_weather(api_keyw, latitude, longitude) 

            st.write(f"Informasi Cuaca dan Tempat {location}")
   
            # --- display the data ---
            st.write(f"Temperature: {temp} F Feels Like: {feels_like} F   Humidity: {humidity} % ")
            st.write(f"weather: {weather_description} % ")
                
            # image of the weather
            icon_url = f"http://openweathermap.org/img/wn/{weather_icon}@2x.png" 
            st.image(icon_url, width=200)

            # --- Create DataFrame with Sentiments ---
            df = pd.DataFrame(reviews)
            df['sentiment_score'] = sentiments
            df['sentiment'] = df['sentiment_score'].apply(lambda score: 'positive' if score > 0 else ('negative' if score < 0 else 'neutral'))

            # --- Calculate Sentiment Counts ---
            positive_count = df['sentiment'].value_counts().get('positive', 0)
            negative_count = df['sentiment'].value_counts().get('negative', 0)
            neutral_count = df['sentiment'].value_counts().get('neutral', 0)

            # --- Donut Chart with Plotly ---
            fig = px.pie(
                values=[positive_count, negative_count, neutral_count],
                names=['Positive', 'Negative', 'Neutral'],
                hole=0.4,  # Create a donut chart
                color_discrete_sequence=['#2ecc71', '#e74c3c', '#f1c40f']  # Custom colors
            )

            fig.update_traces(
                textinfo='percent+label',  # Show percentage and label on hover
                textposition='inside',  # Position text inside the segments
                hoverinfo='label+percent',  # Show label and percentage on hover
                marker=dict(line=dict(color='#000000', width=1))  # Add black border to segments
            )

            fig.update_layout(
                title_text='Sentiment Distribution',
                title_x=0.5,
                showlegend=False,  # Hide the legend
                font=dict(family="Arial", size=14),
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
                paper_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig)

            # --- Word Cloud ---
            all_reviews_text = " ".join([review.get('text', '') for review in reviews])
            wordcloud = WordCloud(background_color='mintcream', width=1500, height=600, colormap='viridis', max_words=50).generate(all_reviews_text)
        
            st.header("what do they say about this place?")
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

            # --- Display Sentiment Results in Table ---
            st.header("Sentiment Analysis Results")
            st.dataframe(df[['author_name', 'text', 'sentiment']])

            # --- Display Sentiment Counts ---
            st.write(f"Positive Sentiments: {positive_count}")
            st.write(f"Negative Sentiments: {negative_count}")
            st.write(f"Neutral Sentiments: {neutral_count}")

        else:
            st.error("Enter another location, the searched location can't be found")
else:
    st.error("enter location")

st.subheader("Google Maps Reviews Analysis")
