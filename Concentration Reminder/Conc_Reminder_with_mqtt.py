import face_recognition
import cv2
import time
import os
import sys


# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.


# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# Load a sample picture and learn how to recognize it.

your_image = face_recognition.load_image_file("abhinav.jpg")
your_face_encoding = face_recognition.face_encodings(your_image)[0]


# Create arrays of known face encodings and their names
known_face_encodings = [
    your_face_encoding
]
known_face_names = [
    "Concentrated"
]

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

conc_count = 0
start_time = time.clock()

flag = 0
while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        if len(face_encodings)==0:
            conc_count = time.clock() - start_time
            #print("%.2f"% round(conc_count,2))
            os.system("mosquitto_pub -d -u username -P 1234 -t dev/test -m '0'")

            if conc_count > 6 and flag==0:

                os.system("notify-send You need to focus")
                os.system("espeak --stdout 'YOU NEED TO FOCUS' | paplay")
                flag = 1

        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                os.system("mosquitto_pub -d -u username -P 1234 -t dev/test -m '1'")
                start_time = time.clock()
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                from subprocess import call
                call = (["echo","Hello"])
                flag = 0
            else:
                print("asaa")
                print(conc_count)
                # import subprocess
                # test = subprocess.Popen(["xrandr","--output","eDP-1-1","--brightness","1"],stdout=subprocess.PIPE)
                # output = test.communicate()[0]
            conc_count = time.clock() - start_time

            if conc_count > 6 and flag==0:
                os.system("notify-send mc")
                flag = 1

            face_names.append(name)

    process_this_frame = not process_this_frame


    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
