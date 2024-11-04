import cv2
import mediapipe as mp
import numpy as np
import logging
from collections import deque


logging.basicConfig(filename='physical_therapy_ar.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)


exercise_instructions = {
    "arm_raise": "Raise both arms straight out to the sides until they are parallel to the ground.",
    "squat": "Stand with feet shoulder-width apart, then lower your body as if sitting back into a chair.",
    "leg_raise": "Stand on one leg and raise the other leg straight out in front of you.",
    "shoulder_shrug": "Raise your shoulders towards your ears, hold, then lower them back down.",
    "knee_extension": "Sit on a chair, straighten one leg in front of you, then lower it back down."
}


def analyze_pose(frame):
    """Analyze the pose in the given frame using MediaPipe."""
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
    return results


def draw_landmarks(frame, results):
    """Draw pose landmarks on the frame."""
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)


def calculate_angle(a, b, c):
    """Calculate the angle between three points."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


def verify_exercise(results, exercise_type, angle_history):
    """Verify if the exercise is performed correctly."""
    if results.pose_landmarks is None:
        return False, "No pose detected", angle_history

    landmarks = results.pose_landmarks.landmark

    if exercise_type == "arm_raise":
        left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                      landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                      landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

        right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
        right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

        left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

        angle_history.append((left_angle, right_angle))
        if len(angle_history) > 10:
            angle_history.popleft()

        avg_left = sum([a[0] for a in angle_history]) / len(angle_history)
        avg_right = sum([a[1] for a in angle_history]) / len(angle_history)

        if avg_left > 160 and avg_right > 160:
            return True, "Arms raised correctly", angle_history
        else:
            return False, f"Raise both arms higher (L: {avg_left:.1f}, R: {avg_right:.1f})", angle_history

    elif exercise_type == "squat":
        left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                      landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        knee_angle = calculate_angle(left_hip, left_knee, left_ankle)

        angle_history.append(knee_angle)
        if len(angle_history) > 10:
            angle_history.popleft()

        avg_angle = sum(angle_history) / len(angle_history)

        if 80 < avg_angle < 100:
            return True, f"Good squat form (Angle: {avg_angle:.1f})", angle_history
        elif avg_angle >= 100:
            return False, f"Squat lower (Angle: {avg_angle:.1f})", angle_history
        else:
            return False, f"Don't squat too low (Angle: {avg_angle:.1f})", angle_history

    elif exercise_type == "shoulder_shrug":
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y
        right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value].y

        left_distance = left_ear - left_shoulder
        right_distance = right_ear - right_shoulder

        angle_history.append((left_distance, right_distance))
        if len(angle_history) > 10:
            angle_history.popleft()

        avg_left = sum([a[0] for a in angle_history]) / len(angle_history)
        avg_right = sum([a[1] for a in angle_history]) / len(angle_history)

        if avg_left < 0.15 and avg_right < 0.15:
            return True, "Good shoulder shrug", angle_history
        else:
            return False, f"Raise shoulders higher (L: {avg_left:.2f}, R: {avg_right:.2f})", angle_history

    elif exercise_type in ["leg_raise", "knee_extension"]:
        return False, f"Unable to detect {exercise_type} properly", angle_history

    return False, "Unknown exercise type", angle_history


def main():
    """Main function to capture video and process each frame."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open webcam")
        raise IOError("Cannot open webcam")

    exercises = ["arm_raise", "squat", "leg_raise", "shoulder_shrug", "knee_extension"]
    current_exercise = 0
    rep_count = 0
    exercise_state = False
    angle_history = deque(maxlen=10)

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Failed to grab frame")
            print("Failed to grab frame")
            break

        results = analyze_pose(frame)
        draw_landmarks(frame, results)

        # Check if the exercise is done correctly
        is_correct, feedback, angle_history = verify_exercise(results, exercises[current_exercise], angle_history)

        # Count reps
        if is_correct:
            if not exercise_state:
                exercise_state = True
            elif exercise_state:
                rep_count += 1
                exercise_state = False
                logging.info(f"Completed rep {rep_count} for {exercises[current_exercise]}")


        cv2.putText(frame, feedback, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0) if is_correct else (0, 0, 255), 2)


        cv2.putText(frame, f"Exercise: {exercises[current_exercise]}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 0), 2)  # Changed color to black (0, 0, 0)

        cv2.putText(frame, f"Reps: {rep_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


        instruction = exercise_instructions[exercises[current_exercise]]
        y = frame.shape[0] - 60
        for line in instruction.split('\n'):
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            y -= 20
        cv2.putText(frame, "Press 'n' to switch exercise", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 255), 1)

        cv2.imshow('Physical Therapy AR', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('n'):
            current_exercise = (current_exercise + 1) % len(exercises)
            rep_count = 0
            angle_history.clear()
            logging.info(f"Manually switched to exercise: {exercises[current_exercise]}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"An error occurred. Please check the log file for details.")

