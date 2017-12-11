function(doc) {
  if(doc.timestamp && doc.coffee){

    var brewing      = 0;
    var idle_heating = 0;
    var grinding     = 0;
    var waterlevel   = 0;
    var carafe       = 0;
    var hotplate     = 0;
    var ready        = 0;

    if (doc.coffee.brewing)      { brewing      = doc.coffee.brewing.value      }
    if (doc.coffee.idle_heating) { idle_heating = doc.coffee.idle_heating.value }
    if (doc.coffee.grinding)     { grinding     = doc.coffee.grinding.value     }
    if (doc.coffee.waterlevel)   { waterlevel   = doc.coffee.waterlevel.value   }
    if (doc.coffee.carafe)       { carafe       = doc.coffee.carafe.value       }
    if (doc.coffee.hotplate)     { hotplate     = doc.coffee.hotplate.value     }
    if (doc.coffee.ready)        { ready        = doc.coffee.ready.value        }

    var data = {"brewing":      brewing,
                "idle_heating": idle_heating,
                "grinding":     grinding,
                "waterlevel":   waterlevel,
                "carafe":       carafe,
                "hotplate":     hotplate,
                "ready":        ready
    };
    emit(doc.timestamp, data);
  }
}
