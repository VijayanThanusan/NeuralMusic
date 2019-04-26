#!/bin/env python

import glob
import pickle
import matplotlib.pyplot as plt
import numpy as np
import msgpack
import csv
from music21 import * #converter, instrument, note, chord
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Activation
from keras.wrappers.scikit_learn import KerasClassifier
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint
from tqdm import tqdm
import argparse
import os
from mido import MidiFile
from midi_util import midi_to_array, quantize


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Save a directory of MIDI files as arrays.')
    parser.add_argument('path', help='Input path')
    parser.add_argument(
        '--use-cached',
        dest='use_cached',
        action='store_true',
        help='Overwrite existing files.')
    parser.add_argument(
        '--quantization',
        default=5,
        help='Defines a 1/2**quantization note quantization grid')
    parser.set_defaults(use_cached=False)
    args = parser.parse_args()
    print(str(args))

    path_prefix, path_suffix = os.path.split(args.path)
    print("the path prefix is " + str(path_prefix))
    print("the path suffix is " + str(path_suffix))

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        print("test 0")
        path_prefix, path_suffix = os.path.split(path_prefix)
        print("test 0 path_prefix" + str(path_prefix))
        print("test 0 path_suffix" + str(path_suffix))
    base_path_out = os.path.join(path_prefix, 'array')
    print("out is " + base_path_out)

    for root, dirs, files in os.walk(args.path):
        for file in files:
            print
            (os.path.join(root, file))
            if file.split('.')[-1] == 'mid':
                print("true " + str(file))
                # Get output file path
                suffix = root.split(args.path)[-1]
                out_dir = base_path_out + '/' + suffix
                out_file = '{}.npy'.format(os.path.join(out_dir, file))
                print("out_dir : " + str(out_dir) + " outfile " + str(out_file))
                if os.path.exists(out_file) and args.use_cached == True:
                    continue

                mid = quantize(MidiFile(os.path.join(root, file)),
                               quantization=args.quantization)
                print("the quantizedMid is " + str(mid))
                time_sig_msgs = [msg for msg in mid.tracks[0] if msg.type == 'time_signature']
                if len(time_sig_msgs) == 1:
                    time_sig = time_sig_msgs[0]
                    if not (time_sig.numerator == 4 and time_sig.denominator == 4):
                        print('Time signature not 4/4. Skipping...')
                        continue
                else:
                    print('No time signature. Skipping...')
                    continue

                array = midi_to_array(mid, int(args.quantization))
                print("len of array is "+ str(len(array)))
                print("array is " + str(array))
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                print ('Saving' + str(out_file))
                np.save(out_file, array)



def main_train():
    path = "normal_songs/"
    instrument_type = ["KeyboardInstrument", "Piano", "Harpsichord", "Clavichord", "Celesta", "Electric Bass", "Electric Guitar", "StringInstrument", ]
    pre_vocab = [[], [], [], [], [], [], [], []]
    s_length = 30
    notes = notes_by_instru(instrument_type, path)
    array_notes = len(notes)
    for i in range(array_notes):    
        pre_vocab[i].append(len(set(notes[i])))

    print("thet_vocab is " + str(pre_vocab))
    t_vocab = np.array(pre_vocab)
    print("thet_vocab is " + str(t_vocab))
    vocab = t_vocab.ravel()
    print("vocab is " + str(vocab))
    for i in range(array_notes):
        print(str(instrument_type[i]) + ": " + str(vocab[i]) + " notes")

    x, y = prepare_sequences(notes, vocab, s_length)
    print(vocab)
    

    if x[0].shape[0] > 50:
        model = net_creation(x, vocab, 0)
        train(model, x[0], y[0], instrument_type, vocab, 0)
    if x[1].shape[0] > 50:
        model2 = net_creation(x, vocab, 1)
        train(model2, x[1], y[1], instrument_type, vocab, 1)
    if x[2].shape[0] > 50:
        model3 = net_creation(x, vocab, 2)
        train(model3, x[2], y[2], instrument_type, vocab, 2)
    if x[3].shape[0] > 50:
        model4 = net_creation(x, vocab, 3)
        train(model4, x[3], y[3], instrument_type, vocab, 3)
    if x[4].shape[0] > 50:
        model5 = net_creation(x, vocab, 4)
        train(model5, x[4], y[4], instrument_type, vocab, 4)
    if x[5].shape[0] > 50:
        model6 = net_creation(x, vocab, 5)
        train(model6, x[5], y[5], instrument_type, vocab, 5)
    if x[6].shape[0] > 50:
        model7 = net_creation(x, vocab, 6)
        train(model7, x[6], y[6], instrument_type, vocab, 6)
    if x[7].shape[0] > 50:
        model8 = net_creation(x, vocab, 7)
        train(model8, x[7], y[7], instrument_type, vocab, 7)
 
def notes_by_instru(instrument_type, path):
    notes = [[], [], [], [], [], [], [], []]
    dumpnote = [[], [], [], [], [], [], [], []]
    files = glob.glob('{}/*.mid*'.format(path))
    for file in tqdm(files):
        midi = converter.parse(file)
        try:
            #partition
            parts = instrument.partitionByInstrument(midi)
        except Exception as e:
            notes_to_parse = midi.flat.notes
        for instru in range(len(parts)):
            if parts.parts[instru].id in instrument_type:
                for element_by_offset in stream.iterator.OffsetIterator(parts[instru]):
                    for entry in element_by_offset:
                        if isinstance(entry, note.Note):
                            notes[instrument_type.index(parts.parts[instru].id)].append(str(entry.pitch))
                        elif isinstance(entry, chord.Chord):
                            notes[instrument_type.index(parts.parts[instru].id)].append('.'.join(str(n) for n in entry.normalOrder))
                        elif isinstance(entry, note.Rest):
                            notes[instrument_type.index(parts.parts[instru].id)].append('Rest')

    array_notes = len(notes)
    for i in range(array_notes):
        with open('data/' + instrument_type[i], 'wb') as filepath: #+ str(i)
            pickle.dump(notes[i], filepath)

    return notes


def prepare_sequences(notes, vocab, sequence_length):
    #Prépare les  séquences
    x = [[], [], [], [], [], [], [], []] #train_x entrée
    y = [[], [], [], [], [], [], [], []]#train_y sortie

    array_notes = len(notes)
    result = []
    n_patterns = [[], [], [], [], [], [], [], []]
    for i in range(array_notes):
        result += notes[i]
        #if(i <= 1):
        #    print("result are for i " + str(i) + " " + str(result) + " and notes are " + str(notes[i]))
    pitchnames = sorted(set(item for item in result))

    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    for nb_notes in range(array_notes):
        for i in range(0, len(notes[nb_notes]) - sequence_length, 1):
            sequence_in = notes[nb_notes][i:i + sequence_length]
            sequence_out = notes[nb_notes][i + sequence_length]
            x[nb_notes].append([note_to_int[char] for char in sequence_in])
            y[nb_notes].append(note_to_int[sequence_out])
        n_patterns[nb_notes] = len(x[nb_notes])
        # reshape les entrées en format compatible avec les couches LSTM
        x[nb_notes] = np.reshape(x[nb_notes], (n_patterns[nb_notes], sequence_length, 1))
        # normalise les entrées
        x[nb_notes] = x[nb_notes] / float(vocab[nb_notes])
        print("x shape is " + str(x[nb_notes].shape[0]))
        if x[nb_notes].shape[0] > 50:
            print("before to cat y " + str(y[nb_notes]))
            y[nb_notes] = np_utils.to_categorical(y[nb_notes])
            print("after to cat y " + str(y[nb_notes]))

    return (x, y)  


def net_creation(x, vocab, i):
    #Structure du réseau de neurone
    model = Sequential()
    model.add(LSTM(512, input_shape=(x[i].shape[1], x[i].shape[2]), return_sequences=True ))
    model.add(Dropout(0.3))
    model.add(LSTM(512, return_sequences=True))
    model.add(Dropout(0.3))
    model.add(LSTM(512))
    model.add(Dense(256))
    model.add(Dropout(0.3))
    model.add(Dense(228))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
    return model

def train(model, x, y, instrument_type, vocab, i):
	#entraîne le réseau de neurones
    filepath = "updates/"+str(instrument_type[i])+"-{epoch:02d}-{loss:.4f}-updates.hdf5"
    checkpoint = ModelCheckpoint(
        filepath,
        monitor='loss',
        verbose=0,
        save_best_only=True,
        mode='min'
    )
    callbacks_list = [checkpoint]
    model.fit(x, y, epochs=50, batch_size=vocab[i],callbacks=callbacks_list)
    
    """
    history = model.fit(x, y, epochs=5, batch_size=8,callbacks=callbacks_list)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.y('prediction')
    plt.x('epoch')
    plt.legend(['training', 'validation'], loc='upper right')
    plt.show()
    """

#if __name__ == '__main__':
#    main_train()