import csv
import logging
import glob
import os
import time
import googlemaps
import parseWorkingHours
from slugify import slugify

KEYS = [ 
        'AIzaSyCgs8C71RqvWoeO69XBXVPQH006i7v4IkM', #Ananth's
        'AIzaSyCcijQW6eCvvt1ToSkjaGA4R22qBdZ0XsI' #Aakash's
]
key_index = 0


class geocoderTest():
    def __init__(self, geo_type='google'):

        try:
            global key_index
            self.gmaps = googlemaps.Client(key=KEYS[key_index])
        except:
            #check for actual error if required set no. of calls = 2500 (or whatever)
            key_index += 1
            self.gmaps = googlemaps.Client(key=KEYS[key_index])

        self.rows = []
        self.FIELDS = []

    def process(self):
        fileNames = glob.glob('./input/*.csv');
        for fileName in fileNames:
            self.rows = []
            self.FIELDS = []
            fileBaseName = os.path.splitext(os.path.basename(fileName))[0];
            self._readCSV(fileName);
            self._addGeocoding();
            #self._addLocationPhoto();
            self._addFeaturedImage();
            self._formatWorkinghours();
            self._writeCSV("./output/processed_"+fileBaseName+".csv");

    def _readCSV(self, fileName):
        inputFile = open(fileName, 'r')
        sample_text = ''.join(inputFile.readline() for x in range(3))
        dialect = csv.Sniffer().sniff(sample_text);
        inputFile.seek(0);
        reader = csv.DictReader(inputFile, dialect=dialect)
        # skip the head row
        # next(reader)
        # append new columns
        reader.fieldnames.extend(["listing_locations", "featured_image", "location_image", "fullAddress", "lat", "lng"]);
        self.FIELDS = reader.fieldnames;
        self.rows.extend(reader);
        inputFile.close();

    def _addGeocoding(self):
        geoLocationAdded = 0;
        geoLocationFailed = 0;
        for row in self.rows:
            if (row["lat"] is None or row["lat"] == ""):
                row["Locality"] = row["Locality"].title()
                row["City"] = row["City"].title()
                address = "%s %s, %s, %s, %s" % (row["Street Address"],row["Locality"],row["City"],row["Pincode"],row["Country"])
                row["fullAddress"] = address;
                row["listing_locations"] = row["Locality"] + ", " + row["City"];
                try:
                    time.sleep(1); # To prevent error from Google API for concurrent calls
                    geocode_result = self.gmaps.geocode(address);
                    if(len(geocode_result)>0):
                        row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                        row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                    else:
                        #logging.warning("Geocode API failure for : '" + address + "'");
                        geocode_result = self.gmaps.geocode(row["Name"] + ", " + address);
                        if (len(geocode_result) > 0):
                            row["lat"] = geocode_result[0]['geometry']['location']['lat'];
                            row["lng"] = geocode_result[0]['geometry']['location']['lng'];
                        else:
                            logging.warning("---- Trying by adding name also failed for : '" + address + "'");
                            geoLocationFailed+=1;
                            row["lat"] = 0;
                            row["lng"] = 0;
                except Exception as err:
                    logging.exception("Something awful happened when processing '"+address+"'");
                    geoLocationFailed+=1;
                    row["lat"] = 0;
                    row["lng"] = 0;
                geoLocationAdded+=1;
                if (geoLocationAdded%20==0):
                    print("Processed "+str(geoLocationAdded)+" rows.");
        time.sleep(1); # To prevent error from Google API for concurrent calls
        print("Successfully completed processing of (" + str(geoLocationAdded-geoLocationFailed) + "/" + str(geoLocationAdded) + ") rows.");

    def _addLocationPhoto(self):
        for row in self.rows:
            if row["lat"]==0:
                row['location_image'] = '';
            else:
                myLocation = (row["lat"], row["lng"]);
                #locationResult = self.gmaps.places_nearby(myLocation);
                #photoReference = locationResult['results'][0]['photos'][0]['photo_reference'];
                #placesPhoto = self.gmaps.places_photo(photoReference, max_width=1000);
                imageFileName = "./output/image_"+slugify(row["Name"])+".jpg"
                #imageFile = open(imageFileName, 'w');
                #for picString in placesPhoto:
                #    imageFile.write(picString);
                #imageFile.close();
                #time.sleep(1);  # To prevent error from Google API for concurrent calls
                row['location_image'] = imageFileName;

    def _addFeaturedImage(self):
        for row in self.rows:
            if not row["Images URL"]:
                row['featured_image'] = '';
            else:
                row['featured_image'] = row['Images URL'].split(",")[0].strip();

    def _formatWorkinghours(self):
        for row in self.rows:
            if not row["Working Hours"]:
                row['Working Hours'] = '';
            else:
                row['Working Hours'] = parseWorkingHours.parseWorkingHours(row['Working Hours']);

    def _writeCSV(self, fileName):
        try:
            # DictWriter
            csvFile = open(fileName, 'w');
            writer = csv.DictWriter(csvFile, fieldnames=self.FIELDS);
            # write header
            writer.writerow(dict(zip(self.FIELDS, self.FIELDS)));
            for row in self.rows:
                writer.writerow(row)
            csvFile.close()
        except Exception as err:
            logging.exception("Something awful happened when processing result.csv");

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    f = geocoderTest()
    f.process()
