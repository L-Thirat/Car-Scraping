import scrapy
import pandas as pd
import re
import json
"""
Run : scrapy runspider <filename>
yield keyword: for output to the log
"""

"""
TODO 10/3/2019
1. PUT data to firebase instead CSV if you can (What is the best way to deal with Database ? CSV or Firebase ?)
2. When we want to check update, it will read on firebase or csv by [hyperlink]
3. If it has update, please update firebase
4. Make it run by schedule (I has sample code)
5. ** Test API (Maybe create web server application for submit Demo to Client)
DEADLINE: 11/3/2019 9:00AM
"""


class Demo(scrapy.Spider):
    name = 'car_spider'
    start_urls = ['https://www.usedcarsni.com/search_results.php']
    formatting_text = lambda self, text : "".join(list(filter(self.clean_text, text)))

    """
    use for check update car in site (Sorted by newest car)
    """
    def Check_update(self):
        df = pd.read_csv(".csv")
        return df
        # url = "https://www.usedcarsni.com/search_results.php?sortby=12|0" #Sorted site
        # yield scrapy.Request(url, callback=self.parse)

    def start_requests(self):
        url = "https://www.usedcarsni.com/search_results.php?sortby=12|0" # Search by sorted
        yield scrapy.Request(url, callback=self.parse)

    """
    use for search MAKE & MODEL car
    """
    #     search_text = "BMW"
    #     url = "https://www.usedcarsni.com/search_results.php?keywords=&make=2&model={0}&keywords=&sortby=12|0".format(search_text)
    #     # url = "https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText={0}&viewtype=G".format(
    #     #     search_text)
    #     yield scrapy.Request(url, callback=self.parse, meta={"search_text": search_text})

    def parse(self, response):
        for title in response.css('.car-description>a'):
            yield response.follow(title.attrib['href'], self.parse_detail)

        for next_page in response.css('.navbar>.navbar-form>.navbar-navigation>li:nth-last-child(1)>a'):
            if(next_page.css("::text").get() == "Next"):
                yield response.follow(next_page.attrib['href'], self.parse)

        """
        use for test :control page
        """
        # # search_keyword = response.meta["search_text"]
        # for title in response.css('.car-description>a'):
        #     yield response.follow(title.attrib['href'], self.parse_detail)
        #
        # for next_page in response.css('.navbar>.navbar-form>.navbar-navigation>li:nth-last-child(1)>a'):
        #     index = 1
        #     if("index" in response.meta.keys()):
        #         index = response.meta["index"]
        #     if(next_page.css("::text").get() == "Next" and index <= 20):
        #         yield response.follow(next_page.attrib['href'], self.parse, meta={"index":index+1})

    def parse_detail(self, response):
        data = {"hyperlink":response.url}
        description = response.css('.navbar>.nav-caption>strong::text').get()
        data["description"] = description
        data["manufacturer"] = description.strip(" ")[1]
        data["model"] = description.strip(" ")[2]
        data["yearOfManufacture"] = description.strip(" ")[0]
        if "**" in description:
            data["vrt"] = ((description.split("**"))[1].split("**")[0])
        else: data["vrt"] = ""
        for technical_item in response.css('.technical-params>.row'):
            title = technical_item.css('.technical-headers::text').get()
            detail = technical_item.css('.technical-info::text').get()
            if(title != None):
                #Tax Cost
                if(title == "Tax Cost "):
                    title = "yearlyTax"
                    detail = self.formatting_text(technical_item.css('.technical-info>a::text').get())[1:]
                    detail = self.check_int_float(re.sub("[^0-9]", "", detail))

                #Seller Section // Features
                elif("Seller" in title):
                    title = "sellerType"
                    if technical_item.css('.technical-info>span::text').get():
                        detail = technical_item.css('.technical-info>span::text').get()
                    elif technical_item.css('.technical-info>img').get():
                        detail = "Dealer"
                    else:detail = ""

            #History check section
            if(technical_item.css('.technical-headers>.technical-p-headers::text').get() == "History Check"):
                title = technical_item.css('.technical-headers>.technical-p-headers::text').get()
                detail = {}
                for i in [1,3]:
                    for item in technical_item.css(".technical-info>div:nth-child({})>div".format(i)):
                        if(item.css("span:nth-child(1)::text") != None and item.css("span:nth-child(2)>a::text").get() != None):
                            detail[item.css("span:nth-child(1)::text").get()] = self.formatting_text(item.css("span:nth-child(2)>a::text").get())

            #Engine Size
            if title == "Engine Size":
                title = "engineSize"
            #fuelType
            if title == "Fuel Type":
                title = "fuelType"
            #bodyStyle
            if title == "Body Style":
                title = "bodyStyle"
            #transmissionType
            if title == "Transmission":
                title = "transmissionType"
            #mileage
            if title == "Mileage":
                title = "mileage"
            #colour
            if title == "Colour":
                title = "colour"
            #co2emission
            if title == "CO2 Emission":
                title = "co2emission"
            #doors
            if title == "Doors":
                title = "doors"
            #location
            if title == "Location":
                title = "location"

            #Price Section
            if(len(technical_item.css('.finance-purchase__purchase-content')) > 0):
                title = "price"
                detail = technical_item.css(".finance-purchase__payment-content>.finance-purchase__caption>span::text").get()[1:]
                detail = self.check_int_float(re.sub("[^0-9]", "", detail))

            if(title != None and detail != None):
                if(isinstance(detail,dict)):
                    for item in detail.keys():
                        if "was" in detail[item]:
                            data["was"+item[:5]] = True
                        else: data["was"+item[:5]] = False
                    break
                if(title[0] != "\n") & ("MOT Expiry" not in title) & ("Insurance" not in title) & ("Warranty" not in title):
                    number_list = ["mileage","engineSize","co2emission","Towing Weight","Payload","doors"]
                    if (title in number_list):
                        data[title] = self.check_int_float((re.sub("[^0-9]", "", detail)))
                    else:data[title] = detail

        return data

    def clean_text(self, char):
        if(char == "\n"):
            return False
        elif(char == " "):
            return False
        return True

    def check_int_float(self,data):
        if isinstance(data, int):
            return int(data)
        else:
            return float(data)