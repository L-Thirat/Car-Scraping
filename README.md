# Scrape_data
I was create 2 file API to deal with this problem
/spiders
1. main_CSV.py: It's for POST information (API). 
For example, To scrape by select Make/Model of car (It will call data from CSV_scrapy_car.py)
2. CSV_scrapy_car.py: 
This one is use for scrape data from web and create database. If it check update then it wasn't founded, 
it will be scrapes data from .csv instead on Website. That's mean, it don't need to re-scrape every time

To run all of process
1. Go to setup.py of directory
2. Create Egg file
$python setup.py bdist_egg
3. To create first scrapes data of /csv file
$scrapy runspider .\CSV_scrapy_car.py --output csv_scrapes.csv
4. Run Crawing API: go to /dist directory
curl http://localhost:6800/addversion.json -F project=myproject -F version=r23 -F egg=@ScrapAPI-1-py3.7.egg
5. Run API to get POST data (such as, Make/Model): go to main_CSV.py directory
$python main_CSV.py