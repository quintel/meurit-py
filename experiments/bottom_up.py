'''The bottom up experiment'''
from pathlib import Path

from lib.models import Country, InactiveCountry, Area
from lib.logger import DataLogger

path = Path.home() / 'Dropbox (Quintel)' / 'Quintel' / 'Projects' / 'Active' / '538 Coupled Markets'

# Setup the coutries and put them in an Area for enabling 'all' methods
nl = Country('nl')
de = Country('de')
be = Country('be')
dk = Country('dk')

# Add an inactive coutry
at = InactiveCountry.from_price_curve_file('at' ,path / 'vertrouwelijk - at 2015.csv')
fr = InactiveCountry.from_price_curve_file('fr' ,path / 'vertrouwelijk - fr 2015.csv')
no = InactiveCountry.from_price_curve_file('no' ,path / 'vertrouwelijk - no 2015.csv')
se = InactiveCountry.from_price_curve_file('se' ,path / 'vertrouwelijk - se 2015.csv')
uk = InactiveCountry.from_price_curve_file('uk' ,path / 'vertrouwelijk - uk 2015.csv')
lu = InactiveCountry.from_price_curve_file('lu' ,path / 'vertrouwelijk - oth 2015.csv')
ch = InactiveCountry.from_price_curve_file('ch' ,path / 'vertrouwelijk - oth 2015.csv')
oth = InactiveCountry.from_price_curve_file('oth' ,path / 'vertrouwelijk - oth 2015.csv')

area = Area(nl, be, de, dk, at, fr, no, se, uk, lu, ch, oth)

# Add interconnectors and capacities
be.build_interconnector_to(lu, 680, import_availability=26.0)     # static
be.build_interconnector_to(fr, 3300, export_availability=55.0)    # static
be.build_interconnector_to(nl, 2400, import_availability=58.0)    # dynamic

de.build_interconnector_to(oth, 7815)                             # static
de.build_interconnector_to(fr, 2300, import_availability=78.0)    # static
de.build_interconnector_to(dk, 2765, import_availability=90.0)    # dynamic
de.build_interconnector_to(ch, 4600, import_availability=59.0)    # static
de.build_interconnector_to(nl, 4250)                              # dynamic
de.build_interconnector_to(at, 5400)                              # static

nl.build_interconnector_to(no, 700)                               # static
nl.build_interconnector_to(uk, 1000)                              # static
nl.build_interconnector_to(be, 2400, export_availability=58.0)    # dynamic
nl.build_interconnector_to(de, 4250)                              # dynamic

dk.build_interconnector_to(no, 1640)                              # static
dk.build_interconnector_to(se, 2440, import_availability=81.0)    # static
dk.build_interconnector_to(de, 2765, export_availability=90.0)    # dynamic

# Let's call the ETM to calculate some price-curves and volumes for us
iterations = 2

logger = DataLogger(iterations, [nl, be, de, dk])
area.attach_logger(logger)

# First caluclate with interconnectors disabled
area.calculate_all() # This does the same as nl.calculate /n be.calculate() /n de.calculate()
area.enable_all_interconnectors()

for i in range(1, iterations):
    # Put each other's price curves in!
    area.update_all()

    # And recalculate again!
    area.calculate_all(iteration=i)

logger.plot()
logger.export(path / 'output')
