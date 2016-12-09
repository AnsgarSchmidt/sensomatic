function(doc) {
  if(doc.timestamp && doc.livingroom.tank){

    var sun       = 0;
    var moon      = 0;
    var heater    = 0;
    var watertemp = 0;
    var settemp   = 0;
    var airtemp   = 0;
    var humidity  = 0;

    if (doc.livingroom.tank.whitelight) { sun       = doc.livingroom.tank.whitelight.value }
    if (doc.livingroom.tank.bluelight)  { moon      = doc.livingroom.tank.bluelight.value  }
    if (doc.livingroom.tank.heater)     { heater    = doc.livingroom.tank.heater.value     }
    if (doc.livingroom.tank.watertemp)  { watertemp = doc.livingroom.tank.watertemp.value  }
    if (doc.livingroom.tank.settemp)    { settemp   = doc.livingroom.tank.settemp.value    }    
    if (doc.livingroom.tank.airtemp)    { airtemp   = doc.livingroom.tank.airtemp.value    }
    if (doc.livingroom.tank.humidity)   { humidity  = doc.livingroom.tank.humidity.value   }
    
    var data = {"sun":       sun,
                "moon":      moon,
                "heater":    heater,
                "watertemp": watertemp,
                "settemp":   settemp,
                "airtemp":   airtemp,
                "humidity":  humidity
    };

    emit(doc.timestamp, data);

  }  
}