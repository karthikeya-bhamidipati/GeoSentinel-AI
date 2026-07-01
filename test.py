from shapely.geometry import Polygon

from src.eo.aoi.geometry import AOI
from src.eo.aoi.validator import AOIValidator

polygon = Polygon(

    [

        (78.35, 17.25),

        (78.40, 17.25),

        (78.40, 17.30),

        (78.35, 17.30),

    ]

)

aoi = AOI(polygon)

validator = AOIValidator()

validator.validate(aoi)

print("AOI Valid")