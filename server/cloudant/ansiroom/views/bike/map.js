function(doc) {

 if(doc.timestamp && doc.bike.battery.value){

     emit(doc.timestamp, doc.bike.battery.value);

    }

}
