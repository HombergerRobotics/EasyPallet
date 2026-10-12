from DRCF import *
import easypallet

# Load the palletizing project created with the EasyPallet Editor.
builder = easypallet.EasyPalletBuilder("my_project")

# Set the starting position of the palletizing sequence.
# The first argument is the layer index and the second is the box index.
builder.start_from(0, 0)

# Iterate through the boxes in the palletizing sequence.
# Each iteration returns a BoxPlacement object containing the
# position and orientation of the current box.
for box_placement in builder:

    # Get the current layer and box indexes.
    print("Layer:", builder.get_current_layer())
    print("Box:", builder.get_current_box())

    # Get the box position from the BoxPlacement object.
    # X and Y are the box coordinates defined by the EasyPallet layout.
    print("X:", box_placement.x)
    print("Y:", box_placement.y)

    # Get the orientation of the box.
    # The value can be TH0, TH90, TH180, or TH270.
    print("Orientation:", box_placement.th)
