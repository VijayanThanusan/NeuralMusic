'''Model a sequence of MIDI data. Each point in the sequence is a
number from 0 to 2**p-1 that represents a configuration of p pitches
that may be on or off.'''

from datetime import datetime
import itertools
import json
import os
import shutil

from keras import backend as K
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.layers import CuDNNLSTM
from keras.models import Sequential
from keras.optimizers import RMSprop
import numpy as np
from numpy import array

from data import *
from midi_util import array_to_midiN, print_array
from mido import Message,MidiFile,MidiTrack
np.random.seed(10)

# All the pitches represented in the MIDI data arrays.
# TODO: Read pitches from pitches.txt file in corresponding midi array
# directory.
PITCHES = [36, 37, 38, 40, 41, 42, 44, 45, 46, 47, 49, 50, 58, 59, 60, 61, 62, 63, 64, 66,72,76,79,74,71,69,67,77]
# The subset of pitches we'll actually use.
#IN_PITCHES = [36, 38, 42, 58, 59, 61]  # [36, 38, 41, 42, 47, 58, 59, 61]
IN_PITCHES = [72,76,79,74,71,69]
# The pitches we want to generate (potentially for different drum kit)
OUT_PITCHES = IN_PITCHES  # [54, 56, 58, 60, 61, 62, 63, 64]
# The minimum number of hits to keep a drum loop after the types of
# hits have been filtered by IN_PITCHES.
MIN_HITS = 8

########################################################################
# Network architecture parameters.
########################################################################
NUM_HIDDEN_UNITS = 128
# The length of the phrase from which the predict the next symbol.
#PHRASE_LEN = 64
PHRASE_LEN = 10
# Dimensionality of the symbol space.
SYMBOL_DIM = 2 ** len(IN_PITCHES)
NUM_ITERATIONS = 11
BATCH_SIZE = 64

VALIDATION_PERCENT = 0.1
#0.1
BASE_DIR = '/Users/vijayakulanathanthanushan/Downloads/NeuralMuusic'
# BASE_DIR = '/home/ubuntu/neural-beats'

# MIDI_IN_DIR = os.path.join(BASE_DIR, 'midi_arrays/mega/')
# MIDI_IN_DIR = os.path.join(BASE_DIR, 'midi_arrays/mega/Electronic Live 9 SD/Jungle')
MIDI_IN_DIR = os.path.join(BASE_DIR, 'array/')
# MIDI_IN_DIR = os.path.join(BASE_DIR, 'midi_arrays/mega/Rock Essentials 2 Live 9 SD/Preview Files/Fills/4-4 Fills')

MODEL_OUT_DIR = os.path.join(BASE_DIR, 'models')
MODEL_NAME = '2016-07-08'
TRIAL_DIR = os.path.join(MODEL_OUT_DIR, MODEL_NAME)

MIDI_OUT_DIR = os.path.join(TRIAL_DIR, 'gen-midi')

LOAD_WEIGHTS = True

# Encode each configuration of p pitches, each on or off, as a
# number between 0 and 2**p-1.
#assert len(IN_PITCHES) <= 8, 'Too many configurations for this many pitches!'
encodings = {
    config: i
    for i, config in enumerate(itertools.product([0, 1], repeat=len(IN_PITCHES)))
}

decodings = {
    i: config
    for i, config in enumerate(itertools.product([0, 1], repeat=len(IN_PITCHES)))
}


def sample(a, temperature=1.0):
    # helper function to sample an index from a probability array
    # a = np.log(a) / temperature
    # a = np.exp(a) / np.sum(np.exp(a))
    # return np.argmax(np.random.multinomial(1, a, 1))
    a = np.log(a) / temperature
    dist = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(a))
    return np.random.choice(choices, p=dist)

def encode(midi_array):
    '''Encode a folded MIDI array into a sequence of integers.'''
    return [
        encodings[tuple((time_slice > 0).astype(int))]
        for time_slice in midi_array
    ]


def decode(config_ids):
    '''Decode a sequence of integers into a folded MIDI array.'''
    velocity = 120
    return velocity * np.vstack(
        [list(decodings[id]) for id in config_ids])


def unfold(midi_array, pitches):
    '''Unfold a folded MIDI array with the given pitches.'''
    # Create an array of all the 128 pitches and fill in the
    # corresponding pitches.
    res = np.zeros((midi_array.shape[0], 128))
    assert midi_array.shape[1] == len(pitches), 'Mapping between unequal number of pitches!'
    for i in range(len(pitches)):
        res[:, pitches[i]] = midi_array[:, i]
    return res

def crop_center(img,cropx,cropy):
    y,x = img.shape
    startx = x//2-(cropx//2)
    starty = y//2-(cropy//2)
    return img[starty:starty+cropy,startx:startx+cropx]

def prepare_data():
    # Load the data.
    # Concatenate all the vectorized midi files.
    num_steps = 0

    # Sequence of configuration numbers representing combinations of
    # active pitches.
    config_sequences = []
    num_dirs = len([x for x in os.walk(MIDI_IN_DIR)])
    assert num_dirs > 0, 'No data found at {}'.format(MIDI_IN_DIR)

    in_pitch_indices = [PITCHES.index(p) for p in IN_PITCHES]
    for dir_idx, (root, dirs, files) in enumerate(os.walk(MIDI_IN_DIR)):
        for filename in files:
            print("filename"+filename)
            if filename.split('.')[-1] != 'npy':
                continue
            array = np.load(os.path.join(root, filename))
            newArray = []
            #array = crop_center(array,)
            print("array is " + str(array))
            for i,val in enumerate(array):
                for j, valJ in enumerate(val):
                    #print(" for i " + str(i) + " val : " + str(val) + " j = " + str(j) + " valj : " + str(valJ))
                    if(valJ > 0):
                        newArray.append(val)
                        break
            newArray = np.asarray(newArray,dtype=np.float32)
            print("the type of array is " + str(type(array)))
            print("the type of newArray is " + str(type(newArray)))
            #array = newArray
            print("sizzzzzeOfArray is " + str(len(array)))
            print("what I want to know is " + str(np.sum(np.sum(array[:, in_pitch_indices] > 0))))
            if np.sum(np.sum(array[:, in_pitch_indices] > 0)) < MIN_HITS:
                continue
            print("in_pitch_indices "+ str(in_pitch_indices))
            config_sequences.append(np.array(encode(array[:, in_pitch_indices])))
            print("the len of config_sequences are "  + str(len(config_sequences)))
        print
        'Loaded {}/{} directories'.format(dir_idx + 1, num_dirs)
    print("config_sequences"+str(config_sequences))
    # Construct labeled examples.
    # Use a generator for X and y as the whole dataset may not fit in
    # memory.
    train_generator = SequenceDataGenerator(config_sequences,
                                            phrase_length=PHRASE_LEN,
                                            dim=SYMBOL_DIM,
                                            batch_size=BATCH_SIZE,
                                            is_validation=False,
                                            validation_percent=VALIDATION_PERCENT)

    valid_generator = SequenceDataGenerator(config_sequences,
                                            phrase_length=PHRASE_LEN,
                                            dim=SYMBOL_DIM,
                                            batch_size=BATCH_SIZE,
                                            is_validation=True,
                                            validation_percent=VALIDATION_PERCENT)

    return config_sequences, train_generator, valid_generator


def generate(model, seed, mid_name, temperature=1.0, length=512):
    '''Generate sequence using model, seed, and temperature.'''

    generated = []
    phrase = seed

    if not hasattr(temperature, '__len__'):
        temperature = [temperature for _ in range(length)]

    for temp in temperature:
        x = np.zeros((1, PHRASE_LEN, SYMBOL_DIM))
        for t, config_id in enumerate(phrase):
            x[0, t, config_id] = 1
        preds = model.predict(x, verbose=0)[0]
        next_id = sample(preds, temp)

        generated += [next_id]
        phrase = phrase[1:] + [next_id]

    mid = array_to_midiN(unfold(decode(generated), OUT_PITCHES), mid_name)
    print("the mid is + " + str(type(mid)))
    for element in mid:
        print("the intitial mid is " + str(element))
        #element = updateValue(element)
        #element.time = int(element.time)
        #print("theChecko " + str(type(element)))
    mid = updateValue(mid)
    for element in mid:
       print("elmentsdfdf is " + str(element))

    print("the mid_name is + " + str(mid_name))
    mid.save(os.path.join(MIDI_OUT_DIR, mid_name))
    return mid




def init_model():
    # Build the model.
    model = Sequential()
    model.add(LSTM(
        NUM_HIDDEN_UNITS,
        return_sequences=True,
        input_shape=(PHRASE_LEN, SYMBOL_DIM)))
    model.add(Dropout(0.3))
    '''
    model.add(LSTM(
        NUM_HIDDEN_UNITS,
        return_sequences=True,
        input_shape=(SYMBOL_DIM, SYMBOL_DIM)))
    model.add(Dropout(0.2))
    '''
    model.add(LSTM(NUM_HIDDEN_UNITS, return_sequences=False))
    model.add(Dropout(0.3))
    model.add(Dense(SYMBOL_DIM))
    model.add(Activation('softmax'))
    model.compile(
        loss='categorical_crossentropy',
        optimizer=RMSprop(lr=1e-03, rho=0.9, epsilon=1e-08))
    return model


def updateValue(midiFileInput):
    midiFileToReturn = MidiFile()
    track = MidiTrack()
    midiFileToReturn.tracks.append(track)
    tmpTime = 0
    #for element in midiFileInput:
    #    print("notrack: "+ str(element))
    for element in midiFileInput.tracks:
        print("inFOrefe is " + str(element))
        #if(element.type == "note_on" or element.type == "note_off"):
            #print("timoIs " + str(element.time))
            ##element.time = int(element.time*480)
            #element.time = int(element.time*480)
            #tmpTime+=1
            #track.append(element)
        for msg in element:
            msg.time = int(msg.time)
            print("track" + str(msg.time))
            track.append(msg)
        #else:
        #    track.append(element)
    #print("for message + " + str(messageInput) + " type " + str(messageInput.type))
    #print("from updatevalue " + str(message.channel))
    #print("from uV2 " + str(Message(message.type, message.channel, message.note, message.velocity, int(message.time))))
    #message.time = int(message.time)
    #return Message(message.type,message.channel,message.note,message.velocity,int(message.time))
    #if(messageInput.type == "note_on" or messageInput.type == "note_off"):
    #    message =
    return midiFileToReturn

def train(config_sequences, train_generator, valid_generator):
    '''Train model and save weights.'''

    # Create the trial directory.
    if not os.path.exists(TRIAL_DIR):
        os.makedirs(TRIAL_DIR)
    # Copy the source file, with a version number, to the trial directory.
    source_filename = __file__
    versioned_source_filename = ''.join([
        ''.join(source_filename.split('.')[:-1]),
        '-' + datetime.strftime(datetime.now(), '%Y%m%d%H%M%S') + '.',
        source_filename.split('.')[-1]
    ])
    shutil.copyfile(
        source_filename,
        os.path.join(TRIAL_DIR, versioned_source_filename))

    # Initialize the model.
    model = init_model()
    print
    model.summary()

    # Train the model
    if not os.path.exists(MIDI_OUT_DIR):
        os.makedirs(MIDI_OUT_DIR)
    if not os.path.exists(MODEL_OUT_DIR):
        os.makedirs(MODEL_OUT_DIR)
    print('Training the model...')

    if LOAD_WEIGHTS:
        print('Attempting to load previous weights...')
        weights_path = os.path.join(TRIAL_DIR, MODEL_NAME)
        if os.path.exists(weights_path):
            model.load_weights(weights_path)

    best_val_loss = None

    sequence_indices = idx_seq_of_length(config_sequences, PHRASE_LEN + 1)
    n_points = len(sequence_indices)

    nb_val_samples = n_points * VALIDATION_PERCENT
    print('Number of training points: {}'.format(n_points))
    print('Using {} validation batches'.format(nb_val_samples))

    for i in range(NUM_ITERATIONS):
        print('Iteration {}'.format(i))

        history = model.fit_generator(
            train_generator.gen(),
            samples_per_epoch=BATCH_SIZE,
            nb_epoch=1,
            validation_data=valid_generator.gen(),
            nb_val_samples=nb_val_samples)

        val_loss = history.history['val_loss'][-1]
        if best_val_loss is None or val_loss < best_val_loss:
            print
            'Best validation loss so far. Saving...'
            best_val_loss = val_loss
            model.save_weights(os.path.join(TRIAL_DIR, MODEL_NAME),
                               overwrite=True)
        # Write history.
        with open(os.path.join(TRIAL_DIR, 'history.jsonl'), 'a') as fp:
            json.dump(history.history, fp)
            fp.write('\n')

        # Reset seed so we can compare generated patterns across iterations.
        np.random.seed(0)

        sequence_indices = idx_seq_of_length(config_sequences, PHRASE_LEN)
        seq_index, phrase_start_index = sequence_indices[
            np.random.choice(len(sequence_indices))]
        gen_length = 512

        # Generate samples.
        if not (i > 9 and i % 10 == 0):
            continue
        print("checkpoint 1 + " + str(i))
        for temperature in [0.5, 0.75, 1.0]:
            generated = []
            phrase = list(
                config_sequences[seq_index][
                phrase_start_index: phrase_start_index + PHRASE_LEN])

            print('----- Generating with temperature:', temperature)
            print("checkpoint 2 + " + str(i))
            generate(model,
                     phrase,
                     'out_{}_{}_{}.mid'.format(gen_length, temperature, i),
                     temperature=temperature,
                     length=gen_length)
    return model


def run_train():
    config_sequences, train_generator, valid_generator = prepare_data()
    train(config_sequences, train_generator, valid_generator)


def run_generate():
    print
    'Loading model...'
    model = init_model()
    model.load_weights(os.path.join(TRIAL_DIR, MODEL_NAME))
    seed = np.zeros((32, 6))

    config_sequences, train_generator, valid_generator = prepare_data()
    sequence_indices = idx_seq_of_length(config_sequences, PHRASE_LEN)

    print(
    'Generating...')
    length = 512
    for i in range(5):
        print
        'i', i
        np.random.seed(0)
        seq_index, phrase_start_index = sequence_indices[
            np.random.choice(len(sequence_indices))]

        seed = list(
            config_sequences[seq_index][
            phrase_start_index: phrase_start_index + PHRASE_LEN])

        for temperature in [0.5, 0.9, 1.5, 2]:
            print
            'Temperature', temperature
            generate(model,
                     seed,
                     'house_randseed_{}_{}_{}.mid'.format(length, temperature, i),
                     temperature=temperature,
                     length=length)

    """
    # Normal techno pattern
    seed[0,0] = 1 # kick
    seed[4,2] = 1 # hat
    seed[6,2] = 1 # hat
    seed[8,0] = 1 # kick
    seed[12,2] = 1 # hat
    seed[16,0] = 1 # kick
    seed[20,2] = 1 # hat
    seed[22,2] = 1 # hat
    seed[24,0] = 1 # kick
    seed[28,2] = 1 # hat
    """
    """
    # Broken beat / electro pattern
    seed[0,0] = 1 # Kick
    seed[8,1] = 1 # Snare
    seed[12,0] = 1 # Kick
    seed[24,1] = 1 # Snare
    seed[30,1] = 1 # Snare
    """

    """
    print 'Generating...'
    length = 512
    for temperature in [0.5,0.9,1.5,2]:
        print 'Temperature', temperature
        for i in xrange(3):
            print 'i', i
            generate(model,
                     encode(seed),
                     'house_{}_{}_{}.mid'.format(length, temperature, i),
                     temperature=temperature,
                     length=length)
    """

    """
    length = 32 * 16
    base_temperature = 0.7
    high_temperature = 2
    temperature = np.array([base_temperature] * length)
    temperature[::16] = high_temperature
    #temperature[1::16] = high_temperature
    #temperature[2::16] = high_temperature
    #temperature[3::16] = high_temperature

    for i in xrange(4):
        print 'pattern', i
        generate(model,
                 encode(seed),
                 'out_tempsched_techno2_{}_{}_{}.mid'.format(base_temperature, high_temperature, i),
                 temperature=temperature,
                 length=length)
    """


run_train()