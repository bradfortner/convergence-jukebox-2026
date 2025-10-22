"""
Grid Layout Component - Grid-based layout system for UI
"""

import pygame
from typing import Optional, Tuple, Callable, List, Any, Dict
import config


class GridLayout:
    """Flexible grid layout system for positioning UI elements"""

    def __init__(
        self,
        x: int,
        y: int,
        cols: int,
        rows: int,
        cell_width: int,
        cell_height: int,
        spacing: int = 5,
        padding: int = 0
    ):
        """Initialize grid layout"""
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.spacing = spacing
        self.padding = padding
        self.cells: Dict[Tuple[int, int], Any] = {}
        self.cell_rects: Dict[Tuple[int, int], pygame.Rect] = {}

        # Pre-calculate all cell positions
        self._calculate_cells()

    def _calculate_cells(self):
        """Pre-calculate all cell positions and rectangles"""
        for row in range(self.rows):
            for col in range(self.cols):
                cell_key = (row, col)
                x = self.x + self.padding + col * (self.cell_width + self.spacing)
                y = self.y + self.padding + row * (self.cell_height + self.spacing)
                self.cell_rects[cell_key] = pygame.Rect(x, y, self.cell_width, self.cell_height)

    def add_item(self, row: int, col: int, item: Any) -> bool:
        """Add item to grid cell"""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False

        self.cells[(row, col)] = item
        return True

    def get_item(self, row: int, col: int) -> Optional[Any]:
        """Get item from grid cell"""
        if (row, col) in self.cells:
            return self.cells[(row, col)]
        return None

    def remove_item(self, row: int, col: int) -> bool:
        """Remove item from grid cell"""
        if (row, col) in self.cells:
            del self.cells[(row, col)]
            return True
        return False

    def clear(self):
        """Clear all items from grid"""
        self.cells.clear()

    def get_cell_rect(self, row: int, col: int) -> Optional[pygame.Rect]:
        """Get rectangle for a grid cell"""
        cell_key = (row, col)
        if cell_key in self.cell_rects:
            return self.cell_rects[cell_key]
        return None

    def get_cell_at_position(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get grid cell (row, col) at screen position"""
        x, y = pos

        for (row, col), rect in self.cell_rects.items():
            if rect.collidepoint(x, y):
                return (row, col)

        return None

    def draw(self, screen: pygame.Surface, draw_func: Callable, show_grid: bool = False):
        """Draw all grid items"""
        for (row, col), item in self.cells.items():
            rect = self.cell_rects.get((row, col))
            if rect and item:
                draw_func(screen, item, rect)

        if show_grid:
            self._draw_grid_lines(screen)

    def _draw_grid_lines(self, screen: pygame.Surface, color: Tuple[int, int, int] = config.COLOR_WHITE):
        """Draw grid lines for debugging"""
        for rect in self.cell_rects.values():
            pygame.draw.rect(screen, color, rect, 1)

    def get_grid_rect(self) -> pygame.Rect:
        """Get bounding rectangle of entire grid"""
        if not self.cell_rects:
            return pygame.Rect(self.x, self.y, 0, 0)

        min_x = min(rect.x for rect in self.cell_rects.values())
        min_y = min(rect.y for rect in self.cell_rects.values())
        max_x = max(rect.right for rect in self.cell_rects.values())
        max_y = max(rect.bottom for rect in self.cell_rects.values())

        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def set_spacing(self, spacing: int):
        """Update grid spacing and recalculate"""
        self.spacing = spacing
        self._calculate_cells()

    def set_padding(self, padding: int):
        """Update grid padding and recalculate"""
        self.padding = padding
        self._calculate_cells()

    def get_total_width(self) -> int:
        """Get total width of grid"""
        return self.cols * self.cell_width + (self.cols - 1) * self.spacing + 2 * self.padding

    def get_total_height(self) -> int:
        """Get total height of grid"""
        return self.rows * self.cell_height + (self.rows - 1) * self.spacing + 2 * self.padding

    def get_all_cells(self) -> List[Tuple[int, int]]:
        """Get all cell positions in order"""
        cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                cells.append((row, col))
        return cells

    def get_filled_cells(self) -> List[Tuple[Tuple[int, int], Any]]:
        """Get all filled cells with their items"""
        return [(key, item) for key, item in self.cells.items()]

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        """Get all empty cell positions"""
        all_cells = self.get_all_cells()
        return [cell for cell in all_cells if cell not in self.cells]


class DynamicGrid(GridLayout):
    """Dynamic grid that auto-adjusts based on content"""

    def __init__(
        self,
        x: int,
        y: int,
        cols: int,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        spacing: int = 5,
        padding: int = 0
    ):
        """Initialize dynamic grid"""
        self.target_width = target_width
        self.target_height = target_height

        # Calculate cell size based on target width
        if target_width:
            cell_width = (target_width - (cols - 1) * spacing - 2 * padding) // cols
        else:
            cell_width = 100

        # Initialize parent
        super().__init__(x, y, cols, 1, cell_width, cell_width, spacing, padding)

    def add_items(self, items: List[Any]):
        """Add multiple items and auto-calculate rows"""
        self.cells.clear()
        self.rows = (len(items) + self.cols - 1) // self.cols
        self.cell_rects.clear()
        self._calculate_cells()

        for idx, item in enumerate(items):
            row = idx // self.cols
            col = idx % self.cols
            self.add_item(row, col, item)
