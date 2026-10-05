# ==========================================
# AIR GEOMETRY CONFIGURATION
# ==========================================


MODEL_PATH = "hand_landmarker.task"


# ------------------------------------------
# CAMERA
# ------------------------------------------

CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

WINDOW_WIDTH = 383
WINDOW_HEIGHT = 217


# ------------------------------------------
# HAND TRACKING
# ------------------------------------------

NUM_HANDS = 2

MIN_DETECTION_CONFIDENCE = 0.35
MIN_PRESENCE_CONFIDENCE = 0.35
MIN_TRACKING_CONFIDENCE = 0.35


# ------------------------------------------
# PINCH
# ------------------------------------------

PINCH_DISTANCE = 30


# ------------------------------------------
# VISUALS
# ------------------------------------------

GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (0, 0, 255)

# 2x thicker than 2.1
HAND_LINE_THICKNESS = 4

# 2x thicker than 2.1
WHITE_LINE_THICKNESS = 2

LANDMARK_RADIUS = 3

CONTROL_DOT_RADIUS = 10
