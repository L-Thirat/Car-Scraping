import scrapy
import pandas as pd
import re
import csv,json
from scrapy_car import settings
from scrapy.utils.project import get_project_settings

"""
yield keyword: for output to the log
Run API : $curl http://localhost:6800/schedule.json -d project=myproject1 -d spider=first_run
"""

class First(scrapy.Spider):
    name = 'first_run'
    formatting_text = lambda self, text : "".join(list(filter(self.clean_text, text)))
    custom_settings = {
        "FEED_URI" : settings.CSV_FILE_ROOT+"csv_scrapes.csv",
        "FEED_FORMAT" : "csv"
    }

    def start_requests(self):
        self.make, self.model = self.make_model_data()
        url = "https://www.usedcarsni.com/search_results.php?" # Search by sorted
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for title in response.css('.car-description>a'):
            yield response.follow(title.attrib['href'], self.parse_detail)
        
        for next_page in response.css('.navbar>.navbar-form>.navbar-navigation>li:nth-last-child(1)>a'):
            if(next_page.css("::text").get() == "Next"):
                yield response.follow(next_page.attrib['href'], self.parse)

    def parse_detail(self, response):
        """
        OUTPUT & Cleaning section
        """
        modal, make = self.model, self.make
        data = {"hyperlink":response.url}
        description = response.css('.navbar>.nav-caption>strong::text').get()
        data["description"] = description

        for item in make:
            if item in (description):
                data["manufacturer"] =item
        temp_list_item = []
        for item in modal:
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

    def make_model_data(self):
        return (['BMW', 'Abarth', 'Alfa Romeo', 'Aston Martin', 'Audi', 'Bentley', 'Chevrolet', 'Chrysler', 'Citroen', 'Dacia', 'Daihatsu', 'Dodge', 'DS', 'Dutton', 'Ferrari', 'Fiat', 'Ford', 'Honda', 'Hyundai', 'Infiniti', 'Isuzu', 'Jaguar', 'Jeep', 'Kia', 'Lamborghini', 'Land Rover', 'Lexus', 'Lotus', 'Man', 'Maserati', 'Mazda', 'Mercedes', 'MG', 'MINI', 'Mitsubishi', 'Morgan', 'Nissan', 'Peugeot', 'Porsche', 'Proton', 'Renault', 'Rover', 'SAAB', 'Seat', 'Skoda', 'Smart', 'SsangYong', 'Subaru', 'Suzuki', 'TESLA', 'Toyota', 'Vauxhall', 'Volkswagen', 'Volv'], 
        ["{'62981323': 'A1'}\n{'98': 'A2'}\n{'99': 'A3'}\n{'208299236': 'A3 Cabriolet'}\n{'102': 'A4'}\n{'71721286': 'A4 Cabriolet'}\n{'6357519': 'A5'}\n{'103': 'A6'}\n{'10270937': 'A7'}\n{'104': 'A8'}\n{'279140': 'Cabriolet'}\n{'190583596': 'Q2'}\n{'81391901': 'Q3'}\n{'17588741': 'Q5'}\n{'360929': 'Q7'}\n{'240877370': 'Q8'}\n{'9932846': 'R8'}\n{'171673088': 'RS Q3'}\n{'81391902': 'RS3'}\n{'281387': 'RS4'}\n{'62981324': 'RS5'}\n{'606676': 'RS6'}\n{'208272635': 'RS7'}\n{'119074': 'S3'}\n{'105': 'S4'}\n{'6726681': 'S5'}\n{'8402520': 'S8'}\n{'237022200': 'SQ2'}\n{'166294511': 'SQ5'}\n{'194191372': 'SQ7'}\n{'3995': 'TT'}", "{'195661402': 'DB11'}\n{'7406260': 'DB9'}\n{'17120394': 'Rapide'}\n{'7794076': 'Vantage'}",
         "{'236989510': 'Aventador'}", "{'18109808': '500'}\n{'171264602': '595'}", "{'916218': '159'}\n{'157951549': '4C'}\n{'1102742': 'Brera'}\n{'192289046': 'Giulia'}\n{'54475223': 'Giulietta'}\n{'279826': 'GT'}\n{'11267': 'GTV'}\n{'18003526': 'MiTo'}\n{'167356': 'Spider'}\n{'206025925': 'Stelvio'}", "{'995': 'Cherokee'}\n{'6312339': 'Commander'}\n{'4900025': 'Compass'}\n{'139591': 'Grand Cherokee'}\n{'6414212': 'Patriot'}\n{'7187167': 'Renegade'}\n{'139669': 'Wrangler'}", "{'998': 'Carens'}\n{'2526562': 'Ceed'}\n{'158045': 'Cerato'}\n{'174559928': 'Niro'}\n{'87636525': 'Optima'}\n{'6285': 'Picanto'}\n{'11598509': 'Pro Ceed'}\n{'1002': 'Rio'}\n{'6255': 'Sedona'}\n{'7716': 'Sorento'}\n{'17663677': 'Soul'}\n{'7711': 'Sportage'}\n{'226147699': 'Stinger'}\n{'211206096': 'Stonic'}\n{'29085533': 'Venga'}", 
         "{'69111968': 'CT 200h'}\n{'7539': 'GS-Series'}\n{'7537': 'IS-Series'}\n{'161441418': 'NX-Series'}\n{'197152782': 'RC'}\n{'45581': 'RX-Series'}\n{'236990335': 'UX'}", "{'1993': 'Defender'}\n{'1998': 'Discovery'}\n{'144790717': 'Discovery Sport'}\n{'1006': 'Freelander'}\n{'139873': 'Range Rover'}\n{'80190609': 'Range Rover Evoque'}\n{'17111411': 'Range Rover Sport'}\n{'220561215': 'Range Rover Velar'}", "{'165999087': 'Q30'}\n{'165999089': 'Q50'}\n{'235007636': 'Q60'}\n{'165999091': 'QX30'}\n{'165999095': 'QX70'}", "{'1513196': 'D-Max'}", "{'1954': 'Accord'}\n{'956': 'Civic'}\n{'5670': 'CR-V'}\n{'280385': 'FR-V'}\n{'124263': 'HR-V'}\n{'18369078': 'Insight'}\n{'5522': 'Jazz'}\n{'1600792': 'Legend'}\n{'17036940': 'S2000'}", 
         "{'100152871': 'B-Max'}\n{'2027413': 'Courier'}\n{'130144658': 'EcoSport'}\n{'170916505': 'Edge'}\n{'902': 'Fiesta'}\n{'18687336': 'Fiesta Van'}\n{'908': 'Focus'}\n{'2421': 'Focus C-max'}\n{'29055589': 'Focus CC-3'}\n{'13098': 'Fusion'}\n{'4033': 'Galaxy'}\n{'76564649': 'Grand C-MAX'}\n{'927': 'Ka'}\n{'15599695': 'Kuga'}\n{'929': 'Mondeo'}\n{'7968535': 'Mustang'}\n{'4202': 'Ranger'}\n{'279061': 'S-Max'}\n{'473092': 'Sierra'}\n{'9307': 'StreetKa'}\n{'5667': 'Tourneo'}\n{'130156092': 'Tourneo Connect'}\n{'17170475': 'Transit Connect'}\n{'148245119': 'Transit Courier'}", "{'973': 'Amica'}\n{'978': 'Coupe'}\n{'5205': 'Getz'}\n{'17036939': 'i10'}\n{'17375267': 'i20'}\n{'9667393': 'i30'}\n{'237022205': 'i30 Fastback'}\n{'237022207': 'i30 n'}\n{'81254421': 'i40'}\n{'17113597': 'i800'}\n{'18111145': 'iLoad'}\n{'17120405': '124'}\n{'15221871': '500'}\n{'148916433': '500L'}\n{'148916438': '500X'}\n{'13150': 'Doblo'}\n{'17170474': 'Fiorino'}\n{'178010769': 'Fullback'}\n{'16847009': 'Grande Punto'}\n{'193982277': 'Ioniq'}\n{'63118372': 'ix20'}\n{'29106897': 'ix35'}\n{'209641956': 'Kona'}\n{'982': 'Santa Fe'}\n{'3893': 'Tucson'}\n{'85584835': 'Veloster'}", "{'7484': 'Multipla'}\n{'13524': 'Panda'}\n{'887': 'Punto'}\n{'17942277': 'Qubo'}\n{'81391960': 'Tipo'}", 
         "{'222380194': 'E-Pace'}\n{'175443647': 'F-Pace'}\n{'130390647': 'F-Type'}\n{'237022210': 'i-Pace'}\n{'9127': 'S-Type'}\n{'992': 'X-Type'}\n{'156502391': 'XE'}\n{'17111409': 'XF'}\n{'139865': 'XJ Series'}\n{'34610': 'XK'}\n{'50': 'Undefined'}", "{'1161858': '245'}\n{'3010441': 'C30'}\n{'8437': 'C70'}\n{'1364': 'S40'}\n{'1366': 'S60'}\n{'8090': 'S80'}\n{'81392081': 'S90'}\n{'17108690': 'V40'}\n{'17108866': 'V50'}\n{'65711584': 'V60'}\n{'17107255': 'V70'}\n{'81392082': 'V90'}\n{'234050101': 'XC40'}\n{'17460926': 'XC60'}\n{'17108828': 'XC70'}\n{'17108899': 'XC90'}", "{'201211164': 'Model X'}", "{'2054005': 'Auris'}\n{'1248': 'Avensis'}\n{'5065': 'Aygo'}\n{'188741687': 'C-HR'}\n{'356578': 'Camry'}\n{'3106': 'Carina'}\n{'1250': 'Celica'}\n{'1254': 'Corolla'}\n{'78477011': 'Corolla Verso'}\n{'99693893': 'GT 86'}\n{'8964': 'Hilux'}\n{'17391293': 'iQ'}\n{'3884': 'Land Cruiser'}\n{'2025655': 'MR2'}\n{'2574': 'Prius'}\n{'7822': 'RAV4'}\n{'45234': 'Supra'}\n{'18142038': 'Urban Cruiser'}\n{'17113590': 'Verso'}\n{'1262': 'Yaris'}\n{'50': 'Undefined'}", "{'110498620': 'Adam'}\n{'4221': 'Agila'}\n{'7096182': 'Antara'}\n{'1265': 'Astra'}\n{'136826412': 'Astra GTC'}\n{'136826735': 'Astra Tourer'}\n{'253628442': 'Astra VXR'}\n{'112146156': 'Cascada'}\n{'2609': 'Alto'}\n{'587039': 'Baleno'}\n{'147757460': 'Celerio'}\n{'1241': 'Grand Vitara'}\n{'2891': 'Ignis'}\n{'2201': 'Jimny'}\n{'4536': 'Cavalier'}\n{'1409': 'Combo'}\n{'1281': 'Corsa'}\n{'17170468': 'Corsavan'}\n{'204148155': 'Crossland X'}\n{'216415314': 'Grandland X'}\n{'17363498': 'Insignia'}\n{'1283': 'Meriva'}\n{'103782543': 'Mokka'}\n{'141057': 'Forester'}\n{'5459': 'Impreza'}\n{'13631': 'Legacy'}\n{'17111400': 'Outback'}\n{'137967987': 'WRX STI'}\n{'98355413': 'XV'}", "{'16063526': 'Splash'}\n{'6160': 'Swift'}\n{'131957': 'SX4'}\n{'141284329': 'SX4 S-Cross'}\n{'1245': 'Vitara'}", "{'247024584': 'Mokka X'}\n{'9265': 'Monaro'}\n{'9034': 'Tigra'}\n{'1292': 'Vectra'}\n{'29048685': 'Viva'}\n{'17113568': 'VXR'}\n{'1308': 'Zafira'}\n{'136965226': 'Zafira Tourer'}", "{'18810908': 'Actyon'}\n{'5998255': 'Korando'}\n{'137968188': 'Korando Sports'}\n{'2537031': 'Musso'}\n{'6354': 'Rexton'}\n{'461493': 'Rodius'}\n{'160264261': 'Tivoli'}\n{'209639908': 'Tivoli XLV'}\n{'140066710': 'Turismo'}",
          "{'323592': 'Forfour'}\n{'902102': 'Fortwo'}\n{'44702': 'Roadster'}", "{'79331684': 'Amarok'}\n{'206609096': 'Arteon'}\n{'1319': 'Beetle'}\n{'1321': 'Bora'}\n{'903389': 'Caddy'}\n{'147705155': 'Caddy Maxi'}\n{'18501534': 'California'}\n{'1331': 'Caravelle'}\n{'95975628': 'CC'}\n{'896697': 'Eos'}\n{'254159': 'Fox'}\n{'1333': 'Golf'}\n{'67748145': 'Golf Plus'}\n{'144280611': 'Golf SV'}\n{'78666': 'Jetta'}\n{'1346': 'Lupo'}\n{'1348': 'Passat'}\n{'78602006': 'Passat CC'}\n{'4158': 'Phaeton'}\n{'1355': 'Polo'}\n{'158667': 'Scirocco'}\n{'3296': 'Sharan'}\n{'236993485': 'T-Cross'}\n{'216789267': 'T-Roc'}\n{'10857105': 'Tiguan'}\n{'229226589': 'Tiguan Allspace'}\n{'3365': 'Touareg'}\n{'3355': 'Touran'}\n{'80703562': 'Transporter mobility'}\n{'81392079': 'Up'}", "{'4586': '200 Series'}\n{'2417': 'Mini'}", "{'95764640': 'Citigo'}\n{'1237': 'Fabia'}\n{'215753566': 'Karoq'}\n{'191819038': 'Kodiaq'}\n{'2355': 'Octavia'}\n{'432483': 'Rapid'}\n{'1265720': 'Roomster'}\n{'1960': 'Superb'}\n{'29054057': 'Yeti'}", "{'1205': '9-3'}\n{'8075': '9-5'}",
          "{'1210': 'Alhambra'}\n{'1213': 'Altea'}\n{'208291125': 'Arona'}\n{'174559937': 'Ateca'}\n{'17942607': 'Exeo'}\n{'1216': 'Ibiza'}\n{'1221': 'Leon'}\n{'95764903': 'Mii'}\n{'236993191': 'Tarraco'}\n{'1228': 'Toledo'}", "{'116905745': 'Captur'}\n{'1136': 'Clio'}\n{'5707': 'Grand Espace'}\n{'137968217': 'Grand Modus'}\n{'139628': 'Grand Scenic'}\n{'155627944': 'Kadjar'}\n{'1149': 'Kangoo'}\n{'16878234': 'Koleos'}\n{'1155': 'Laguna'}\n{'1170': 'Megane'}\n{'1976': 'Modus'}\n{'1178': 'Scenic'}\n{'138115115': 'Scenic XMOD'}\n{'7407535': 'Twingo'}\n{'51394750': 'Wind'}\n{'119784622': 'Zoe'}\n{'50': 'Undefined'}", "{'799652': 'Satria'}", "{'7553': '911'}\n{'5471': '944'}\n{'2115731': '968'}\n{'4497': 'Boxster'}\n{'5405': 'Cayenne'}\n{'524604': 'Cayman'}\n{'144610354': 'Macan'}\n{'29106905': 'Panamera'}", "{'17375271': '4/4'}", "{'1065': '350Z'}\n{'19072832': '370Z'}\n{'1067': 'Almera'}\n{'17088154': 'Almera Tino'}\n{'10697928': 'Figaro'}\n{'18254252': 'GT-R'}\n{'58088882': 'Juke'}\n{'81392030': 'LEAF'}\n{'1076': 'Micra'}\n{'2019': 'Murano'}\n{'17088147': 'Navara'}\n{'139678': 'Note'}\n{'17779969': 'NP300'}\n{'5465': 'Pathfinder'}\n{'18713778': 'Pixo'}\n{'858902': 'Pulsar'}\n{'2265920': 'Qashqai'}\n{'106573228': 'Qashqai+2'}\n{'18160912': 'Tiida'}\n{'4481': 'X-Trail'}\n{'50': 'Undefined'}", 
          "{'17438671': 'Clubman'}\n{'166427226': 'Convertible'}\n{'68192828': 'Countryman'}\n{'166427227': 'Coupe'}\n{'166427224': 'Hatch'}\n{'166427229': 'John Cooper Works'}\n{'125389925': 'Paceman'}\n{'166427228': 'Roadster'}", "{'50853840': 'ASX'}\n{'1375': 'Colt'}\n{'206944317': 'Eclipse Crossover'}\n{'2694': 'Grandis'}\n{'1056': 'L200'}\n{'1983': 'Lancer'}\n{'734976': 'Mirage'}\n{'4474': 'Outlander'}\n{'1910': 'Shogun'}", "{'81118968': '6'}\n{'187921832': 'GS'}\n{'29094934': 'MG3'}\n{'81392018': 'MG6'}\n{'1045': 'TF'}\n{'8316': 'ZS'}\n{'2626': 'ZT'}", "{'2181': '106'}\n{'4795': '107'}\n{'137821914': '108'}\n{'1092': '206'}\n{'282288': '207'}\n{'16842564': '1007'}\n{'128677803': '2008'}\n{'55472161': '207 cc'}\n{'70527751': '208'}\n{'1103': '307'}\n{'9169442': '308'}\n{'29010732': '3008'}\n{'55472194': '308 cc'}\n{'1117': '406'}\n{'1903': '407'}\n{'71159067': '508'}\n{'8731': '807'}\n{'18687331': '4007'}\n{'29070743': '5008'}\n{'17113586': 'Bipper'}\n{'29055585': 'Horizon'}\n{'1128': 'Partner'}\n{'88786936': 'Partner Tepee'}\n{'29137705': 'RCZ'}", "{'1012': '2'}\n{'3081': '3'}\n{'946185': '5'}\n{'2506': '6'}\n{'153507380': 'CX-3'}\n{'91680728': 'CX-5'}\n{'6681340': 'CX-7'}\n{'16844034': 'MX-5'}\n{'2959009': 'RX-8'}", "{'144396': '420'}\n{'81392003': 'GHIBLI'}\n{'17120399': 'GranTurismo'}\n{'215899394': 'Levante'}\n{'149806': 'Quattroporte'}", "{'50': 'Undefined'}", "{'518658': '190'}\n{'277337': 'A-Class'}\n{'413012': 'B-Class'}\n{'139996': 'C-Class'}\n{'118062605': 'Citan'}\n{'17107128': 'CL-Class'}\n{'113985348': 'CLA-Class'}\n{'17107024': 'CLC-Class'}\n{'1025': 'CLK-Class'}\n{'58128': 'CLS-Class'}\n{'414829': 'E-Class'}\n{'17107232': 'G-Class'}\n{'1072458': 'GL-Class'}\n{'128053237': 'GLA-Class'}\n{'323977': 'Elise'}\n{'29025605': 'Evora'}", "{'183291994': 'GLC-Class'}\n{'156739435': 'GLE-Class'}\n{'251185402': 'GLS-Class'}\n{'678695': 'M-Class'}\n{'1277927': 'R-Class'}\n{'44645': 'S-Class'}\n{'45890': 'SL'}\n{'253900212': 'SLC-Class'}\n{'6160530': 'SLK-Class'}\n{'17107192': 'V-Class'}\n{'2620': 'Vito'}\n{'224353721': 'X-Class'}\n{'50': 'Undefined'}", "{'255019636': 'Phaeton'}", "{'81391954': '458'}\n{'237022204': '488'}\n{'29047526': 'California'}\n{'249875499': 'F12 Berlinetta'}\n{'81391958': 'FF'}\n{'249874416': 'Portofino'}\n{'50': 'Undefined'}",
           "{'170978732': '3'}\n{'237022203': '3 Crossback'}\n{'170978738': '4'}\n{'170978743': '5'}\n{'211219836': '7 Crossback'}", "{'6929958': 'Nitro'}", "{'1900': 'Terios'}", "{'81391935': 'Duster'}\n{'140034275': 'Logan'}\n{'102036428': 'Sandero'}", "{'39809': '300'}\n{'81391918': 'Delta'}\n{'149802': 'Grand Voyager'}\n{'111': 'Voyager'}", "{'2388': 'Berlingo'}\n{'18468636': 'Berlingo Multispace'}\n{'9114879': 'C-Crosser'}\n{'299023': 'C1'}\n{'1971': 'C2'}\n{'844': 'C3'}\n{'210972030': 'C3 Aircross'}\n{'17166406': 'C3 Picasso'}\n{'4204': 'C4'}\n{'136401435': 'C4 Cactus'}\n{'7406368': 'C4 Picasso'}\n{'245649506': 'C4 Spacetourer'}\n{'849': 'C5'}\n{'237022202': 'C5 Aircross'}\n{'2213': 'C8'}\n{'187450711': 'Dispatch Combi'}\n{'29083553': 'DS3'}\n{'76443122': 'DS4'}\n{'81391925': 'DS5'}\n{'106634450': 'Grand C4 Picasso'}\n{'17108496': 'Nemo'}\n{'58818844': 'Nemo Multispace'}\n{'195054991': 'Space Tourer'}\n{'140157': 'Xsara Picasso'}", "{'11523200': 'Aveo'}\n{'17170470': 'Camaro'}\n{'11523201': 'Captiva'}\n{'29006828': 'Cruze'}\n{'378910': 'Lacetti'}\n{'17658': 'Matiz'}\n{'69470698': 'Orlando'}\n{'29085572': 'Spark'}\n{'116939794': 'Trax'}", "{'395362': '1 Series'}\n{'152692631': '2 Series'}\n{'139959': '3 Series'}\n{'130390641': '4 series'}\n{'9078': '5 Series'}\n{'395363': '6 Series'}\n{'395364': '7 Series'}\n{'17113562': '8 Series'}\n{'203957288': 'i3'}\n{'180486982': 'i8'}\n{'81391909': 'M COUPE'}\n{'207836415': 'M2'}\n{'824': 'M3'}\n{'146671409': 'M4'}\n{'7653': 'M5'}\n{'278177': 'M6'}\n{'29100118': 'X1'}\n{'216474895': 'X2'}\n{'4846': 'X3'}\n{'152692627': 'X4'}\n{'827': 'X5'}\n{'16855076': 'X6'}\n{'11192': 'Z4'}", "{'20973': 'Continental'}\n{'202201272': 'Flying Spur'}\n{'18813855': 'Mulsanne'}"])