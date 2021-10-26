'''The bottom up experiment'''

from lib.models import Country, Area
from lib.logger import DataLogger

# Setup the coutries and put them in an Area for enabling 'all' methods
nl = Country('nl')
de = Country('de')
be = Country('be')

area = Area(nl, be, de)

# Add interconnectors and capacities
nl.build_interconnector_to(de, 3000)
nl.build_interconnector_to(be, 3000)

de.build_interconnector_to(nl, 3000)
de.build_interconnector_to(be, 3000)

be.build_interconnector_to(nl, 3000)
be.build_interconnector_to(de, 3000)

# Let's call the ETM to calculate some price-curves and volumes for us
iterations = 2

logger = DataLogger(iterations, [nl, be, de])
area.attach_logger(logger)

# First caluclate with interconnectors disabled
area.calculate_all() # This does the same as nl.calculate /n be.calculate() /n de.calculate()
area.enable_all_interconnectors()

for i in range(1, iterations):
    # Put each other's price curves in!
    area.update_all()

    # And recalculate again!
    area.calculate_all(iteration=i)

print(logger.prices)
logger.plot()
