# ============================================================================
# CONVERGENCE JUKEBOX 2026 - SELECTION HANDLER MODULE
# ============================================================================
# This module processes user song selections and manages UI state
# Purpose: Handle A1-C7 selection input validation and button state management
# ============================================================================

from breakdown_button_controls import (
    disable_a_selection_buttons, disable_b_selection_buttons,
    disable_c_selection_buttons, disable_numbered_selection_buttons
)

# ============================================================================
# SELECTION ENTRY COMPLETE HANDLER
# ============================================================================

def selection_entry_complete(selection_entry_letter, selection_entry_number,
                           jukebox_selection_window, control_button_window):
    """
    Processes a complete song selection (A1-C7) from user input.

    This function:
    - Combines letter and number into selection code (e.g., "A1")
    - Disables all buttons to prevent multiple selections
    - Re-enables only the selected song's buttons
    - Re-enables the select confirmation button

    Args:
        selection_entry_letter (str): Selection section letter (A, B, or C)
        selection_entry_number (str): Selection number (1-7)
        jukebox_selection_window: PySimpleGUI window for song selection display
        control_button_window: PySimpleGUI window for control buttons

    Returns:
        str: The complete selection code (e.g., "A3", "B5", "C1")
    """
    # Combine letter and number to create selection code
    if selection_entry_number:
        selection_entry = selection_entry_letter + selection_entry_number
    else:
        return None

    # Disable all A, B, C section buttons
    disable_a_selection_buttons(jukebox_selection_window, control_button_window)
    disable_b_selection_buttons(jukebox_selection_window, control_button_window)
    disable_c_selection_buttons(jukebox_selection_window, control_button_window)

    # Disable numbered buttons (1-7)
    disable_numbered_selection_buttons(control_button_window)

    # Mapping of selection codes to window keys and button pairs
    selection_mapping = {
        "A1": (['--A1--', '--button0_top--', '--button0_bottom--']),
        "A2": (['--A2--', '--button1_top--', '--button1_bottom--']),
        "A3": (['--A3--', '--button2_top--', '--button2_bottom--']),
        "A4": (['--A4--', '--button3_top--', '--button3_bottom--']),
        "A5": (['--A5--', '--button4_top--', '--button4_bottom--']),
        "A6": (['--A6--', '--button5_top--', '--button5_bottom--']),
        "A7": (['--A7--', '--button6_top--', '--button6_bottom--']),
        "B1": (['--B1--', '--button7_top--', '--button7_bottom--']),
        "B2": (['--B2--', '--button8_top--', '--button8_bottom--']),
        "B3": (['--B3--', '--button9_top--', '--button9_bottom--']),
        "B4": (['--B4--', '--button10_top--', '--button10_bottom--']),
        "B5": (['--B5--', '--button11_top--', '--button11_bottom--']),
        "B6": (['--B6--', '--button12_top--', '--button12_bottom--']),
        "B7": (['--B7--', '--button13_top--', '--button13_bottom--']),
        "C1": (['--C1--', '--button14_top--', '--button14_bottom--']),
        "C2": (['--C2--', '--button15_top--', '--button15_bottom--']),
        "C3": (['--C3--', '--button16_top--', '--button16_bottom--']),
        "C4": (['--C4--', '--button17_top--', '--button17_bottom--']),
        "C5": (['--C5--', '--button18_top--', '--button18_bottom--']),
        "C6": (['--C6--', '--button19_top--', '--button19_bottom--']),
        "C7": (['--C7--', '--button20_top--', '--button20_bottom--']),
    }

    # Re-enable only the selected song's buttons
    if selection_entry in selection_mapping:
        buttons_to_enable = selection_mapping[selection_entry]
        for button_key in buttons_to_enable:
            jukebox_selection_window[button_key].update(disabled=False)

    # Re-enable the select/confirm button
    control_button_window['--select--'].update(disabled=False)

    return selection_entry
