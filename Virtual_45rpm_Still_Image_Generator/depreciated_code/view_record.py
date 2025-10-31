from PIL import Image, ImageTk
import tkinter as tk

# Open the generated record image
img = Image.open('record_labels/record_test_Quiet Riot_Cum On Feel The Noize.png')

# Display image information
print(f"Image size: {img.size}")
print(f"Image format: {img.format}")
print(f"Image mode: {img.mode}")

# Create Tkinter window
root = tk.Tk()
root.title("Generated Record with Overlay Text")

# Convert PIL image to PhotoImage for Tkinter
photo = ImageTk.PhotoImage(img)

# Create label with image
label = tk.Label(root, image=photo)
label.image = photo  # Keep a reference to prevent garbage collection
label.pack()

# Run the window
root.mainloop()
