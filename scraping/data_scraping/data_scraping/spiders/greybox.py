from scrapy import Spider, Request
import re
from urllib.parse import urlparse, parse_qs
import scrapy


class DebatySpider(scrapy.Spider):
    name = "greybox"

    def start_requests(self):
        #for debate_id in range(11012, 11380):
        for debate_id in range(10700, 11380):
       # for debate_id in range(11360, 11380):git init
            yield scrapy.Request(
                f"https://statistiky.debatovani.cz/?page=debata&debata_id={debate_id}",
                callback=self.parseDebateDetail,
                cb_kwargs={'debate_id': debate_id}  # Pass it here
            )

    def parseDebateDetail(self, response, debate_id):

        def extract_id(url, key):
            if not url:
                return None
            return parse_qs(urlparse(url).query).get(key, [None])[0]

        # ---------- COMPETITION / LEAGUE / TOURNAMENT ----------
        base_p = response.xpath("//p[starts-with(normalize-space(.),'soutěž:')]")

        competition_a = base_p.xpath(".//a[contains(@href,'soutez')]")
        league_a = base_p.xpath(".//a[contains(@href,'liga')]")
        tournament_a = base_p.xpath(".//a[contains(@href,'turnaj')]")

        competition_name = competition_a.xpath("text()").get()
        competition_link = response.urljoin(competition_a.xpath("@href").get())

        league_name = league_a.xpath("text()").get()
        league_link = response.urljoin(league_a.xpath("@href").get())

        tournament_name = tournament_a.xpath("text()").get()
        tournament_link = response.urljoin(tournament_a.xpath("@href").get())

        # ---------- DATE ----------
        date_text = response.xpath("//p[contains(normalize-space(.),'datum:')]/text()").getall()
        date_text = " ".join(t.strip() for t in date_text)
        date_match = re.search(r"datum:\s*([0-9:\- ]+)", date_text)
        date = date_match.group(1) if date_match else None

        # ---------- MOTION ----------
       #motion = response.xpath("//p[a[contains(@href,'teze')]]/a/text()").get()
      # motion2 = response.xpath("//a[contains(@href, 'teze_id')]/text()").get()
      # motion3 = response.xpath("//p[contains(text(), 'teze:')]/a/text()").get()
        motion = response.xpath("//div[@id='mainbody']//a[contains(@href, 'teze_id')]/text()").get()

        # ---------- TEAMS ----------
        team_names = response.xpath("//tr[th[text()='tým']]/td/a/text()").getall()

        # ---------- SCORE ----------
        score = response.xpath(
            "//tr[th[text()='výsledek']]//text()[contains(.,':')]").get()
        score2 = score.strip() if score else None

        # ---------- SPEAKERS ----------
        speakers_by_side = {"aff": [], "neg": []}

        speaker_rows = response.xpath("//tr[th[contains(text(),'řečník')]]")

        for row in speaker_rows:
            cells = row.xpath("./td")

            left_name = cells[0].xpath(".//a/text()").get()
            left_points = cells[1].xpath("text()").get()
            left_win = "sieg" in (cells[0].attrib.get("class", "") + cells[1].attrib.get("class", ""))

            right_name = cells[2].xpath(".//a/text()").get()
            right_points = cells[3].xpath("text()").get()
            right_win = "sieg" in (cells[2].attrib.get("class", "") + cells[3].attrib.get("class", ""))

            if left_name:
                speakers_by_side["aff" if left_win else "neg"].append({
                    "name": left_name.strip(),
                    "points": int(left_points) if left_points else None
                })

            if right_name:
                speakers_by_side["aff" if right_win else "neg"].append({
                    "name": right_name.strip(),
                    "points": int(right_points) if right_points else None
                })
            # ---------- JUDGES (ROZHODČÍ) ----------
        # ---------- JUDGES (ROZHODČÍ) ----------
        judges = []

        judge_rows = response.xpath(
            "//h2[normalize-space()='rozhodčí']/following-sibling::table[1]/tr[position()>1]"
        )

        for row in judge_rows:
            cells = row.xpath("./td")

            if len(cells) >= 2:
                judge_name = cells[0].xpath(".//a/text()").get()
                decision_side = cells[1].xpath("normalize-space(text())").get()

                # score is optional (3rd column may not exist)
                decision_score = (
                    cells[2].xpath("normalize-space(text())").get()
                    if len(cells) >= 3
                    else None
                )

                judges.append({
                    "name": judge_name.strip() if judge_name else None,
                    "side": decision_side,
                    "score": decision_score
                })

        # ---------- BUILD TEAM STRUCTURE ----------
        teams = []

        for i, name in enumerate(team_names):
            side = "aff" if i == 0 else "neg"
            teams.append({
                "team_name": name.strip(),
                "side": side,
                "speakers": speakers_by_side[side]
            })

        # ---------- OUTPUT ----------
        yield {
            "type": "debate",
            "id": debate_id,
         #   "url": response.url,
            "date": date,
            "comp": competition_name,

            "league_name": league_name,
            "league_id": extract_id(league_link, "liga_id"),
            "motion": motion,
            "tournament_name": tournament_name,
            "tournament_id": extract_id(tournament_link, "turnaj_id"),
            "judges_scoring": judges,
            "score": score2,


        #    "competition": {
         #       "name": competition_name,
          #      "id": extract_id(competition_link, "soutez_id")
           # },


            "teams": teams
        }