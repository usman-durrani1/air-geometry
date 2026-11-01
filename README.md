# Air Geometry

Air Geometry is a real-time, webcam-based hand-gesture drawing project built with Python, OpenCV, and MediaPipe. It uses hand landmarks and finger gestures to create and place geometric line structures in the camera view.

The project is complete as a gesture-driven drawing demo. It is not a CAD tool or a precision measurement application.

## Features

- Tracks up to two hands using MediaPipe Hand Landmarker.
- Displays detected hand landmarks and tracking connections.
- Creates live lines using thumb-and-index-finger pinches.
- Builds two-hand triangle and rectangle structures when the control points are brought together.
- Supports one-hand rectangle and triangle drawing.
- Lets you place completed geometry so it remains on screen.
- Clears the drawing with a fist gesture.
- Displays the current frame rate (FPS).

## Requirements

- Python 3.11 is recommended.
- A working webcam.
- Windows, macOS, or Linux.
- The included `hand_landmarker.task` model file must remain in the project root.

Python dependencies:

- MediaPipe
- OpenCV

## Installation

Clone the repository:

```bash
git clone https://github.com/usman-durrani1/air-geometry.git
cd air-geometry
```

Create and activate a virtual environment.

**Windows (Command Prompt):**

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

From the repository directory, with the virtual environment activated:

```bash
python main.py
```

Allow the application to use your webcam if your operating system asks for permission. Press **Q** while the camera window is active to quit.

## Gesture controls

| Gesture | Action |
| --- | --- |
| Pinch thumb and index finger | Create a live line for that hand |
| Bring three control points together | Form a two-hand triangle |
| Bring all four control points together | Form a two-hand rectangle |
| Hold the one-hand geometry pose for about 1 second | Start one-hand geometry |
| Pinch while one-hand geometry is active | Switch the one-hand shape to a triangle |
| Thumb and index open; middle, ring, and pinky closed | Place/implant the current geometry |
| Close all five fingers into a fist | Clear the drawing |
| Press `Q` | Quit |

Gesture recognition depends on camera angle, lighting, hand visibility, and tracking quality. Keep your hands inside the camera frame for the most reliable interaction.

## Project structure

```text
air-geometry/
├── camera.py              # Webcam capture and display window
├── config.py              # Camera, model, tracking, and visual settings
├── geometry.py            # Polygon and geometry helper functions
├── gestures.py            # Finger-state and gesture analysis
├── hand_tracking.py       # MediaPipe hand tracking and landmark drawing
├── lines.py               # Live, fixed, and one-hand geometry systems
├── main.py                # Application entry point and interaction loop
├── hand_landmarker.task   # MediaPipe hand landmark model asset
└── requirements.txt       # Python dependencies
```

## Troubleshooting

- **Camera does not open:** Close other applications using the webcam and check your operating system's camera permissions.
- **Model file error:** Confirm that `hand_landmarker.task` is in the same directory as `main.py`.
- **Missing Python module:** Activate the virtual environment and run `python -m pip install -r requirements.txt` again.
- **Poor or inconsistent tracking:** Improve lighting, keep your hands visible, and avoid backgrounds that make your hands difficult to distinguish.

## Credits

- Built with [OpenCV](https://opencv.org/) and [MediaPipe](https://developers.google.com/mediapipe).
- Hand tracking uses the MediaPipe Hand Landmarker task model distributed with this repository.

## Project status

The feature development of Air Geometry is complete. This repository is maintained as the final project release; the documentation and setup files are provided to make it easier to install, run, and understand.
