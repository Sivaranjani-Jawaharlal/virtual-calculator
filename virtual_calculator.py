import cv2
import mediapipe as mp
import numpy as np
import time
import math

class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value
        self.active = False

    def draw(self, img):
        x, y = self.pos
        overlay = img.copy()
        color = (200, 200, 200) if not self.active else (0, 255, 0)
        cv2.rectangle(overlay, (x, y), (x + self.width, y + self.height), color, cv2.FILLED)
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        cv2.rectangle(img, (x, y), (x + self.width, y + self.height), (50, 50, 50), 2)
        cv2.putText(img, self.value, (x + 15, y + 35), cv2.FONT_HERSHEY_PLAIN, 1.8, (0, 0, 0), 2)

    def is_clicked(self, x, y):
        bx, by = self.pos
        return bx < x < bx + self.width and by < y < by + self.height

values = [['7', '8', '9', '/'],
          ['4', '5', '6', '*'],
          ['1', '2', '3', '-'],
          ['C', '0', '=', '+']]

# Target output size
frame_w, frame_h = 801, 636

cap = cv2.VideoCapture(0)
cap.set(3, frame_w)
cap.set(4, frame_h)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Calculator layout settings
btn_w, btn_h = 55, 55
gap = 10
calc_width = 4 * btn_w + 3 * gap
calc_height = 4 * btn_h + 3 * gap
display_height = 60

# Center the calculator
start_x = (frame_w - calc_width) // 2
start_y = (frame_h - calc_height - display_height - 10) // 2 + display_height + 10

button_list = []
for i in range(4):
    for j in range(4):
        x = start_x + j * (btn_w + gap)
        y = start_y + i * (btn_h + gap)
        button_list.append(Button((x, y), btn_w, btn_h, values[i][j]))

equation = ''
last_click_time = 0

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

while True:
    success, img = cap.read()
    img = cv2.resize(cv2.flip(img, 1), (frame_w, frame_h))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    lm_list = []

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        for id, lm in enumerate(hand_landmarks.landmark):
            cx, cy = int(lm.x * frame_w), int(lm.y * frame_h)
            lm_list.append((cx, cy))
        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if lm_list:
            x1, y1 = lm_list[8]  # Index tip
            x2, y2 = lm_list[12]  # Middle tip

            if distance((x1, y1), (x2, y2)) < 40:
                current_time = time.time()
                if current_time - last_click_time > 0.5:
                    last_click_time = current_time
                    for button in button_list:
                        if button.is_clicked(x1, y1):
                            button.active = True
                            val = button.value
                            if val == 'C':
                                equation = ''
                            elif val == '=':
                                try:
                                    equation = str(eval(equation))
                                except:
                                    equation = 'Error'
                            else:
                                equation += val
                else:
                    for button in button_list:
                        button.active = False
            else:
                for button in button_list:
                    button.active = False

    # Draw calculator display
    cv2.rectangle(img, (start_x, start_y - display_height - 10),
                  (start_x + calc_width, start_y - 10), (255, 255, 255), cv2.FILLED)
    cv2.putText(img, equation, (start_x + 10, start_y - 25), cv2.FONT_HERSHEY_PLAIN, 2.2, (0, 0, 0), 2)

    # Draw buttons
    for button in button_list:
        button.draw(img)

    cv2.imshow("Virtual Calculator", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
