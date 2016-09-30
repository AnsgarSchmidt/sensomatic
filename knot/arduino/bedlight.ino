#include "FastLED.h"
#include <avr/wdt.h>

#define OVERHEAD                  0
#define NUM_LEDS_OVERHEAD        20
#define PIN_OVERHEAD              2

#define SLEEP                     1
#define NUM_LEDS_SLEEP          144
#define PIN_SLEEP                 3

#define BED_LEFT                  2
#define NUM_LEDS_BED_LEFT        18
#define BED_CENTER                3
#define NUM_LEDS_BED_CENTER      14
#define NUM_LEDS_BED_LEFT_CENTER (NUM_LEDS_BED_LEFT + NUM_LEDS_BED_CENTER)
#define PIN_BED_LEFT_CENTER       4
 
#define BED_RIGHT                 4
#define NUM_LEDS_BED_RIGHT       18
#define PIN_BED_RIGHT             5

#define COOLING                  80
#define SPARKING                120
#define INTENSITYDIFF            95

#define SECOND                 1000
#define MINUTE        (60 * SECOND)
#define HOUR          (60 * MINUTE)

#define PLANT_MEASURE_PIN        A0
#define PLANT_ENABLE_PIN         10
#define PLANT_ENABLE_DELTA       23
#define PLANT_UPDATE_VALUE    30000
#define PLANT_ENABLE_COUNTER  (PLANT_UPDATE_VALUE - PLANT_ENABLE_DELTA)

#define COMMAND_RGB               0
#define COMMAND_HSV               1
#define COMMAND_FIRE              2

#define DATA_SIZE            (50*3)

CRGB     OverheadLeds      [NUM_LEDS_OVERHEAD        ];
CRGB     SleepLeds         [NUM_LEDS_SLEEP           ];
CRGB     BedLedsLeftCenter [NUM_LEDS_BED_LEFT_CENTER ];
CRGB     BedLedsRight      [NUM_LEDS_BED_RIGHT       ];

         uint16_t PlantCounter    = 0;

volatile bool     newCommand      = false;
volatile uint8_t  DataIndex       = 0;
volatile uint8_t  Command         = 0;
volatile uint8_t  Device          = 0;
volatile uint8_t  data[DATA_SIZE];
volatile uint8_t  SleepFireActive = 0;
volatile uint8_t  BedFireActive   = 0;

void setup() {

  wdt_enable(WDTO_250MS);
  wdt_reset();

  Serial.begin(9600);

  pinMode(PLANT_ENABLE_PIN, OUTPUT); 

  FastLED.addLeds<WS2811,  PIN_OVERHEAD,        RBG>(OverheadLeds,      NUM_LEDS_OVERHEAD        ).setCorrection( TypicalLEDStrip );
  FastLED.addLeds<WS2812B, PIN_SLEEP,           GRB>(SleepLeds,         NUM_LEDS_SLEEP           ).setCorrection( TypicalLEDStrip );
  FastLED.addLeds<WS2811,  PIN_BED_LEFT_CENTER, BRG>(BedLedsLeftCenter, NUM_LEDS_BED_LEFT_CENTER ).setCorrection( TypicalLEDStrip );
  FastLED.addLeds<WS2811,  PIN_BED_RIGHT,       BRG>(BedLedsRight,      NUM_LEDS_BED_RIGHT       ).setCorrection( TypicalLEDStrip );

  wdt_reset();

  FastLED.clear(true);
  FastLED.show();

  PlantCounter = 0;

  wdt_reset();

}

void serialEvent() {
  
  while (Serial.available()) {
  
    uint8_t c = (uint8_t)Serial.read();

    if (c == ';') {
      newCommand  = true;
      DataIndex       = 0;
    } else {
      switch(DataIndex){
        case 0:
          Command = c;
          break;  
        case 1:
          Device = c;
          break;
        default:     
          data[(DataIndex - 2)] = c;
          if(Command == COMMAND_FIRE && Device == SLEEP){
            SleepFireActive  = c;
          }
          if(Command == COMMAND_FIRE && Device == BED_CENTER){
            BedFireActive    = c;
          }
          break;
      }
      DataIndex++;     
    }
  }
}

void processCommand(){
  if(Command == COMMAND_HSV){
    if(Device == OVERHEAD){
      for(uint8_t i = 0; i < NUM_LEDS_OVERHEAD; i++){ 
        OverheadLeds[i] = CHSV(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == SLEEP){ 
      for(uint8_t i = 0; i < NUM_LEDS_SLEEP; i++){ 
        SleepLeds[i] = CHSV(data[0], data[1], data[2]);
      } 
    }
    if(Device == BED_LEFT){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_LEFT; i++){ 
        BedLedsLeftCenter[NUM_LEDS_BED_CENTER + i] = CHSV(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == BED_CENTER){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_CENTER; i++){ 
        BedLedsLeftCenter[i] = CHSV(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == BED_RIGHT){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_RIGHT; i++){       
        BedLedsRight[i] = CHSV(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
  }
  if(Command == COMMAND_RGB){
    if(Device == OVERHEAD){
      for(uint8_t i = 0; i < NUM_LEDS_OVERHEAD; i++){ 
        OverheadLeds[i] = CRGB(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == SLEEP){ 
      for(uint8_t i = 0; i < NUM_LEDS_SLEEP; i++){
        SleepLeds[i] = CRGB(data[0], data[1], data[2]);
      } 
    }
    if(Device == BED_LEFT){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_LEFT; i++){ 
        BedLedsLeftCenter[NUM_LEDS_BED_CENTER + i] = CRGB(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == BED_CENTER){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_CENTER; i++){ 
        BedLedsLeftCenter[i] = CRGB(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
    if(Device == BED_RIGHT){ 
      for(uint8_t i = 0; i < NUM_LEDS_BED_RIGHT; i++){       
        BedLedsRight[i] = CRGB(data[(i*3) + 0], data[(i*3) + 1], data[(i*3) + 2]); 
      }
    }
  }
  for(uint8_t i = 0; i < DATA_SIZE; i++){
    data[i] = 0;
  }
  newCommand = false;
}

void plantCheck(){

  PlantCounter++;

  if (PlantCounter > PLANT_ENABLE_COUNTER){
    digitalWrite(PLANT_ENABLE_PIN, HIGH);
  }else{
    digitalWrite(PLANT_ENABLE_PIN, LOW);
  }

  if (PlantCounter > PLANT_UPDATE_VALUE){
    Serial.println(analogRead(PLANT_MEASURE_PIN));
    digitalWrite(PLANT_ENABLE_PIN, LOW);
    PlantCounter = 0;
  }
  
}

void loop() {

  wdt_reset();

  plantCheck();

  if(SleepFireActive > 0){
     SleepFire(SleepFireActive);
  }

  if(BedFireActive > 0){
     BedFire(BedFireActive);
  }

  if(newCommand){
    processCommand();
  }

  FastLED.show();
}

void BedFire(uint8_t intensity){
  // Array of temperature readings at each simulation cell
  static uint8_t heat  [25];
         uint8_t num  = 25;
         uint8_t low  = 0;
         uint8_t high = intensity;
         
  if (intensity < INTENSITYDIFF) {
    low  = 0;
  } else {
    low  = intensity - INTENSITYDIFF;
  }

  // Step 1.  Cool down every cell a little
  for (uint8_t i = 0; i < num; i++) {
    heat[i] = qsub8( heat[i],  random8(0, ((COOLING * 10) / num) + 2));
  }

  // Step 2.  Heat from each cell drifts 'up' and diffuses a little
  for (uint8_t k = num - 1; k >= 2; k--) {
    heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2] ) / 3;
  }

  // Step 3.  Randomly ignite new 'sparks' of heat near the bottom
  if ( random8() < SPARKING ) {
    int y = random8(7); //160 255
    heat[y] = qadd8( heat[y], random8(low, high) );
  }

  // Step 4.  Map from heat cells to LED colors
  for ( int j = 0; j < num; j++) {
    CRGB color = HeatColor(heat[j]);
      BedLedsLeftCenter[7 + j] = color;
      if(j < 7){
        BedLedsLeftCenter[6 - j] = color;        
      }else{
        BedLedsRight     [j - 7] = color;        
      }
      if(j < 10){
        OverheadLeds[10 - 1 - j] = color;
        OverheadLeds[10     + j] = color;
      }
  }  
}

void SleepFire(uint8_t intensity){
  // Array of temperature readings at each simulation cell
  static uint8_t heat  [NUM_LEDS_SLEEP / 2];
         uint8_t num  = NUM_LEDS_SLEEP / 2;
         uint8_t low  = 0;
         uint8_t high = intensity;
         
  if (intensity < INTENSITYDIFF) {
    low  = 0;
  } else {
    low  = intensity - INTENSITYDIFF;
  }

  // Step 1.  Cool down every cell a little
  for (uint8_t i = 0; i < num; i++) {
    heat[i] = qsub8( heat[i],  random8(0, ((COOLING * 10) / num) + 2));
  }

  // Step 2.  Heat from each cell drifts 'up' and diffuses a little
  for (uint8_t k = num - 1; k >= 2; k--) {
    heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2] ) / 3;
  }

  // Step 3.  Randomly ignite new 'sparks' of heat near the bottom
  if ( random8() < SPARKING ) {
    int y = random8(7); //160 255
    heat[y] = qadd8( heat[y], random8(low, high) );
  }

  // Step 4.  Map from heat cells to LED colors
  for ( int j = 0; j < num; j++) {
    CRGB color = HeatColor(heat[j]);
      SleepLeds[num - 1 - j] = color;
      SleepLeds[num     + j] = color;
  }
}
