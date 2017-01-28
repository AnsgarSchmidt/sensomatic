function(doc) {
  if(doc.timestamp && doc.bathroom){

    var humidity    = 0;
    var temperature = 0;

    if (doc.livingroom.humidity   ) { humidity     = doc.livingroom.humidity.value    }
    if (doc.livingroom.temperature) { temperature  = doc.livingroom.temperature.value }

    var data = {"humidity"    : humidity,
                "temperature" : temperature
    };

    emit(doc.timestamp, data);

  }
}