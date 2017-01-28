function(doc) {
  if(doc.timestamp && doc.bathroom){

    var humidity    = 0;
    var temperature = 0;
    var combustible = 0;

    if (doc.bathroom.humidity   ) { humidity     = doc.bathroom.humidity.value    }
    if (doc.bathroom.temperature) { temperature  = doc.bathroom.temperature.value }
    if (doc.bathroom.combustible) { combustible  = doc.bathroom.combustible.value }

    var data = {"humidity"    : humidity,
                "temperature" : temperature,
                "combustible" : combustible
    };

    emit(doc.timestamp, data);

  }
}