import pandas as pd
# import plotly.express as px
import streamlit as st
import data
import os


@st.cache
def get_data(file, columns=None):
    data = pd.read_csv(file)
    if columns:
        data = data[columns]
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'])

    print(data.head())
    return data


def add_filter(data, column, selected_values):
    if not selected_values or len(selected_values) == 0:
        return data
    if isinstance(data, list):
        for df in data:
            df = df.loc[df[column].isin(selected_values)]
    else:
        data = data.loc[data[column].isin(selected_values)]
    return data


settings = data.get_settings('settings.yaml')
data_path = settings['data_path']


# get data
account_values_history_file = os.path.join(data_path, data.ACCOUNT_VALUES_HISTORY_FILE)
accounts_file = os.path.join(data_path, data.ACCOUNTS_FILE)
transactions_file = os.path.join(data_path, data.TRANSACTIONS_FILE)
account_values = get_data(account_values_history_file)
accounts = get_data(accounts_file, columns=['id', 'name', 'type', 'systemStatus'])
transactions = get_data(transactions_file)

# joins
account_values = pd.merge(account_values, accounts, how='left', on='name')
account_values = pd.merge(transactions, accounts, how='left', left_on='accountId', right_on='id')

# sidebar
st.sidebar.header("Account:")
account_names = st.sidebar.multiselect('Account name:', options=account_values['name'].unique())
account_types = st.sidebar.multiselect('Account type:', options=account_values['type'].unique())

add_filter([account_values, transactions], 'name', account_names)
add_filter([account_values, transactions], 'type', account_types)
account_worths = account_values.groupby('date')['value'].sum()


# main page
st.dataframe(transactions)
st.dataframe(account_values)

st.line_chart(account_worths, use_container_width=True)
