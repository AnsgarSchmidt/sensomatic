function(doc) {
  if(doc.timestamp && doc.cortex){

    var NEWG_RX = 0;
    var NEWG_TX = 0;
    var WAN_RX  = 0;
    var WAN_TX  = 0;
    var OLDG_RX = 0;
    var OLDG_TX = 0;

    if (doc.cortex.cortex.rx)    { NEWG_RX = doc.cortex.cortex.rx.value}
    if (doc.cortex.cortex.tx)    { NEWG_TX = doc.cortex.cortex.tx.value}
    if (doc.cortex.phawxansi.rx) { OLDG_RX = doc.cortex.phawxansi.rx.value}
    if (doc.cortex.phawxansi.tx) { OLDG_TX = doc.cortex.phawxansi.tx.value}
    if (doc.cortex.wan.rx)       { WAN_RX  = doc.cortex.wan.rx.value}
    if (doc.cortex.wan.tx)       { WAN_TX  = doc.cortex.wan.tx.value}

    var data = {"WAN":
                        {"RX": WAN_RX,
                         "TX": WAN_TX
                        },
                "5G":
                        {"RX": NEWG_RX,
                         "TX": NEWG_TX
                        },
                "2.4G":
                        {"RX": OLDG_RX,
                         "TX": OLDG_TX
                        }
    };
    emit(doc.timestamp, data);
  }
}