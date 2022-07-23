import pandas as pd
import streamlit as st
from util.dftools import clean


class NetWorth():
    def __init__(self, data):
        account_values = data['accountValues']

        invest_values = account_values[account_values['accountType'] == 'Investment']
        invest_worths = pd.DataFrame(invest_values.groupby('date')[['value', 'deposits']].sum()).rename(columns={'value': 'invest'})
        invest_worths['gain'] = invest_worths['invest'] - invest_worths['deposits']
        account_worths = pd.DataFrame(account_values.groupby('date')[['value']].sum()).rename({'value': 'net'})
        account_worths = clean(pd.merge(account_worths, invest_worths, how='left', on='date'))

        # display charts
        st.header('Net Worth')
        st.line_chart(account_worths, use_container_width=True)
