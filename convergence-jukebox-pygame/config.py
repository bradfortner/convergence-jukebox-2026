"""
Configuration constants for Convergence Jukebox Pygame Application
"""

import os
import sys

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
FULLSCREEN = False

# ============================================================================
# COLORS (RGB)
# ============================================================================
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_LIGHT_GRAY = (200, 200, 200)
COLOR_SEAGREEN = (46, 139, 87)
COLOR_SEAGREEN_LIGHT = (84, 255, 159)
COLOR_SEAGREEN_PALE = (176, 226, 200)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)

# ============================================================================
# FONTS
# ============================================================================
FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "OpenSans-ExtraBold.ttf")
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 32
FONT_SIZE_SMALL = 24
FONT_SIZE_TINY = 16

# Fallback to system font if not found
try:
    pygame = __import__('pygame')
    if not os.path.exists(FONT_PATH):
        FONT_PATH = pygame.font.get_default_font()
except:
    FONT_PATH = None

# ============================================================================
# ASSET PATHS
# ============================================================================
BASE_PATH = os.path.dirname(__file__)
ASSETS_PATH = os.path.join(BASE_PATH, "assets")
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")
FONTS_PATH = os.path.join(ASSETS_PATH, "fonts")
SOUNDS_PATH = os.path.join(ASSETS_PATH, "sounds")
RECORD_LABELS_PATH = os.path.join(ASSETS_PATH, "record_labels")

# Sound files
SOUND_BUZZ = os.path.join(SOUNDS_PATH, "buzz.mp3")
SOUND_SUCCESS = os.path.join(SOUNDS_PATH, "success.mp3")

# Image files
IMAGE_BUTTON_BG = os.path.join(IMAGES_PATH, "button_id_bg.png")
IMAGE_BUTTON_BLACK_BG = os.path.join(IMAGES_PATH, "button_id_black_bg.png")
IMAGE_SELECTION_BG = os.path.join(IMAGES_PATH, "new_selection_top_bg.png")
IMAGE_ARROW_LEFT = os.path.join(IMAGES_PATH, "lg_arrow_left.png")
IMAGE_ARROW_RIGHT = os.path.join(IMAGES_PATH, "lg_arrow_right.png")

# ============================================================================
# DATA PERSISTENCE
# ============================================================================
DATA_DIR = os.path.dirname(os.path.dirname(__file__))  # Parent directory
SONG_LIST_FILE = os.path.join(DATA_DIR, "MusicMasterSongList.txt")
SONG_LIST_CHECK_FILE = os.path.join(DATA_DIR, "MusicMasterSongListCheck.txt")
PAID_PLAYLIST_FILE = os.path.join(DATA_DIR, "PaidMusicPlayList.txt")
CURRENT_PLAYING_FILE = os.path.join(DATA_DIR, "CurrentSongPlaying.txt")
BANDS_FILE = os.path.join(DATA_DIR, "the_bands.txt")
EXEMPTED_BANDS_FILE = os.path.join(DATA_DIR, "the_exempted_bands.txt")
GENRE_FLAGS_FILE = os.path.join(DATA_DIR, "GenreFlagsList.txt")
LOG_FILE = os.path.join(DATA_DIR, "log.txt")

# ============================================================================
# MUSIC DIRECTORY
# ============================================================================
if sys.platform.startswith('win32'):
    MUSIC_DIR = os.path.join(DATA_DIR, "main_jukebox_engine", "music")
elif sys.platform.startswith('linux'):
    MUSIC_DIR = os.path.join(DATA_DIR, "main_jukebox_engine", "music")
else:
    MUSIC_DIR = os.path.join(DATA_DIR, "main_jukebox_engine", "music")

# ============================================================================
# UI LAYOUT CONSTANTS
# ============================================================================

# Selection Screen
SELECTION_GRID_COLS = 3
SELECTION_GRID_ROWS = 7
SONGS_PER_PAGE = SELECTION_GRID_COLS * SELECTION_GRID_ROWS

# Button dimensions
BUTTON_LETTER_WIDTH = 80
BUTTON_LETTER_HEIGHT = 60
BUTTON_SONG_WIDTH = 250
BUTTON_SONG_HEIGHT = 30

ARROW_BUTTON_WIDTH = 100
ARROW_BUTTON_HEIGHT = 500

# Margins and spacing
MARGIN_LEFT = 20
MARGIN_RIGHT = 20
MARGIN_TOP = 20
MARGIN_BOTTOM = 20
SPACING_H = 10
SPACING_V = 5

# ============================================================================
# CREDIT SYSTEM
# ============================================================================
CREDIT_INCREMENT = 0.25  # $0.25 per selection
INITIAL_CREDIT = 0.00

# ============================================================================
# UPCOMING QUEUE
# ============================================================================
MAX_UPCOMING_ITEMS = 10

# ============================================================================
# RECORD LABEL ANIMATION
# ============================================================================
RECORD_LABEL_WIDTH = 680
RECORD_LABEL_HEIGHT = 394
RECORD_LABEL_DURATION = 600  # frames (10 seconds at 60 FPS)
RECORD_LABEL_TEXT_X = 340  # center position
RECORD_LABEL_TEXT_Y = 515  # start position

# Font sizes for record labels
RECORD_LABEL_FONT_LARGE = 30
RECORD_LABEL_FONT_MEDIUM = 20
RECORD_LABEL_FONT_SMALL = 15

# ============================================================================
# STATE MANAGEMENT
# ============================================================================
SELECTION_MODES = ['A', 'B', 'C']
SELECTION_NUMBERS = ['1', '2', '3', '4', '5', '6', '7']

# ============================================================================
# MONITORING
# ============================================================================
FILE_CHECK_INTERVAL = 3  # seconds - check for song changes
THREAD_SLEEP_INTERVAL = 0.1  # seconds

# ============================================================================
# LOGGING
# ============================================================================
LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# TEXT TRUNCATION
# ============================================================================
TEXT_WRAP_WIDTH_TITLE = 37
TEXT_WRAP_WIDTH_ARTIST = 30
TEXT_LENGTH_THRESHOLD_LARGE = 37
TEXT_LENGTH_THRESHOLD_MEDIUM = 28
TEXT_LENGTH_THRESHOLD_SMALL = 21
TEXT_LENGTH_THRESHOLD_TINY = 17
