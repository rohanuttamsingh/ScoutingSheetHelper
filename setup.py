import gspread, requests, json
from oauth2client.service_account import ServiceAccountCredentials

class Setup:

    # gsheets credentials setup
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret_gsheets.json', scope)
    client = gspread.authorize(creds)

    # tabs of google sheet
    key_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs/edit').sheet1
    teams_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs/edit').sheet2

    # tba setup
    base_url = 'www.thebluealliance.com/api/v3'
    key = ''

    def __init__(self):
        # tba credentials setup
        with open('client_secret_tba.json') as json_file:
            data = json.load(json_file)
            self.key = data['tba_auth_key']