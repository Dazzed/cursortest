import streamlit as st
import psycopg2
import pandas as pd
from anthropic import Anthropic
import json
import os

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
    # For local development, you can use environment variables
    db_host = os.environ.get("DB_HOST", "db-tcp-read-proxy.dripshop.live")
    db_port = os.environ.get("DB_PORT", 5432)
    db_name = os.environ.get("DB_NAME", "production_drip_shop")
    db_user = os.environ.get("DB_USER", "googledatastudio")
    db_password = os.environ.get("DB_PASSWORD", "")  # Don't hardcode this
    
    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

# User input
if prompt := st.chat_input("Ask about your data"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Get database data - replace with an actual table name from your database
        conn = get_connection()
        # It's better to specify the table and columns you need
        df = pd.read_sql("SELECT * FROM orders LIMIT 1000", conn)
        
        # Get Claude's response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Use environment variable for API key
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                client = Anthropic(api_key=api_key)
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
    except Exception as e:
        st.error(f"Error: {e}")
