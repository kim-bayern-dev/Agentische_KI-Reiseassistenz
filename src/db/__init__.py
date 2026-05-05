from db.db import TourenDB, Tour
from processing.touren_loader import load_touren

TOUREN_DB = TourenDB()
tours = load_touren("./data/raw/tours.xml")
for raw_tour in tours:
    tour = Tour.from_raw_dict(raw_tour)
    TOUREN_DB.add_tour(tour)
