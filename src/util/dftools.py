import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype
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


def cell_to_dict(cell):
    cell = str(cell.replace('"', '').replace("'", '"'))
    return json.loads(cell)


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
