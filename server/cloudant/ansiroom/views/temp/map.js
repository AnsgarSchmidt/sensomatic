function(doc) {
 if(doc.timestamp && doc.ansiroom.temperature.value){
     emit(doc.timestamp, doc.ansiroom.temperature.value);
    }
}