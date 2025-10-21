# app.py
import os
import requests
import streamlit as st

st.set_page_config(page_title="Contact Crawler", layout="centered")

st.title("Website Contact Crawler — Streamlit + RapidAPI")
st.write("Enter a full URL (https://example.com) or domain (example.com) and hit **Search**.")

# Input
query = st.text_input("URL or domain", placeholder="https://example.com or example.com")
search_btn = st.button("Search")

# Config / secrets
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # set in your environment or Streamlit secrets
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "email-scraper.p.rapidapi.com")
# NOTE: If the API you subscribed to uses a different host string, replace it in your environment.

# Helper to call RapidAPI endpoint
def call_contact_api(target):
    """
    Make request to the RapidAPI contact-crawler API.
    Replace path '/v1/extract' with the actual path shown in the RapidAPI console for your API.
    """
    if not RAPIDAPI_KEY:
        raise RuntimeError("RAPIDAPI_KEY not set in environment. Add it to secrets or env variables.")
    # Example base URL - adjust endpoint path to the API's documentation in the RapidAPI playground
    base_url = f"https://{RAPIDAPI_HOST}"
    endpoint_path = "/v1/extract"  # <-- CHANGE this to match the API's endpoint path in RapidAPI
    url = base_url + endpoint_path

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Accept": "application/json",
    }
    params = {
        "url": target  # many contact-scraper APIs accept 'url' or 'domain' param — check the playground
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

# Main interaction
if search_btn:
    if not query:
        st.error("Please provide a URL or domain.")
    else:
        with st.spinner("Querying API..."):
            try:
                data = call_contact_api(query.strip())
            except requests.HTTPError as e:
                st.error(f"HTTP error: {e} — check your RAPIDAPI_KEY, host, and endpoint path.")
            except Exception as e:
                st.error(f"Error: {e}")
            else:
                st.success("Data retrieved.")
                # Pretty-print the raw JSON for debugging
                st.subheader("Raw Response")
                st.json(data)

                # Try to normalize common fields if present
                st.subheader("Parsed Contacts")
                emails = data.get("emails") or data.get("email") or []
                phones = data.get("phones") or data.get("phone") or []
                socials = data.get("socials") or data.get("social_links") or []

                if emails:
                    st.markdown("**Emails**")
                    for e in emails:
                        st.write(e)
                else:
                    st.write("No emails found (field 'emails' missing or empty).")

                if phones:
                    st.markdown("**Phone numbers**")
                    for p in phones:
                        st.write(p)
                else:
                    st.write("No phone numbers found (field 'phones' missing or empty).")

                if socials:
                    st.markdown("**Social links**")
                    for s in socials:
                        st.write(s)
                else:
                    st.write("No social links found (field 'socials' missing or empty).")

                # If API returns a hierarchical page list or score, show it:
                pages = data.get("pages") or data.get("results") or []
                if pages:
                    st.subheader("Pages scanned / results")
                    for idx, page in enumerate(pages[:20], start=1):
                        st.markdown(f"**{idx}.** {page.get('url') or page.get('page_url')}")
                        text_snippet = page.get("snippet") or page.get("text") or ""
                        if text_snippet:
                            st.caption(text_snippet[:300] + ("..." if len(text_snippet) > 300 else ""))
