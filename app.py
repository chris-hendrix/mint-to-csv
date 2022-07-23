import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype
# import plotly.express as px
import streamlit as st
import data
import os
import json


def clean(df):
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date

    for col in df.columns:
        if not is_bool_dtype(df[col]) and not is_numeric_dtype(df[col]):
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


def add_date_filter(df, date_0, date_1, column='date'):
    if not date_0 or not date_1:
        return df
    df = df.loc[(df[column] >= date_0) & (df[column] <= date_1)]
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


def get_deposit(transactions, row, start=None):
    if row['accountType'] != 'Investment':
        return 0

    mask = (
        (transactions['name'] == row['name']) &
        (transactions['date'] <= row['date']) &
        (transactions['categoryName'].isin(['Deposit', 'Withdrawal']))
    )
    if start:
        mask = (mask) & (transactions['date'] >= start)
    filtered = transactions.loc[mask]
    return filtered['amount'].sum()


def set_deposits(account_values, transactions):
    inv_transactions = transactions[transactions['accountType'] == 'Investment']
    account_values['deposits'] = account_values.apply(lambda row: get_deposit(inv_transactions, row), axis=1)
    return account_values


def cell_to_dict(cell):
    cell = str(cell.replace('"', '').replace("'", '"'))
    return json.loads(cell)


def get_categories(transactions):
    categories = sorted(transactions['category'].unique())
    cat_data = [cell_to_dict(c) for c in categories if '{' in c]
    categories = pd.DataFrame.from_dict(cat_data)
    categories = clean(categories.rename(columns={'name': 'categoryName'}))
    categories['parentName'] = categories.apply(lambda row: row['categoryName'] if row['parentName'] == 'Root' else row['parentName'], axis=1)
    return categories


def set_transaction_categories(transactions, categories):
    transactions['categoryName'] = transactions['category'].apply(lambda cell: cell_to_dict(cell)['name'] if '{' in cell else cell)
    transactions = clean(pd.merge(transactions, categories, how='left', on='categoryName'))
    return transactions


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
categories = get_categories(transactions)

# rename columns
accounts = clean(accounts.rename(columns={'type': 'accountType', 'value': 'accountValue'}))

# joins
account_values = clean(pd.merge(account_values, accounts, how='left', on='name'))
transactions = clean(pd.merge(transactions, accounts, how='left', left_on='accountId', right_on='id'))

# add columns
transactions = set_transaction_categories(transactions, categories)
account_values = set_deposits(account_values, transactions)

# sidebar filters
date_0, date_1 = st.sidebar.slider(
    'Date:',
    transactions['date'].min(), transactions['date'].max(),
    (transactions['date'].min(), transactions['date'].max())
)
st.sidebar.header("Account:")
transactions = add_date_filter(transactions, date_0, date_1)
account_values = add_date_filter(account_values, date_0, date_1)
account_names = get_active_accounts(account_values)
account_types = get_multiselect(account_values, 'accountType')
accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'accountType', account_types)
account_names = get_multiselect(transactions, 'name')
accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'name', account_names)

# net and investment worths
invest_values = account_values[account_values['accountType'] == 'Investment']
invest_worths = pd.DataFrame(invest_values.groupby('date')[['value', 'deposits']].sum()).rename(columns={'value': 'invest'})
invest_worths['gain'] = invest_worths['invest'] - invest_worths['deposits']
account_worths = pd.DataFrame(account_values.groupby('date')[['value']].sum()).rename({'value': 'net'})
account_worths = clean(pd.merge(account_worths, invest_worths, how='left', on='date'))

# display sidebar
st.sidebar.header("Category:")
parent_names = get_multiselect(transactions, 'parentName')
transactions = add_filter(transactions, 'parentName', parent_names)
category_names = get_multiselect(transactions, 'categoryName')
transactions = add_filter(transactions, 'categoryName', category_names)


# display tables
st.header('Transactions')
st.dataframe(transactions[['date', 'name', 'description', 'amount', 'categoryName', 'parentName']])
st.header('Accounts')
st.dataframe(accounts[['name', 'accountValue']])
st.header('Account Values')
st.dataframe(account_values[['date', 'name', 'value', 'deposits']])

# display charts
st.header('Net Worth')
st.line_chart(account_worths, use_container_width=True)
