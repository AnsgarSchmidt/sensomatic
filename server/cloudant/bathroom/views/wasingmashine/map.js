function(doc) {

   if(doc.timestamp && doc.bathroom && doc.bathroom.washingmachine && doc.bathroom.washingmachine.state){

     if (doc.bathroom.washingmachine.state.value == 1 && doc.bathroom.washingmachine.current.value > 0.04){
         emit(doc.timestamp, doc.bathroom.washingmachine.current.value);
     }

   }

}
