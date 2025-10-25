# ============================================================================
# CONVERGENCE JUKEBOX 2026 - BAND NAME FORMATTING MODULE
# ============================================================================
# This module handles special formatting for band names
# Purpose: Add "The" prefix to band names and apply exemptions
# ============================================================================

import sys
import os

# ============================================================================
# BAND NAME CHECK AND FORMATTING
# ============================================================================

def the_bands_name_check(jukebox_selection_window, dir_path):
    """
    Checks and formats band names by adding "The" prefix where appropriate.

    This function:
    - Reads the_bands.txt for band names that need "The" prefix
    - Reads the_exempted_bands.txt for bands that should not get "The"
    - Updates all 21 artist display buttons with formatted names
    - Adjusts font size if band name is too long (>22 characters)

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection display
        dir_path (str): Directory path for accessing configuration files

    Returns:
        None - Updates window elements directly
    """
    # List of all artist display buttons (bottom buttons of each song pair)
    jukebox_selection_windows_to_update = [
        '--button0_bottom--', '--button1_bottom--', '--button2_bottom--', '--button3_bottom--',
        '--button4_bottom--', '--button5_bottom--', '--button6_bottom--', '--button7_bottom--',
        '--button8_bottom--', '--button9_bottom--', '--button10_bottom--', '--button11_bottom--',
        '--button12_bottom--', '--button13_bottom--', '--button14_bottom--', '--button15_bottom--',
        '--button16_bottom--', '--button17_bottom--', '--button18_bottom--', '--button19_bottom--',
        '--button20_bottom--'
    ]

    # Check platform and use appropriate path separators
    if sys.platform.startswith('linux'):
        file_separator = '/'
    else:  # Windows
        file_separator = '\\'

    # Process each artist button
    for jukebox_selection_windows in jukebox_selection_windows_to_update:
        # Read the band names list from the_bands.txt
        with open(dir_path + file_separator + 'the_bands.txt', 'r') as the_bands_text_file:
            the_bands = the_bands_text_file.read()

            def band_names_exemptions(the_band_to_update):
                """
                Checks if a band name is in the exemptions list.

                If the formatted band name is in the exemptions list, returns the
                original band name without "The". Otherwise returns the formatted name.

                Args:
                    the_band_to_update (str): The band name to check (may have "The" prefix)

                Returns:
                    str: Either the formatted name or original name if exempted
                """
                # Read the exempted bands list
                with open(dir_path + file_separator + 'the_exempted_bands.txt', 'r') as file:
                    # Create list by stripping newlines from each line
                    exempted_bands = [line.strip() for line in file]

                # If formatted name is in exemptions, return original band name
                if the_band_to_update in exempted_bands:
                    the_band_to_update = band_to_check

                return the_band_to_update

            # Get the current artist name from the button
            band_to_check = (jukebox_selection_window[jukebox_selection_windows].get_text())

            # Check if band name is in the bands list (case-insensitive)
            if band_to_check.lower() in the_bands:
                # Add "The" prefix to the band name
                the_band_to_update = 'The ' + band_to_check

                # Apply exemptions (check if this band should not have "The")
                the_band_to_update = band_names_exemptions(the_band_to_update)

                print(the_band_to_update)

                # Check if formatted name is too long (>22 characters)
                if len(the_band_to_update) > 22:
                    # Use smaller font for long names
                    jukebox_selection_window[jukebox_selection_windows].Widget.config(font='Helvetica 10 bold')
                else:
                    # Update button with formatted band name
                    jukebox_selection_window[jukebox_selection_windows].update(the_band_to_update)
