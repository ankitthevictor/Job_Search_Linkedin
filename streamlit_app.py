import streamlit as st
import pandas as pd
from job_search_agent import JobSearchAgent  # ensure this module is in your repo

st.set_page_config(page_title="LinkedIn Job Scraper", layout="wide")

st.title("LinkedIn Job Scraper")

# Sidebar inputs
st.sidebar.header("Search Parameters")
job_term = st.sidebar.text_input("Job Search Term", value="Business Analyst")
location = st.sidebar.text_input("Location", value="Worldwide")
num_results = st.sidebar.number_input("Number of Results", min_value=1, max_value=200, value=50, step=1)
headless = st.sidebar.checkbox("Headless Browser", value=True)

if st.sidebar.button("Search"):
    with st.spinner("Scraping LinkedIn..."):
        agent = JobSearchAgent(headless=headless)
        try:
            df = agent.search(job_term, location, num_results)
        except Exception as e:
            st.error(f"Error during scraping: {e}")
            agent.close()
        else:
            agent.close()
            if df.empty:
                st.warning("No jobs found. Try different terms or increase number of results.")
            else:
                # Display DataFrame
                st.success(f"Collected {len(df)} jobs")
                st.dataframe(df)

                # Provide download link
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name="jobs.csv", mime="text/csv")
