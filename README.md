# YC Summer 2025 Scraper

This Streamlit app collects data on all startups from the Y Combinator Summer 2025 batch.  
It extracts the following information:
- Company name
- Website
- Description
- YC company page
- LinkedIn page
- Whether the LinkedIn page mentions "YC S25"

## Features

- Parses all companies tagged "summer 2025" via the Algolia API
- Uses Serper.dev API to check LinkedIn pages for the phrase "YC S25"
- Displays results in a table
- CSV download available
- Secrets (API keys) stored in `.streamlit/secrets.toml`
- Streamlit button triggers scraping manually
