#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <Ticker.h>
#include <DHT.h>

#define DHT_PIN                               6
#define HUMIDIFIER_PIN                        5
#define PUMP_PIN                              6
#define UVLED_PIN                             7
#define FAN_PIN                               8
#define WATERLEVEL_LOW_PIN                    9
#define WATERLEVEL_HIGH_PIN                  10
#define SOIL_MEASURE_PIN                     A0
#define DHT_TYPE                          DHT22
#define SSID                        "XXX"
#define SSID_PASSWD      "XXX"
#define MQTT_SERVER                    "cortex"
#define MQTT_CLIENT     "LivingRoomPlantClient"
#define TEMP_CAL                          23.80
#define TEMP_MEASURE                      22.89
#define TEMP_DELTA    (TEMP_CAL - TEMP_MEASURE)
#define PRE_HUMIDIFIER_TIMER                0.8
#define HUMIDIFIER_TIMER                    0.7
#define HUMIDIFIER_TIMER_COUNTS              15
#define PRE_PUMP_TIMER                      1.1
#define PUMP_TIMER                          4.2

WiFiClient                           espClient;
PubSubClient                   mqtt(espClient);
DHT                     dht(DHT_PIN, DHT_TYPE);
Ticker                           prePumpTicker;
Ticker                              pumpTicker;
Ticker                       preHumidifyTicker;
Ticker                          humidifyTicker;
char                                  msg[500];
uint64_t                           counter = 0;
uint8_t                         humcounter = 0;
float                            airtemp = 0.0;
float                           humidity = 0.0;
bool                     highwatermark = false;
bool                      lowwatermark = false;
float                               soil = 0.0;
bool                      humidifieron = false;

void setup() {
  Serial.begin(115200);
  pinMode(     HUMIDIFIER_PIN, OUTPUT  );
  digitalWrite(HUMIDIFIER_PIN, true    );  
  setup_wifi();
  delay(100);
  mqtt.setServer(MQTT_SERVER, 1883);
  mqtt.setCallback(callback);
  mqttConnector();
  delay(100);
  //dht.begin();
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

void PreHumidifier(){
  Serial.println("PreHumidifier");
  preHumidifyTicker.attach(PRE_HUMIDIFIER_TIMER, HumidifierOn);
}

void HumidifierOn(){
  Serial.println("HumidifierON");
  preHumidifyTicker.detach();
  humcounter = HUMIDIFIER_TIMER_COUNTS;
  humidifyTicker.attach(HUMIDIFIER_TIMER, HumidifierToggle);
}

void HumidifierToggle(){
  if(humcounter--){
    if(humidifieron){
      Serial.println("Humi OFF");
      humidifieron = false;
      digitalWrite(HUMIDIFIER_PIN, true);            
    }else{
      Serial.println("Humi ON");
      digitalWrite(HUMIDIFIER_PIN, false);            
      humidifieron = true;
    }
  }else{
    Serial.println("Switching Humidity Timer OFF");
    humidifyTicker.detach();
    humidifieron = false;    
    digitalWrite(HUMIDIFIER_PIN, true);      
  }  
}

void PrePump(){
  Serial.print("PrePump");
  prePumpTicker.attach(PRE_PUMP_TIMER, PumpOn);
}

void PumpOn(){
  Serial.print("PumpON");
  prePumpTicker.detach();
  pumpTicker.attach(PUMP_TIMER, PumpOff);
}

void PumpOff(){
  Serial.print("PumpOFF");
  pumpTicker.detach();
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
   
  if (String("livingroom/humidifier") == s){
    Serial.print("Humidify");
    PreHumidifier();
  }

  if (String("livingroom/plant/water") == s){
    Serial.print("Water");
    PrePump();
  }
  
}

void mqttConnector() {
  while (!mqtt.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqtt.connect(MQTT_CLIENT)) {
      Serial.println("connected");
      snprintf(msg, sizeof(msg), "%ld", millis());
      mqtt.publish("livingroom/plant/online", msg);
      mqtt.subscribe("livingroom/humidifier");
      mqtt.subscribe("livingroom/plant/water");
      mqtt.subscribe("livingroom/plant/light");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void measure(){
  airtemp   = dht.readTemperature();
  humidity  = dht.readHumidity();
}

void msgString(float f){
  uint8_t h = floor(f); 
  uint8_t l = (f - h) * pow(10, 2);
  snprintf (msg, sizeof(msg), "%d.%02d", h, l);      
}

void sendMessage(){  
  msgString(airtemp + TEMP_DELTA);
  mqtt.publish("livingroom/plant/airtemp", msg);  
  msgString(humidity);
  mqtt.publish("livingroom/plant/humidity", msg);      
  msgString(highwatermark);
  mqtt.publish("livingroom/plant/waterlevelhigh", msg);      
  msgString(lowwatermark);
  mqtt.publish("livingroom/plant/waterlevellow", msg);
  msgString(soil);
  mqtt.publish("livingroom/plant/soil", msg);        
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
    //measure();
    yield();
    sendMessage();
    counter = 0;
  }
  delay(10);
}
