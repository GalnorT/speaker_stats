import scrapy


class GreyboxCompetitionsSpider(scrapy.Spider):
    name = "greybox_competitions"
    start_urls = ["https://statistiky.debatovani.cz/?page=souteze"]

    def parse(self, response):
        rows = response.xpath(
            "//*[local-name()='div' and @id='mainbody']"
            "//*[local-name()='table']"
            "//*[local-name()='tr'][td]"
        )

        for row in rows:
            yield {
                "Type": "Competition",
                "Sezóna": row.xpath("./td[1]/text()").get("").strip(),
                "Soutěž": row.xpath("./td[2]//text()").get("").strip(),
                "Druh": row.xpath("./td[3]/text()").get("").strip(),
                "Jazyk": row.xpath("./td[4]/text()").get("").strip(),
                "Aktivní": row.xpath("./td[5]/text()").get("").strip(),
                "Debaty": row.xpath("./td[6]/text()").get("").strip(),
            }

