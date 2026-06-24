/**
 * Finger Controlled LED - ESP32 Firmware
 * Listens for Serial commands from Python to control an LED.
 */

// GPIO 2 controls the onboard blue LED on most ESP32 dev boards
const int ledPin = 2; 

void setup() {
  // Initialize the LED pin as an output
  pinMode(ledPin, OUTPUT);
  
  // Start serial communication at 9600 bits per second
  Serial.begin(9600); 
  
  // Flash the LED once at startup to confirm it works
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
}

void loop() {
  // Check if bytes are available to read from Python
  if (Serial.available() > 0) {
    
    // Read the incoming character
    char data = Serial.read();

    // If Python sends '1', turn the LED ON
    if (data == '1') {
      digitalWrite(ledPin, HIGH);
    }

    // If Python sends '0', turn the LED OFF
    if (data == '0') {
      digitalWrite(ledPin, LOW);
    }
  }
}