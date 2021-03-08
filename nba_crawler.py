import requests
from bs4 import BeautifulSoup
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opt = Options()
opt.add_argument('--headless')
opt.add_argument('--disable-gpu')

crawl_basic_url = "https://www.basketball-reference.com"
crawl_player_url = "https://www.basketball-reference.com/players/{}/"
PLAYER_BASIC_PROFILE_CSV = 'info/player_stat.csv'
PLAYER_PERFORMANCE_CSV = 'info/player_details.csv'
TEAM_BASIC_INFO_CSV = 'info/team_basic.csv'
TEAM_SEASONAL_STATS_CSV = 'info/team_stats.csv'
PLAYER_SALARIES_CSV = 'info/player_salaries.csv'
PLAYER_3P_LEADERS_CSV = 'info/player_3p_leaders_data.csv'


class NbaCrawl:
    def crawl_player_basic(self):
        header = ['url', 'name', 'from', 'to', 'pos', 'ht', 'wt', 'dob', 'college', 'active', 'recruiting_rank',
                  'draft_team', 'experience(year)']

        with open(PLAYER_BASIC_PROFILE_CSV, 'w', encoding="utf-8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)
        list = [chr(y) for y in range(97, 123)]
        # A_Z
        return_urls = []
        for i in range(0, 26):
            # crawl  player basic profile
            url = crawl_player_url.format(list[i])
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            template_url = '/players/{}/[^\.]*.html'.format(list[i])
            urls = soup.find_all(href=re.compile(template_url))

            players_profiles, return_urls = self.crawl_player_basic_pages(urls, return_urls)
            with open(PLAYER_BASIC_PROFILE_CSV, 'a', encoding="utf-8") as f:
                a = csv.writer(f, delimiter=',')
                a.writerows(players_profiles)
        return return_urls

    def crawl_player_basic_pages(self, urls, return_urls):
        players_profiles = []
        for player_url in urls:
            player_profiles = [player_url.get('href')]
            tr = player_url.parent.parent
            active = False
            if player_url.parent.name == 'strong':
                tr = player_url.parent.parent.parent
                active = True
            td = tr.find_all('td')
            if td:
                # name
                th = tr.find('th')
                player_profiles.append(th.text)
                # other
                for data in td:
                    player_profiles.append(data.text)
                player_profiles.append(active)
                # set the range of (2010-2020)
                if int(player_profiles[2]) < 2020 and int(player_profiles[3]) > 2009:
                    return_urls.append(player_url.get('href'))
                    player_profiles = self.crawl_player_details(player_url.get('href'), player_profiles)
                    players_profiles.append(player_profiles)
                    print(player_profiles)
        return players_profiles, return_urls

    def crawl_player_details(self, url, player_profiles):
        url_player = crawl_basic_url + url
        response = requests.get(url_player)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find("div", id="meta")
        pat = re.compile('(/teams/[a-zA-Z]+/draft.html)')
        if rows.find("strong", text="Recruiting Rank: "):
            rank = rows.find("strong", text="Recruiting Rank: ").parent.text
            rank = rank.split("(")[1]
            rank = rank.split(")")[0]
            player_profiles.append(rank)
        else:
            player_profiles.append('None')
        if rows.find(href=pat):
            draft = rows.find(href=pat).text
            player_profiles.append(draft)
        else:
            player_profiles.append('None')
        if rows.find("strong", text="Experience:"):
            experience = rows.find("strong", text="Experience:").nextSibling
            experience = experience[1:]
            experience = experience[:-10]
            player_profiles.append(experience)
        else:
            if rows.find("strong", text="Career Length:"):
                experience = rows.find("strong", text="Career Length:").nextSibling
                experience = experience[1:]
                experience = experience[:-10]
                if experience == '' or experience == ' ' or experience == '  ':
                    player_profiles.append('1')
                else:
                    player_profiles.append(experience)
            else:
                player_profiles.append('1')
        return player_profiles

    def crawl_player_salaries(self, urls):
        header = ['player_url', 'season', 'team', 'lg', 'salary']
        with open(PLAYER_SALARIES_CSV, 'w') as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)
        for url in urls:
            real_url = crawl_basic_url + url
            driver = webdriver.Chrome(chrome_options=opt)
            driver.get(real_url)
            try:
                table_tr_list = driver.find_element_by_id("all_salaries").find_element_by_tag_name(
                    "tbody").find_elements_by_tag_name("tr")
                table_list = []
                for tr in table_tr_list:  # 遍历每一个tr
                    # 将每一个tr的数据根据td查询出来，返回结果为list对象
                    table_th = tr.find_element_by_tag_name("th").text
                    table_td_list = tr.find_elements_by_tag_name("td")
                    row_list = [url, table_th]
                    # print(table_td_list)
                    for td in table_td_list:  # 遍历每一个td
                        row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                    table_list.append(row_list)
                print(table_list)
                with open(PLAYER_SALARIES_CSV, 'a', encoding="utf-8") as f:
                    a = csv.writer(f, delimiter=',')
                    a.writerows(table_list)
            except:
                print("crash")

    def crawl_players_performance_stats(self, urls):
        header = ['player_url', 'Season', 'Age', 'Tm', 'Tm_url', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P',
                  '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL',
                  'BLK', 'TOV', 'PF', 'PTS']

        with open(PLAYER_PERFORMANCE_CSV, 'w', encoding="utf-8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)

        for link in urls:
            # crawl https://www.basketball-reference.com/players/{a to z}/{player_code}.html
            url = crawl_basic_url + link

            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('caption', text="Per Game Table").parent
            rows = table.find("tbody").find_all('tr')
            players_stats = []
            for row in rows:
                if row.find('th'):
                    season = row.find('th').text
                    items = row.find_all('td')
                    player_stats = [url, season]
                    i = 0
                    for item in items:
                        if i == 2:
                            if item.find('a'):
                                target_url = re.compile('(/teams/[a-zA-Z]+/)[\d\d\d\d.html]?')
                                if row.find(href=target_url):
                                    team_url = row.find(href=target_url).get('href')
                                    player_stats.append(team_url)
                                else:
                                    team_url = ''
                                    player_stats.append(team_url)
                            else:
                                player_stats.append('')
                        player_stats.append(item.text)
                        i += 1
                    print(player_stats)
                    players_stats.append(player_stats)
                with open(PLAYER_PERFORMANCE_CSV, 'a', encoding="utf-8") as f:
                    a = csv.writer(f, delimiter=',')
                    a.writerows(players_stats)

    def crawl_team_basic(self):
        header = ['name', 'url', 'lg', 'from', 'to', 'years', 'games', 'wins', 'losses', 'wlpercent', 'playoffs',
                  'div', 'conf', 'champ', 'location', 'seasons_played', 'record']
        with open(TEAM_BASIC_INFO_CSV, 'a', encoding="utf-8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)
        url_team = "https://www.basketball-reference.com/teams/"
        response = requests.get(url_team)
        soup = BeautifulSoup(response.text, 'html.parser')
        team = soup.find('table', id="teams_active")
        rows = team.find_all('tr', class_='full_table')
        teams_data = []
        return_urls = []
        for row in rows:
            if row.find('th'):
                if row.find('a'):
                    name = row.find('th').text
                    team_url = row.find('th').a.get('href')
                    return_urls.append(team_url)
                    data = row.find_all('td')
                    team_data = [name, team_url]
                    for d in data:
                        team_data.append(d.text)
                    team_data = self.crawl_team_detail(team_url, team_data)
                    print(team_data)
                    teams_data.append(team_data)
                    with open(TEAM_BASIC_INFO_CSV, 'a', encoding="utf-8") as f:
                        a = csv.writer(f, delimiter=',')
                        a.writerows(teams_data)

        return return_urls

    def crawl_team_detail(self, team_url, team_data):
        real_team_url = crawl_basic_url + team_url
        response = requests.get(real_team_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find("div", id="info")
        if rows.find("strong", text="Location:"):
            location = rows.find("strong", text="Location:").parent.text
            location = location.split("\n")[2]
            location = location[2:]
            team_data.append(location)
        else:
            team_data.append('')
        if rows.find("strong", text="Seasons:"):
            seasons = rows.find("strong", text="Seasons:").parent.text
            seasons = seasons.split("\n")[3]
            seasons = seasons.split(';')[0]
            seasons = seasons[4:]

            team_data.append(seasons)
        else:
            team_data.append('')
        if rows.find("strong", text="Record:"):
            records = rows.find("strong", text="Record:").parent.text
            records = records.split("\n")[2]
            records = records[2:]
            team_data.append(records)
        else:
            team_data.append('')
        return team_data

    def crawl_team_stats(self, urls):
        header = ['url', 'Season', 'Lg', 'Team', 'W', 'L', 'W/L%', 'Finish', 'SRS', 'Pace', 'Rel_Pace', 'ORtg',
                  'Rel_ORtg', 'DRtg', 'Rel_DRtg', 'Playoffs', 'Coaches', 'Top_WS']
        with open(TEAM_SEASONAL_STATS_CSV, 'w', encoding="utf=8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)
        all_season = []
        for url in urls:
            response = requests.get("https://www.basketball-reference.com" + url)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('tbody')
            rows = table.find_all("tr")
            for row in rows:
                season_period = row.find('th').text
                period = season_period.split("-")[0]
                if int(period) < 2009 or int(period) >= 2020:
                    continue
                else:
                    season_period = row.find('th').text
                    season_period_url = row.find('th').a.get('href')
                    data = row.find_all('td')
                    season_data = [season_period_url, season_period]
                    for d in data:
                        season_data.append(d.text)
                    print(season_data)
                    all_season.append(season_data)
            with open(TEAM_SEASONAL_STATS_CSV, 'a', encoding="utf=8") as f:
                a = csv.writer(f, delimiter=',')
                a.writerows(all_season)

    def crawl_3p_leader_data(self):
        header = ['rank', 'web_name', 'player_url','real_name', '3P']
        with open(PLAYER_3P_LEADERS_CSV, 'w', encoding="utf=8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerow(header)
        response = requests.get("https://www.basketball-reference.com/leaders/fg3_career.html")
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', id="nba")
        rows = table.find_all("tr")
        all_data = []
        for row in rows:
            rank_data = []
            data = row.find_all('td')
            rank = 0
            for d in data:
                i = 0
                if i == 0:
                    if d.text.split(".")[0] != '\xa0':
                        rank_data.append(d.text.split(".")[0])
                        i += 1
                        rank += 1
                    else:
                        rank_data.append(rank)
                        i += 1

                if i == 1:
                    if (d.a):
                        rank_data.append(d.a.get('href'))
                        rank_data.append(d.text.split("\n")[0])
                        i += 1
                else:
                    rank_data.append(d.text)
                    i += 1
            print(rank_data)
            all_data.append(rank_data)

        with open(PLAYER_3P_LEADERS_CSV, 'a', encoding="utf=8") as f:
            a = csv.writer(f, delimiter=',')
            a.writerows(all_data)


if __name__ == '__main__':
    crawl = NbaCrawl()
    player_list = crawl.crawl_player_basic()
    crawl.crawl_players_performance_stats(player_list)
    crawl.crawl_player_salaries(player_list)
    team_urls = crawl.crawl_team_basic()
    crawl.crawl_team_stats(team_urls)
    crawl.crawl_3p_leader_data()
