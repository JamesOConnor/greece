function sync_get(theUrl) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", theUrl, false); // false for synchronous request
    xmlHttp.send(null);
    return xmlHttp;
}

function sync_post(theUrl, data) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", theUrl, false); // false for synchronous request
    xmlHttp.setRequestHeader("Content-Type", "application/json");
    xmlHttp.send(JSON.stringify(data));
    if (xmlHttp.status !== 404) {
        return JSON.parse(xmlHttp.responseText);
    }
}

function draw_image(geoj) {
    let im = sync_post('image/', geoj);
    image = L.imageOverlay("data:image/png;base64," + im['image'], JSON.parse(im['bounds']));
    image.addTo(mymap);
    return image
}

function make_chart(ndvi_filtered_stats, ndwi_filtered_stats, geoj, boundary) {
    const parsed = {ndvi: [], ranges: [], ndwi: []};
    var ndvifilteredArray = _.filter(ndvi_filtered_stats, function (obj) {
        if (obj['Mean NDVI'] === "--") {
            return obj.ignore;
        } else if (parseFloat(obj['Mean NDVI']) < 0.01) {
            return obj.ignore;
        }
        return obj
    });

    var ndwifilteredArray = _.filter(ndwi_filtered_stats, function (obj) {
        if (obj['Mean NDWI'] === "--") {
            return obj.ignore;
        }
        return obj
    });


    parsed["ndvi"] = _.map(ndvifilteredArray, function (item) {
        val = parseFloat(item['Mean NDVI']);
        return [moment.utc(item.Date).valueOf(), val]
    });

    parsed["ndwi"] = _.map(ndwifilteredArray, function (item) {
        val = parseFloat(item['Mean NDWI']);
        return [moment.utc(item.Date).valueOf(), val]
    });

    console.log(parsed);
    parsed['ranges'] = _.map(ndvifilteredArray, function (item) {
        min_val = parseFloat(item['Min NDVI']);
        max_val = parseFloat(item['Max NDVI']);
        return [moment.utc(item.Date).valueOf(), min_val, max_val];
    });

    Highcharts.chart('chart', {
        xAxis: {type: 'datetime'},
        title: {
            text: 'Data for plot'
        },

        yAxis: {
            title: {
                text: 'NDVI'
            }
        },

        series: [{
            data: parsed["ndvi"],
            tooltip: {
                valueDecimals: 2
            },
            name: 'NDVI'
        },{
            data: parsed["ndwi"],
            tooltip: {
                valueDecimals: 2
            },
            name: 'NDWI'
        },
            {
                data: parsed['ranges'],
                type: 'arearange',
                linkedTo: 'curve',
                color: Highcharts.getOptions().colors[0],
                fillOpacity: 0.3,
                zIndex: 0,
                name: 'Min/max',
                tooltip: {
                    valueDecimals: 2
                },
                marker: {
                    enabled: false
                }
            }],
        plotOptions: {
            series: {
                cursor: 'pointer',
                point: {
                    events: {
                        click: function () {
                            console.log(this);
                            mymap.removeLayer(image);
                            geoj['properties']['layer_name'] = this.series.userOptions.name + ':' + moment(this.x).toDate().toISOString().split('T')[0];
                            geoj['properties']['image_type'] = this.series.userOptions.name;
                            image = draw_image(geoj, boundary);
                            overlays.push(image);
                        }
                    }
                }
            },
            spline: {
                marker: {
                    radius: 4,
                    lineColor: '#666666',
                    lineWidth: 1
                }
            }
        },

    });
}
