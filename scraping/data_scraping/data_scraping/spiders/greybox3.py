import scrapy
import re


class GreyboxTeamsSpider(scrapy.Spider):
    name = "greybox_teams"
    allowed_domains = ["debatovani.cz"]
    start_urls = [
        "https://statistiky.debatovani.cz/?page=tymy"
    ]

    def parse(self, response):
        self.logger.info("PAGE LOADED OK")

        # Select rows from the main teams table (skip header)
        rows = response.xpath("//div[@id='mainbody']//table/tr[td]")
        self.logger.info(f"Found {len(rows)} rows")

        for row in rows:
            tym_a = row.xpath("./td[1]/a")
            klub_a = row.xpath("./td[2]/a")

            href = tym_a.xpath("@href").get()
            team_id = None

            if href:
                match = re.search(r"tym_id=(\d+)", href)
                if match:
                    team_id = int(match.group(1))

            yield {
                "Type": "Teams",
                "Team_ID": team_id,
                "Team": tym_a.xpath("normalize-space(.)").get(),
                "Klub": klub_a.xpath("normalize-space(.)").get(),
                "Členové": row.xpath("normalize-space(./td[3])").get(),
                "Debaty": row.xpath("normalize-space(./td[4])").get(),
            }
