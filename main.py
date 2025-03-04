import streamlit as st
import psycopg2
import pandas as pd
from anthropic import Anthropic
import json

st.title("Data Chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Connect to database
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        dbname="production_drip_shop",
        user="googledatastudio",
        password="JKLsng265SkAbngpabnsSAkl6",
        host="db-tcp-read-proxy.dripshop.live",
        port=5432
    )

# User input
if prompt := st.chat_input("Ask about your data"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get database data
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM your_table LIMIT 1000", conn)
    
    # Get Claude's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            client = Anthropic(api_key="your_api_key")
            response = client.messages.create(
                model="claude-3-5-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": "You help analyze database data and suggest visualizations. When appropriate, return JSON visualization specs the app can render."},
                    {"role": "user", "content": f"Here is data from our database:\n\n{df.head(20).to_string()}\n\nData has {df.shape[0]} rows and columns: {', '.join(df.columns)}\n\nUser query: {prompt}"}
                ]
            )
            
            result = response.content[0].text
            
            # Check if the response contains a visualization spec
            if "```json" in result:
                st.markdown(result.split("```json")[0])
                viz_spec = result.split("```json")[1].split("```")[0]
                try:
                    viz_data = json.loads(viz_spec)
                    # Render visualization based on type
                    if viz_data["type"] == "bar":
                        st.bar_chart(data=df, x=viz_data["x"], y=viz_data["y"])
                    elif viz_data["type"] == "line":
                        st.line_chart(data=df, x=viz_data["x"], y=viz_data["y"])
                    elif viz_data["type"] == "scatter":
                        st.scatter_chart(data=df, x=viz_data["x"], y=viz_data["y"])
                    # Add more chart types as needed
                except Exception as e:
                    st.error(f"Failed to create visualization: {e}")
            else:
                st.markdown(result)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": result})
