# These are the functions involve with the customer_premise_equipment

# state constants
IDLE = 0
IN_USED = 1


# LBU class
class LBU:
    def __init__(self, identifier, state, signal_strength, privilege):
        self.identifier = identifier
        self.state = state
        self.signal_strength = signal_strength
        self.privilege = privilege

    def get_identifier(self):
        return self.identifier

    def get_state(self):
        return self.state

    def get_signal_strength(self):
        return self.signal_strength

    def get_privilege(self):
        return self.privilege

    def set_state(self, new_state):
        self.state = new_state

    def set_signal_strength(self, new_signal_strength):
        self.signal_strength = new_signal_strength

    def set_privilege(self, new_privilege):
        self.privilege = new_privilege


def function():
    print("this is a licensed band user function")
    return 0


def lbu_status(lbu):
    if type(lbu) != LBU:
        print("This is not a LBU")
        return 0

    print("LBU status:" +
          "\n  id: " + str(lbu.identifier) +
          "\n  state: " + str(lbu.state) +
          "\n  signal_strength: " + str(lbu.signal_strength) +
          "\n  privilege: " + str(lbu.privilege))

    return 1


