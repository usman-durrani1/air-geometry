import cv2 
import time 
 
from camera import Camera 
from hand_tracking import ( 
    HandTracker, 
    extract_hands, 
    draw_hands, 
) 
 
from gestures import analyze_gestures 
from lines import LineSystem 
 
 
WINDOW_NAME = "Air Geometry" 
 
 
def build_anchors( 
    hands 
): 
 
    anchors = {} 
 
    if "left" in hands: 
 
        anchors["left_thumb"] = ( 
            hands["left"]["thumb"] 
        ) 
 
        anchors["left_index"] = ( 
            hands["left"]["index"] 
        ) 
 
    if "right" in hands: 
 
        anchors["right_thumb"] = ( 
            hands["right"]["thumb"] 
        ) 
 
        anchors["right_index"] = ( 
            hands["right"]["index"] 
        ) 
 
    return anchors 
 
 
def main(): 
 
    print( 
        "Air Geometry" 
    ) 
 
    print( 
        "Pinch thumb + index to CREATE a line." 
    ) 
 
    print( 
        "Release the pinch: the line stays LIVE." 
    ) 
 
    print( 
        "Move your hands to deform the geometry." 
    ) 
 
    print( 
        "Thumb + index OPEN, other fingers CLOSED = IMPLANT." 
    ) 
 
    print( 
        "All five fingers CLOSED = CLEAR." 
    ) 
 
    print( 
        "Press Q to quit." 
    ) 
 
    camera = Camera() 
 
    Camera.create_window( 
        WINDOW_NAME 
    ) 
 
    tracker = HandTracker() 
 
    lines = LineSystem() 
 
    previous_left_pinch = False 
    previous_right_pinch = False 
 
    previous_left_implant = False 
    previous_right_implant = False 
 
    previous_left_clear = False 
    previous_right_clear = False 
 
    last_time = time.perf_counter() 
 
    fps = 0.0 
 
    try: 
 
        while True: 
 
            frame = camera.read() 
 
            if frame is None: 
                break 
 
            height, width = ( 
                frame.shape[:2] 
            ) 
 
            # ================================== 
            # HAND TRACKING 
            # ================================== 
 
            result = tracker.detect( 
                frame 
            ) 
 
            hands = extract_hands( 
                result, 
                width, 
                height 
            ) 
 
            draw_hands( 
                frame, 
                hands 
            ) 
 
            # ================================== 
            # GESTURES 
            # ================================== 
 
            left_gesture = None 
            right_gesture = None 
 
            if "left" in hands: 
 
                left_gesture = ( 
                    analyze_gestures( 
                        result.hand_landmarks[ 
                            next( 
                                i 
                                for i, categories 
                                in enumerate( 
                                    result.handedness 
                                ) 
                                if categories 
                                and categories[0] 
                                .display_name 
                                .lower() 
                                == "left" 
                            ) 
                        ] 
                    ) 
                ) 
 
            if "right" in hands: 
 
                right_gesture = ( 
                    analyze_gestures( 
                        result.hand_landmarks[ 
                            next( 
                                i 
                                for i, categories 
                                in enumerate( 
                                    result.handedness 
                                ) 
                                if categories 
                                and categories[0] 
                                .display_name 
                                .lower() 
                                == "right" 
                            ) 
                        ] 
                    ) 
                ) 
 
            # ================================== 
            # CURRENT STATES 
            # ================================== 
 
            left_pinch = ( 
                left_gesture is not None 
                and 
                left_gesture["pinch"] 
            ) 
 
            right_pinch = ( 
                right_gesture is not None 
                and 
                right_gesture["pinch"] 
            ) 
 
            left_implant = ( 
                left_gesture is not None 
                and 
                left_gesture["implant"] 
            ) 
 
            right_implant = ( 
                right_gesture is not None 
                and 
                right_gesture["implant"] 
            ) 
 
            left_clear = ( 
                left_gesture is not None 
                and 
                left_gesture["full_fist"] 
            ) 
 
            right_clear = ( 
                right_gesture is not None 
                and 
                right_gesture["full_fist"] 
            ) 
 
            # ================================== 
            # PINCH CREATION 
            # ================================== 
 
            if ( 
                left_pinch 
                and 
                not previous_left_pinch 
            ): 
 
                lines.create_left_line() 
 
            if ( 
                right_pinch 
                and 
                not previous_right_pinch 
            ): 
 
                lines.create_right_line() 
 
            # ================================== 
            # LIVE ANCHORS 
            # ================================== 
 
            anchors = build_anchors( 
                hands 
            ) 
 
            # ================================== 
            # DRAW LIVE STRUCTURE 
            # ================================== 
 
            lines.draw_live( 
                frame, 
                anchors 
            ) 
 
            # ================================== 
            # IMPLANT 
            # ================================== 
 
            if ( 
                left_implant 
                and 
                not previous_left_implant 
            ): 
 
                lines.implant( 
                    anchors 
                ) 
 
            if ( 
                right_implant 
                and 
                not previous_right_implant 
            ): 
 
                lines.implant( 
                    anchors 
                ) 
 
            # ================================== 
            # CLEAR 
            # ================================== 
 
            if ( 
                left_clear 
                and 
                not previous_left_clear 
            ): 
 
                lines.clear() 
 
            if ( 
                right_clear 
                and 
                not previous_right_clear 
            ): 
 
                lines.clear() 
 
            # ================================== 
            # DRAW FIXED 
            # ================================== 
 
            lines.draw_fixed( 
                frame 
            ) 
 
            # ================================== 
            # FPS 
            # ================================== 
 
            now = time.perf_counter() 
 
            elapsed = ( 
                now - last_time 
            ) 
 
            if elapsed > 0: 
 
                current_fps = ( 
                    1.0 / elapsed 
                ) 
 
                fps = ( 
                    fps * 0.9 
                    + 
                    current_fps * 0.1 
                ) 
 
            last_time = now 
 
            cv2.putText( 
                frame, 
                f"FPS: {fps:.1f}", 
                (15, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 255, 255), 
                1, 
                cv2.LINE_AA 
            ) 
 
            cv2.imshow( 
                WINDOW_NAME, 
                frame 
            ) 
 
            key = ( 
                cv2.waitKey(1) 
                & 0xFF 
            ) 
 
            if key == ord("q"): 
                break 
 
            # ================================== 
            # PREVIOUS STATES 
            # ================================== 
 
            previous_left_pinch = ( 
                left_pinch 
            ) 
 
            previous_right_pinch = ( 
                right_pinch 
            ) 
 
            previous_left_implant = ( 
                left_implant 
            ) 
 
            previous_right_implant = ( 
                right_implant 
            ) 
 
            previous_left_clear = ( 
                left_clear 
            ) 
 
            previous_right_clear = ( 
                right_clear 
            ) 
 
    finally: 
 
        tracker.close() 
 
        camera.release() 
 
        cv2.destroyAllWindows() 
 
 
if __name__ == "__main__": 
 
    main()