from collections import defaultdict
import copy
from math import log, floor, ceil
import pprint
from operator import itemgetter


import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
import numpy as np


DEBUG = True

# The MIDI pitches we use.
PITCHES = [36, 37, 38, 40, 41, 42, 44, 45, 46, 47, 49, 50, 58, 59, 60, 61, 62, 63, 64, 66,72,76,79,74,71,69,67,77]

PITCHES_MAP = { p : i for i, p in enumerate(PITCHES) }
PITCHES_VERSION = '0.1'


def getAllNotesFromTrackWithoutOccur(MidoFile):
    notesArray = []
    for track in MidoFile.tracks:
        for msg in track:
            if msg.type == "note_on":
                notesArray.append(msg.note)
    return list(set(notesArray))

def get_note_track(mid):
    '''Given a MIDI object, return the first track with note events.'''

    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.type == 'note_on':
                return i, track
    raise ValueError(
        'MIDI object does not contain any tracks with note messages.')


def quantize_tick(tick, ticks_per_quarter, quantization):
    '''Quantize the timestamp or tick.

    Arguments:
    tick -- An integer timestamp
    ticks_per_quarter -- The number of ticks per quarter note
    quantization -- The note duration, represented as 1/2**quantization
    '''
    #assert (ticks_per_quarter * 4) % 2 ** quantization == 0, \
    #    'Quantization too fine. Ticks per quantum must be an integer.'
    ticks_per_quantum = (ticks_per_quarter * 4) / float(2 ** quantization)
    quantized_ticks = int(
        round(tick / float(ticks_per_quantum)) * ticks_per_quantum)
    return quantized_ticks


def quantize_track(track, ticks_per_quarter, quantization):
    '''Return the differential time stamps of the note_on, note_off, and
    end_of_track events, in order of appearance, with the note_on events
    quantized to the grid given by the quantization.

    Arguments:
    track -- MIDI track containing note event and other messages
    ticks_per_quarter -- The number of ticks per quarter note
    quantization -- The note duration, represented as
      1/2**quantization.'''

    pp = pprint.PrettyPrinter()

    # Message timestamps are represented as differences between
    # consecutive events. Annotate messages with cumulative timestamps.

    # Assume the following structure:
    # [header meta messages] [note messages] [end_of_track message]
    first_note_msg_idx = None
    for i, msg in enumerate(track):
        if msg.type == 'note_on':
            first_note_msg_idx = i
            break

    cum_msgs = list(zip(
        np.cumsum([msg.time for msg in track[first_note_msg_idx:]]),
        [msg for msg in track[first_note_msg_idx:]]))
    end_of_track_cum_time = cum_msgs[-1][0]
    quantized_track = MidiTrack()
    quantized_track.extend(track[:first_note_msg_idx])
    # Keep track of note_on events that have not had an off event yet.
    # note number -> message
    open_msgs = defaultdict(list)
    quantized_msgs = []
    for cum_time, msg in cum_msgs:
        if DEBUG:
            print ('Message:', msg)
            print ('Open messages:')
            pp.pprint(open_msgs)
        if msg.type == 'note_on' and msg.velocity > 0:
            # Store until note off event. Note that there can be
            # several note events for the same note. Subsequent
            # note_off events will be associated with these note_on
            # events in FIFO fashion.
            open_msgs[msg.note].append((cum_time, msg))
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            #assert msg.note in open_msgs, \
            #    'Bad MIDI. Cannot have note off event before note on event'
            note_on_open_msgs = open_msgs[msg.note]
            if(len(note_on_open_msgs) > 0):
                note_on_cum_time, note_on_msg = note_on_open_msgs[0]
                open_msgs[msg.note] = note_on_open_msgs[1:]
                # Quantized note_on time
                quantized_note_on_cum_time = quantize_tick(
                note_on_cum_time, ticks_per_quarter, quantization)
                # The cumulative time of note_off is the quantized
                # cumulative time of note_on plus the orginal difference
                # of the unquantized cumulative times.
                quantized_note_off_cum_time = quantized_note_on_cum_time + (cum_time - note_on_cum_time)
                quantized_msgs.append((min(end_of_track_cum_time, quantized_note_on_cum_time), note_on_msg))
                quantized_msgs.append((min(end_of_track_cum_time, quantized_note_off_cum_time), msg))

            if DEBUG:
                print ('Appended', quantized_msgs[-2:])
        elif msg.type == 'end_of_track':
            quantized_msgs.append((cum_time, msg))

        if DEBUG:
            print ('\n')

    # Now, sort the quantized messages by (cumulative time,
    # note_type), making sure that note_on events come before note_off
    # events when two event have the same cumulative time. Compute
    # differential times and construct the quantized track messages.


    diff_times = [quantized_msgs[0][0]] + list(
        np.diff([ msg[0] for msg in quantized_msgs ]))
    for diff_time, (cum_time, msg) in zip(diff_times, quantized_msgs):
        quantized_track.append(msg.copy(time=diff_time))
    if DEBUG:
        print ('Quantized messages:')
        pp.pprint(quantized_msgs)
        pp.pprint(diff_times)
    return quantized_track


def letter_cmp(a, b):
    if a.time > b.time:
        return -1
    elif a.time == b.time:
        if a.type == "note_on" & b.time != "note_on":
            return 1
        else:
            return -1
    else:
        return 1

def miniLambda(msg):
    if(msg.type == "note_on"):
        print(msg.time * 10)
        return msg
    else:
        print((msg.time + 0.5))
        msg.time += 0.5
        return msg

def quantize(mid, quantization=5):
    '''Return a midi object whose notes are quantized to
    1/2**quantization notes.

    Arguments:
    mid -- MIDI object
    quantization -- The note duration, represented as
      1/2**quantization.'''

    quantized_mid = copy.deepcopy(mid)
    # By convention, Track 0 contains metadata and Track 1 contains
    # the note on and note off events.
    note_track_idx, note_track = get_note_track(mid)
    quantized_mid.tracks[note_track_idx] = quantize_track(
        note_track, mid.ticks_per_beat, quantization)
    return quantized_mid

def Sort_Tuple(tup):
    # getting length of list of tuples
    print("in sorted")
    lst = len(tup)-1
    for i in range(0, lst):

        for j in range(0, lst - i - 1):
            if (tup[j][1].time > tup[j + 1][1].time):
                temp = tup[j]
                tup[j] = tup[j + 1]
                tup[j + 1] = temp
            elif (tup[j][1].time == tup[j + 1][1].time):
                if((tup[j][1].type != 'note_on') & (tup[j + 1][1].type == 'note_on')):
                    temp = tup[j]
                    tup[j] = tup[j + 1]
                    tup[j + 1] = temp
    return tup



def midi_to_arrayWithPitch(mid, quantization):
    '''Return array representation of a 4/4 time signature, MIDI object.

    Normalize the number of time steps in track to a power of 2. Then
    construct a T x N array A (T = number of time steps, N = number of
    MIDI note numbers) where A(t,n) is the velocity of the note number
    n at time step t if the note is active, and 0 if it is not.

    Arguments:
    mid -- MIDI object with a 4/4 time signature
    quantization -- The note duration, represented as 1/2**quantization.'''

    PITCHES = getAllNotesFromTrackWithoutOccur(mid)
    PITCHES_MAP = {p: i for i, p in enumerate(PITCHES)}


    for msg in mid.tracks[0]:
        if msg.type == 'time_signature':
            time_sig_msgs = [msg]
            break
    assert len(time_sig_msgs) == 1, 'No time signature found'
    time_sig = time_sig_msgs[0]
    assert time_sig.numerator == 4 and time_sig.denominator == 4, 'Not 4/4 time.'

    # Quantize the notes to a grid of time steps.
    mid = quantize(mid, quantization=quantization)

    # Convert the note timing and velocity to an array.
    _, track = get_note_track(mid)
    ticks_per_quarter = mid.ticks_per_beat

    time_msgs = [msg for msg in track if hasattr(msg, 'time')]
    cum_times = np.cumsum([msg.time for msg in time_msgs])
    track_len_ticks = cum_times[-1]
    if DEBUG:
        print ('Track len in ticks:', track_len_ticks)
    notes = [
        (time * (2**quantization/4) / (ticks_per_quarter), msg.note, msg.velocity)
        for (time, msg) in zip(cum_times, time_msgs)
        if msg.type == 'note_on' ]
    num_steps = int(round(track_len_ticks / float(ticks_per_quarter)*2**quantization/4))
    normalized_num_steps = int(nearest_pow2(num_steps))

    if DEBUG:
        print (num_steps)
        print (normalized_num_steps)

    midi_array = np.zeros((normalized_num_steps, len(PITCHES)))
    print("begining of big test")
    for (position, note_num, velocity) in notes:
        print("the notes : " + str(notes) + " position : " + str(position) + " note_num " + str(note_num) + " velocity " + str(velocity) + " note_num in pitches " + str(note_num in PITCHES_MAP))
        if position == normalized_num_steps:
            continue
        if position > normalized_num_steps:
            continue
        if note_num in PITCHES_MAP:
            print("note_numdd"+str(position)+ " pitch " + str(PITCHES_MAP[note_num]))
            midi_array[int(position), PITCHES_MAP[note_num]] = velocity

    return midi_array

def midi_to_array(mid, quantization):
    '''Return array representation of a 4/4 time signature, MIDI object.

    Normalize the number of time steps in track to a power of 2. Then
    construct a T x N array A (T = number of time steps, N = number of
    MIDI note numbers) where A(t,n) is the velocity of the note number
    n at time step t if the note is active, and 0 if it is not.

    Arguments:
    mid -- MIDI object with a 4/4 time signature
    quantization -- The note duration, represented as 1/2**quantization.'''
    for element in mid.tracks[0]:
        print("the element is " + str(element.type))
    for msg in mid.tracks[0]:
        if msg.type == 'time_signature':
            time_sig_msgs = [msg]
            break
    print("time_sig_msgs is " + str(time_sig_msgs))
    print("thetime_sig_msgslen is " + str(len(time_sig_msgs)))
    assert len(time_sig_msgs) == 1, 'No time signature found'
    time_sig = time_sig_msgs[0]
    assert time_sig.numerator == 4 and time_sig.denominator == 4, 'Not 4/4 time.'

    # Quantize the notes to a grid of time steps.
    mid = quantize(mid, quantization=quantization)

    # Convert the note timing and velocity to an array.
    _, track = get_note_track(mid)
    ticks_per_quarter = mid.ticks_per_beat

    time_msgs = [msg for msg in track if hasattr(msg, 'time')]
    cum_times = np.cumsum([msg.time for msg in time_msgs])
    track_len_ticks = cum_times[-1]
    if DEBUG:
        print ('Track len in ticks:', track_len_ticks)
    notes = [
        (time * (2**quantization/4) / (ticks_per_quarter), msg.note, msg.velocity)
        for (time, msg) in zip(cum_times, time_msgs)
        if msg.type == 'note_on' ]
    num_steps = int(round(track_len_ticks / float(ticks_per_quarter)*2**quantization/4))
    normalized_num_steps = int(nearest_pow2(num_steps))

    if DEBUG:
        print (num_steps)
        print (normalized_num_steps)

    midi_array = np.zeros((normalized_num_steps, len(PITCHES)))
    print("begining of big test")
    for (position, note_num, velocity) in notes:
        print("the notes : " + str(notes) + " position : " + str(position) + " note_num " + str(note_num) + " velocity " + str(velocity) + " note_num in pitches " + str(note_num in PITCHES_MAP))
        if position == normalized_num_steps:
            continue
        if position > normalized_num_steps:
            continue
        if note_num in PITCHES_MAP:
            print("note_numdd"+str(position)+ " pitch " + str(PITCHES_MAP[note_num]))
            midi_array[int(position), PITCHES_MAP[note_num]] = velocity

    return midi_array

def array_to_midiWithProgramAndChannel(array,
                  name,
                  quantization=5,
                  pitch_offset=0,
                  midi_type=1,
                  ticks_per_quarter=240,programInput=117,channelInput=14):
    '''Convert an array into a MIDI object.
    When an MIDI object is converted to an array, information is
    lost. That information needs to be provided to create a new MIDI
    object from the array. For this application, we don't care about
    this metadata, so we'll use some default values.
    Arguments:
    array -- An array A[time_step, note_number] = 1 if note on, 0 otherwise.
    quantization -- The note duration, represented as 1/2**quantization.
    pitch_offset -- Offset the pitch number relative to the array index.
    midi_type -- Type of MIDI format.
    ticks_per_quarter -- The number of MIDI timesteps per quarter note.'''

    mid = MidiFile()
    meta_track = MidiTrack()
    note_track = MidiTrack()
    mid.tracks.append(meta_track)
    mid.tracks.append(note_track)

    meta_track.append(MetaMessage('track_name', name=name, time=0))
    meta_track.append(MetaMessage('time_signature',
                                  numerator=4,
                                  denominator=4,
                                  clocks_per_click=24,
                                  notated_32nd_notes_per_beat=8,
                                  time=0))
    meta_track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    meta_track.append(MetaMessage('end_of_track', time=0))

    ticks_per_quantum = ticks_per_quarter * 4 / 2**quantization

    note_track.append(MetaMessage('track_name', name=name, time=0))
    cumulative_events = []


    for t, time_slice in enumerate(array):
        for i, pitch_on in enumerate(time_slice):
            if pitch_on > 0:
                cumulative_events.append(dict(
                    type = 'note_on',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * t
                ))
                cumulative_events.append(dict(
                    type = 'note_off',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * (t+1)
                ))

    cumulative_events.sort(
        key=lambda msg: msg['time'] if msg['type']=='note_on' else msg['time'] + 0.5)
    last_time = 0
    note_track.append(Message('program_change', program=programInput, channel=channelInput, time=0))
    for msg in cumulative_events:
        note_track.append(Message(type=msg['type'],
                                  channel=channelInput,
                                  note=msg['pitch'],
                                  velocity=100,
                                  time=msg['time']-last_time))
        last_time = msg['time']
    note_track.append(MetaMessage('end_of_track', time=0))
    return mid

def array_to_midiN(array,
                   name,
                   quantization=5,
                   pitch_offset=0,
                   midi_type=1,
                   ticks_per_quarter=240):
    '''Convert an array into a MIDI object.
    When an MIDI object is converted to an array, information is
    lost. That information needs to be provided to create a new MIDI
    object from the array. For this application, we don't care about
    this metadata, so we'll use some default values.
    Arguments:
    array -- An array A[time_step, note_number] = 1 if note on, 0 otherwise.
    quantization -- The note duration, represented as 1/2**quantization.
    pitch_offset -- Offset the pitch number relative to the array index.
    midi_type -- Type of MIDI format.
    ticks_per_quarter -- The number of MIDI timesteps per quarter note.'''

    mid = MidiFile()
    meta_track = MidiTrack()
    note_track = MidiTrack()
    mid.tracks.append(meta_track)
    mid.tracks.append(note_track)

    meta_track.append(MetaMessage('track_name', name=name, time=0))
    meta_track.append(MetaMessage('time_signature',
                                  numerator=4,
                                  denominator=4,
                                  clocks_per_click=24,
                                  notated_32nd_notes_per_beat=8,
                                  time=0))
    meta_track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    meta_track.append(MetaMessage('end_of_track', time=0))

    ticks_per_quantum = ticks_per_quarter * 4 / 2**quantization

    note_track.append(MetaMessage('track_name', name=name, time=0))
    cumulative_events = []


    for t, time_slice in enumerate(array):
        for i, pitch_on in enumerate(time_slice):
            if pitch_on > 0:
                cumulative_events.append(dict(
                    type = 'note_on',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * t
                ))
                cumulative_events.append(dict(
                    type = 'note_off',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * (t+1)
                ))

    cumulative_events.sort(
        key=lambda msg: msg['time'] if msg['type']=='note_on' else msg['time'] + 0.5)
    last_time = 0
    note_track.append(Message('program_change', program=117, channel=14, time=0))
    for msg in cumulative_events:
        note_track.append(Message(type=msg['type'],
                                  channel=14,
                                  note=msg['pitch'],
                                  velocity=100,
                                  time=msg['time']-last_time))
        last_time = msg['time']
    note_track.append(MetaMessage('end_of_track', time=0))
    return mid


def array_to_midi2(array,
                  name,
                  quantization=5,
                  pitch_offset=0,
                  midi_type=1,
                  ticks_per_quarter=240):
    '''Convert an array into a MIDI object.

    When an MIDI object is converted to an array, information is
    lost. That information needs to be provided to create a new MIDI
    object from the array. For this application, we don't care about
    this metadata, so we'll use some default values.

    Arguments:
    array -- An array A[time_step, note_number] = 1 if note on, 0 otherwise.
    quantization -- The note duration, represented as 1/2**quantization.
    pitch_offset -- Offset the pitch number relative to the array index.
    midi_type -- Type of MIDI format.
    ticks_per_quarter -- The number of MIDI timesteps per quarter note.'''

    mid = MidiFile()
    meta_track = MidiTrack()
    note_track1 = MidiTrack()
    note_track2 = MidiTrack()
    mid.tracks.append(meta_track)
    mid.tracks.append(note_track1)
    mid.tracks.append(note_track2)

    meta_track.append(MetaMessage('track_name', name=name, time=0))
    meta_track.append(MetaMessage('track_name', name=name, time=0))
    meta_track.append(MetaMessage('time_signature',
                                  numerator=4,
                                  denominator=4,
                                  clocks_per_click=24,
                                  notated_32nd_notes_per_beat=8,
                                  time=0))
    meta_track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    meta_track.append(MetaMessage('end_of_track', time=0))

    ticks_per_quantum = ticks_per_quarter * 4 / 2**quantization

    note_track1.append(MetaMessage('track_name', name=name, time=0))
    note_track2.append(MetaMessage('track_name', name=name, time=0))
    cumulative_events = []
    for t, time_slice in enumerate(array):
        for i, pitch_on in enumerate(time_slice):
            if pitch_on > 0:
                cumulative_events.append(dict(
                    type = 'note_on',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * t
                ))
                cumulative_events.append(dict(
                    type = 'note_off',
                    pitch = i + pitch_offset,
                    time = ticks_per_quantum * (t+1)
                ))

    cumulative_events.sort(
        key=lambda msg: msg['time'] if msg['type']=='note_on' else msg['time'] + 0.5)
    last_time = 0
    for msg in cumulative_events:
        note_track1.append(Message(type=msg['type'],
                                  channel=0,
                                  note=msg['pitch'],
                                  velocity=100,
                                  time=msg['time']-last_time))
        note_track2.append(Message(type=msg['type'],
                                   channel=9,
                                   note=msg['pitch'],
                                   velocity=100,
                                   time=msg['time'] - last_time))
        last_time = msg['time']
    note_track1.append(MetaMessage('end_of_track', time=0))
    note_track2.append(MetaMessage('end_of_track', time=0))

    for track in mid.tracks:
        for msg in track:
            print("the actualMessage is " + str(msg))
    return mid


def nearest_pow2(x):
    '''Normalize input to nearest power of 2, or midpoints between
    consecutive powers of two. Round down when halfway between two
    possibilities.'''

    low = 2**int(floor(log(x, 2)))
    high = 2**int(ceil(log(x, 2)))
    mid = (low + high) / 2

    if x < mid:
        high = mid
    else:
        low = mid
    if high - x < x - low:
        nearest = high
    else:
        nearest = low
    return nearest


def print_array(array):
    '''Print a binary array representing midi notes.'''

    res = ''
    for slice in array:
        for pitch in slice:
            if pitch > 0:
                res += 'O'
            else:
                res += '-'
        res += '\n'
    # Take out the last newline
    print (res[:-1])