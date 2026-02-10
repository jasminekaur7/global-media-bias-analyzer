# global-media-bias-analyzer
A quantitative analytics platform for identifying and visualizing systemic bias in international news streams using the GDELT database.
Overview
The Global Media Bias Analyzer is a data-driven tool designed to track how different news outlets report on countries around the world. By analyzing sentiment scores from the GDELT Project, this platform identifies whether media coverage is leaning toward a positive, negative, or neutral narrative.

Live Application
You can access the live dashboard here:
[INSERT YOUR STREAMLIT URL HERE]

Key Features
Geopolitical Roulette: A feature that selects a random country from the database to explore new media signals.

Bias Classification: Automatically labels news channels as "Systemic Negative," "Neutral," or "Systemic Positive" based on their average sentiment scores.

Interactive Analytics: Visualizes data through charts that show how sentiment is spread across different news sources.

Source Verification: Provides direct links to the original news articles for transparency and fact-checking.

Standardized Data: Cleans and organizes complex location data so that all news related to a specific country is grouped correctly.

How It Works
Data Collection: The system pulls news metadata from the GDELT Project, which monitors global broadcast, print, and web news.

Sentiment Scoring: Each news article is assigned a score. Negative scores often indicate reports on conflict or crisis, while positive scores indicate reports on progress or stability.

Aggregation: The app calculates the average score for each news outlet (e.g., BBC, Al Jazeera, CNN) to determine their overall reporting tone for a specific country.

Visualization: The results are displayed in easy-to-read tables and graphs.

Technologies Used
Python: The core programming language.

Streamlit: Used to build the web interface.

Pandas: Used for data cleaning and organization.

Plotly: Used for creating interactive graphs.

PostgreSQL: Used for local database management.

Limitations and Future Work
Current Focus: This version focuses primarily on English-language news outlets.

Sarcasm Detection: Like most automated tools, the sentiment analysis may sometimes miss sarcasm or complex cultural context.

Future Updates: Plans are in place to move from static data files to a live API connection for real-time tracking.
