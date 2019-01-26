import json
from time import sleep

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials


class Spreadsheet:
    
    # google sheets credentials setup
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret_gsheets.json', scope)
    client = gspread.authorize(creds)

    # tabs of google sheet
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs')
    key_worksheet = sheet.worksheet('Key')
    teams_worksheet = sheet.worksheet('Teams')
    sample_team_worksheet = sheet.worksheet('Sample Team')

    # tba setup
    tba_session = requests.Session()
    BASE_URL = 'https://www.thebluealliance.com/api/v3'

    # event key of intended competition
    event_key = ''

    # tba credentials setup
    with open('client_secret_tba.json') as json_file:
        data = json.load(json_file)
        tba_auth_key = data['tba_auth_key']

    # setting event key to value in spreadsheet
    event_key = key_worksheet.cell(1, 1).value

    def __init__(self):
        """All requests will have authentication key in header"""
        self.tba_session.headers.update({'X-TBA-Auth-Key': self.tba_auth_key})

    def get_teams_from_event(self, event):
        """Returns all team keys from event in a list
        
        event: event key of intended competition (e.g. 2018vahay)
        """
        teams_raw = self.tba_session.get(self.BASE_URL + '/event/%s/teams/keys' % event).json()
        teams = []
        for team_raw in teams_raw:
            teams.append(team_raw[3:])
        return teams

    def fill_teams(self, sheet, event):
        """Fills first column of specified sheet with all teams from specified sheet
        
        sheet: intended google sheet
        event: event key of intended competition (e.g. 2018vahay)
        """
        column = []
        for team in self.get_teams_from_event(event):
            column.append(team)
        for index in range(0, len(column)):
            sheet.update_cell(index + 1, 1, column[index])

    def create_team_sheets(self):
        """Creates a scouting sheet for each team in competition

        event: event key of intended competition (e.g. 2018 vahay)
        """
        teams = self.teams_worksheet.col_values(1)
        for team in teams:
            self.sheet.add_worksheet(team, self.sample_team_worksheet.row_count, self.sample_team_worksheet.col_count)


    def delete_team_sheets(self):
        """Deletes all individual team worksheets

        Used for testing
        """
        teams = self.teams_worksheet.col_values(1)
        for team in teams:
            self.sheet.del_worksheet(self.sheet.worksheet(team))

    def get_sample_sheet(self):
        """Returns the sample team sheet in 2D list format [row][column]"""
        sample_sheet = []
        for row in range(1, self.sample_team_worksheet.row_count + 1):
            sample_sheet.append(self.sample_team_worksheet.row_values(row, value_render_option='FORMULA'))
        return sample_sheet

    def copy_sheet(self, copy_from, copy_to, team_num):
        """Copies every element from a list of values to a specified sheet

        copy_from: list from which values are copied
        copy_to: sheet to which values are copied
        """
        i, j = 1, 1
        for row in copy_from:
            for col in row:
                if col == 'Team #':
                    copy_to.update_cell(i, j, team_num)
                    sleep(1.1)
                elif col != '':
                    copy_to.update_cell(i, j, col)
                    sleep(1.1) # Quota is 100 requests per 100 s, this does 100 requests per 110 s
                j += 1
            i += 1
            j = 1

    def copy_sample_to_team_sheets(self):
        """Copies sample sheet format to every team sheet"""
        for team in self.teams_worksheet.col_values(1):
            self.copy_sheet(self.get_sample_sheet(), self.sheet.worksheet(team), team)

    def get_blue_schedule(self, event):
        # event schedules get updated to elims event schedules once elims are reached
        # only elims schedule accessible in finished events
        blue_schedule = []
        event_list = self.tba_session.get(self.BASE_URL + '/event/%s/matches/simple' % event).json() # list of dicts
        for match in event_list:
            blue_schedule.append(match['alliances']['blue'])
        for quals_alliances in schedule:
            for i in range(len(quals_alliances)):
                quals_alliances[i] = quals_alliances[i][3:]
                # Trims 'frc' from beginning of every team number
        return blue_schedule

    def main(self):
        # self.fill_teams(self.teams_worksheet, self.event_key)
        # self.create_team_sheets()
        # self.delete_team_sheets()
        # print(self.get_sample_sheet())
        # self.copy_sheet(self.get_sample_sheet(), self.sheet.worksheet('1137')) # testing on single sheet
        # print(len(self.get_sample_sheet()))
        # self.copy_sample_to_team_sheets()
        print(self.get_blue_schedule(self.event_key))


if __name__ == '__main__':
    spreadsheet = Spreadsheet()
    spreadsheet.main()
