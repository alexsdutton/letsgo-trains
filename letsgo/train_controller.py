class TrainController:
    name: str


class PoweredUpTrainController(TrainController):
    name = "powered_up"

    def __init__(self, mac_address):
        self.mac_address = mac_address
