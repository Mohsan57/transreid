import cv2

# Set the URL of the video feed from the first camera
url = "http://mohsan:mohsan123[@192.168.100.10/stream1"

# Open the video capture object
cap = cv2.VideoCapture(url)
# Check if the video capture object is successfully opened
if cap.isOpened():
    while True:
        # Read a frame from the video feed
        ret, frame = cap.read()

        # Display the frame
        if ret:
            cv2.imshow('Camera Stream', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close any open windows
    cap.release()
    cv2.destroyAllWindows()
else:
    print("Failed to open the video feed from the first camera.")
