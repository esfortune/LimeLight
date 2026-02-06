#!/home/canopylife/PyEnvs/imagine/bin/python

# automerger.py is a craptastic tool to merge two slightly overlapping 
# images for the Galago device. It relies on cv2 and numpy - using a
# python in a virtual environment.
#
# Usage: automerger.py ImageRightMerge ImageLeftMerge
# where ImageRightMerge is usually camera 0 and the other is camera 1
# Saves the merged image to /tmp/merged_result.jpg
#

import cv2
import numpy as np
import sys

def merge_overlapping(imgMR_path, imgML_path, output="/tmp/merged_result.jpg"):
    # Load images
    img1 = cv2.imread(imgML_path) # Image to merge on left side (typically camera 1)
    img2 = cv2.imread(imgMR_path) # Image to merge on right side (typically camera 0)

    if img1 is None:
        print(f"Error: Could not load image: {img1_path}")
        sys.exit(1)
    if img2 is None:
        print(f"Error: Could not load image: {img2_path}")
        sys.exit(1)

    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # --- 1. Feature Detection ---
    orb = cv2.ORB_create(5000)
    keypoints1, descriptors1 = orb.detectAndCompute(gray1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray2, None)

    # --- 2. Feature Matching ---
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[:50]  # top matches

    # --- 3. Extract matched coordinate pairs ---
    pts1 = np.float32([keypoints1[m.queryIdx].pt for m in good_matches])
    pts2 = np.float32([keypoints2[m.trainIdx].pt for m in good_matches])

    # --- 4. Compute Homography via RANSAC ---
    H, mask = cv2.findHomography(pts2, pts1, cv2.RANSAC)

    # --- 5. Warp second image ---
    height, width, _ = img1.shape
    warped_img2 = cv2.warpPerspective(img2, H, (width * 2, height * 2))

    # --- 6. Paste img1 onto canvas ---
    merged = warped_img2.copy()
    merged[0:height, 0:width] = img1

    # --- 7. Crop black borders ---
    gray = cv2.cvtColor(merged, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    coords = cv2.findNonZero(thresh)
    x, y, w, h = cv2.boundingRect(coords)
    merged_cropped = merged[y:y+h, x:x+w]

    cv2.imwrite(output, merged_cropped)
    print(f"Saved merged image to {output}")


# --------------------------
#      Command Line Use
# --------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge.py <image1> <image2>")
        sys.exit(1)

    img1_path = sys.argv[1]
    img2_path = sys.argv[2]

    merge_overlapping(img1_path, img2_path)

