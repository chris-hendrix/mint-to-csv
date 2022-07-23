import streamlit as st


class Debug():
    def __init__(self, data):
        transactions = data['transactions']
        account_values = data['accountValues']
        accounts = data['accounts']
        categories = data['categories']

        col1, col2 = st.columns(2)
        st.header('Transactions')
        st.dataframe(transactions[['date', 'name', 'description', 'amount', 'categoryName', 'userCategoryGroup', 'userCategoryType']])
        st.header('Categories')
        st.dataframe(categories)
        with col1:
            st.header('Accounts')
            st.dataframe(accounts[['name', 'accountValue']])
        with col2:
            st.header('Account Values')
            st.dataframe(account_values[['date', 'name', 'value', 'deposits']])
