import streamlit as st
import requests
import pandas as pd
import json
import time

st.set_page_config(page_title="Tradl AI News Intelligence", layout="wide")

BASE_URL = "http://localhost:8000/api"

st.title("Tradl AI: Financial News Intelligence")
st.markdown("### Intelligent Multi-Agent System for Traders")

# Sidebar for Controls
with st.sidebar:
    st.header("System Controls")
    if st.button("Ingest New Data"):
        with st.spinner("Ingesting..."):
            try:
                res = requests.post(f"{BASE_URL}/ingest")
                if res.status_code == 200:
                    st.success(res.json()['message'])
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
    
    st.divider()
    st.subheader("System Stats")
    if st.button("Refresh Stats"):
        try:
            res = requests.get(f"{BASE_URL}/stats")
            if res.status_code == 200:
                stats = res.json()
                st.metric("Total Articles", stats['total_articles'])
                st.metric("Unique Stories", stats['unique_articles'])
                st.metric("Duplicates Found", stats['duplicates_detected'])
        except:
            st.warning("Could not fetch stats")

# Main Query Interface
st.header("Market Intelligence Search")
query = st.text_input("Ask about a company, sector, or event...", placeholder="e.g., HDFC Bank news, RBI policy, Banking sector outlook")

if query:
    with st.spinner("Analyzing market data..."):
        try:
            response = requests.get(f"{BASE_URL}/query", params={"q": query})
            if response.status_code == 200:
                data = response.json()
                
                # Display Expanded Context
                st.info(f"**AI Context Expansion:** {', '.join(data['expanded_context'])}")
                
                results = data['results']
                if not results:
                    st.warning("No relevant news found.")
                else:
                    st.success(f"Found {len(results)} relevant articles")
                    
                    for article in results:
                        with st.expander(f"{article['title']} - {article['source']}", expanded=True):
                            st.write(article['content'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Entities Detected:**")
                                if article.get('entities'):
                                    for ent in article['entities']:
                                        st.caption(f"- {ent['name']} ({ent['type']})")
                                else:
                                    st.caption("None")
                            
                            with col2:
                                st.markdown("**Market Impact:**")
                                if article.get('impacted_stocks'):
                                    for stock in article['impacted_stocks']:
                                        color = "green" if stock['confidence'] > 0.8 else "orange"
                                        st.markdown(f":{color}[{stock['symbol']}] (Conf: {stock['confidence']})")
                                else:
                                    st.caption("No direct impact detected")
                                    
                            st.caption(f"Published: {article['published_at']}")
                            
            else:
                st.error("Failed to query system.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.caption("Powered by LangGraph, ChromaDB, and Mistral AI")
