from DRCF import *
import easypallet

# User coordinate frame defined in the Doosan teach pendant.
# EasyPallet box positions are defined relative to the pallet frame,
# so this frame must be configured to match the physical pallet position.
FRAME_A = 101
FRAME_B = 102


# Implement these functions with the logic required to control
# the robot gripper or other end-of-arm tooling.
def grasp():
    pass


def release():
    pass


# Fixed robot pose used to pick each box.
# The same pick position is used for every box.
pick_pose = posx(100, 500, 500, 0, 180, 0)


# Load the palletizing project created with the EasyPallet Editor.
builder = easypallet.EasyPalletBuilder("my_project")


# Iterate through all boxes in the palletizing sequence.
for box_placement in builder:

    # Move to an approach position 100 mm above the pick position.
    # This provides a safe approach before moving down to the box.
    movel(trans(pick_pose, posx(z=100)))

    # Move to the actual pick position.
    movel(pick_pose)

    # Close the gripper and grasp the box.
    grasp()

    # Move back to the approach position after picking the box.
    movel(trans(pick_pose, posx(z=100)))


    # Calculate the pose of the current box according to the
    # EasyPallet layout.
    # The returned pose is expressed relative to the pallet frame.
    place_pose = builder.get_current_pose()

    # Move to an approach position before placing the box.
    # X and Y offsets provide a small lateral approach offset,
    # while the Z offset moves the robot 100 mm above the place position.
    # PALLET_FRAME tells the robot to interpret the pose relative
    # to the configured pallet coordinate frame.
    movel(trans(place_pose, posx(x=20, y=20, z=100)), ref=FRAME_A)

    # Move to the final placement position.
    movel(place_pose, ref=FRAME_A)

    # Open the gripper and release the box.
    release()

    # Move back to the approach position after placing the box.
    movel(trans(place_pose, posx(z=100)), ref=FRAME_A)
