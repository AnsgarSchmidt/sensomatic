function(doc) {
   if(doc.timestamp && doc.bathroom.humidity.value){
     emit(doc.timestamp, doc.bathroom.humidity.value);
    }
}