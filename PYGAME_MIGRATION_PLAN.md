# Convergence Jukebox - Pygame Migration Plan

## Executive Summary
Migrating from PySimpleGUI (abandoned library) to Pygame for complete control over custom UI and superior animation support for the 45 RPM record display.

---

## Phase 1: Project Setup & Architecture (Week 1)

### 1.1 Project Structure
```
convergence-jukebox-pygame/
├── main.py                           # Application entry point
├── config.py                         # Configuration constants
├── data_manager.py                   # Song list, persistence, credits
├── ui_engine.py                      # Pygame rendering engine
├── components/
│   ├── button.py                     # Reusable button widget
│   ├── text_display.py               # Text rendering
│   ├── grid.py                       # Song selection grid
│   └── keypad.py                     # Number/letter pad
├── screens/
│   ├── base_screen.py                # Base screen class
│   ├── selection_screen.py           # Main song selection (21 grid)
│   ├── info_screen.py                # Now playing + upcoming
│   ├── control_screen.py             # A/B/C + numbers + search
│   ├── search_screen.py              # Search modal
│   └── record_label_screen.py        # 45 RPM animation
├── services/
│   ├── vlc_service.py                # VLC integration
│   ├── file_service.py               # File I/O and persistence
│   ├── image_service.py              # PIL integration for labels
│   └── audio_service.py              # Sound effects
├── assets/
│   ├── images/                       # Button backgrounds, arrows, etc.
│   ├── fonts/                        # TTF files
│   ├── sounds/                       # buzz.mp3, success.mp3
│   └── record_labels/                # 45 RPM templates
└── tests/
    └── test_data_manager.py          # Unit tests
```

### 1.2 Dependencies
```
pygame==2.5.2
pillow==10.1.0
python-vlc==3.0.0
tinytag==1.10.1
```

### 1.3 Key Design Patterns
- **Screen Stack Pattern**: Navigate between screens (selection, search, etc.)
- **Event System**: Decouple input handling from business logic
- **Component-based UI**: Reusable button, text, grid components
- **State Machine**: Strict selection flow (A/B/C → 1-7 → Confirm)

---

## Phase 2: Core Data Layer (Week 1)

### 2.1 Data Structures

#### Song Dictionary (from MusicMasterSongList.txt)
```python
{
    'number': int,
    'location': str,          # File path
    'title': str,
    'artist': str,
    'album': str,
    'year': str,
    'comment': str,           # Genre(s)
    'duration': str           # MM:SS format
}
```

#### State Management
```python
class JukeboxState:
    selection_window_number: int      # Current page (0-N)
    credit_amount: float              # in 0.25 increments
    upcoming_playlist: List[str]      # Queue (max 10)
    selected_letter: str              # A, B, or C
    selected_number: str              # 1-7
    last_song_playing: str            # Track file path
```

### 2.2 Persistence Layer
- Load/save JSON files for song list
- Track file modifications (MusicMasterSongListCheck.txt)
- Atomic writes for PaidMusicPlayList.txt
- Append-only logging to log.txt

---

## Phase 3: Pygame Application Shell (Week 1-2)

### 3.1 Main Application Loop
```python
class JukeboxApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = JukeboxState()
        self.screen_stack = [SelectionScreen()]

    def handle_events(self):
        # Unified event handling across all screens
        pass

    def update(self):
        # Background tasks (file monitoring, VLC state)
        pass

    def render(self):
        # Delegate to current screen
        pass

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)  # 60 FPS
```

### 3.2 Screen System
- Base Screen class with lifecycle (load, update, render, unload)
- Screen transitions (push/pop stack)
- Event routing to current screen

---

## Phase 4: UI Component System (Week 2)

### 4.1 Base Components
- **Button**: Clickable area with text, background image, hover state
- **Text**: Static/dynamic text rendering with font sizing
- **Grid**: 3×7 song display with pagination
- **Keypad**: A-Z, 0-9, space, dash, delete

### 4.2 Button Widget
```python
class Button:
    def __init__(self, x, y, width, height, text, image=None, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = image
        self.callback = callback
        self.enabled = True
        self.hovered = False

    def draw(self, surface):
        # Draw background (image or color)
        # Draw text with dynamic sizing
        # Draw hover effect if enabled

    def handle_click(self, pos):
        if self.rect.collidepoint(pos) and self.enabled:
            if self.callback:
                self.callback()
```

### 4.3 Grid Widget (21-Song Display)
```python
class SongGrid:
    def __init__(self, x, y):
        self.buttons = []  # 42 buttons (3 cols × 7 rows × 2 lines/song)
        self.page = 0

    def set_songs(self, songs):
        # Update button text from song list
        # Apply font sizing based on text length

    def next_page(self):
        self.page += 1
        # Check bounds, play buzz if at limit

    def prev_page(self):
        self.page -= 1
        # Check bounds, play buzz if at limit
```

---

## Phase 5: Selection Screen (Week 2)

### 5.1 Layout (1280×720 minimum)
```
┌─────────────────────────────────────────────────────────────┐
│  LEFT ARROW  │    SONG GRID (21 SONGS - 3 COL × 7 ROW)    │ RIGHT ARROW
│              │                                              │
│  ◀  A1-A7    │  B1  Song1     C1   Song15                  │  ▶
│              │  Song1 Artist  Song15 Artist                │
│  ◀  B1-B7    │  A2  Song2     B2   Song9   C2  Song23      │  ▶
│              │  ...                                         │
│  ◀  C1-C7    │  A7  Song7     B7   Song21  C7  Song35      │  ▶
│              │                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Interactions
- Left/Right arrows: Paginate (21 songs per page)
- Click A/B/C button: Disable other columns, enable only selected
- Click number (1-7): Enable only clicked row
- Click song: Select it (highlight)
- Two-button press: Confirm selection

---

## Phase 6: Info Screen (Week 2-3)

### 6.1 Layout
```
NOW PLAYING (title)
───────────────────────────
Song Title (large)
Artist Name (large)

Mode: [Playing Song]
Title: [song name]
Artist: [artist name]
Year: XXXX    Length: MM:SS
Album: [album name]

UPCOMING SELECTIONS (title)
───────────────────────────
[Song 1] - [Artist 1]
[Song 2] - [Artist 2]
...
[Song 10] - [Artist 10]

CREDITS: [X] | 25¢ per selection | [N] Songs Available
```

### 6.2 Real-time Updates
- Monitor CurrentSongPlaying.txt (every 3 seconds)
- Update now playing info
- Detect song change → trigger record label animation
- Pop first item from upcoming queue

---

## Phase 7: Control Panel (Week 3)

### 7.1 Layout
```
┌──────────────────────────┐
│  [A]  [B]  [C]          │  Mode selection
├──────────────────────────┤
│  [1] [2] [3] [4]        │  Number pad
│  [5] [6] [7]            │
├──────────────────────────┤
│ [SELECT]  [CORRECT]     │  Actions
│ [SEARCH]                │
└──────────────────────────┘
```

### 7.2 State Machine
```
IDLE
  ↓ (Press A/B/C)
LETTER_SELECTED (only number buttons enabled)
  ↓ (Press 1-7)
NUMBER_SELECTED (select button enabled)
  ↓ (Press SELECT)
CONFIRM → Add to queue, reset
  ↓ (Press CORRECT)
IDLE (cancel)
```

---

## Phase 8: Search Window (Week 3)

### 8.1 Modal Layout
```
┌─────────────────────────────┐
│  SEARCH BY TITLE/ARTIST     │
├─────────────────────────────┤
│  Keys Entered: [SEARCH___] [DEL] │
├─────────────────────────────┤
│  A B C D E F G H I J K L M  │
│  N O P Q R S T U V W X Y Z  │
│  0 1 2 3 4 5 6 7 8 9 - ' ◆  │
├─────────────────────────────┤
│  Results:                   │
│  ☐ Song1 - Artist1         │
│  ☐ Song2 - Artist2         │
│  ☐ Song3 - Artist3         │
│  [PREV] [NEXT] [EXIT]      │
└─────────────────────────────┘
```

### 8.2 Search Logic
- Build search string as user presses keys
- Filter MusicMasterSongList by title or artist (contains match)
- Display up to 5 results
- Click result → navigate main grid to that song

---

## Phase 9: 45 RPM Record Label Generation (Week 3)

### 9.1 Process
```python
def generate_record_label(song_title, song_artist):
    # 1. Load random template from record_labels/final_black_bg/
    # 2. Use PIL to draw text:
    #    - Title at (680, 515-540)
    #    - Artist at (680, 540-570)
    # 3. Apply dynamic font sizing:
    #    - If (len(title) + len(artist)) > 37 chars: 15pt
    #    - Else if title 21-37 chars: 10pt
    #    - Else if title 17-21 or artist 13-26: 20pt
    #    - Else: 30pt
    # 4. Text wrapping: 37 chars for title, 30 for artist
    # 5. Save as JPEG, resize to 680×394 GIF
    # 6. Display with pygame animation (600 frames × 1ms = 600ms)
```

### 9.2 Animation Loop
- Load GIF frames (use pillow)
- Display at 60 FPS for 600 frames (10 seconds)
- Hide main selection screen during playback
- Unhide after completion

---

## Phase 10: Integration with Jukebox Engine (Week 4)

### 10.1 VLC Service
```python
class VLCService:
    def play_sound(self, filename):
        # Play buzz.mp3 (scroll limit alert)
        # Play success.mp3 (selection confirmed)

    def get_current_song(self):
        # Read CurrentSongPlaying.txt
        # Return file path

    def monitor_playback(self):
        # Background thread monitoring playback status
```

### 10.2 File Service
```python
class FileService:
    def load_song_list(self):
        # Load from MusicMasterSongList.txt
        # Check MusicMasterSongListCheck.txt for changes

    def add_to_paid_queue(self, song_dict):
        # Append to PaidMusicPlayList.txt

    def log_selection(self, artist, title, mode):
        # Append to log.txt with timestamp
```

---

## Phase 11: Testing & Optimization (Week 4)

### 11.1 Test Coverage
- Data persistence (load/save)
- State transitions (selection flow)
- UI rendering (all screens)
- VLC integration
- File I/O error handling

### 11.2 Performance Optimization
- Cache font rendering
- Use display lists for frequently drawn elements
- Optimize event polling
- Profile with cProfile

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1-2 | 3 days | Project structure, data layer, app shell |
| 3-4 | 3 days | UI components, selection screen |
| 5-6 | 3 days | Info screen, control panel |
| 7-8 | 3 days | Search window, record labels |
| 9-10 | 3 days | Engine integration, testing |
| 11 | 2 days | Optimization, deployment |
| **Total** | **17 days** | **Full Pygame GUI** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Pygame learning curve | Start with simple examples, reference documentation |
| Image asset compatibility | Validate all PNG/GIF/JPG files upfront |
| VLC integration issues | Test with python-vlc before main integration |
| File I/O race conditions | Use file locking, atomic writes |
| Performance on older hardware | Profile and optimize rendering pipeline |

---

## Success Criteria

✅ All 6 screens render correctly
✅ Selection flow works (A→1→Confirm)
✅ Song pagination functions
✅ Search finds songs correctly
✅ 45 RPM animation displays smoothly
✅ Credits/queue system operational
✅ Handles all edge cases (empty queue, scroll limits)
✅ Log file maintains audit trail

---

## Next Steps

1. ✅ Review and approve migration plan
2. ⏳ Set up project structure and install dependencies
3. ⏳ Implement data layer
4. ⏳ Build Pygame application shell
5. ⏳ Create UI components
6. ⏳ Implement screens iteratively

**Ready to start Phase 1?**
