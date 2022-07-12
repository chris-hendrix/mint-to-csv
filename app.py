import pandas as pd
# import plotly.express as px
import streamlit as st
import data
import os


@st.cache
def get_data(file):
    return pd.read_csv(file)


settings = data.get_settings('settings.yaml')
data_path = settings['data_path']
account_values_history_file = os.path.join(data_path, data.ACCOUNT_VALUES_HISTORY_FILE)
account_values_history = get_data(account_values_history_file)

account_filter = [True] * account_values_history.shape[0]

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")
account_names = st.sidebar.multiselect(
    "Select accounts:",
    options=account_values_history["accountName"].unique()
)

if len(account_names) > 0:
    account_filter = account_filter & account_values_history['accountName'].isin(account_names)


account_values_history_filtered = account_values_history.loc[account_filter]

st.dataframe(account_values_history_filtered)
