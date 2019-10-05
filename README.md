# Scrape_data
I was create 3 file API to deal with this problem
/spiders
1. main_CSV.py: It's for GET information (API). 

>That's run on flask so first you must install flask before run this file.
Please put file CSV in folder `api` and store the folder on Desktop
because in scrape project set default FEED_URI with `file:///Users/*NAMEOFUSERNAME*/Desktop/api/`
with only 1 endpoint
GET /cars
params make, model > it will filter with keyword ex: /cars?model=Scenic&make=Renault
response CODE 200 Format JSON

2. scrapy_car.py <spider name : first_run> :
  
>This one is run for first time that will store at "file:///Users/*NAMEOFUSERNAME*/Desktop/api/csv_scrapes.csv" automatically 

3. CSV_scrapy_car.py <spider name : car_spider> :

>This one is use for scrape data from web and create database. If it check update then it wasn't founded, 
it will be scrapes data from .csv instead on Website. That's mean, it don't need to re-scrape every time

To run all of process
1. Change FEED_URI in settings.py with your own and make sure `api` folder is follow by FEED_URI
2. Go to setup.py of directory
3. Create Egg file

>$python setup.py bdist_egg

4. Run Scapyd for Crawing API on Terminal:

>$scrapyd

5. Run Crawing API: go to /dist directory

>$curl http://localhost:6800/addversion.json -F project=myproject -F version=r23 -F egg=@ScrapAPI-1-py3.7.egg

6. To create first scrapes data of /csv file

>$curl http://localhost:6800/schedule.json -d project=myproject1 -d spider=first_run

5. Run API : `api` directory | make sure you had put .csv file already or wait after first scrapes finished

>$python main_CSV.py oy npm start or yarn start

6. For Next time To Scrape

>$curl http://localhost:6800/schedule.json -d project=myproject1 -d spider=car_spider
