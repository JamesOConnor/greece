import base64
import json
import logging
import os
import uuid
from io import BytesIO
from urllib.request import urlretrieve

import numpy as np
import numpy.ma as ma
import rasterio as rio
import requests
from PIL import Image
from django.conf import settings
from django.http import HttpResponse
from matplotlib import cm
from pyproj import Proj
from rasterio import mask
# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView

from ndvi.queries import clip_image, generate_request, reproject_coordinates, to_geojson, color_image

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)
colormaps = {'NDVI': cm.Greens, 'NDWI': cm.Blues}

class ListLayersView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        layers_url = 'http://geoserver:8080/geoserver/rest/layers/'
        layers_on_server = requests.get(layers_url, auth=(settings.GEOSERVER_USER, settings.GEOSERVER_PASS)).json()
        ndvi_names = [i['name'] for i in layers_on_server['layers']['layer'] if 'NDVI' in i['name']]
        ndwi_names = [i['name'] for i in layers_on_server['layers']['layer'] if 'NDWI' in i['name']]
        layer_names = {'ndvi': ndvi_names, 'ndwi': ndwi_names}
        return HttpResponse(json.dumps(layer_names))


class ColorView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        color = float(self.request.GET.get('color'))
        image_type = self.request.GET.get('type')
        color_triplet = (np.array(colormaps.get(image_type)(color)[:3]) * 255).astype(np.uint8)
        return HttpResponse('#%02x%02x%02x' % tuple(color_triplet))


class ImageView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        image_type = data['properties']['image_type']
        coords_poly, layer_name, req_url = generate_request(data, out_crs='EPSG:3857')
        with rio.open(req_url) as src:
            out_image, out_transform = mask.mask(src, [to_geojson(coords_poly)],
                                                 crop=False, nodata=-9999)
            masked_image = ma.masked_equal(out_image, -9999)
        bounds2 = [[out_transform[2], out_transform[5]], [out_transform[2] + out_transform[0] * out_image.shape[2],
                                                          out_transform[5] + out_image.shape[1] * out_transform[4]]]
        min_x2, min_y2, max_x2, max_y2 = reproject_coordinates(bounds2, Proj(init='EPSG:3857'), Proj(init='EPSG:4326'),
                                                               flat=True)
        bounds = ((min_y2, min_x2), (max_y2, max_x2))
        sio = BytesIO()
        im = Image.fromarray(np.uint8(color_image(image_type, masked_image)))
        im.save(sio, 'png')
        sio.seek(0)
        return HttpResponse(json.dumps({'image': base64.b64encode(sio.read()).decode(), 'bounds': json.dumps(bounds)}))


class StatsView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        image_type = data['properties']['image_type']
        coords_poly, layer_name, req_url = generate_request(data)
        fname = str(uuid.uuid4())
        try:
            urlretrieve(req_url, filename='%s.tif' % fname)
        except:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        masked_image = clip_image(coords_poly, fname)
        os.remove('%s.tif' % fname)
        return HttpResponse(json.dumps({'Date': layer_name.split(':')[1],
                                        'Mean {image_type}'.format(image_type=image_type): str(masked_image.mean()),
                                        'Median {image_type}'.format(image_type=image_type): str(ma.median(masked_image)),
                                        'Min {image_type}'.format(image_type=image_type): str(ma.min(masked_image)),
                                        'Max {image_type}'.format(image_type=image_type): str(ma.max(masked_image))}))
