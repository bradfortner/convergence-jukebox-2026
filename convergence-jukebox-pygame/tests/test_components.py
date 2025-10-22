"""
Unit Tests - Components Testing
"""

import unittest
import sys
import os
import pygame

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components import Button, TextDisplay, GridLayout, Keypad, RowSelector


class TestButton(unittest.TestCase):
    """Test Button component"""

    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.button = Button(10, 10, 100, 50, text="Test")

    def test_initialization(self):
        """Test button initialization"""
        self.assertEqual(self.button.text, "Test")
        self.assertEqual(self.button.rect.x, 10)
        self.assertEqual(self.button.rect.y, 10)
        self.assertEqual(self.button.rect.width, 100)
        self.assertEqual(self.button.rect.height, 50)

    def test_enabled_disabled(self):
        """Test button enable/disable"""
        self.assertTrue(self.button.enabled)

        self.button.set_enabled(False)
        self.assertFalse(self.button.enabled)

    def test_update_text(self):
        """Test updating button text"""
        self.button.update_text("New Text")
        self.assertEqual(self.button.text, "New Text")

    def test_hover_state(self):
        """Test hover state"""
        self.assertFalse(self.button.is_hovered())

        self.button.handle_hover((15, 15))
        self.assertTrue(self.button.is_hovered())

        self.button.handle_hover((200, 200))
        self.assertFalse(self.button.is_hovered())

    def test_position_update(self):
        """Test updating position"""
        self.button.update_position(50, 50)
        self.assertEqual(self.button.rect.x, 50)
        self.assertEqual(self.button.rect.y, 50)


class TestTextDisplay(unittest.TestCase):
    """Test TextDisplay component"""

    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.text_display = TextDisplay(100, 100, text="Test Text")

    def test_initialization(self):
        """Test text display initialization"""
        self.assertEqual(self.text_display.text, "Test Text")
        self.assertEqual(self.text_display.x, 100)
        self.assertEqual(self.text_display.y, 100)

    def test_update_text(self):
        """Test updating text"""
        self.text_display.update_text("New Text")
        self.assertEqual(self.text_display.text, "New Text")

    def test_visibility(self):
        """Test visibility toggle"""
        self.assertTrue(self.text_display.visible)

        self.text_display.set_visible(False)
        self.assertFalse(self.text_display.visible)

    def test_truncate_text(self):
        """Test text truncation"""
        long_text = "This is a very long text that should be truncated"
        truncated = self.text_display.truncate_text(long_text, max_length=20)
        self.assertLessEqual(len(truncated), 20)
        self.assertTrue(truncated.endswith("..."))

    def test_position_update(self):
        """Test updating position"""
        self.text_display.update_position(200, 200)
        self.assertEqual(self.text_display.x, 200)
        self.assertEqual(self.text_display.y, 200)


class TestGridLayout(unittest.TestCase):
    """Test GridLayout component"""

    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.grid = GridLayout(0, 0, cols=3, rows=3, cell_width=100, cell_height=100)

    def test_initialization(self):
        """Test grid initialization"""
        self.assertEqual(self.grid.cols, 3)
        self.assertEqual(self.grid.rows, 3)

    def test_add_item(self):
        """Test adding item to grid"""
        item = {"name": "Test"}
        result = self.grid.add_item(0, 0, item)
        self.assertTrue(result)

    def test_get_item(self):
        """Test getting item from grid"""
        item = {"name": "Test"}
        self.grid.add_item(0, 0, item)
        retrieved = self.grid.get_item(0, 0)
        self.assertEqual(retrieved, item)

    def test_remove_item(self):
        """Test removing item from grid"""
        self.grid.add_item(0, 0, {"name": "Test"})
        result = self.grid.remove_item(0, 0)
        self.assertTrue(result)
        self.assertIsNone(self.grid.get_item(0, 0))

    def test_clear(self):
        """Test clearing grid"""
        self.grid.add_item(0, 0, {"name": "Test1"})
        self.grid.add_item(1, 1, {"name": "Test2"})

        self.grid.clear()
        self.assertIsNone(self.grid.get_item(0, 0))
        self.assertIsNone(self.grid.get_item(1, 1))

    def test_get_all_cells(self):
        """Test getting all cells"""
        cells = self.grid.get_all_cells()
        self.assertEqual(len(cells), 9)  # 3x3 grid

    def test_grid_bounds(self):
        """Test grid bounds checking"""
        result = self.grid.add_item(10, 10, {"name": "Out of bounds"})
        self.assertFalse(result)


class TestKeypad(unittest.TestCase):
    """Test Keypad component"""

    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.keypad = Keypad(0, 0, keypad_type="numeric")

    def test_initialization(self):
        """Test keypad initialization"""
        self.assertIsNotNone(self.keypad)
        self.assertEqual(self.keypad.keypad_type, "numeric")

    def test_get_input(self):
        """Test getting input"""
        input_text = self.keypad.get_input()
        self.assertEqual(input_text, "")

    def test_add_input(self):
        """Test adding input"""
        self.keypad.add_input("1")
        self.assertEqual(self.keypad.get_input(), "1")

        self.keypad.add_input("2")
        self.assertEqual(self.keypad.get_input(), "12")

    def test_backspace(self):
        """Test backspace"""
        self.keypad.add_input("1")
        self.keypad.add_input("2")
        self.keypad.backspace()
        self.assertEqual(self.keypad.get_input(), "1")

    def test_clear(self):
        """Test clearing input"""
        self.keypad.add_input("1")
        self.keypad.add_input("2")
        self.keypad.clear()
        self.assertEqual(self.keypad.get_input(), "")

    def test_enable_disable_key(self):
        """Test enabling/disabling keys"""
        if "1" in self.keypad.buttons:
            btn = self.keypad.get_button("1")
            self.keypad.disable_key("1")
            self.assertFalse(btn.enabled)

            self.keypad.enable_key("1")
            self.assertTrue(btn.enabled)


class TestRowSelector(unittest.TestCase):
    """Test RowSelector component"""

    def setUp(self):
        """Set up test fixtures"""
        pygame.init()
        self.selector = RowSelector(0, 0, rows=7)

    def test_initialization(self):
        """Test row selector initialization"""
        self.assertIsNone(self.selector.get_selected_row())

    def test_set_selected_row(self):
        """Test setting selected row"""
        self.selector.set_selected_row(3)
        self.assertEqual(self.selector.get_selected_row(), 3)

    def test_clear_selection(self):
        """Test clearing selection"""
        self.selector.set_selected_row(5)
        self.selector.clear_selection()
        self.assertIsNone(self.selector.get_selected_row())

    def test_invalid_row(self):
        """Test setting invalid row"""
        self.selector.set_selected_row(10)
        self.assertIsNone(self.selector.get_selected_row())


if __name__ == '__main__':
    unittest.main()
