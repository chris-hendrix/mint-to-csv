import os
import pandas as pd
import util.data as data
from util.dftools import add_filters, add_filter, add_date_filter, clean, get_categories, set_deposits, set_transaction_categories
from components.sidebar import SideBar
from components.networth import NetWorth
from components.spending import Spending
from components.debug import Debug


class App:
    def __init__(self, data_path):

        self.data = {
            'accountValues': None,
            'accounts': None,
            'categories': None,
            'transactions': None
        }
        self.filters = {
            'dateMin': None,
            'dateMax': None,
            'accountNames': None,
            'accountTypes': None,
            'categoryType': None,
            'categoryNames': None,
            'categoryGroups': None,
        }
        self.get_data(data_path)
        self.sidebar = SideBar(self.data, self.filters)
        self.filter_data()
        self.networth = NetWorth(self.data)
        self.spending = Spending(self.data)
        self.debug = Debug(self.data)

    def get_data(self, data_path):
        print(self.filters)

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

        # set data
        self.data = {
            'accountValues': account_values,
            'accounts': accounts,
            'categories': categories,
            'transactions': transactions
        }

    def filter_data(self):
        transactions = self.data['transactions']
        account_values = self.data['accountValues']
        accounts = self.data['accounts']

        # add filters
        transactions = add_date_filter(transactions, self.filters['dateMin'], self.filters['dateMax'])
        account_values = add_date_filter(account_values, self.filters['dateMin'], self.filters['dateMax'])
        accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'accountType', self.filters['accountTypes'])
        accounts, account_values, transactions = add_filters([accounts, account_values, transactions], 'name', self.filters['accountNames'])
        transactions = add_filter(transactions, 'categoryType', self.filters['categoryTypes'])
        transactions = add_filter(transactions, 'parentName', self.filters['categoryGroups'])
        transactions = add_filter(transactions, 'categoryName', self.filters['categoryNames'])
        self.data['accountValues'] = account_values
        self.data['accounts'] = accounts
        self.data['transactions'] = transactions


if __name__ == "__main__":
    settings = data.get_settings('../settings.yaml')
    data_path = settings['data_path']
    app = App(data_path)
