
BASE_URL = "http://127.0.0.1:8000"
EMAIL = "campus.surveillance.system@gmail.com"
PASSWORD  = "bfomqqctqfobtgta"
QUEUE_LENGTH = 3
INPUT_VIDEO_SIZE_IN_BYTES = 15000000
VIDEO_CONVERT_FPS  = 7
TRANSREID_MODEL_NAME = "transformer_120.pth"
DEVICE = 'cpu'

TRANSREID_ACCURACY_MATCH = 0.71

# whos can access these API's
ORIGINS = [
       "http://localhost",
       "http://localhost:3000",
       "https://gregarious-pothos-f687f0.netlify.app",]


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
