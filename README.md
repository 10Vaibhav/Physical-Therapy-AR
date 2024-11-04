Physical Therapy AR

Description
This project is a physical therapy assistant that uses computer vision and pose estimation to help users perform exercises correctly. The system uses the MediaPipe library to detect and track the user's pose, and provides real-time feedback on the user's form.
Features

Supports multiple exercises: arm raise, squat, leg raise, shoulder shrug, and knee extension.
Provides real-time feedback on the user's form, indicating whether the exercise is being performed correctly.
Counts the number of completed reps for each exercise.
Displays instructions for each exercise on the screen.
Allows the user to switch between exercises.

Installation

Install the required dependencies:

OpenCV: pip install opencv-python
MediaPipe: pip install mediapipe
NumPy: pip install numpy


Save the provided code in a file (e.g., physical_therapy_ar.py).

Usage

Run the script:
Copypython physical_therapy_ar.py

The program will start capturing video from your webcam and display the pose estimation results.
To switch between exercises, press the 'n' key on your keyboard.
To exit the program, press the 'q' key on your keyboard.

Contributors

Tanmay Chikhale
Sushrut Wadhankar
Tanish Hande

Project Details

This project was created for the DIP (Digital Image Processing) Lab in YCCE (Yeshwantrao Chavan College of Engineering), where the contributors are students of the AIDS (Applied Instrumentation and Digital Systems) branch in their 3rd year.

Acknowledgments

This project uses the MediaPipe library for pose estimation, which was developed by Google.
The project's structure and functionality were inspired by various online resources and tutorials on computer vision and pose estimation.
