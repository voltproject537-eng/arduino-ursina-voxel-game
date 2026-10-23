# Arduino-Powered 3D Voxel Game Controller 🎮🕹️

A DIY physical gaming controller built using an **Arduino Uno**, an analog joystick, and push buttons to play a custom 3D voxel survival game built in Python using the **Ursina** engine.

---

## 🛠️ Components Needed

* **Arduino Uno** (or compatible board)
* Analog **Joystick Module**
* **2x Standard Push Buttons**
* **Breadboard** & **10-15 Male-to-Male Jumper Wires**
* **Arduino USB Cable**
* Computer Mouse *(Optional)*[cite: 1]

---

## 🔌 Wiring Guide

### 1. Joystick Wiring
| Joystick Pin | Arduino Pin |
| :--- | :--- |
| **GND** | GND[cite: 1] |
| **VCC** | 5V[cite: 1] |
| **VX** | Analog A0[cite: 1] |
| **VY** | Analog A1[cite: 1] |
| **SW (Switch)** | Digital D2[cite: 1] |

### 2. Push Button Wiring
* **Button 1:** Connect one leg to **GND**, and the diagonally opposite leg to **Digital D3**[cite: 1].
* **Button 2:** Connect one leg to **GND**, and the diagonally opposite leg to **Digital D4**[cite: 1].

---

## 💻 Software Setup & Installation

### Step 1: Upload the Arduino Code
1. Connect your Arduino Uno to your PC via USB.
2. Open the **Arduino IDE**, open the code from the `arduino/` folder, and select your board and correct **COM port**[cite: 1].
3. Upload the code to your Arduino. 
4. *Important:* Note down your COM port number and **do not** unplug the Arduino from your device[cite: 1].

### Step 2: Install Python Dependencies
Make sure you have Python installed, then open your Command Prompt (or terminal) and run the following commands to install the required external packages[cite: 1]:

```bash
pip install ursina
pip install pyserial
