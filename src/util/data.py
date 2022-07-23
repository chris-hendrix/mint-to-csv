
import os
import glob
import mintapi
import pandas as pd
import yaml
from datetime import date, datetime, timedelta

INDEX_NAME = 'id'

TRANSACTIONS_PATH = 'transactions'
ACCOUNTS_PATH = 'accounts'
ACCOUNT_VALUES_PATH = 'account_values'
ACCOUNT_VALUES_HISTORY_PATH = 'account_values_history'

RAW_TRANSACTIONS_FILE = f'{TRANSACTIONS_PATH}_raw.csv'
RAW_ACCOUNTS_FILE = f'{ACCOUNTS_PATH}_raw.csv'

TRANSACTIONS_FILE = f'{TRANSACTIONS_PATH}.csv'
ACCOUNTS_FILE = f'{ACCOUNTS_PATH}.csv'
ACCOUNT_VALUES_FILE = f'{ACCOUNT_VALUES_PATH}.csv'
ACCOUNT_VALUES_HISTORY_FILE = f'{ACCOUNT_VALUES_HISTORY_PATH}.csv'


def remove_unnamed_cols(data):
    data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
    data = data.drop(columns=['id'])
    return data


def get_settings(settings_yaml):
    with open(settings_yaml, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return


def get_files(path):
    files = glob.glob(path + '/*.csv')
    files = sorted(files, key=os.path.getmtime)
    files = [os.path.abspath(f) for f in files]
    return files


def get_mint(email, password, wait_for_sync=False):
    '''email=None, password=None, mfa_method=None, mfa_token=None,
    mfa_input_callback=None, intuit_account=None, headless=False, session_path=None,
    imap_account=None, imap_password=None, imap_server=None,
    imap_folder="INBOX", wait_for_sync=True, wait_for_sync_timeout=5 * 60,
    use_chromedriver_on_path=False, chromedriver_download_path=os.getcwd()):'''
    if not email or not password:
        return
    mint = mintapi.Mint(email, password, headless=False, wait_for_sync=wait_for_sync)
    return mint


def get_transactions(mint, data_path=None):
    '''limit=5000, include_investment=False, start_date=None,
        end_date=None, remove_pending=True, id=0,'''
    trans = mint.get_transaction_data(limit=100000, include_investment=True)
    trans = pd.DataFrame(trans)

    if data_path is not None:
        trans.to_csv(os.path.join(data_path, RAW_TRANSACTIONS_FILE))

    return trans


def get_accounts(mint, data_path):
    '''limit=5000,'''
    accounts = mint.get_account_data()
    accounts = pd.DataFrame(accounts)
    if data_path is not None:
        accounts.to_csv(os.path.join(data_path, RAW_ACCOUNTS_FILE))

    return accounts


def load_recent_data_from_csv(file, data_path, min_days_old=1):
    fullname = os.path.join(data_path, file)
    if not os.path.isfile(fullname):
        return None

    old_date = datetime.today() - timedelta(days=min_days_old)
    file_date_modified = datetime.fromtimestamp(os.path.getmtime(fullname))

    if file_date_modified < old_date:
        return None

    data = remove_unnamed_cols(pd.read_csv(fullname))

    return data


def format_transactions(trans, out_path=None):
    trans['date'] = pd.to_datetime(trans['date'])
    trans['date'] = trans['date'].dt.date
    trans = trans.sort_values(by=['date'])

    # renumber index
    trans = trans.reset_index(drop=True)
    trans.index = trans.index.rename('id')

    if out_path is not None:
        trans.to_csv(os.path.join(out_path, TRANSACTIONS_FILE))

    return trans


def format_accounts(accounts, data_path=None):
    trouble_cols = ['possibleLinkAccounts', 'closeDateInDate']
    accounts = accounts.drop(trouble_cols, axis=1, errors='ignore')
    accounts['date'] = pd.to_datetime('today')
    accounts['date'] = accounts['date'].dt.date

    accounts = accounts.drop_duplicates(subset=['name'], keep='last').reset_index(drop=True)

    account_values = accounts[['name', 'value', 'date']]

    if data_path is not None:
        accounts.to_csv(os.path.join(data_path, ACCOUNTS_FILE))
        account_values.to_csv(os.path.join(data_path, ACCOUNT_VALUES_FILE))

        account_values_path = os.path.join(data_path, ACCOUNT_VALUES_PATH)
        account_values.to_csv(os.path.join(account_values_path, ACCOUNT_VALUES_FILE.replace('.csv', f'_{str(date.today())}.csv')))

    return accounts, account_values


def append_transaction_history(trans, data_path):
    transactions_path = os.path.join(data_path, TRANSACTIONS_PATH)
    history_files = get_files(transactions_path)
    for history_file in history_files:
        history = pd.read_csv(history_file, parse_dates=['date'])
        trans = trans.append(history)
    return trans


def get_account_values_history(account_values, data_path):
    account_values_history_path = os.path.join(data_path, ACCOUNT_VALUES_HISTORY_PATH)
    history_files = get_files(account_values_history_path)
    latest_file = history_files[-1]
    account_values_history = pd.read_csv(latest_file, parse_dates=['date'])
    account_values_history = remove_unnamed_cols(account_values_history)
    account_values_history = account_values_history.append(account_values).reset_index(drop=True)

    account_values_history = account_values_history.reset_index(drop=True)
    account_values_history.index = account_values_history.index.rename('id')

    account_values_history.to_csv(os.path.join(account_values_history_path, ACCOUNT_VALUES_HISTORY_FILE.replace('.csv', f'_{str(date.today())}.csv')))

    if data_path is not None:
        accounts.to_csv(os.path.join(data_path, ACCOUNTS_FILE))
        account_values_history.to_csv(os.path.join(data_path, ACCOUNT_VALUES_HISTORY_FILE))

    return account_values_history


if __name__ == "__main__":
    settings = get_settings('settings.yaml')
    data_path = settings['data_path']
    account_values_path = os.path.join(data_path, ACCOUNT_VALUES_PATH)
    account_values_history_path = os.path.join(data_path, ACCOUNT_VALUES_HISTORY_PATH)
    mint = None

    # get transactions
    trans = load_recent_data_from_csv(RAW_TRANSACTIONS_FILE, data_path, min_days_old=1)
    if trans is None:
        mint = get_mint(settings['email'], settings['password'])
        trans = get_transactions(mint, data_path)
    trans = append_transaction_history(trans, data_path)
    trans = format_transactions(trans, data_path)

    # get accounts
    accounts = load_recent_data_from_csv(RAW_ACCOUNTS_FILE, data_path, min_days_old=1)
    if accounts is None:
        mint = get_mint(settings['email'], settings['password']) if mint is None else mint
        accounts = get_accounts(mint, data_path)
    accounts, account_values = format_accounts(accounts, data_path,)
    account_values_history = get_account_values_history(account_values, data_path)
