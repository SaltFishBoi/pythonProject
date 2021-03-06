from multiprocessing import Process, Value
from transmission import *
import time
# These are the functions involve with the customer_premise_equipment or AP (Access points for BS)

# task 1/9 need to double check the state, can't be at request all time. Need to come out to listen

# state constants
IDLE = 0
CR_REQUEST = 1
CR_RESPONSE = 2
CR_SEND = 3
CR_RECEIVE = 4
CR_DONE = 5
BS_REQUEST = 6
BS_RESPONSE = 7

# request timeout using prime number
CPE_TIMEOUT = [2, 3, 5, 7, 9, 11, 13, 17, 19, 23]
TIME_INTERVAL = 0.1
# time out true or fault
TIMER_DEFAULT = 0
TIME_OUT = 1

# default
COUNTER_DEFAULT = 1
STATE_DEFAULT = IDLE
SIGNAL_STRENGTH_DEFAULT = 1
PRIVILEGE_DEFAULT = 0
NUM_CPE_DEFAULT = 7

INTERRUPT_FLAG = 0


# CPE class
class CPE:
    def __init__(self, identifier,
                 state=STATE_DEFAULT,
                 signal_strength=SIGNAL_STRENGTH_DEFAULT,
                 channel=RESERVED_CH,
                 target=None):

        self.identifier = identifier
        self.state = state
        self.signal_strength = signal_strength
        self.channel = channel
        self.target = target

    def get_identifier(self):
        return self.identifier

    def get_state(self):
        return self.state

    def get_signal_strength(self):
        return self.signal_strength

    def get_channel(self):
        return self.channel

    def set_state(self, new_state):
        self.state = new_state

    def set_signal_strength(self, new_signal_strength):
        self.signal_strength = new_signal_strength

    def set_channel(self, new_channel):
        self.channel = new_channel

    def get_target(self):
        return self.target

    def set_target(self, new_target):
        self.target = new_target


class ACTION:
    def __init__(self, target, delay, duration):
        self.target = target
        self.delay = delay
        self.duration = duration

    def get_target(self):
        return self.target

    def get_delay(self):
        return self.delay

    def get_duration(self):
        return self.duration

    def set_delay(self, new_delay):
        self.delay = new_delay


# actions is construct of list of actions to be execute after certain amount of delay


def function():
    print("this is a customer premise equipment function")
    return 0


def cpe_process(env, source_num, device, actions):
    device.set_state(IDLE)
    i = 0

    print("CPE " + str(source_num) + " process begins")

    while INTERRUPT_FLAG == 0:
        if device.get_state() == CR_REQUEST:
            delay = actions[i].get_delay()
            # clear out delay
            #actions[i].set_delay(0)
            cpe_request(env, device, actions[i].get_target(), delay)
        elif device.get_state() == CR_SEND:
            cpe_send(env, device, actions[i].get_target(), device.get_channel(), actions[i].get_duration())
        elif device.get_state() == CR_RECEIVE:
            cpe_receive(env, device, device.get_target(), device.get_channel())
        # IDLE state
        elif device.get_state() == CR_DONE:
            cpe_done(env, device, actions[i].get_target(), device.get_channel())
            i = i + 1
        else:
            if i < len(actions):
                device.set_state(CR_REQUEST)
            else:
                cpe_idle(env, device)

    return 0


def cpe_status(cpe):

    print("CPE status:" +
          "\n  id: " + str(cpe.identifier) +
          "\n  state: " + str(cpe.state) +
          "\n  signal_strength: " + str(cpe.signal_strength) +
          "\n  channel: " + str(cpe.channel) +
          "\n  timer: " + str(cpe.timer))

    return 1


# Timer expire
def cpe_timer_handler(timer, delay):
    timer.value = TIMER_DEFAULT
    time.sleep(delay)
    timer.value = TIME_OUT
    return 0


# make a request phrase to a CR device through BS
# request with unknown ch, let BS decide
def cpe_request(env, source, target, delay):
    print("CPE " + str(source.get_identifier()) + " -> " + str(target) + " request begins")

    timer = Value('i', TIMER_DEFAULT)
    d = Process(target=cpe_timer_handler, args=(timer, delay))
    d.start()
    # setup time before the time out.
    # loop through these while source's timer times up

    while timer.value != TIME_OUT:
        # extract msg from the air
        msg = receive(env, RESERVED_CH)
        time.sleep(TIME_INTERVAL)

        # this won't raise a death lock because only one request BS is processing.
        # in this case, BS picked up other CPE request.
        if (msg[1] == source.get_identifier()) and (msg[2] == BS_REQUEST):
            print("CPE " + str(msg[0]) + " -> " + str(source.get_identifier()) + " request receive")
            cpe_response(env, source, msg[0], msg[3])
            #source.set_state(CR_RECEIVE)
            #source.set_channel(msg[3])

            # end the timer
            timer.value = TIME_OUT
            d.terminate()
            d.join()

    # start to send out the request
    # if the source still active and receive not response from other device, it keeps sending request
    p = 0
    while source.get_state() == CR_REQUEST:
        # send request
        # channel is 0 because it doesn't know what channel to be selected yet
        send(env, source.get_identifier(), target, CR_REQUEST, 0, RESERVED_CH)
        print("CPE " + str(source.get_identifier()) + " -> " + str(target) + " request sends")
        time.sleep(TIME_INTERVAL)

        # start timer
        # prime number wait time
        timer.value = TIMER_DEFAULT
        #print("CPE " + str(source.get_identifier()) + " time out at " + str(CPE_TIMEOUT[p]) + " seconds")
        t = Process(target=cpe_timer_handler, args=(timer, CPE_TIMEOUT[p]))
        p = (p + 1) % len(CPE_TIMEOUT)
        t.start()

        # loop through these while source's timer times up
        while timer.value != TIME_OUT:
            # extract msg from the air
            msg = receive(env, RESERVED_CH)
            time.sleep(TIME_INTERVAL)
            # match the message expected
            if (msg[0] == target) and (msg[1] == source.get_identifier()) and (msg[2] == BS_RESPONSE):
                source.set_state(CR_SEND)
                # selected channel is in the msg[3]
                source.set_channel(msg[3])
                # need to set it to time out to get out of this loop

                # end the timer
                print("CPE " + str(source.get_identifier()) + " <- " + str(target) + " response receive")
                timer.value = TIME_OUT
                t.terminate()
                t.join()

            # this won't raise a death lock because only one request BS is processing.
            # in this case, BS picked up other CPE request.
            elif (msg[1] == source.get_identifier()) and (msg[2] == BS_REQUEST):
                print("CPE " + str(msg[0]) + " -> " + str(source.get_identifier()) + " request receive")
                cpe_response(env, source, msg[0], msg[3])
                # source.set_state(CR_RECEIVE)
                # source.set_channel(msg[3])

                # need to set it to time out to get out of this loop
                # end the timer
                timer.value = TIME_OUT
                t.terminate()
                t.join()

    return 1


# make a response phrase to a CR device through BS
# receiver side never set a timer (either on setup or communication)
def cpe_response(env, source, target, ch):
    print("CPE " + str(target) + " <- " + str(str(source.get_identifier())) + " response begins")

    send(env, source.get_identifier(), target, CR_RESPONSE, ch, RESERVED_CH)
    print("CPE " + str(target) + " <- " + str(str(source.get_identifier())) + " response sends")
    time.sleep(TIME_INTERVAL)
    source.set_state(CR_RECEIVE)
    source.set_target(target)
    source.set_channel(ch)

    return 1


# timer thread is require
def cpe_send(env, source, target, ch, duration):
    print("CPE " + str(source.get_identifier()) + " -> " + str(target) + " send begins")

    # environment update
    set_ch_state(env, ch, LEASE)

    loop_time = float(duration) / TIME_INTERVAL

    for i in range(int(loop_time)):
        if get_ch_state(env, ch) == BUSY:
            source.set_state(CR_REQUEST)
        time.sleep(TIME_INTERVAL)

    source.set_state(CR_DONE)

    return 1


def cpe_receive(env, source, target, ch):
    print("CPE " + str(source.get_identifier()) + " listen to " + str(target) + " receive begins")

    # if the source still active and receive not response from other device, it keeps sending request
    while source.get_state() == CR_RECEIVE:
        # check for valid receive message

        if get_ch_state(env, ch) == BUSY:
            source.set_state(IDLE)

        msg = receive(env, ch)
        time.sleep(TIME_INTERVAL)

        # check end of the message
        if (msg[0] == target) and (msg[1] == source.get_identifier()) and (msg[2] == CR_DONE) and (msg[3] == 0):

            source.set_state(IDLE)
            set_ch_state(env, ch, IDLE)

        # match the message expected
        # if get_ch_state(env, ch) == BUSY:
        #    source.set_state(IDLE)

    return 1


def cpe_done(env, source, target, ch):
    print("CPE " + str(source.get_identifier()) + " done begins")
    while source.get_state() == CR_DONE:
        # send request
        send(env, source.get_identifier(), target, CR_DONE, 0, ch)

        # start timer
        timer = Value('i', TIMER_DEFAULT)
        t = Process(target=cpe_timer_handler, args=(timer, 10))
        t.start()

        # loop through these while source's timer times up
        while timer.value != TIME_OUT:
            # extract msg from the air
            msg = receive(env, ch)
            time.sleep(TIME_INTERVAL)

            # in case no message received, but the state is changed
            if get_ch_state(env, ch) != LEASE:
                source.set_state(IDLE)
                timer.value = TIME_OUT
                t.terminate()
                t.join()

            # match the message expected
            elif (msg[0] == target) and (msg[1] == source.get_identifier()) and (msg[2] == CR_RECEIVE):

                # end the timer
                timer.value = TIME_OUT
                t.terminate()
                t.join()

    source.set_state(IDLE)
    return 1

def cpe_idle(env, source):
    msg = receive(env, RESERVED_CH)
    time.sleep(TIME_INTERVAL)
    if (msg[1] == source.get_identifier()) and (msg[2] == BS_REQUEST):
        print("CPE " + str(msg[0]) + " -> " + str(source.get_identifier()) + " request receive")
        cpe_response(env, source, msg[0], msg[3])

    return 1
