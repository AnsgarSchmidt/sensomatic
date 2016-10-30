#include <DHT.h>
#include <CmdMessenger.h>
#include <avr/wdt.h>

#define PIN_RX       1 // Serial
#define PIN_TX       2 // Serial
#define PIN_LED_G    3 // LED G
#define PIN_D4       4 // 
#define PIN_DHT      5 // Hum and Temp Sensor
#define PIN_D6       6 // 
#define PIN_D7       7 // 
#define PIN_D8       8 // 
#define PIN_LED_B    9 // LED B
#define PIN_LED_R   10 // LED R
#define PIN_MOSI    11 // Programming
#define PIN_MISO    12 // Programming
#define PIN_SCK     13 // Programming
#define PIN_BUTTON  A0 // Button
#define PIN_LIGHT   A1 // Light
#define PIN_MOTION  A2 // Motion
#define PIN_COMBUST A3 // Combustible 
#define PIN_A4      A4 //
#define PIN_A5      A5 // 

#define AVERAGE_COUNTER  100

CmdMessenger cmdMessenger          = CmdMessenger(Serial, ',', ';');
DHT          dht(PIN_DHT, DHT22);
bool         reported              = false;
uint64_t     motionreportedCounter = 0;

enum{
  kAcknowledge,     // 0 
  kError,           // 1
  kSetR,            // 2
  kSetG,            // 3
  kSetB,            // 4
  kGetTemp,         // 5
  kGetHumidity,     // 6
  kGetLight,        // 7
  kGetCombustible,  // 8
  knix9,
  kTemp,            // 10          
  kHumidity,        // 11
  kLight,           // 12
  kButtonPressed,   // 13
  kMotionDetected,  // 14 
  kCombustible,     // 15
};

void attachCommandCallbacks(){
  cmdMessenger.attach(                 OnUnknownCommand);
  cmdMessenger.attach(kSetR,           OnSetR          );
  cmdMessenger.attach(kSetG,           OnSetG          );
  cmdMessenger.attach(kSetB,           OnSetB          );
  cmdMessenger.attach(kGetTemp,        OnGetTemp       );
  cmdMessenger.attach(kGetHumidity,    OnGetHumidity   );
  cmdMessenger.attach(kGetLight,       OnGetLight      );
  cmdMessenger.attach(kGetCombustible, OnGetCombustible);
}

void OnUnknownCommand(){
  cmdMessenger.sendCmd(kError,"Command without attached callback");
}

void OnSetR(){
  int16_t r = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_R, r);
  cmdMessenger.sendCmdStart(kAcknowledge);
}

void OnSetG(){
  int16_t g = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_G, g);
  cmdMessenger.sendCmdStart(kAcknowledge);
}

void OnSetB(){
  int16_t b = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_B, b);
  cmdMessenger.sendCmdStart(kAcknowledge);
}

void OnGetTemp(){
  cmdMessenger.sendCmd(kTemp, dht.readTemperature());
}

void OnGetHumidity(){
  cmdMessenger.sendCmd(kHumidity, dht.readHumidity());
}

void OnGetLight(){
  uint32_t light = 0;
  for (uint8_t i = 0; i < AVERAGE_COUNTER; i++){
    light += analogRead(PIN_LIGHT);
  }
  cmdMessenger.sendCmd(kLight, light / AVERAGE_COUNTER);
}

void OnGetCombustible(){
  uint32_t comp = 0;
  for (uint8_t i = 0; i < AVERAGE_COUNTER; i++){
    comp += analogRead(PIN_COMBUST);
  }
  cmdMessenger.sendCmd(kCombustible, comp / AVERAGE_COUNTER);  
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  cmdMessenger.printLfCr(true);
  attachCommandCallbacks();
  wdt_enable(WDTO_1S);
  analogWrite(PIN_LED_R, 0);
  analogWrite(PIN_LED_G, 0);
  analogWrite(PIN_LED_B, 0);
  pinMode(PIN_LIGHT,   INPUT);
  pinMode(PIN_BUTTON,  INPUT);
  pinMode(PIN_COMBUST, INPUT);
  cmdMessenger.sendCmd(kAcknowledge, "Arduino ready!");
}

void checkButtons(){
  uint32_t button = 0;
  for (uint8_t i = 0; i < AVERAGE_COUNTER; i++){
    uint16_t b = analogRead(PIN_BUTTON);
    if (b < 400) {
      reported = false;
      return; 
    }
    button += b;
  }
  button /= AVERAGE_COUNTER;

  if(button > 976){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 1);    
      reported = true;
    }
  }

  if(button > 890){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 2);    
      reported = true;
    }
  }

  if(button > 820){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 3);    
      reported = true;
    }
  }

  if(button > 760){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 4);    
      reported = true;
    }
  }

  if(button > 705){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 5);    
      reported = true;
    }
  }

  if(button > 660){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 6);    
      reported = true;
    }
  }

  if(button > 620){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 7);    
      reported = true;
    }
  }

  if(button > 585){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 8);    
      reported = true;
    }
  }

  if(button > 555){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 9);    
      reported = true;
    }
  }

  if(button > 525){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 10);    
      reported = true;
    }
  }

  if(button > 500){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 11);    
      reported = true;
    }
  }

  if(button > 480){
    if(!reported){
      cmdMessenger.sendCmd(kButtonPressed, 12);    
      reported = true;
    }
  }

}

void checkMotion(){
   bool motion = digitalRead(PIN_MOTION);
   if (motion){
    if (motionreportedCounter == 0){
     cmdMessenger.sendCmd(kMotionDetected, 23);    
    }
    motionreportedCounter++;
    if (motionreportedCounter > 50000){
      motionreportedCounter = 0;
    }
   }else{
    motionreportedCounter = 0;
   }
}

void loop() {  
  cmdMessenger.feedinSerialData();
  wdt_reset();
  checkButtons();
  checkMotion();
}
