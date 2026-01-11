void setup() {
  // Velocidad rápida para no perder tiempo imprimiendo
  Serial.begin(115200); 

}

void loop() {
    Serial.print("{\"rpm\":");
    Serial.print(7.00, 2);
    Serial.print(",\"lift\":");
    Serial.print(456.00, 4);
    Serial.println("}");
    delay(1000); 
}
