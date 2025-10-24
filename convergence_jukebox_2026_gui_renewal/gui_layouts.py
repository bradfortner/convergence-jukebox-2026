# ============================================================================
# CONVERGENCE JUKEBOX 2026 - GUI LAYOUT FUNCTIONS MODULE
# ============================================================================
# This module contains all PySimpleGUI layout functions used by the GUI
# Purpose: Separate layout logic from main initialization for modularity
# ============================================================================

import PySimpleGUI as sg

# ============================================================================
# TITLE BAR LAYOUT FUNCTION
# ============================================================================
# Purpose: Creates a PySimpleGUI layout for a custom title bar with background
# ============================================================================

def title_bar(title, text_color, background_color):
    """
    Creates a title bar layout row with expandable columns.

    This function returns a list of PySimpleGUI Column elements that form a title bar.
    The layout creates a spread-out design with empty space on the left and content
    on the right.

    Args:
        title (str): Title text to display (NOTE: Currently unused in implementation)
        text_color (str): Color of the text (NOTE: Currently unused in implementation)
        background_color (str): Background color (NOTE: Currently unused in implementation)

    Returns:
        list: A list containing two sg.Col() objects that form the title bar layout

    Note:
        The parameters (title, text_color, background_color) are not currently used
        in the implementation. They may be intended for future use or need to be
        integrated into the layout.
    """
    # Return a list of Column elements that form the title bar
    return [
        # First column: Empty column that expands to fill available space
        # This creates a spacer/padding on the left side of the title bar
        sg.Col([]),

        # Second column: Contains text elements with right-alignment
        # - sg.T() creates an empty Text element
        # - sg.Text() creates another text element
        # - element_justification='r' right-aligns all elements in this column
        # - key='--BG--' provides a unique identifier to reference this element later
        #   (useful for updating content or styling dynamically)
        sg.Col(
            [[sg.T(), sg.Text()]],
            element_justification='r',
            key='--BG--'
        )
    ]
