import cv2

from config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)


class Camera:

    def __init__(self):

        self.capture = cv2.VideoCapture(
            CAMERA_INDEX
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT
        )

        if not self.capture.isOpened():

            raise RuntimeError(
                "Could not open webcam."
            )

    def read(self):

        success, frame = self.capture.read()

        if not success:
            return None

        # Selfie view
        frame = cv2.flip(
            frame,
            1
        )

        return frame

    def release(self):

        self.capture.release()

    @staticmethod
    def create_window(name):

        cv2.namedWindow(
            name,
            cv2.WINDOW_NORMAL
        )

        cv2.resizeWindow(
            name,
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        )