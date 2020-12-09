# These are the functions involve with the customer_premise_equipment

# state constants
IDLE = 0
REQUEST = 1
RESPONSE = 2
SEND = 3
RECEIVE = 4

# responses
ACK = 1
NACK = 0

TIMEOUT = 10
COUNTER_DEFAULT = 1


# CPE class
class CPE:
    def __init__(self, identifier, state, signal_strength, privilege):
        self.identifier = identifier
        self.state = state
        self.signal_strength = signal_strength
        self.privilege = privilege
        self.counter = COUNTER_DEFAULT

    def get_identifier(self):
        return self.identifier

    def get_state(self):
        return self.state

    def get_signal_strength(self):
        return self.signal_strength

    def get_privilege(self):
        return self.privilege

    def get_counter(self):
        return self.counter

    def set_state(self, new_state):
        self.state = new_state

    def set_signal_strength(self, new_signal_strength):
        self.signal_strength = new_signal_strength

    def set_privilege(self, new_privilege):
        self.privilege = new_privilege

    def increment_counter(self):
        if self.counter == TIMEOUT:
            self.counter = 1
        else:
            self.counter += 1


def function():
    print("this is a customer premise equipment function")
    return 0


def cpe_status(cpe):
    if type(cpe) != CPE:
        print("This is not a CPE")
        return 0

    print("CPE status:" +
          "\n  id: " + str(cpe.identifier) +
          "\n  state: " + str(cpe.state) +
          "\n  signal_strength: " + str(cpe.signal_strength) +
          "\n  privilege: " + str(cpe.privilege) +
          "\n  counter: " + str(cpe.counter))

    return 1



