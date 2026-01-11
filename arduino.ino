// --- Pinbelegung ---
const int btnPrev    = 8;
const int btnPlay    = 9;
const int btnNext    = 10;
const int btnMute    = 7;
const int btnMicMute = 6;
const int btnSleep   = 5;
const int btnDiscord = 4;
const int btnFirefox = 2;

const int potiVol = A0;
const int potiMic = A1;

int lastPotiVol = 0;
int lastPotiMic = 0;

// Zustandsspeicher für Buttons
bool lastState[10] = {0};

void setup() {
  Serial.begin(9600);

  for (int pin = 2; pin <= 9; pin++) {
    pinMode(pin, INPUT);  // Pull-Down: kein Pullup
  }
}

void loop() {
  checkButton(btnPrev,    "PREV");
  checkButton(btnPlay,    "PLAY");
  checkButton(btnNext,    "NEXT");
  checkButton(btnMute,    "MUTE");
  checkButton(btnMicMute, "MICMUTE");
  checkButton(btnSleep,   "SLEEP");
  checkButton(btnDiscord, "DISCORD");
  checkButton(btnFirefox, "FIREFOX");

  checkPotentiometer(potiVol, "VOL", lastPotiVol);

  delay(50);
}

void checkButton(int pin, const char* label) {
  int index = pin - 2;
  bool current = digitalRead(pin);

  if (current && !lastState[index]) {
    Serial.println(label);
    delay(20); // Debounce
  }

  lastState[index] = current;
}

void checkPotentiometer(int pin, const char* label, int &lastVal) {
  int val = analogRead(pin) / 4; // 0–1023 → 0–255
  if (abs(val - lastVal) > 5) {
    Serial.print(label);
    Serial.print(":");
    Serial.println(val);
    lastVal = val;
  }
}
