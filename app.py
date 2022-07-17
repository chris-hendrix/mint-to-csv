import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype
# import plotly.express as px
import streamlit as st
import data
import os


@st.cache
def clean(df):
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    for col in df.columns:
        if is_bool_dtype(df[col]) or is_numeric_dtype(df[col]):
            continue
        df[col] = df[col].fillna('null')

    if 'accountType' in df.columns and 'name' in df.columns:
        df.loc[df['name'].str.contains('Wallet'), 'accountType'] = 'CryptoAccount'
        df['accountType'] = df['accountType'].str.replace('Account', '')

    return df


def add_filter(df, column, selected_values):
    if not selected_values or len(selected_values) == 0:
        return df
    df = df.loc[df[column].isin(selected_values)]
    return df


def add_filters(dfs, column, selected_values):
    filtered = []
    for df in dfs:
        filtered.append(add_filter(df, column, selected_values))
    return filtered


def get_active_accounts(account_values):
    active = account_values[['name', 'value']]
    active['value'] = active['value'].abs()
    active = pd.DataFrame(account_values.groupby('name')['value'].max()).reset_index()
    active = active.loc[active['value'] > 0]


def get_multiselect(df, column, name=None):
    options = sorted(df[column].unique())
    return st.sidebar.multiselect(f'{name or column}: ', options=options)


settings = data.get_settings('settings.yaml')
data_path = settings['data_path']


# get data
account_values_history_file = os.path.join(data_path, data.ACCOUNT_VALUES_HISTORY_FILE)
accounts_file = os.path.join(data_path, data.ACCOUNTS_FILE)
transactions_file = os.path.join(data_path, data.TRANSACTIONS_FILE)
account_values = clean(pd.read_csv(account_values_history_file))
accounts = clean(pd.read_csv(accounts_file))[['id', 'name', 'type', 'systemStatus', 'value']]
transactions = clean(pd.read_csv(transactions_file))

# rename columns
accounts = clean(accounts.rename(columns={'type': 'accountType', 'value': 'accountValue'}))

# joins
account_values = clean(pd.merge(account_values, accounts, how='left', on='name'))
transactions = clean(pd.merge(transactions, accounts, how='left', left_on='accountId', right_on='id'))

# sidebar filters
st.sidebar.header("Account:")
account_names = get_active_accounts(account_values)
account_types = get_multiselect(account_values, 'accountType')
accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'accountType', account_types)
account_names = get_multiselect(transactions, 'name')
accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'name', account_names)
account_worths = account_values.groupby('date')['value'].sum()

# main dashboard
st.dataframe(accounts[['name', 'accountValue']])
st.dataframe(transactions[['date', 'name', 'category', 'description', 'amount']])
st.dataframe(account_values[['date', 'name', 'value']])
st.line_chart(account_worths, use_container_width=True)
