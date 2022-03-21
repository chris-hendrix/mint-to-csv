
import os
import mintapi
import pandas as pd
import yaml
from datetime import date


def get_mint(email, password, wait_for_sync=False):

    # return if invalid credentials
    if not email or not password:
        return

    # get connection
    '''email=None, password=None, mfa_method=None, mfa_token=None,
    mfa_input_callback=None, intuit_account=None, headless=False, session_path=None,
    imap_account=None, imap_password=None, imap_server=None,
    imap_folder="INBOX", wait_for_sync=True, wait_for_sync_timeout=5 * 60,
    use_chromedriver_on_path=False, chromedriver_download_path=os.getcwd()):'''
    mint = mintapi.Mint(email, password, headless=False, wait_for_sync=wait_for_sync)
    return mint


def get_transactions(mint, data_path=None):
    # get transactions
    trans = mint.get_transactions(include_investment=True).copy()

    # convert datetime to date
    trans['date'] = pd.to_datetime(trans['date'])
    trans['date'] = trans['date'].dt.date

    # sort by date
    trans = trans.sort_values(by=['date'])

    # title case for categories
    trans['category'] = trans['category'].str.title()

    # renumber index
    trans = trans.reset_index(drop=True)
    trans.index = trans.index.rename('id')

    # export
    if data_path:
        trans.to_csv(os.join(data_path, 'transactions.csv'))

    return trans


def get_account_data(mint, data_path):

    # get account data
    account_data = pd.DataFrame.from_records(mint.get_accounts())
    trouble_cols = ['possibleLinkAccounts', 'closeDateInDate']
    account_data = account_data.drop(trouble_cols, axis=1, errors='ignore')
    account_data['date'] = pd.to_datetime('today')
    account_data['date'] = account_data['date'].dt.date

    # accounts
    accounts = account_data.drop_duplicates(subset=['accountName'], keep='last').reset_index(drop=True)

    # account values
    account_values = account_data[['accountName', 'value', 'date']]

    # export
    if data_path:
        accounts.to_csv(os.join(data_path, 'accounts.csv'))
        account_values.to_csv(os.join(data_path, f'account_values_{str(date.today())}.csv'))

    return accounts, account_values


def get_settings(settings_yaml):
    with open(settings_yaml, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return


if __name__ == "__main__":
    settings = get_settings('settings.yaml')
    print(settings)
    mint = get_mint(settings['email'], settings['password'])
    trans = get_transactions(mint, 'data')
    accounts, account_values = get_account_data(mint, 'data')
