import json

import numpy as np
import numpy.ma as ma
import rasterio as rio
from django.http import HttpResponse
from pyproj import transform, Proj
from rasterio import mask
# Create your views here.
from rest_framework.generics import GenericAPIView
from shapely.geometry import Polygon
from urllib.request import urlretrieve

class NDVIView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        mean_ndvi = []
        for n, feature in enumerate(json_data['features']):
            poly = Polygon(feature['geometry']['coordinates'][0])
            coords_poly = reproject_coordinates(feature['geometry']['coordinates'][0], Proj(init='EPSG:4326'), Proj(init='EPSG:32634'))
            coords = [[poly.bounds[0], poly.bounds[1]], [poly.bounds[2], poly.bounds[3]]]
            min_x, min_y, max_x, max_y = reproject_coordinates(coords, Proj(init='EPSG:4326'), Proj(init='EPSG:32634'), flat=True)
            req_url = "http://127.0.0.1:8600/geoserver/wcs?service=WCS&version=2.0.1&request=getcoverage&coverageid=test:greece&subset=E(%%22%f%%22,%%22%f%%22)&subset=N(%%22%f%%22,%%22%f%%22)" % (
            min_x, max_x, min_y, max_y)
            urlretrieve(req_url, filename='%s.tif'%n)
            with rio.open("%s.tif"%n) as src:
                out_image, out_transform = mask.mask(src, [to_geojson(coords_poly)],
                                                              crop=True, nodata=-9999)
                out_meta = src.meta.copy()
                mean_ndvi.append(str(ma.masked_equal(out_image, -9999).mean()))
        return HttpResponse(', '.join(mean_ndvi))


def reproject_coordinates(coordinates, inproj, outproj, flat=False):
    """
    Given a shapely polygon, reproject the polygon and return in a dictionary usable by rasterio downstream.
    This method iterates over all points within the polygon and reprojects them individually
    :param polygon: polygon to reproject
    :param inproj: input projection (pyproj Proj object)
    :param outproj: output projection (pyproj Proj object)
    :return: dictonary for use within rasterio's mask method
    """
    if flat:
        return np.array([transform(inproj, outproj, coord[0], coord[1]) for coord in coordinates]).flatten()
    return [list(transform(inproj, outproj, coord[0], coord[1])) for coord in coordinates]

def to_geojson(coords):
    return {"type": "Polygon", "coordinates": [coords]}