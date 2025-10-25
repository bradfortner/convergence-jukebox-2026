# ============================================================================
# CONVERGENCE JUKEBOX 2026 - BUTTON CONTROL FUNCTIONS MODULE
# ============================================================================
# This module contains all button enable/disable control functions
# Purpose: Manage UI button states (enable/disable) based on user interactions
# ============================================================================

# ============================================================================
# DISABLE A SELECTION BUTTONS
# ============================================================================

def disable_a_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disables all A-section selection buttons and controls.

    Prevents user interaction with A selection group when another section is active.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons (A/B/C)
    """
    # Buttons in A section (buttons 0-6, top and bottom)
    buttons_to_disable = ['--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
                          '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
                          '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
                          '--button6_top--', '--button6_bottom--']

    # Control buttons (B and C) to disable when A is selected
    control_buttons_to_disable = ['--B--', '--C--']

    # Selection windows in A section (A1-A7)
    selection_windows_to_disable = ['--A1--', '--A2--', '--A3--', '--A4--', '--A5--', '--A6--', '--A7--']

    # Disable all identified buttons
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)


# ============================================================================
# DISABLE B SELECTION BUTTONS
# ============================================================================

def disable_b_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disables all B-section selection buttons and controls.

    Prevents user interaction with B selection group when another section is active.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons (A/B/C)
    """
    # Buttons in B section (buttons 7-13, top and bottom)
    buttons_to_disable = ['--button7_top--', '--button7_bottom--', '--button8_top--', '--button8_bottom--',
                          '--button9_top--', '--button9_bottom--', '--button10_top--', '--button10_bottom--',
                          '--button11_top--', '--button11_bottom--', '--button12_top--', '--button12_bottom--',
                          '--button13_top--', '--button13_bottom--']

    # Control buttons (A and C) to disable when B is selected
    control_buttons_to_disable = ['--A--', '--C--']

    # Selection windows in B section (B1-B7)
    selection_windows_to_disable = ['--B1--', '--B2--', '--B3--', '--B4--', '--B5--', '--B6--', '--B7--']

    # Disable all identified buttons
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)


# ============================================================================
# DISABLE C SELECTION BUTTONS
# ============================================================================

def disable_c_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disables all C-section selection buttons and controls.

    Prevents user interaction with C selection group when another section is active.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons (A/B/C)
    """
    # Buttons in C section (buttons 14-20, top and bottom)
    buttons_to_disable = ['--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
                          '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
                          '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
                          '--button20_top--', '--button20_bottom--']

    # Control buttons (A and B) to disable when C is selected
    control_buttons_to_disable = ['--A--', '--B--']

    # Selection windows in C section (C1-C7)
    selection_windows_to_disable = ['--C1--', '--C2--', '--C3--', '--C4--', '--C5--', '--C6--', '--C7--']

    # Disable all identified buttons
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)


# ============================================================================
# DISABLE NUMBERED SELECTION BUTTONS
# ============================================================================

def disable_numbered_selection_buttons(control_button_window):
    """
    Disables numbered selection buttons (1-7).

    Prevents user from selecting song numbers when selection criteria not met.

    Args:
        control_button_window: PySimpleGUI window for control buttons
    """
    # Numbered buttons (1-7) to disable
    control_buttons_to_disable = ['--1--', '--2--', '--3--', '--4--', '--5--', '--6--', '--7--']

    # Disable all numbered buttons
    for buttons in control_buttons_to_disable:
        control_button_window[buttons].update(disabled=True)


# ============================================================================
# ENABLE NUMBERED SELECTION BUTTONS
# ============================================================================

def enable_numbered_selection_buttons(control_button_window):
    """
    Re-enables numbered selection buttons (1-7).

    Allows user to select song numbers after section is selected.

    Args:
        control_button_window: PySimpleGUI window for control buttons
    """
    # Numbered buttons (1-7) to enable
    buttons_to_enable = ['--1--', '--2--', '--3--', '--4--', '--5--', '--6--', '--7--']

    # Enable all numbered buttons
    for buttons in buttons_to_enable:
        control_button_window[buttons].update(disabled=False)


# ============================================================================
# ENABLE ALL BUTTONS
# ============================================================================

def enable_all_buttons(jukebox_selection_window, control_button_window):
    """
    Re-enables all selection and control buttons.

    Resets the interface to allow full user interaction with all selections.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons (A/B/C)
    """
    # All song selection buttons (buttons 0-20, top and bottom)
    buttons_to_enable = ['--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
                         '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
                         '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
                         '--button6_top--', '--button6_bottom--', '--button7_top--', '--button7_bottom--',
                         '--button8_top--', '--button8_bottom--', '--button9_top--', '--button9_bottom--',
                         '--button10_top--', '--button10_bottom--', '--button11_top--', '--button11_bottom--',
                         '--button12_top--', '--button12_bottom--', '--button13_top--', '--button13_bottom--',
                         '--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
                         '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
                         '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
                         '--button20_top--', '--button20_bottom--']

    # Section control buttons (A, B, C)
    control_buttons_to_enable = ['--A--', '--B--', '--C--']

    # All selection windows (A1-A7, B1-B7, C1-C7)
    selection_windows_to_enable = ['--A1--', '--A2--', '--A3--', '--A4--', '--A5--', '--A6--', '--A7--',
                                   '--B1--', '--B2--', '--B3--', '--B4--', '--B5--', '--B6--', '--B7--',
                                   '--C1--', '--C2--', '--C3--', '--C4--', '--C5--', '--C6--', '--C7--']

    # Enable all song selection buttons
    for buttons in buttons_to_enable:
        jukebox_selection_window[buttons].update(disabled=False)

    # Enable all control buttons
    for control_buttons in control_buttons_to_enable:
        control_button_window[control_buttons].update(disabled=False)

    # Enable all selection windows
    for selection_windows in selection_windows_to_enable:
        jukebox_selection_window[selection_windows].update(disabled=False)
