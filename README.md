# Arduino Tetris Controller

<img width="1024" height="761" alt="schemat" src="https://github.com/user-attachments/assets/af774912-27b6-4c92-bc78-a7dacb2d57a7" />

This project combines **Arduino Mega 2560** with a **Python-based Tetris game** to create a physical gaming controller. Instead of using a keyboard, the player controls the game with a joystick and hardware buttons, while additional electronic components provide visual and audio feedback.

## Features

* 🎮 Joystick control for moving, rotating, and dropping Tetrominoes
* ⏸️ Dedicated pause/resume button
* ⚙️ Adjustable game speed using a potentiometer
* 📟 16×2 LCD display for game information
* 🔊 Buzzer for sound effects (rotation, line clear, game over, etc.)
* 💻 Python game with smooth animations and visual effects
* 🔌 Real-time serial communication between Arduino and the PC

## Hardware

The project uses the following components:

* Arduino Mega 2560
* Analog joystick module
* 16×2 LCD display
* 2× Potentiometers

  * LCD contrast adjustment
  * Game speed control
* Push button (Pause/Resume)
* Piezo buzzer
* Breadboard and jumper wires

## How It Works

The Arduino continuously reads input from the joystick, push button, and potentiometer. These values are sent to the Python application over a serial (USB) connection.

The Python application is responsible for:

* Rendering the Tetris game using **Pygame**
* Handling game logic and collision detection
* Updating the score
* Playing animations and visual effects
* Sending game events back to the Arduino

The Arduino receives these events and controls the connected peripherals, such as the buzzer and LCD display, providing additional feedback during gameplay.

## Controls

| Hardware            | Function             |
| ------------------- | -------------------- |
| Joystick Left/Right | Move Tetromino       |
| Joystick Up/Down    | Faster drop          |
| Joystick Button     | Rotate Tetromino     |
| Push Button         | Pause / Resume game  |
| Potentiometer       | Adjust falling speed |

## Software

* Python 3
* Pygame
* PySerial
* Arduino IDE

## Communication

The project uses **serial communication (USB)** between the Arduino and the computer.

**Arduino → Python**

* Joystick X position
* Joystick Y position
* Joystick button state
* Potentiometer value
* Pause button state

**Python → Arduino**

* Current score
* Game start
* Line cleared
* Piece dropped
* Game over
* Sound effect commands

## Project Goal

The goal of this project was to integrate embedded hardware with a desktop game, creating a more interactive and immersive version of Tetris. By combining Arduino with Python and Pygame, the project demonstrates real-time communication between a microcontroller and a PC application while providing a custom physical controller and hardware feedback system.
