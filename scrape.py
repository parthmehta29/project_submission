import requests
import pandas as pd
import time
from datetime import datetime

# API credentials
email = "your_email"
key = "your_key"

# Define the base URL for the API
base_url = "https://aqs.epa.gov/data/api"

# Define parameters
start_year = 2019
end_year = 2020
states = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19", "20", "21", "22",
          "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
          "42", "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56"]

def fetch_data(endpoint, params):
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['Header'][0]['status'] == 'Success':
            return pd.DataFrame(data['Data'])
        else:
            error_message = data['Header'][0].get('error', 'Unknown error occurred')
            print(f"API Error: {error_message}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return pd.DataFrame()
    except KeyError as e:
        print(f"Unexpected response structure: {e}")
        print(f"Response content: {data}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()
def fetch_aqi_and_temp_data(year, state, county=None):
    params = {
        "email": email,
        "key": key,
        "bdate": f"{year}0101",
        "edate": f"{year}1231",
        "param": "44201,62101",  # Ozone (for AQI) and Temperature
        "state": state
    }
    if county:
        params["county"] = county

    endpoint = "annualData/byState" if not county else "annualData/byCounty"
    return fetch_data(endpoint, params)

def process_data(df, year, state, county=None):
    if df.empty:
        return pd.DataFrame()

    aqi_data = df[df['parameter_code'] == '44201'].copy()
    temp_data = df[df['parameter_code'] == '62101'].copy()

    if aqi_data.empty or temp_data.empty:
        return pd.DataFrame()

    result = pd.DataFrame({
        'year': [year],
        'state': [state],
        'county': [county] if county else [None],
        'aqi_mean': [aqi_data['arithmetic_mean'].mean()],
        'aqi_max': [aqi_data['arithmetic_mean'].max()],
        'temp_mean': [temp_data['arithmetic_mean'].mean()],
        'temp_max': [temp_data['arithmetic_mean'].max()]
    })

    return result

# Fetch and process state data
all_state_data = []
for year in range(start_year, end_year + 1):
    for state in states:
        print(f"Fetching state data for {state}, {year}...")
        state_data = fetch_aqi_and_temp_data(year, state)
        processed_data = process_data(state_data, year, state)
        if not processed_data.empty:
            all_state_data.append(processed_data)
        time.sleep(5)  # Delay to avoid hitting rate limits

# Fetch and process county data
all_county_data = []
for year in range(start_year, end_year + 1):
    for state in states:
        print(f"Fetching county data for state {state}, {year}...")
        county_data = fetch_aqi_and_temp_data(year, state, county="")
        for _, county_row in county_data.groupby('county_code'):
            processed_data = process_data(county_row, year, state, county_row['county'].iloc[0])
            if not processed_data.empty:
                all_county_data.append(processed_data)
        time.sleep(5)  # Delay to avoid hitting rate limits

# Combine and save state data
if all_state_data:
    state_df = pd.concat(all_state_data, ignore_index=True)
    state_df.to_csv('states.csv', index=False)
    print("State data saved to states.csv")
else:
    print("No state data collected.")

# Combine and save county data
if all_county_data:
    county_df = pd.concat(all_county_data, ignore_index=True)
    county_df.to_csv('county.csv', index=False)
    print("County data saved to county.csv")
else:
    print("No county data collected.")

print("Data collection complete.")
