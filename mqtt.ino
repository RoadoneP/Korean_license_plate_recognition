#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <Ultrasonic.h>
#include <String.h>

// Global variables Setting
unsigned long startMillis; 
unsigned long currentMillis;

const unsigned long count = 1000; // milliseconds
bool detected = false;
int inTime = 0; // how long detected
int period = 30; // 3 minutes setting

// Function prototypes
void subscribeReceive(char* topic, byte* payload, unsigned int length);

// Set your MAC address and IP address here
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(0, 0, 0, 0);

// MQTT Server Setting
// const char* server = "test.mosquitto.org";
const char* server = "0.0.0.0";
 
// Ethernet and MQTT related objects
EthernetClient ethClient; // control ethernet
PubSubClient mqttClient(ethClient); // takes the Ethernet object

Ultrasonic ultrasonic(2, 3); // (Trig PIN, Echo PIN)

void setup()
{
  // Enable Serial port
  Serial.begin(9600); 

  // Start the ethernet connection
  Ethernet.begin(mac, ip);              
  
  // Ethernet takes some time to boot!
  delay(3000);                          
 
  // Set the MQTT server to the server stated above ^
  mqttClient.setServer(server, 1883);   
 
  // Attempt to connect to the server with the ID "myClientID"
  if (mqttClient.connect("myClientID")) 
  {
    Serial.println("Connection has been established, well done!"); 
    
    // Establish the subscribe event
    mqttClient.setCallback(subscribeReceive);
  } 
  else 
  {
    Serial.println("Looks like the server connection failed...");
  }

  // initial start time
  startMillis = millis(); 
}

void loop()
{
  // This is needed at the top of the loop!
  mqttClient.loop();

  // Time Count implementation
  Serial.print("Start time: ");
  Serial.println(startMillis);
  
  Serial.print("Current time: ");
  Serial.println(inTime);
  
  currentMillis = millis();  // get the current time (the number of milliseconds since the program started)
  Serial.print("CurrentMillis: ");
  Serial.println(currentMillis);

  if (inTime == period) { // when enough period passed
    detected = true;
    
    // MQTT Publish Implementation
    mqttClient.subscribe("test"); // Subscribe Topic
    
    if (mqttClient.publish("test", "A1 - In")) {
      Serial.println("Published MQTT message successfully :)");
    }
    else {
      Serial.println("Could not publish MQTT message :(");
    }

    // To reduce overload server
    delay(4000);
  }
  
  if (currentMillis - startMillis >= count)  // test whether the period has elapsed
  {
    Serial.println("1 second passed");
    startMillis = currentMillis;

    int len = ultrasonic.Ranging(CM);
    Serial.print(len);
    Serial.println("cm");
    
    if (len < 51) { // when In Range
      inTime += 1;
    }

    else { // when Out of Range
      if (detected == true) {
        if (mqttClient.publish("test", "A1 - Out")) {
          Serial.println("Published MQTT message successfully :)");
        }
        else {
          Serial.println("Could not publish MQTT message :(");
        }

        // To reduce overload server
        delay(4000);
      }
      inTime = 0;
      detected = false;
    }
  }
  
  delay(1000);                
}

void subscribeReceive(char* topic, byte* payload, unsigned int length)
{
  // Print the topic
  Serial.print("Topic:");
  Serial.println(topic);
 
  // Print the message
  Serial.print("Message:");
  for(int i = 0; i < length; i ++)
  {
    Serial.print(char(payload[i]));
  }
 
  // Print a newline
  Serial.println("");
}