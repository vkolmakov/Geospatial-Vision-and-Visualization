import csv
from peewee import *
from pathlib import Path

from matching import (latlon_to_xy, extract_shape_info_bounds)
from utils import (in_chunks, add_items)

db = SqliteDatabase('probe.db')

class ProbeBase(Model):
  class Meta: 
    database = db

class ProbePoint(ProbeBase):
  sampleID    = BigIntegerField() # ID is NOT unique
  dateTime    = DateTimeField()
  sourceCode  = IntegerField()
  latitude    = DecimalField()
  longitude   = DecimalField()
  altitude    = IntegerField()
  speed       = IntegerField() # stored in KPH 
  heading     = IntegerField() # degrees
  x           = DecimalField()
  y           = DecimalField()
  
  def get_csv_headers():
    return("sampleID", 
          "dateTime", 
          "sourceCode", 
          "latitude", 
          "longitude", 
          "altitude", 
          "speed", 
          "heading")

class LinkPoint(ProbeBase):
  linkPVID          = BigIntegerField()
  refNodeID         = BigIntegerField()
  nrefNodeID        = BigIntegerField
  length            = DecimalField()
  functionalClass   = IntegerField()
  directionOfTravel = CharField()
  speedCategory     = IntegerField()
  fromRefSpeedLimit = IntegerField()
  toRefSpeedLimit   = IntegerField()
  fromRefNumLanes   = IntegerField()
  toRefNumLanes     = IntegerField()
  multiDigitized    = BooleanField()
  urban             = BooleanField()
  timeZone          = DecimalField()
  shapeInfo         = TextField() # array
  curvatureInfo     = TextField() # array
  slopeInfo         = TextField() # array 

  def get_csv_headers(): 
    return("linkPVID", 
          "refNodeID", 
          "nrefNodeID", 
          "length", 
          "functionalClass", 
          "directionOfTravel", 
          "speedCategory", 
          "fromRefSpeedLimit", 
          "toRefSpeedLimit", 
          "fromRefNumLanes", 
          "toRefNumLanes", 
          "multiDigitized", 
          "urban", 
          "timeZone", 
          "shapeInfo", 
          "curvatureInfo", 
          "slopeInfo")

class MatchedPoints(ProbeBase):
  sampleID      = IntegerField() # ID is NOT unique
  dateTime      = DateTimeField()
  sourceCode    = IntegerField()
  latitude      = DecimalField()
  longitude     = DecimalField()
  altitude      = IntegerField()
  speed         = IntegerField() # stored in KPH 
  heading       = IntegerField() # degrees 
  linkPVID      = BigIntegerField()
  direction     = CharField()
  distFromRef   = IntegerField()
  distFromLink  = IntegerField()

def db_connect_handler(): 
  db.connect() # explicitness for safety

def db_close_handler():
  db.close()

def setup(db): 
  db_connect_handler()
  db.create_tables([ProbePoint, LinkPoint, MatchedPoints], safe=True)
  
  # Probe Data 
  f = open('probe_data_map_matching/Partition6467ProbePoints.csv', 'rU')
  ProbeRead = csv.DictReader(f, fieldnames=ProbePoint.get_csv_headers())

  with db.atomic():
    update_point = lambda point, x, y: add_items(point, [('x', x), ('y', y)])
    for raw_points in in_chunks(ProbeRead, 500):
      points = [update_point(p, *latlon_to_xy((float(p['latitude']), float(p['longitude']))))
                for p in raw_points]

      ProbePoint.insert_many(points).execute()
    
  # Link Data
  f = open('probe_data_map_matching/Partition6467LinkData.csv', 'rU')
  LinkRead = csv.DictReader(f, fieldnames=LinkPoint.get_csv_headers())
    
  with db.atomic(): 
    for point in LinkRead:
      LinkPoint.create(**point).save()
  db_close_handler()

def main(): 
  file = Path('probe.db')
  if not file.is_file():
    print("Setting up database...")
    setup(db)
    print("Database created.")
  else:
    print("Database found!")

if __name__ == "__main__":
  main()