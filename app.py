import streamlit as st
import requests
import json
from urllib.parse import urlparse

# --- Configuration ---
# IMPORTANT: Replace these with the actual host and endpoint path 
# provided by your subscribed RapidAPI service.
RAPIDAPI_HOST = "website-contactcrawler.p.rapidapi.com"
RAPIDAPI_URL = f"https://{RAPIDAPI_HOST}/" 

# --- UI Setup ---
st.set_page_config(
    page_title="Website Contact Scraper", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("📞 Website Contact Scraper")
st.markdown("Enter a full website URL (e.g., `https://www.example.com`) and click 'Scrape' to find contact details.")

# --- API Interaction Function ---
# Use st.cache_data to cache results and avoid unnecessary API calls for the same URL
@st.cache_data(show_spinner="Scraping website... this may take a moment.")
def scrape_contacts(url_to_scrape):
    """
    Calls the RapidAPI endpoint to scrape contact information.
    """
    if not url_to_scrape or not url_to_scrape.startswith(('http://', 'https://')):
        st.error("Please enter a valid URL starting with http:// or https://.")
        return None

    # Retrieve the API key from Streamlit secrets
    try:
        api_key = st.secrets["RAPIDAPI_KEY"]
    except KeyError:
        st.error("API Key not found in Streamlit secrets. Please configure the RAPIDAPI_KEY.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while accessing secrets: {e}")
        return None

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    # The exact endpoint path might vary, assuming the base URL is sufficient 
    # and the API uses a 'url' query parameter.
    querystring = {"url": url_to_scrape} 

    try:
        response = requests.get(RAPIDAPI_URL, headers=headers, params=querystring, timeout=30)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Check for API-specific errors in the response body (common in RapidAPI responses)
        if data.get("status") == "ERROR" or 'error' in data:
            st.error(f"API Error: {data.get('error', {}).get('message', 'Unknown API Error')}")
            return None

        # Return the main data object
        return data.get('data', data)

    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        st.error(f"Timeout Error: {errt}. The server took too long to respond.")
    except requests.exceptions.RequestException as err:
        st.error(f"An unexpected error occurred during the request: {err}")
    except json.JSONDecodeError:
        st.error("Failed to parse JSON response from the API.")
    
    return None

# --- Main App Logic ---
website_url = st.text_input(
    "Website URL to Scrape:", 
    placeholder="https://www.google.com", 
    value="",
    key="url_input"
)

if st.button("🚀 Scrape Contacts", type="primary"):
    with st.spinner('Requesting data...'):
        result_data = scrape_contacts(website_url)
    
    if result_data:
        st.success("Scraping Complete!")
        
        # Display extracted data in a structured way
        st.subheader("Extracted Details")

        # Function to display lists of items
        def display_list_data(title, data_list):
            if data_list and isinstance(data_list, list):
                st.markdown(f"**{title} ({len(data_list)} found):**")
                for item in data_list:
                    # Handle if the item is a string or a dictionary (e.g., for social media links)
                    if isinstance(item, str):
                        st.code(item, language='text')
                    elif isinstance(item, dict):
                        # Assuming a dict might have 'url' or 'value'
                        display_val = item.get('url') or item.get('value') or json.dumps(item)
                        st.code(display_val, language='text')
                st.divider()
            else:
                st.info(f"No {title.lower()} found.")
        
        # Display Emails
        emails = result_data.get('emails') or result_data.get('email')
        display_list_data("Emails", emails)

        # Display Phone Numbers
        phones = result_data.get('phoneNumbers') or result_data.get('phone')
        display_list_data("Phone Numbers", phones)

        # Display Social Media Links (if available in the response)
        socials = result_data.get('socialLinks') or result_data.get('social_media')
        display_list_data("Social Media Links", socials)

        # Display Other Relevant Data (if the response structure is different)
        other_fields = {k: v for k, v in result_data.items() if k not in ['emails', 'email', 'phoneNumbers', 'phone', 'socialLinks', 'social_media']}
        if other_fields:
            st.subheader("Other Data Fields")
            st.json(other_fields)

    else:
        st.warning("Could not retrieve contact data. Check the URL and your API configuration.")

# --- Footer/Instructions ---
st.sidebar.header("Deployment Instructions")
st.sidebar.info(
    "To deploy this app on Streamlit Cloud, commit this `app.py` file to a GitHub repository "
    "and ensure you have created a `.streamlit/secrets.toml` file in your repository root "
    "with your RapidAPI Key."
)

st.sidebar.markdown("**Required `secrets.toml` Content:**")
st.sidebar.code("[secrets]\nRAPIDAPI_KEY=\"YOUR_RAPIDAPI_KEY_HERE\"", language="toml")
st.sidebar.markdown(
    "Replace `YOUR_RAPIDAPI_KEY_HERE` with your actual key from RapidAPI."
)

st.sidebar.caption("The host for this app is set to: `website-contactcrawler.p.rapidapi.com`")
