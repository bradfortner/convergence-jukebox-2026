from breakdown_disable_a_selection_buttons import disable_a_selection_buttons
from breakdown_disable_b_selection_buttons import disable_b_selection_buttons
from breakdown_disable_c_selection_buttons import disable_c_selection_buttons
from breakdown_disable_numbered_selection_buttons import disable_numbered_selection_buttons


def selection_entry_complete(selection_entry_letter, selection_entry_number, jukebox_selection_window, control_button_window):
    """
    Process a complete song selection (A1-C7) and disable/enable appropriate buttons.

    Args:
        selection_entry_letter: Letter portion of selection (A, B, or C)
        selection_entry_number: Number portion of selection (1-7)
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons

    Returns:
        str: The complete selection string (e.g., "A1", "B5")
    """
    selection_entry = ""
    if selection_entry_number:
        selection_entry = selection_entry_letter + selection_entry_number

    disable_a_selection_buttons(jukebox_selection_window, control_button_window)
    disable_b_selection_buttons(jukebox_selection_window, control_button_window)
    disable_c_selection_buttons(jukebox_selection_window, control_button_window)
    disable_numbered_selection_buttons(control_button_window)

    selection_map = {
        "A1": ('--A1--', '--button0_top--', '--button0_bottom--'),
        "A2": ('--A2--', '--button1_top--', '--button1_bottom--'),
        "A3": ('--A3--', '--button2_top--', '--button2_bottom--'),
        "A4": ('--A4--', '--button3_top--', '--button3_bottom--'),
        "A5": ('--A5--', '--button4_top--', '--button4_bottom--'),
        "A6": ('--A6--', '--button5_top--', '--button5_bottom--'),
        "A7": ('--A7--', '--button6_top--', '--button6_bottom--'),
        "B1": ('--B1--', '--button7_top--', '--button7_bottom--'),
        "B2": ('--B2--', '--button8_top--', '--button8_bottom--'),
        "B3": ('--B3--', '--button9_top--', '--button9_bottom--'),
        "B4": ('--B4--', '--button10_top--', '--button10_bottom--'),
        "B5": ('--B5--', '--button11_top--', '--button11_bottom--'),
        "B6": ('--B6--', '--button12_top--', '--button12_bottom--'),
        "B7": ('--B7--', '--button13_top--', '--button13_bottom--'),
        "C1": ('--C1--', '--button14_top--', '--button14_bottom--'),
        "C2": ('--C2--', '--button15_top--', '--button15_bottom--'),
        "C3": ('--C3--', '--button16_top--', '--button16_bottom--'),
        "C4": ('--C4--', '--button17_top--', '--button17_bottom--'),
        "C5": ('--C5--', '--button18_top--', '--button18_bottom--'),
        "C6": ('--C6--', '--button19_top--', '--button19_bottom--'),
        "C7": ('--C7--', '--button20_top--', '--button20_bottom--'),
    }

    if selection_entry in selection_map:
        selection_key, button_top, button_bottom = selection_map[selection_entry]
        jukebox_selection_window[selection_key].update(disabled=False)
        jukebox_selection_window[button_top].update(disabled=False)
        jukebox_selection_window[button_bottom].update(disabled=False)

    control_button_window['--select--'].update(disabled=False)
    return selection_entry
