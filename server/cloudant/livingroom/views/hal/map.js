function(doc) {
  if(doc.timestamp && doc.livingroom && doc.livingroom.hal){

    var loadlevel = 0;
    var cputemp   = 0;
    var fan       = 0;

    if (doc.livingroom.hal.loadlevel ) { loadlevel = doc.livingroom.hal.humidity.value }
    if (doc.livingroom.hal.cputemp   ) { cputemp   = doc.livingroom.hal.cputemp.value  }
    if (doc.livingroom.hal.fan       ) { fan       = doc.livingroom.hal.fan.value      }

    var data = {"loadlevel" : loadlevel,
                "cputemp"   : cputemp,
                "fan"       : fan
    };

    emit(doc.timestamp, data);

  }
}