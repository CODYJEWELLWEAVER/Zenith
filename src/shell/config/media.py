# HEADPHONE DEVICES
# add more headphones by appending device description, shows different icon for
# sinks in this list
HEADPHONES = [
    "alsa_output.usb-SteelSeries_Arctis_Nova_7X-00.analog-stereo",
    "bluez_output.88_08_94_15_DC_49.1",  # SK Hesh ANC
]

VOLUME_AND_MUTED_UPDATE_INTERVAL = 100  # milliseconds

# My bluetooth speak will present itself as a player
# but does not provide full support for mpris properties. I
# use this as a workaround for keeping playerctl from crashing
# while I use my speaker. Will find a better way to do this in the future.
UNSUPPORTED_PLAYER_NAMES = ["JBL_Charge_5"]
