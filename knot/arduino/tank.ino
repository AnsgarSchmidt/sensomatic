#include <DallasTemperature.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <OneWire.h>
#include <Ticker.h>
#include <DHT.h>

#define DALLAS_PIN                            2
#define DHT_PIN                               4
#define DHT_TYPE                          DHT22
#define FURTILIZER_PIN                       15
#define FURTILIZER_TIME                     1.3
#define HEATER_PIN                           13
#define HEATER_DELTA                        0.0 
#define WHITE_LED_PIN                        12
#define BLUE_LED_PIN                         14
#define WATER_LEVEL_PIN                       5
#define SSID                        "XXX"
#define SSID_PASSWD      "XXX"
#define MQTT_SERVER                    "cortex"
#define MQTT_CLIENT                "TankClient"
#define TEMP_CAL                          23.00
#define TEMP_MEASURE                      23.00
#define TEMP_DELTA    (TEMP_CAL - TEMP_MEASURE)

WiFiClient                           espClient;
PubSubClient                   mqtt(espClient);
OneWire                    oneWire(DALLAS_PIN);
DallasTemperature             dallas(&oneWire);
DeviceAddress                    dallasAddress;
DHT                     dht(DHT_PIN, DHT_TYPE);
Ticker                        furtilizerTicker;
char                                  msg[500];
uint64_t                           counter = 0;
float                          watertemp = 0.0;
float                            airtemp = 0.0;
float                           humidity = 0.0;
float                           settemp = 23.0;
bool                          heaterON = false;
bool                           waterOK = false;

void setup() {
  Serial.begin(115200);
  pinMode(     LED_BUILTIN,     OUTPUT      );
  digitalWrite(LED_BUILTIN,     FALSE       );
  pinMode(     FURTILIZER_PIN,  OUTPUT      );
  digitalWrite(FURTILIZER_PIN,  TRUE        );
  pinMode(     HEATER_PIN,      OUTPUT      );
  digitalWrite(HEATER_PIN,      FALSE       );
  analogWrite( WHITE_LED_PIN,   PWMRANGE    );
  analogWrite( BLUE_LED_PIN,    PWMRANGE    );
  pinMode(     WATER_LEVEL_PIN, INPUT       ); //Pullup in hardware
  setup_wifi();
  delay(100);
  mqtt.setServer(MQTT_SERVER, 1883);
  mqtt.setCallback(callback);
  mqttConnector();
  delay(100);
  dallas.begin();
  dallas.setWaitForConversion(true);
  dallas.getAddress(dallasAddress, 0);
  dallas.setResolution(dallasAddress, TEMP_12_BIT);
  dallas.setResolution(TEMP_12_BIT);
  Serial.print("Number of found dallas Sensors:");
  Serial.println(dallas.getDeviceCount());
  delay(100);
  dht.begin();
}

void setup_wifi() {
  delay(100);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(SSID);

  WiFi.begin(SSID, SSID_PASSWD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void furtilizerOn(){
  digitalWrite(FURTILIZER_PIN, FALSE);           
  furtilizerTicker.attach(FURTILIZER_TIME, furtilizerOff);
  Serial.println("Starting Furtilizer Pump");
}

void furtilizerOff(){
  digitalWrite(FURTILIZER_PIN, TRUE); 
  furtilizerTicker.detach();
  Serial.println("Stop Furtilizer Pump");
}

void callback(char* topic, byte* payload, unsigned int length) {
  String s = String(topic);
  char vchar[50];
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (uint8_t i = 0; i < length; i++) {
    vchar[i] = payload[i];
  }
  vchar[length] = '\0';
  Serial.println(vchar);
  double dval = atof(vchar);
   
  if (String("livingroom/tank/settemp") == s){
    Serial.print("Settemp ");
    if(dval < 29){
      settemp = dval;      
      Serial.println(settemp);
    }
  }
  
  if (String("livingroom/tank/fertilizer") == s){
    Serial.println("fertilizer");
    if(dval){
      furtilizerOn();
    }
  }

  if (String("livingroom/tank/whitelight") == s){
    Serial.print("White:");
    if(dval >= 0 && dval <= 100){
      analogWrite(WHITE_LED_PIN, map(int(100 - dval), 0, 100, 0, PWMRANGE));      
    }
    Serial.println(int(dval));
  }

  if (String("livingroom/tank/bluelight") == s){
    Serial.println("Blue:");
    if(dval >= 0 && dval <= 100){
      analogWrite(BLUE_LED_PIN, map(int(100 - dval), 0, 100, 0, PWMRANGE));      
    }
    Serial.println(int(dval));
  }

}

void mqttConnector() {
  while (!mqtt.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqtt.connect(MQTT_CLIENT)) {
      Serial.println("connected");
      snprintf(msg, sizeof(msg), "%ld", millis());
      mqtt.publish("livingroom/tank/online", msg);
      mqtt.subscribe("livingroom/tank/settemp");
      mqtt.subscribe("livingroom/tank/fertilizer");
      mqtt.subscribe("livingroom/tank/whitelight");
      mqtt.subscribe("livingroom/tank/bluelight");      
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void measure(){
  waterOK = digitalRead(WATER_LEVEL_PIN);
  
  dallas.requestTemperatures();
  
  float t = 0;
  
  t = dallas.getTempC(dallasAddress);
  if(t <= 40 && t >= 10){
    watertemp = t;  
  }else{
    mqtt.publish("livingroom/tank/error", "watertemp");        
  }

  t = dht.readTemperature();
  if(t <= 50 && t >= 5){
    airtemp = t;
  }else{
    mqtt.publish("livingroom/tank/error", "airtemp");            
  }

  t = dht.readHumidity();
  if(t <= 100 && t >= 10){
    humidity = t;
  }else{
    mqtt.publish("livingroom/tank/error", "humidity");                
  }
}

void msgString(float f){
  uint8_t h = floor(f); 
  uint8_t l = (f - h) * pow(10, 2);
  snprintf (msg, sizeof(msg), "%d.%02d", h, l);      
}

void sendMessage(){  
  snprintf(msg, sizeof(msg), "%ld", millis());
  mqtt.publish("livingroom/tank/uptime", msg);
  msgString(watertemp);
  mqtt.publish("livingroom/tank/watertemp", msg);  
  msgString(airtemp + TEMP_DELTA);
  mqtt.publish("livingroom/tank/airtemp", msg);  
  msgString(humidity);
  mqtt.publish("livingroom/tank/humidity", msg);      
  msgString(float(heaterON));
  mqtt.publish("livingroom/tank/heater", msg);
  msgString(float(waterOK));
  mqtt.publish("livingroom/tank/waterlevel", msg);        
}

void heaterCheck(){
  if(!heaterON && watertemp < (settemp - HEATER_DELTA)){
    digitalWrite(HEATER_PIN, true);   
    heaterON = true;
  }

  if(heaterON && watertemp > (settemp + HEATER_DELTA)){
    digitalWrite(HEATER_PIN, false);   
    heaterON = false;
  }
}

void loop() {
  yield();
  mqttConnector();
  yield();
  mqtt.loop();
  yield();
  counter++;
  yield();
  if(counter > 1000){
    digitalWrite(LED_BUILTIN, LOW);
    measure();
    yield();
    heaterCheck();
    yield();
    sendMessage();
    counter = 0;
    digitalWrite(LED_BUILTIN, HIGH);
  }
  delay(10);
}
