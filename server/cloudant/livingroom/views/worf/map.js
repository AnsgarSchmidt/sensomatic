function(doc) {
  if(doc.timestamp && doc.livingroom.worf){
    var center = 0;
    var east = 0;
    var west = 0;
    var moon = 0;
    var watertemp = 0;
    var platetemp = 0;
    var heat = 0;

    if (doc.livingroom.worf.center_cloud) { center = doc.livingroom.worf.center_cloud.value}
    if (doc.livingroom.worf.east_cloud) { east = doc.livingroom.worf.east_cloud.value}
    if (doc.livingroom.worf.west_cloud) { west = doc.livingroom.worf.west_cloud.value}
    if (doc.livingroom.worf.moon && doc.livingroom.worf.moon.value) { moon = doc.livingroom.worf.moon.value}
    if (doc.livingroom.worf.watertemp) { watertemp = doc.livingroom.worf.watertemp.value}
    if (doc.livingroom.worf.platetemp) { platetemp = doc.livingroom.worf.platetemp.value}
    if (doc.livingroom.worf.heatpercent) { heat = doc.livingroom.worf.heatpercent.value}
    
    var data = {"light":
                        {"center": center,
                         "west": west,
                         "east": east,
                         "moon": moon
                        },
                "heat": heat,
                "temp": {"water": watertemp,
                         "plate": platetemp}
    };
    emit(doc.timestamp, data);
  }  
}