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


# Load the palletizing project created with the EasyPallet Editor.
builder = easypallet.EasyPalletBuilder("my_project")


# User coordinate frame defined in the Doosan teach pendant.
# This frame represents the reference coordinate system used to
# define the box picking position.
BOX_FRAME = 103


# Get the box dimensions from the EasyPallet project.
# X and Y are set to half of the box length and width so that
# the reference position corresponds to the center of the box.
# Z is set to the full box height so that the pose is positioned
# at the top surface of the box.
box_x = builder.get_project().get_box().get_length() / 2
box_y = builder.get_project().get_box().get_width() / 2
box_z = builder.get_project().get_box().get_height()


# Define the picking pose relative to the box coordinate frame.
# Transform the pose from BOX_FRAME to the Doosan base coordinate
# frame so that it can be used directly for robot motion.
pick_pose = coord_transform(
    posx(box_x, box_y, box_z, 0, 180, 0),
    ref_in=BOX_FRAME,
    ref_out=DR_BASE
)


# Iterate through all boxes in the palletizing sequence.
for box_placement in builder:

    # Move to an approach position 100 mm above the pick position.
    # This provides a safe approach before moving down to the box.
    movejx(trans(pick_pose, posx(z=100)), sol=get_current_solution_space())

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
    movejx(trans(place_pose, posx(x=20, y=20, z=100)), ref=FRAME_A, sol=get_current_solution_space())

    # Move to the final placement position.
    movel(place_pose, ref=FRAME_A)

    # Open the gripper and release the box.
    release()

    # Move back to the approach position after placing the box.
    movel(trans(place_pose, posx(z=100)), ref=FRAME_A)
