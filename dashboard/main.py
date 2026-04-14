import streamlit as st
import httpx as hx
import time
import pandas as pd
import plotly.express as px

API_BASE_URL=st.secrets["API_BASE_URL"]
# page setup
st.set_page_config(page_title="Vortex Analytics", layout="wide")

st.title("Vortex Telemetry Engine")
st.caption("Premium telemetry analytics for your workspace")

hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.secret_key = ""


with st.sidebar:
    st.header('Authentication')

    # if not logged in
    if st.session_state.authenticated is False:
        with st.form("Login Form"):
            input_key=st.text_input("Please Enter The Secret Key", type="password")
            submit_button=st.form_submit_button("Authenticate")

            if submit_button:
                if input_key:
                    with st.spinner("Verifying Key..."):
                        try:
                            #hit the verify endpoint first
                            verify_res = hx.get(
                                f"{API_BASE_URL}/verify", 
                                headers={"X-API-Key": input_key}, 
                                timeout=3.0
                            )
                            
                            if verify_res.status_code == 401:
                                st.session_state.authenticated = False
                                st.session_state.secret_key = ""
                                st.error("Invalid API Key. Please try again.")
                                st.stop()

                            if verify_res.status_code == 200:
                                # Key is valid go to dashboard.
                                st.session_state.authenticated = True
                                st.session_state.secret_key = input_key
                                st.rerun()
                            else:
                                st.error(f"Unexpected response: {verify_res.status_code}")
                                st.stop()
                                
                        except hx.ConnectError:
                            st.error("CRITICAL: Cannot connect to Vortex Backend.")
                            st.stop()
                else:
                    st.error("Please Enter A Valid Key")
    else:
        st.success("Successfully Authenticated")
        if st.button("Log Out"):
            st.session_state.secret_key = ""
            st.session_state.authenticated = False
            st.rerun()

if not st.session_state.authenticated:
    st.info("Please authenticate in the sidebar to view your analytics.")
    st.stop()

# navigation bar

st.sidebar.divider()
st.sidebar.header("Navigation")

# create the clickable menu
current_page = st.sidebar.radio(
    "Select View:",
    ["Overview", "Traffic Trends", "Top URLs"]
)

if current_page != "Overview":
    st.sidebar.divider()
    st.sidebar.header("Filters")


if current_page == "Traffic Trends":
    days_filter= st.sidebar.number_input(
        "Time Range",
        min_value=1,
        max_value=3650,
        value=7, # default
        step=1,
    )
    # imp point 1
    # max_value = 3650 last 10 years is the max limit
    # pandas and plotly can handle way more than this but json response become the bottleneck
    # for large values the json response may become very big and slow down response
    # imm point 2
    # step=1 , user can only enter whole integer number -> 1,2,3,4 .....

elif current_page == "Top URLs":
    days_filter= st.sidebar.number_input(
        "Time Range",
        min_value=1,
        max_value=3650,
        value=7, # default
        step=1,
    )
    top_n_filter = st.sidebar.number_input(
        "Top URLs to display", 
        min_value=1,       # atleast 1 url
        max_value=100,    # max limit of 100 urls
        value=5,          # deafult
        step=1            
    )


with st.spinner("Fetching Live Data"):
    try:
        headers={"X-API-Key":st.session_state.secret_key}

        # total events
        stats_result=hx.get(url=f"{API_BASE_URL}/stats", headers=headers, timeout=5)

        if stats_result.status_code == 401:
            # false api key, invalidate the user 
            st.session_state.authenticated = False
            st.session_state.secret_key = ""
            st.error("Invalid Key. You have been logged out.")

            time.sleep(2) # Pause for 2 seconds so the user can read the error
            st.rerun()
        
        stats_result.raise_for_status()
        stats_data=stats_result.json()

    except hx.ConnectError :
        st.error("Critical Error, Cant Connect To Api")
        st.stop()

metric_cols = st.columns(2)

with metric_cols[0]:
    with st.container(border=True):
        st.metric(label="All-Time Events Tracked", value=stats_data.get("Total_Count", 0))

with metric_cols[1]:
    with st.container(border=True):
        st.metric(label="Workspace Tenant", value=stats_data.get("tenant", "Admin"))

st.divider()


# render page based on condition
# only calls that api

if current_page == "Overview":
    with st.container(border=True):
        st.subheader("Welcome to your Workspace")
        st.write("Use the navigation sidebar to explore your telemetry, traffic trends, and top URL performance.")

elif current_page == "Traffic Trends":
    with st.container(border=True):
        st.subheader(f"Traffic Trend (Last {days_filter} Days)")
        st.write("")
        with st.spinner("Fetching time-series data..."):

            # events per day
            time_res = hx.get(f"{API_BASE_URL}/events-per-day", headers=headers, params={"from_days": days_filter}, timeout=5.0)
            time_res.raise_for_status()
            raw_data = time_res.json()["data"]
            # take out the date wise data from the json

            if len(raw_data)>0:
                # if len=0 , no data for the specified date

                df=pd.DataFrame(raw_data)
                # dump the json into pandas so it can build a data frame
                #  data frame -> 2D structure (table)

                # now using plotly, plot the diagram
                # px.line() -> line chart
                fig=px.line(
                    data_frame=df,
                    x="date",
                    y="visits",
                    markers=True
                )
                
                fig.update_traces(line=dict(width=3), marker=dict(size=8))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                if len(df) <= 6:
                    fig.update_xaxes(type='category')

                # now use streamlit to display the chart on screen
                st.plotly_chart(fig, width="stretch")
            else:
                # if there is no data
                st.info(f"No traffic data found for the last {days_filter} days.")

elif current_page == "Top URLs":
    with st.container(border=True):
        st.subheader(f"Top {top_n_filter} URLs (Last {days_filter} Days)")
        st.write("")
        with st.spinner("Fetching ranking data..."):
            # top urls
            url_res = hx.get(f"{API_BASE_URL}/top-urls", headers=headers, params={"days_ago": days_filter, "top": top_n_filter}, timeout=5.0)
            url_res.raise_for_status()
            raw_url_data = url_res.json()["data"]
            # data = [{"url": and "visits":}]

            if(len(raw_url_data)>0):
                df=pd.DataFrame(raw_url_data)
                # a data frame of url and visits
            
            # reverse the order so the highest number is at the top of the chart
                df = df.sort_values(by="visits", ascending=True)

            # bar chart using plotly
                fig = px.bar(
                    data_frame=df, 
                    x="visits",       # no of visits -> length on bar
                    y="url",          # url is label for the bars
                    orientation="h",  # h -> horizontal
                    color="visits",   # auto color bar based on size
                    color_continuous_scale="Viridis" # Professional color scale
                )
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
                    yaxis=dict(showgrid=False),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
            # use streamlit to render chart
                st.plotly_chart(fig, width="stretch")
                
            else:
                st.info(f"No URLs found for the last {days_filter} days.") 

                