
const int JOY_X = A0;
const int JOY_Y = A1;
const int JOY_SW = 2;

const int MINE_BUTTON = 3;
const int PLACE_BUTTON = 4;

void setup() {
  Serial.begin(115200);

  pinMode(JOY_SW, INPUT_PULLUP);
  pinMode(MINE_BUTTON, INPUT_PULLUP);
  pinMode(PLACE_BUTTON, INPUT_PULLUP);
}

void loop() {
  int x = analogRead(JOY_X);
  int y = analogRead(JOY_Y);

  // LOW means pressed
  int joystickButton = digitalRead(JOY_SW);
  int mineButton = digitalRead(MINE_BUTTON);
  int placeButton = digitalRead(PLACE_BUTTON);

  // Format: X,Y,JOYSTICK,MINE,PLACE
  Serial.print(x);
  Serial.print(",");

  Serial.print(y);
  Serial.print(",");

  Serial.print(joystickButton);
  Serial.print(",");

  Serial.print(mineButton);
  Serial.print(",");

  Serial.println(placeButton);

  delay(20);
}
