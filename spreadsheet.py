import gspread, requests, json
from oauth2client.service_account import ServiceAccountCredentials

class Spreadsheet:
        
    # gsheets credentials setup
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret_gsheets.json', scope)
    client = gspread.authorize(creds)

    # tabs of google sheet
    key_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs').worksheet('Key')
    teams_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs').worksheet('Teams')

    # tba setup
    session = requests.Session()
    BASE_URL = 'https://www.thebluealliance.com/api/v3'

    # event key of intended competition
    event_key = ''

    # tba credentials setup
    with open('client_secret_tba.json') as json_file:
        data = json.load(json_file)
        tba_auth_key = data['tba_auth_key']

    # setting event key to value in spreadsheet
    event_key = key_sheet.cell(1, 1).value

    def __init__(self):
        # lets us pass tba auth key in header to each individual request with only 1 line
        self.session.headers.update({'X-TBA-Auth-Key': self.tba_auth_key})

    def getTeamsFromEvent(self):
        return self.session.get(self.BASE_URL + '/event/%s/teams/keys' % self.event_key).json()
    
    def main(self):
        print(self.getTeamsFromEvent())

if __name__ == '__main__':
    spreadsheet = Spreadsheet()
    spreadsheet.main()