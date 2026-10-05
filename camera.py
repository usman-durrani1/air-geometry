import cv2

from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)


class Camera:

    def __init__(self):

        self.cap = cv2.VideoCapture(0)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT
        )

    def read(self):

        success, frame = (
            self.cap.read()
        )

        if not success:
            return None

        frame = cv2.flip(
            frame,
            1
        )

        return frame

    def release(self):

        if self.cap is not None:

            self.cap.release()

    @staticmethod
    def create_window(
        name
    ):

        cv2.namedWindow(
            name,
            cv2.WINDOW_NORMAL
        )

        cv2.resizeWindow(
            name,
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        )
