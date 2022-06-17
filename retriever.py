
import os
import mintapi
import pandas as pd
import yaml
from datetime import date, datetime, timedelta

RAW_TRANSACTIONS_FILE = 'transactions_raw.csv'
RAW_ACCOUNTS_FILE = 'accounts_raw.csv'
TRANSACTIONS_FILE = 'transactions.csv'
ACCOUNTS_FILE = 'accounts.csv'
ACCOUNT_VALUES_FILE = 'account_values.csv'


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
    '''
        limit=5000,
        include_investment=False,
        start_date=None,
        end_date=None,
        remove_pending=True,
        id=0,
    '''
    trans = mint.get_transaction_data(limit=100000, include_investment=True)
    trans = pd.DataFrame(trans)

    if data_path is not None:
        trans.to_csv(os.path.join(data_path, RAW_TRANSACTIONS_FILE))

    return trans


def get_accounts(mint, data_path):
    '''
    limit=5000,
    '''
    accounts = mint.get_account_data()
    accounts = pd.DataFrame(accounts)
    if data_path is not None:
        accounts.to_csv(os.path.join(data_path, RAW_ACCOUNTS_FILE))

    return accounts


def load_data_from_csv(file, data_path, min_days_old=1):
    fullname = os.path.join(data_path, file)
    if not os.path.isfile(fullname):
        return None

    old_date = datetime.today() - timedelta(days=min_days_old)
    file_date_modified = datetime.fromtimestamp(os.path.getmtime(fullname))

    if file_date_modified < old_date:
        return None

    return pd.read_csv(fullname)


def format_transactions(trans, out_path=None):
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
    if out_path is not None:
        trans.to_csv(os.path.join(out_path, TRANSACTIONS_FILE))

    return trans


def format_accounts(accounts, out_path=None):

    # get account data
    trouble_cols = ['possibleLinkAccounts', 'closeDateInDate']
    accounts = accounts.drop(trouble_cols, axis=1, errors='ignore')
    accounts['date'] = pd.to_datetime('today')
    accounts['date'] = accounts['date'].dt.date

    # accounts
    accounts = accounts.drop_duplicates(subset=['name'], keep='last').reset_index(drop=True)

    # account values
    account_values = accounts[['name', 'value', 'date']]

    # export
    if out_path is not None:
        accounts.to_csv(os.path.join(data_path, ACCOUNTS_FILE))
        account_values.to_csv(os.path.join(data_path, f'account_values_{str(date.today())}.csv'))

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
    data_path = ''
    mint = None

    trans = load_data_from_csv(RAW_TRANSACTIONS_FILE, data_path)
    if trans is None:
        mint = get_mint(settings['email'], settings['password'])
        trans = get_transactions(mint, data_path)
    trans = format_transactions(trans, data_path)

    accounts = load_data_from_csv(RAW_ACCOUNTS_FILE, data_path)
    if accounts is None:
        mint = get_mint(settings['email'], settings['password']) if mint is None else mint
        accounts = get_accounts(mint, data_path)
    accounts, account_values = format_accounts(accounts, data_path)
    print(accounts.info())
