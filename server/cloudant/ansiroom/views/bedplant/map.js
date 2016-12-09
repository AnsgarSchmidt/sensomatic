function(doc) {
 if(doc.timestamp && doc.ansiroom.bed.plant.value){
     emit(doc.timestamp, doc.ansiroom.bed.plant.value);
    }
}