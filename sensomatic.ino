#include <dht.h>
#include <CmdMessenger.h>
#include <avr/wdt.h>

#define PIN_RX     1 // Serial
#define PIN_TX     2 // Serial
#define PIN_LED_G  3 // LED
#define PIN_D4     4 // Button
#define PIN_DHT    5 // Hum and Temp Sensor
#define PIN_D6     6 // Button
#define PIN_D7     7 // Button
#define PIN_D8     8 // Button
#define PIN_LED_B  9 // LED
#define PIN_LED_R 10 // LED
#define PIN_MOSI  11 // Programming
#define PIN_MISO  12 // Programming
#define PIN_SCK   13 // Programming
#define PIN_A1    A1 //
#define PIN_A2    A2 //
#define PIN_LIGHT A3 // Light
#define PIN_A4    A4 //
#define PIN_A5    A5 // 

#define SAMPLE_DELAY    1000
#define BUTTON_DELAY     500
#define AVERAGE_COUNTER  100
#define NUM_BUTTONS        4

dht          DHT;
CmdMessenger cmdMessenger = CmdMessenger(Serial, ',', ';');
uint32_t     lastSampleTime;
uint32_t     lastButtonTime[NUM_BUTTONS];

enum{
  kAcknowledge,
  kError,
  kSetRgb,
  kSetR,
  kSetG,
  kSetB,
  kGetTemp,
  kGetHumidity,
  kGetLight,
  kTemp,
  kHumidity,
  kLight,
  kButtonPressed,
};

void attachCommandCallbacks(){
  cmdMessenger.attach(              OnUnknownCommand);
  cmdMessenger.attach(kSetRgb,      OnSetRgb        );
  cmdMessenger.attach(kSetR,        OnSetR          );
  cmdMessenger.attach(kSetG,        OnSetG          );
  cmdMessenger.attach(kSetB,        OnSetB          );
  cmdMessenger.attach(kGetTemp,     OnGetTemp       );
  cmdMessenger.attach(kGetHumidity, OnGetHumidity   );
  cmdMessenger.attach(kGetLight,    OnGetLight      );
}

void OnUnknownCommand(){
  cmdMessenger.sendCmd(kError,"Command without attached callback");
}

void OnSetRgb(){
  int16_t r = cmdMessenger.readInt16Arg();
  int16_t g = cmdMessenger.readInt16Arg();
  int16_t b = cmdMessenger.readInt16Arg();

  analogWrite(PIN_LED_R, r);
  analogWrite(PIN_LED_G, g);
  analogWrite(PIN_LED_B, b);

  cmdMessenger.sendCmdStart(kAcknowledge);
}

void OnSetR(){
  int16_t r = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_R, r);
  cmdMessenger.sendCmd(kAcknowledge, r);
}

void OnSetG(){
  int16_t g = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_G, g);
  cmdMessenger.sendCmd(kAcknowledge, g);
}

void OnSetB(){
  int16_t b = cmdMessenger.readInt16Arg();
  analogWrite(PIN_LED_B, b);
  cmdMessenger.sendCmd(kAcknowledge, b);
}

void checkSampleTime(){
  if( (millis() - lastSampleTime) > SAMPLE_DELAY){
    DHT.read22(PIN_DHT);  
    lastSampleTime = millis();
  }
}

void OnGetTemp(){
  checkSampleTime();
  cmdMessenger.sendCmd(kTemp, DHT.temperature);
}

void OnGetHumidity(){
  checkSampleTime();
  cmdMessenger.sendCmd(kHumidity, DHT.humidity);
}

void OnGetLight(){
  uint32_t light = 0;
  for (uint16_t i = 0; i < AVERAGE_COUNTER; i++){
    light += analogRead(PIN_LIGHT);
  }
  cmdMessenger.sendCmd(kLight, light / AVERAGE_COUNTER);
}

void setup() {
  Serial.begin(9600);
  cmdMessenger.printLfCr(true);
  attachCommandCallbacks();
  cmdMessenger.sendCmd(kAcknowledge, "Arduino ready!");
  wdt_enable(WDTO_2S);
  lastSampleTime = 0;
  for(uint8_t i = 0; i < NUM_BUTTONS; i++){
    lastButtonTime[i] = 0;    
  }
  analogWrite(PIN_LED_R, 0);
  analogWrite(PIN_LED_G, 0);
  analogWrite(PIN_LED_B, 0);
  pinMode(PIN_D4, INPUT_PULLUP);
  pinMode(PIN_D6, INPUT_PULLUP);
  pinMode(PIN_D7, INPUT_PULLUP);
  pinMode(PIN_D8, INPUT_PULLUP);
}

void buttonCheck(uint16_t pin, uint8_t button){
  if(!digitalRead(pin)) { 
    if( (millis() - lastButtonTime[button]) > BUTTON_DELAY){
      cmdMessenger.sendCmd(kButtonPressed, button);
      lastButtonTime[button] = millis(); 
    }  
  }
}

void parseButtons(){
  buttonCheck(PIN_D4, 0);
  buttonCheck(PIN_D6, 1);
  buttonCheck(PIN_D7, 2);
  buttonCheck(PIN_D8, 3);
}

void loop() {  
  cmdMessenger.feedinSerialData();
  parseButtons();
  wdt_reset();
}

