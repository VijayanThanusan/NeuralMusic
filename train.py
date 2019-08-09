#!/bin/env python

import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Activation
from keras.callbacks import ModelCheckpoint
import argparse
import os
from mido import MidiFile,MidiTrack
from midi_util import quantize,midi_to_arrayWithPitch


def updateValue(midiFileInput):
    midiFileToReturn = MidiFile()

    for element in midiFileInput.tracks:
        tmpTrack = MidiTrack()
        midiFileToReturn.tracks.append(tmpTrack)
        for msg in element:
            if (msg.type == 'time_signature'):
                msg.numerator = 4
                msg.denominator = 4
            msg.time = msg.time
            tmpTrack.append(msg)
    return midiFileInput

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

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)
    base_path_out = os.path.join(path_prefix, 'array')

    for root, dirs, files in os.walk(args.path):
        for file in files:
            print
            (os.path.join(root, file))
            if file.split('.')[-1] == 'mid':
                # Get output file path
                suffix = root.split(args.path)[-1]
                out_dir = base_path_out + '/' + suffix
                out_file = '{}.npy'.format(os.path.join(out_dir, file))
                if os.path.exists(out_file) and args.use_cached == True:
                    continue

                mid = quantize(MidiFile(os.path.join(root, file)),
                               quantization=args.quantization)
                mid = updateValue(mid)

                for msg in mid.tracks[0]:
                    if msg.type == 'time_signature':
                        time_sig_msgs = [msg]
                        break

                if len(time_sig_msgs) >= 1:
                    time_sig = time_sig_msgs[0]
                    if not (time_sig.numerator == 4 and time_sig.denominator == 4):
                        print('Time signature not 4/4. Skipping...')
                        continue
                else:
                    print('No time signature. Skipping...')
                    continue

                array = midi_to_arrayWithPitch(mid, int(args.quantization))
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                print ('Saving' + str(out_file))
                np.save(out_file, array)






def net_creation(x, vocab, i):

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
    


