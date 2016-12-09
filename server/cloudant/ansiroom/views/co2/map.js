function(doc) {
 if(doc.timestamp && doc.ansiroom.co2.value){
     emit(doc.timestamp, doc.ansiroom.co2.value);
    }
}