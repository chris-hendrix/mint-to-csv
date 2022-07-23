import streamlit as st
from util.dftools import get_active_accounts, add_filters, add_filter


def get_multiselect(df, column, name=None):
    options = sorted(df[column].unique())
    return st.sidebar.multiselect(f'{name or column}: ', options=options)


class SideBar():
    def __init__(self, data, filters):
        transactions = data['transactions']
        account_values = data['accountValues']
        accounts = data['accounts']
        date_min, date_max = st.sidebar.slider(
            'Date:',
            transactions['date'].min(), transactions['date'].max(),
            (transactions['date'].min(), transactions['date'].max())
        )
        st.sidebar.header("Account:")
        account_names = get_active_accounts(account_values)
        account_types = get_multiselect(account_values, 'accountType')
        accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'accountType', account_types)
        account_names = get_multiselect(transactions, 'name')
        accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'name', account_names)

        st.sidebar.header("Category:")
        category_types = get_multiselect(transactions, 'categoryType')
        transactions = add_filter(transactions, 'categoryType', category_types)
        category_groups = get_multiselect(transactions, 'parentName')
        transactions = add_filter(transactions, 'parentName', category_groups)
        category_names = get_multiselect(transactions, 'categoryName')
        transactions = add_filter(transactions, 'categoryName', category_names)

        filters['dateMin'] = date_min
        filters['dateMax'] = date_max
        filters['accountNames'] = account_names
        filters['accountTypes'] = account_types
        filters['categoryTypes'] = category_types
        filters['categoryGroups'] = category_groups
        filters['categoryNames'] = category_names

        self.filters = filters
