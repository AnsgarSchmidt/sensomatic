function(doc, req) {

      if (doc.status != req.query.status){
        return false;
      }

      return true;

}
