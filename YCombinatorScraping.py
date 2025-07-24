import os
import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import streamlit as st

APP_ID = st.secrets["algolia"]["app_id"]
API_KEY = st.secrets["algolia"]["api_key"]
SERPER_API_KEY = st.secrets["serper"]["api_key"]

HEADERS = {
    'Content-Type': 'application/json',
    'x-algolia-agent': 'Algolia for JavaScript (3.35.1); Browser; JS Helper (3.16.1)',
    'x-algolia-application-id': APP_ID,
    'x-algolia-api-key': API_KEY
}

BASE_COMPANY_URL = "https://www.ycombinator.com/companies/"
BROWSER_HEADERS = {'User-Agent': 'Mozilla/5.0'}
SERPER_SEARCH_URL = "https://google.serper.dev/search"


def fetch_page(page):
    url = f'https://{APP_ID}-dsn.algolia.net/1/indexes/*/queries'
    payload = {
        "requests": [
            {
                "indexName": "YCCompany_By_Launch_Date_production",
                "params": f'filters=batch:"summer 2025"&hitsPerPage=40&page={page}'
            }
        ]
    }
    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    r.raise_for_status()
    return r.json()


def get_company_links(slug):
    url = f"{BASE_COMPANY_URL}{slug}"
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        website = None
        linkedin = None

        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href'].strip()
            if 'linkedin.com' in href and not linkedin:
                linkedin = href
            elif (
                href.startswith('http')
                and all(excl not in href for excl in ['ycombinator.com', 'startupschool.org', 'github.com', 'linkedin.com'])
                and not website
            ):
                website = href

        return website, linkedin
    except Exception:
        return None, None


def check_linkedin_snippet_with_serper(linkedin_url, phrase="YC S25"):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": f'site:{linkedin_url} {phrase}'
    }

    try:
        r = requests.post(SERPER_SEARCH_URL, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        for res in data.get("organic", []):
            text_parts = [res.get("title", ""), res.get("subtitle", ""), res.get("snippet", "")]
            if any(phrase.lower() in part.lower() for part in text_parts):
                return True
    except Exception:
        pass

    return False


def load_companies():
    all_companies = []
    page = 0

    while True:
        data = fetch_page(page)
        hits = data['results'][0]['hits']
        if not hits:
            break
        all_companies.extend(hits)
        page += 1
        time.sleep(0.5)

    return all_companies


def main():
    st.title("YC Summer 2025 Companies Tracker")

    if st.button("Start Data Collection"):
        with st.spinner("Fetching data..."):
            companies = load_companies()

            records = []
            for company in tqdm(companies, desc="Processing"):
                name = company.get("name")
                description = company.get("long_description", "-")
                slug = company.get("slug")
                yc_url = f"{BASE_COMPANY_URL}{slug}" if slug else "-"
                website, linkedin = get_company_links(slug) if slug else (None, None)
                flag = check_linkedin_snippet_with_serper(linkedin, "YC S25") if linkedin else False

                records.append({
                    "Company Name": name,
                    "Website": website,
                    "Description": description,
                    "YC URL": yc_url,
                    "LinkedIn": linkedin,
                    "Mentions YC S25 on LinkedIn": "Yes" if flag else "No"
                })

            df = pd.DataFrame(records)
            st.dataframe(df)

            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, file_name="yc_s25_companies.csv", mime="text/csv")


if __name__ == "__main__":
    main()