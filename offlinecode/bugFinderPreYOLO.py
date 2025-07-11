import cv2
import numpy as np
import os

# === PARAMETERS ===
# VIDEO_PATH = '117722760_Tiputini_2025May30.mp4'
VIDEO_PATH = '120308045-12-jun-2025.mp4'
# VIDEO_PATH = '117722760_Tiputini_2025Jul03.mp4'
BACKGROUND_AVG_TimeConstant = 0.002
THRESHOLD = 40 # Darkness threshold
MIN_AREA = 10 # Minimum number of pixels CAREFUL! CHANGES WITH IMAGE SIZE!
CLASS_ID = 0
OUTPUT_LABELS_DIR = 'yolo_labels'

# === OUTPUT VIDEO NAMES ===
VIDEO_BOXED_ORIG = 'jboxed_original.mp4'
VIDEO_BOXED_THRESH = 'jboxed_thresh.mp4'
VIDEO_THRESH_ONLY = 'jplain_thresh.mp4'

# === SETUP ===
cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
if not ret:
    print("Failed to open video.")
    exit()

height, width = frame.shape[:2]
fps = cap.get(cv2.CAP_PROP_FPS)

# Create label output directory
os.makedirs(OUTPUT_LABELS_DIR, exist_ok=True)

# Video writers
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_boxed_orig = cv2.VideoWriter(VIDEO_BOXED_ORIG, fourcc, fps, (width, height))
out_boxed_thresh = cv2.VideoWriter(VIDEO_BOXED_THRESH, fourcc, fps, (width, height))
out_plain_thresh = cv2.VideoWriter(VIDEO_THRESH_ONLY, fourcc, fps, (width, height), isColor=False)

# Background model init
background_model = np.float32(frame)
frame_number = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_orig = frame.copy()

    # Background subtraction
    cv2.accumulateWeighted(frame, background_model, BACKGROUND_AVG_TimeConstant)
    background_display = cv2.convertScaleAbs(background_model)
    diff = cv2.absdiff(frame, background_display)

    ### gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    ### _, thresh = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY)

    # Grayscale absolute difference
    gray_diff = cv2.cvtColor(cv2.absdiff(frame, background_display), cv2.COLOR_BGR2GRAY)

    # Threshold the difference to get foreground mask
    _, thresh = cv2.threshold(gray_diff, THRESHOLD, 255, cv2.THRESH_BINARY)

    # Morphological operations to reduce noise/shadows
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)  # remove small noise
    thresh = cv2.dilate(thresh, kernel, iterations=1)           # close small holes

#    # Get absolute intensity difference
#    gray_diff = cv2.cvtColor(cv2.absdiff(frame, background_display), cv2.COLOR_BGR2GRAY)
#
#    # Apply binary threshold to isolate significant change (light or dark)
#    _, thresh = cv2.threshold(gray_diff, THRESHOLD, 255, cv2.THRESH_BINARY)



    # For YOLO format output
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    labels = []
    thresh_colored = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        x_center = (x + w / 2) / width
        y_center = (y + h / 2) / height
        norm_w = w / width
        norm_h = h / height
        labels.append(f"{CLASS_ID} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

        # Draw boxes
        cv2.rectangle(frame_orig, (x, y), (x + w, y + h), (0,255,0), 2)
        cv2.rectangle(thresh_colored, (x, y), (x + w, y + h), (0,255,0), 2)

    # Save YOLO label file
    label_path = os.path.join(OUTPUT_LABELS_DIR, f"{frame_number:06}.txt")
    with open(label_path, 'w') as f:
        for line in labels:
            f.write(line + '\n')

    # Write all video versions
    out_boxed_orig.write(frame_orig)
    out_boxed_thresh.write(thresh_colored)
    out_plain_thresh.write(thresh)

    # Optional: preview
    cv2.imshow('Boxed Original', frame_orig)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_number += 1

cap.release()
out_boxed_orig.release()
out_boxed_thresh.release()
out_plain_thresh.release()
cv2.destroyAllWindows()

