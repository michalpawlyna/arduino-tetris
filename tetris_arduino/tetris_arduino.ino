#include <LiquidCrystal.h>
String command = "";
unsigned long startTime = 0;
unsigned long pausedTime = 0;
bool gameStarted = false;
bool gameOver = false;
bool gamePaused = false;
bool lastPauseButtonState = HIGH;
bool pauseButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
int score = 0;
const int redPin = 9;
const int greenPin = 10;
const int bluePin = 11;
const int buzzerPin = 5;
const int pauseButtonPin = 24;
const int lcdRs = 13;
const int lcdEn = 4;
const int lcdD4 = 3;
const int lcdD5 = 12;
const int lcdD6 = 6;
const int lcdD7 = 8;
LiquidCrystal lcd(lcdRs, lcdEn, lcdD4, lcdD5, lcdD6, lcdD7);

// Additional variables for better input handling
bool pauseButtonPressed = false;
unsigned long lastPauseTime = 0;
const unsigned long pauseCooldown = 300; // Minimum time between pause toggles

void setup() {
  Serial.begin(9600);
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  pinMode(2, INPUT_PULLUP);
  pinMode(pauseButtonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  lcd.begin(20, 4);
  lcd.setCursor(0, 0);
  lcd.print("Game Starting...");
  
  // Initialize button states
  lastPauseButtonState = digitalRead(pauseButtonPin);
  pauseButtonState = lastPauseButtonState;
}

void loop() {
  int x = analogRead(A0);
  int y = analogRead(A1);
  int btn = digitalRead(2);
  int pot = analogRead(A2);
  
  // Handle pause button with improved debouncing
  handlePauseButton();
  
  Serial.print(x);
  Serial.print(",");
  Serial.print(y);
  Serial.print(",");
  Serial.print(btn);
  Serial.print(",");
  Serial.print(pot);
  Serial.print(",");
  Serial.println(gamePaused ? 1 : 0); // Send pause state to serial
  
  readSerial(); // Read data from serial port
  
  if (gameStarted && !gameOver && !gamePaused) {
    unsigned long currentTime = millis();
    unsigned long elapsedSeconds = (currentTime - startTime - pausedTime) / 1000;
    lcd.setCursor(0, 0);
    lcd.print("Score: ");
    lcd.print(score);
    lcd.print("      ");  // Clear end of line
    lcd.setCursor(0, 1);
    lcd.print("Time: ");
    lcd.print(elapsedSeconds);
    lcd.print("s       ");  // Clear end of line
  } else if (gameStarted && !gameOver && gamePaused) {
    // Display pause screen
    lcd.setCursor(0, 0);
    lcd.print("Score: ");
    lcd.print(score);
    lcd.print("      ");
    lcd.setCursor(0, 1);
    lcd.print("*** PAUSED ***   ");
    lcd.setCursor(0, 2);
    lcd.print("Press btn to resume ");
    lcd.setCursor(0, 3);
    lcd.print("                    ");
  }
  
  delay(50); // Reduced delay for better responsiveness
}

void handlePauseButton() {
  int reading = digitalRead(pauseButtonPin);
  unsigned long currentTime = millis();
  
  // Debouncing with improved logic
  if (reading != lastPauseButtonState) {
    lastDebounceTime = currentTime;
  }
  
  if ((currentTime - lastDebounceTime) > debounceDelay) {
    // If button state has changed and enough time has passed
    if (reading != pauseButtonState) {
      pauseButtonState = reading;
      
      // Button pressed (HIGH to LOW transition) and cooldown period passed
      if (pauseButtonState == LOW && !pauseButtonPressed && 
          (currentTime - lastPauseTime) > pauseCooldown) {
        
        pauseButtonPressed = true;
        lastPauseTime = currentTime;
        
        // Only toggle pause if game is active
        if (gameStarted && !gameOver) {
          togglePause();
        }
      }
      // Button released (LOW to HIGH transition)
      else if (pauseButtonState == HIGH && pauseButtonPressed) {
        pauseButtonPressed = false;
      }
    }
  }
  
  lastPauseButtonState = reading;
}

void togglePause() {
  static unsigned long pauseStartTime = 0;
  
  if (!gamePaused) {
    // Pause the game
    gamePaused = true;
    pauseStartTime = millis();
    setColor(255, 255, 0); // Yellow color for pause
    Serial.println("GAME:PAUSED");
    
    // Play pause sound
    tone(buzzerPin, 800, 100);
    delay(110);
    tone(buzzerPin, 600, 100);
    delay(110);
    noTone(buzzerPin);
    
  } else {
    // Resume the game
    gamePaused = false;
    pausedTime += millis() - pauseStartTime;
    setColor(0, 255, 0); // Green color for playing
    Serial.println("GAME:RESUMED");
    lcd.clear();
    
    // Play resume sound
    tone(buzzerPin, 600, 100);
    delay(110);
    tone(buzzerPin, 800, 100);
    delay(110);
    noTone(buzzerPin);
  }
}

void readSerial() {
  static String input = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      input.trim();
      if (input.length() > 0) {
        handleCommand(input);
      }
      input = "";
    } else {
      input += c;
    }
  }
}

void handleCommand(String command) {
  Serial.print("Received command: ");
  Serial.println(command);
  
  if (command == "STATE:START") {
    setColor(0, 0, 255);
    gameStarted = false;
    gameOver = false;
    gamePaused = false;
    pausedTime = 0;
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Game Starting...");
  }
  else if (command == "STATE:PLAY") {
    setColor(0, 255, 0);
    startTime = millis();
    gameStarted = true;
    gameOver = false;
    gamePaused = false;
    pausedTime = 0;
    lcd.clear();
  }
  else if (command == "STATE:OVER") {
    setColor(255, 0, 0);
    gameOver = true;
    gameStarted = false;
    gamePaused = false;
    lcd.clear();
    lcd.setCursor(2, 1);
    lcd.print("=== GAME OVER ===");
    lcd.setCursor(6, 2);
    lcd.print("Score: ");
    lcd.print(score);
  }
  else if (command.startsWith("STATE:SCORE:")) {
    score = command.substring(12).toInt();
  }
  else if (command.startsWith("STATE:BUZZ:")) {
    String buzzType = command.substring(11);
    if (!gamePaused) { // Only play game sounds when not paused
      playSound(buzzType);
    }
  }
  else if (command == "GAME:PAUSE") {
    if (gameStarted && !gameOver && !gamePaused) {
      togglePause();
    }
  }
  else if (command == "GAME:RESUME") {
    if (gameStarted && !gameOver && gamePaused) {
      togglePause();
    }
  }
}

void setColor(int r, int g, int b) {
  analogWrite(redPin, r);
  analogWrite(greenPin, g);
  analogWrite(bluePin, b);
}

void playSound(String type) {
  Serial.print("Playing sound: ");
  Serial.println(type);
  if (type == "LINE") {
    tone(buzzerPin, 1046, 100);
    delay(120);
    tone(buzzerPin, 1318, 100);
    delay(120);
    tone(buzzerPin, 1567, 100);
    delay(120);
    noTone(buzzerPin);
  } else if (type == "ROTATE") {
    tone(buzzerPin, 1200, 40);
    delay(50);
    tone(buzzerPin, 1400, 40);
    delay(50);
    noTone(buzzerPin);
  } else if (type == "DROP") {
    tone(buzzerPin, 1000, 50);
    delay(60);
    tone(buzzerPin, 800, 50);
    delay(60);
    tone(buzzerPin, 600, 50);
    delay(60);
    noTone(buzzerPin);
  } else if (type == "GAMEOVER") {
    tone(buzzerPin, 600, 300);
    delay(300);
    tone(buzzerPin, 500, 300);
    delay(300);
    tone(buzzerPin, 400, 600);
    delay(600);
    noTone(buzzerPin);
  } else if (type == "START") {
    tone(buzzerPin, 660, 150);
    delay(150);
    tone(buzzerPin, 880, 150);
    delay(150);
    tone(buzzerPin, 1046, 150);
    delay(150);
    tone(buzzerPin, 1308, 150);
    delay(150);
    tone(buzzerPin, 1568, 150);
    delay(150);
    noTone(buzzerPin);
  }
}