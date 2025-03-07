from flask import Flask, render_template, Response
import cv2
import os
import time
import torch
import face_recognition
import pygame
import smtplib
import datetime
import imaplib
import email
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email Credentials
sender_email = "vinayabhi4403@gmail.com"
sender_password = "jmcv ibei fmcv uhae"
receiver_email = "vinayabhi44@gmail.com"

# Load Face Recognition Model
folder_path = "C:/Users/sadda/OneDrive/Desktop/images"
image_encodings = []
image_names = []
for filename in os.listdir(folder_path):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(folder_path, filename)
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)
        if len(encoding) > 0:
            image_encodings.append(encoding[0])
            image_names.append(filename)

# Load YOLOv5 Model
model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)

app = Flask(__name__)
cap = cv2.VideoCapture(0)

def play_alarm(audio):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio)
        pygame.mixer.music.play()
        print("Alarm is playing!")
    except Exception as e:
        print(f"Error playing alarm: {e}")
def send_email(frame):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = ' < Alert !!! > '
        body = 'Pics of Intruder'
        msg.attach(MIMEText(body, 'plain'))

        cur = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')
        image_path = f'C:/Users/sadda/OneDrive/Desktop/detected_images/image{cur}.jpg'
        cv2.imwrite(image_path, frame)
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            image = MIMEImage(image_data, name='intruder.jpg')
            msg.attach(image)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print("Successfully sent email alert")
        alarm_path = "C:/Users/sadda/OneDrive/Desktop/alarm-clock-90867.wav"
        if os.path.exists(alarm_path):
            play_alarm(alarm_path)
        else:
            print("Alarm file not found!")

    except Exception as e:
        print(f"Failed to send email alert: {e}")


def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        results = model(frame)
        frame = results.render()[0]

        face_loc = face_recognition.face_locations(frame)
        if face_loc:
            face_encoding = face_recognition.face_encodings(frame, face_loc)[0]
            matches = face_recognition.compare_faces(image_encodings, face_encoding)
            if not any(matches):
                send_email(frame)
                time.sleep(10)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)