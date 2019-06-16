from blinker import signal

piece_added = signal('piece-added')
piece_removed = signal('piece-removed')

train_added = signal('train-added')
train_removed = signal('train-removed')

train_maximum_motor_speed_changed = signal('train-maximum-motor-speed-changed')
train_motor_speed_changed = signal('train-motor-speed-changed')
train_lights_on_changed = signal('train-lights-on-changed')

train_name_changed = signal('train-name-changed')

train_hub_connected = signal('train-hub-connected')
train_hub_disconnected = signal('train-hub-disconnected')

tick = signal('tick')

station_added = signal('station-added')
station_removed = signal('station-removed')

platform_added = signal('platform-added')
platform_removed = signal('platform-removed')

itinerary_added = signal('itinerary-added')
itinerary_removed = signal('itinerary-removed')
