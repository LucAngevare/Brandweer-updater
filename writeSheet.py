# Copyright (c) 2023 Luc Angevare - lucangevare@gmail.com
#
# Hierbij wordt gratis toestemming verleend aan een ieder die een kopie verkrijgt
# van deze software en bijbehorende documentatiebestanden (de "Software"), om te handelen
# in de Software zonder beperking, inclusief zonder beperking de rechten
# te gebruiken, kopiëren, wijzigen, samenvoegen, publiceren, distribueren, in sublicentie te geven en/of te verkopen
# kopieën van de Software, en om personen aan wie de Software is
# verstrekt om dit te doen, onder de volgende voorwaarden:
#
# De bovenstaande copyrightmelding en deze toestemmingsmelding zullen worden opgenomen in
# alle kopieën of substantiële delen van de Software.
#
# DE SOFTWARE WORDT GELEVERD "AS IS", ZONDER ENIGE VORM VAN GARANTIE, UITDRUKKELIJK OF
# IMPLICIET, INCLUSIEF MAAR NIET BEPERKT TOT DE GARANTIES VAN VERKOOPBAARHEID,
# GESCHIKTHEID VOOR EEN BEPAALD DOEL EN NIET-INBREUK. IN GEEN GEVAL ZULLEN DE
# AUTEURS OF AUTEURSRECHTHEBBENDEN AANSPRAKELIJK ZIJN VOOR ENIGE CLAIM, SCHADE OF ANDERE
# AANSPRAKELIJKHEID, HETZIJ IN EEN ACTIE VAN CONTRACT, ONRECHTMATIGE DAAD OF ANDERSZINS, VOORTVLOEIEND UIT,
# OF IN VERBAND MET DE SOFTWARE OF HET GEBRUIK OF ANDERE OMGANG MET DE SOFTWARE.

import gspread, feedparser, schedule, time, pytz
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
from datetime import datetime

scope = ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name("Brandweer_Keys.json", scope)
client = gspread.authorize(credentials)

sheet = client.open("Alarmeringen Brandweer").sheet1

iteration = 1

class RssIntoGSheet:
    """Een class voor alle functies, zodat een cron job gedaan kan worden """
    def __init__(self):
        self.iteration = 0
    def run(self):
        self.iteration += 1
        self.items = self.get_rss()
        self.save_feed(self.items)
        print(f"{self.iteration=}")

    def get_rss(self):
        newsFeed = feedparser.parse("https://alarmeringen.nl/feeds/discipline/brandweer.rss")
        return newsFeed.entries

    def save_feed(self, items):
        for emergency in items:
            try:
                if (sheet.find(emergency.id).col == 5): # als het ID van de alarmering al is gevonden, stopt ie met de for loop en wacht ie weer 10 minuten om te kijken of er alweer nieuwe alarmeringen met unieke IDs gevonden zijn.
                    break
            except AttributeError:
                numArr = []
                pprint(emergency)
                for word in emergency["title"].split()[::-1]: #de array van woorden wordt achteruitgedaan, zodat alle nummers vooraan staan
                    try:
                        if (len(word) == 6 and word.isdigit()):
                            numArr.append(word) #als het woord omgezet kan worden in een nummer, en uit 6 tekens bestaat, wordt het aan een array toegevoegd. Op deze manier weten we dat als er na alle nummers toevallig nog een nummer staat zoals een huisnummer of dergelijken, weten we vrijwel zeker dat het niet per ongeluk toegevoegd wordt aan de array. Ook kijken we naar isdigit() ipv de vorige manier omdat ik opmerkte dat er een 0 vooraan het nummer kan staan, en anders wordt die weggelaten.
                    except ValueError:
                        break
                else:
                    numStr = ", ".join(numArr) #op deze manier kunnen er zo veel nummers in als er zijn, en is het weer gemakkelijk in een array te zetten door .split(", ") te doen.
                    print(f"numArr: {len(numArr)}, numStr: {numStr}")
                summary = "" if not hasattr(emergency, "summary") else emergency.summary
                date_obj = datetime.strptime(emergency.published, "%a, %d %b %Y %H:%M:%S %z")
                timezone = pytz.timezone("Europe/Amsterdam")
                date_obj = date_obj.astimezone(timezone)
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                if "074231" in numArr or "074261" in numArr or "074280" in numArr:
                    sheet.append_row([emergency.title, emergency.link, summary, date_str, emergency.id, numStr])
                else:
                    continue
                    

KickStartDB = RssIntoGSheet()
schedule.every(1).minutes.do(KickStartDB.run)
KickStartDB.run()
while True:
    schedule.run_pending()
    time.sleep(10)