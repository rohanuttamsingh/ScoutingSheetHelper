import json
from time import sleep

import gspread
import requests
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials


class Spreadsheet:

    # comment out all but one of these depending on which spreadsheet being used
    # URL = 'https://docs.google.com/spreadsheets/d/1WhExw_ReHnyPQYXl0p-kT6jYXpZW5w8-cq2ffK7niOs' # Sample Deep Space Scouting Sheet Machine
    # URL = 'https://docs.google.om/spreadsheets/d/1lOTML4TgNqv5OKUJU32keWu62__T9cFT3IL52kmPbKk' # Bethesda Week 2 Scouting Sheet Machine
    # URL = 'https://docs.google.com/spreadsheets/d/1C8hjCqMZmacyUe3SlRgW4o4HGqTRFozviK4WZ6Mu4yc' # Week 0 Scouting Sheet Machine
    # URL = 'https://docs.google.com/spreadsheets/d/1uYb9n_2IaGSRvOPZcuE59eUQjinaTSIN1SKqTQ6z2lQ' # Dickinson Center Week 0 Scouting Sheet Machine
    # URL = 'https://docs.google.com/spreadsheets/d/1_8tFjgxjGVA0__1BLkMV-ookfPLrnGDE8gZj6pQc1_k' # Centurion-KnightKrawler Week 0 Scouting Sheet Machine
    # URL = 'https://docs.google.com/spreadsheets/d/1Ftzcn5u5axYUkob1MXI8wV1KAD-8qjGkywqQjP4_AMo' # Haymarket Week 1 Scouting Sheet Machine
    # URL = 'https://docs.google.com/spreadsheets/d/1fRm4nZIT457zIpW5cyZrIvR0gSGt6oEcphVYiaH6eK8' # Owings Mills Week 3 Scouting Sheet Machine
    URL = 'https://docs.google.com/spreadsheets/d/1y8xtKJftg1mDbhfcmISWkyi4MgmSauveD9BY2bPNUCo/edit#gid=168604214' # CHCMP Scouting Sheet Machine

    # google sheets  setup
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret_gsheets.json', scope)
    client = gspread.authorize(creds)

    # google sheets document
    sheet = client.open_by_url(URL)
    
    # individual worksheets of google sheets document
    key_worksheet = sheet.worksheet('Key')
    teams_worksheet = sheet.worksheet('Teams')
    sample_team_worksheet = sheet.worksheet('Sample Team')
    schedule_worksheet = sheet.worksheet('Schedule')
    team_data_worksheet = sheet.worksheet('Team Data')

    # setting event key to value in A1 of Key worksheet
    event_key = key_worksheet.cell(1, 1).value

    # 2537 cell format
    format_2537 = CellFormat(backgroundColor=Color(.148, .98, .216)) # 25fa37 converted to rgb out of 1

    # tba setup
    tba_session = requests.Session()
    BASE_URL = 'https://www.thebluealliance.com/api/v3'

    # tba credentials setup
    with open('client_secret_tba.json') as json_file:
        data = json.load(json_file)
        tba_auth_key = data['tba_auth_key']

    def __init__(self):
        """All TBA requests will have authentication key in header"""
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
                    sleep(1.01)
                elif col != '':
                    copy_to.update_cell(i, j, col)
                    sleep(1.01) # Quota is 100 requests per 100s, this does 100 requests per 101s
                j += 1
            i += 1
            j = 1

    def copy_sample_to_team_sheets(self):
        """Copies sample sheet format to every team sheet"""
        sample_sheet = self.get_sample_sheet()
        for team in self.teams_worksheet.col_values(1):
            self.copy_sheet(sample_sheet, self.sheet.worksheet(team), team)

    def get_color_schedule(self, event, color):
        """Returns match schedule of specified color alliance in list
        
        event: event key of intended competition (e.g. 2018vahay)
        color: color of desired alliance schedule (e.g. red or blue)
        """
        # event schedules get updated to elims event schedules once elims are reached
        # only elims schedule accessible in finished events
        schedule = []
        event_list = self.tba_session.get(self.BASE_URL + '/event/%s/matches/simple' % event).json() # list of dicts
        for match in event_list:
            schedule.append(match['alliances'][color]['team_keys'])
        for alliance in schedule:
            for i in range(len(alliance)):
                alliance[i] = alliance[i][3:]
                # trims 'frc' from beginning of every team number
        return schedule

    def fill_schedule(self, event):
        """Auto fills Schedule worksheet with schedule
        
        event: event key of intended competition (e.g. 2018vahay)
        """
        red_schedule = self.get_color_schedule(event, 'red')
        blue_schedule = self.get_color_schedule(event, 'blue')
        # updates num_matches to the correct number of matches and fill column 1 of spreadsheet with match number
        num_matches = 1
        for match in range(len(red_schedule)):
            self.schedule_worksheet.update_cell(match + 1, 1, match + 1)
            num_matches += 1
            sleep(1.01)
        for i in range(num_matches):
            for j in range(3):
                self.schedule_worksheet.update_cell(i + 1, j + 2, red_schedule[i][j])
                sleep(1.01)
                self.schedule_worksheet.update_cell(i + 1, j + 5, blue_schedule[i][j])
                sleep(1.01)

    def get_team_metrics_from_event(self, event):
        """Returns OPRs, DPRs, and CCWMs of all teams at event in dictionary of dictionaries

        event: event key of intended competition (e.g. 2018vahay)
        """
        return self.tba_session.get(self.BASE_URL + '/event/%s/oprs' % event).json()
    
    def fill_team_data(self, event):
        """Auto fills Team Data worksheet with teams and their corresponding OPR, DPR, and CCWM

        event: event key if intended competition (e.g. 2018vahay)
        """
        teams = self.get_teams_from_event(event)
        metrics = self.get_team_metrics_from_event(event)
        row = 2
        team_col, opr_col, dpr_col, ccwm_col = 1, 2, 3, 4
        for team in teams:
            self.team_data_worksheet.update_cell(row, team_col, team)
            sleep(1.01)
            self.team_data_worksheet.update_cell(row, opr_col, metrics['oprs']['frc' + team])
            sleep(1.01)
            self.team_data_worksheet.update_cell(row, dpr_col, metrics['dprs']['frc' + team])
            sleep(1.01)
            self.team_data_worksheet.update_cell(row, ccwm_col, metrics['ccwms']['frc' + team])
            sleep(1.01)
            row += 1

    def get_predictions_from_event(self, event):
        return self.tba_session.get(self.BASE_URL + '/event/%s/predictions' % event).json()

    def format_cells_in_schedule(self):
        cells_2537_raw = self.schedule_worksheet.findall('2537')
        cells_2537 = []
        for cell in cells_2537_raw:
            cells_2537.append([cell.col + 64, cell.row]) # add 64 to column to match ascii character decimals
        for cell in cells_2537:
            b = bytes(str(cell[0]), 'utf8')
            ascii_char = b.decode('ascii')
            cell[0] = chr(int(ascii_char))
        for i in range(len(cells_2537)):
            format_cell_range(self.schedule_worksheet, '%s%i:%s%i' % (cells_2537[i][0], cells_2537[i][1], cells_2537[i][0], cells_2537[i][1]), self.format_2537)


    def main(self):
        self.fill_teams(self.teams_worksheet, self.event_key)
        self.create_team_sheets()
        # self.delete_team_sheets()
        # print(self.get_sample_sheet())
        # self.copy_sheet(self.get_sample_sheet(), self.sheet.worksheet('1086'), 1086) # testing on single sheet
        # print(len(self.get_sample_sheet()))
        self.copy_sample_to_team_sheets()
        # print(self.get_color_schedule(self.event_key, 'red'))
        self.fill_schedule(self.event_key)
        self.fill_team_data(self.event_key)
        # print(self.get_team_metrics_from_event(self.event_key))
        # print(self.get_predictions_from_event(self.event_key))
        self.format_cells_in_schedule()


if __name__ == '__main__':
    spreadsheet = Spreadsheet()
    spreadsheet.main()
