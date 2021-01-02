from blinker import signal

layout_changed = signal("layout-changed")
"Signal sent when a layout is changed in any way. Will have cleared=True if the layout has been completely reset."

piece_added = signal("piece-added")
piece_removed = signal("piece-removed")
piece_positioned = signal("piece-positioned")

train_added = signal("train-added")
train_removed = signal("train-removed")

train_maximum_motor_speed_changed = signal("train-maximum-motor-speed-changed")
train_motor_speed_changed = signal("train-motor-speed-changed")
train_lights_on_changed = signal("train-lights-on-changed")

train_spotted = signal("train-spotted")

train_name_changed = signal("train-name-changed")

tick = signal("tick")

station_added = signal("station-added")
station_removed = signal("station-removed")

platform_added = signal("platform-added")
platform_removed = signal("platform-removed")

itinerary_added = signal("itinerary-added")
itinerary_removed = signal("itinerary-removed")

controller_added = signal("controller-added")
controller_removed = signal("controller-removed")

sensor_added = signal("sensor-added")
sensor_removed = signal("sensor-removed")
sensor_activity = signal("sensor-activity")
sensor_positioned = signal("sensor-positioned")

controller_changed = signal("controller-changed")
controller_presence_changed = signal("controller-presence-changed")

connected_changed = signal("connected-changed")
battery_level_changed = signal("battery-level-changed")

selection_changed = signal("selection-changed")
