function(doc) {

 if( doc.timestamp && doc.ansiroom && (doc.ansiroom.co2 || doc.ansiroom.temperature) ){

  	var co2         = 0
  	var temperature = 0

    if (doc.ansiroom.co2)         { co2         = doc.ansiroom.co2.value}
    if (doc.ansiroom.temperature) { temperature = doc.ansiroom.temperature.value}
    
    var data = {"co2":         co2,
                "temperature": temperature
               }

    emit(doc.timestamp, data)
  }

}