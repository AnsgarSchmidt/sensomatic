#include <dht.h>
#include <CmdMessenger.h>
#include <avr/wdt.h>

#define PIN_RX     1 // Serial
#define PIN_TX     2 // Serial
#define PIN_LED_R  3 // LED
#define PIN_D4     4 //
#define PIN_DHT    5 // Hum and Temp Sensor
#define PIN_D6     6 //
#define PIN_D7     7 //
#define PIN_D8     8 //
#define PIN_LED_G  9 // LED
#define PIN_LED_B 10 // LED
#define PIN_MOSI  11 // Programming
#define PIN_MISO  12 // Programming
#define PIN_SCK   13 // Programming
#define PIN_A1    A1 //
#define PIN_A2    A2 //
#define PIN_A3    A3 //
#define PIN_A4    A4 //
#define PIN_A5    A5 // fff

#define sampleDelay 1000

dht          DHT;
CmdMessenger cmdMessenger = CmdMessenger(Serial, ',', ';');
uint32_t     lastSampleTime;

enum{
  kAcknowledge,
  kError,
  kSetRgb,
  kSetR,
  kSetG,
  kSetB,
  kGetTemp,
  kGetHumidity,
};

void attachCommandCallbacks(){
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kSetRgb,   OnSetRgb);
  cmdMessenger.attach(kSetR,        OnSetR);
  cmdMessenger.attach(kSetG,        OnSetG);
  cmdMessenger.attach(kSetB,        OnSetB);
  cmdMessenger.attach(kGetTemp,     OnGetTemp);
  cmdMessenger.attach(kGetHumidity, OnGetHumidity);
}

void OnUnknownCommand(){
  cmdMessenger.sendCmd(kError,"Command without attached callback");
}

void OnSetRgb(){
  cmdMessenger.sendCmd(kAcknowledge);
}

void OnSetR(){
  uint16_t r = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_R, r);
  cmdMessenger.sendCmd(kAcknowledge);
}

void OnSetG(){
  uint16_t g = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_G, g);
  cmdMessenger.sendCmd(kAcknowledge);
}

void OnSetB(){
  uint16_t b = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_B, b);
  cmdMessenger.sendCmd(kAcknowledge);
}

void checkSampleTime(){
  if( (millis() - lastSampleTime) > sampleDelay){
    wdt_reset();
    DHT.read22(PIN_DHT);  
    wdt_reset();
    lastSampleTime = millis();
  }
}

void OnGetTemp(){
  checkSampleTime();
  cmdMessenger.sendCmd(kAcknowledge, DHT.temperature);
}

void OnGetHumidity(){
  checkSampleTime();
  cmdMessenger.sendCmd(kAcknowledge, DHT.humidity);
}

void setup() {
  Serial.begin(9600);
  cmdMessenger.printLfCr(true);
  attachCommandCallbacks();
  cmdMessenger.sendCmd(kAcknowledge, "Arduino ready!");
  wdt_enable(WDTO_2S);
  lastSampleTime = 0;
  analogWrite(PIN_LED_R, 255);
  analogWrite(PIN_LED_G, 255);
  analogWrite(PIN_LED_B, 255);
}

void loop() {  
  cmdMessenger.feedinSerialData();
  wdt_reset();
}


