import scrapy
import pandas as pd
import re
import csv,json

"""
Run : scrapy runspider <filename> --output <output.csv>
yield keyword: for output to the log
Run API : Go to "START/dist/" ->  $curl http://localhost:6800/addversion.json -F project=myproject -F version=r23 -F egg=@ScarpAPI-1-py3.7.egg
"""

class Demo(scrapy.Spider):
    name = 'car_spider'
    formatting_text = lambda self, text : "".join(list(filter(self.clean_text, text)))
    def __init__(self):
        self.filename = "csv_scrapes.csv"#_origin
        self.filename_json = "json_scrape.json"
        self.columns = ["hyperlink","description","manufacturer","model","yearOfManufacture","vrt","mileage",
                        "location","colour","engineSize","fuelType","transmissionType","door","bodyStyle",
                        "co2emission","yearlyTax","sellerType","price","wasStole","wasScrap","wasWrite"]
        self.df = None
        self.update = False

    def update_csv(self,data):
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        self.df = self.df.append(data, ignore_index=True)

    """
    use for check update car in site (Sorted by newest car)
    """
    def Check_update(self,hyperlink):
        df = pd.read_csv(self.filename)
        if hyperlink in list(df["hyperlink"]):
            return False
        self.update = True
        return True

    def start_requests(self):
        url = "https://www.usedcarsni.com/search_results.php?" # Search by sorted
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for title in response.css('.car-description>a'):
            hyper_link = title.attrib['href']
            yield response.follow(title.attrib['href'], self.parse_detail)
            try:
                self.df = pd.read_csv(self.filename)
                check = self.Check_update(hyper_link)
                if check:
                    yield response.follow(title.attrib['href'], self.parse_detail)
                else:
                    yield self.convert_csv_json()
                    break
            except ValueError:
                print("No database %s: scrapy runspider <filename (This py)> --output <%s>"%(self.filename,self.filename))
                break
                # self.df = pd.DataFrame(columns=self.columns)
                # self.df.to_csv(self.filename)
        for next_page in response.css('.navbar>.navbar-form>.navbar-navigation>li:nth-last-child(1)>a'):
            if(next_page.css("::text").get() == "Next"):
                yield response.follow(next_page.attrib['href'], self.parse)
        if check: # If it have update, it should update .csv
            self.convert_csv_json()

    def parse_detail(self, response):
        file = open("make_model.txt", "r")
        f = file.read()
        list_make = []
        make_data = list(f[5:].split("\nModel\n"))[0]
        for item in make_data.split(","):
            list_make.append(item.split(":")[1][2:-1])
        model_data = (list(f[5:].split("\nModel\n"))[1])
        lst_make_data = (model_data.split("\n---\n"))

        """
        OUTPUT & Cleaning section
        """
        data = {"hyperlink":response.url}
        description = response.css('.navbar>.nav-caption>strong::text').get()
        data["description"] = description

        for item in list_make:
            if item in (description):
                data["manufacturer"] =item
        temp_list_item = []
        for item in lst_make_data:
            for sub_item in item.split("\n"):
                check = sub_item.split(":")[1][2:-2]
                if check in description:
                    temp_list_item.append(check)
        if temp_list_item:
            data['model'] = (max(temp_list_item, key=len))
        data["yearOfManufacture"] = description.split(" ")[0]
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
        if (self.update):
            self.update_csv(data)
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

    def convert_csv_json(self):
        self.df.to_csv(self.filename, index=False)
        data = {}
        with open(self.filename) as csvFile:
            csvReader = csv.DictReader(csvFile)
            for rows in csvReader:
                id = rows['id']
                data[id] = rows

        with open(self.filename_json,'w') as jsonFile:
            jsonFile.write(json.dumps(data,indent=4))
            return json.dumps(data,indent=4)

