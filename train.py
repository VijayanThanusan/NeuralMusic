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
from mido import MidiFile,MidiTrack,MetaMessage
from midi_util import midi_to_array, quantize,midi_to_arrayWithPitch


def updateValue(midiFileInput):
    midiFileToReturn = MidiFile()
    #track = MidiTrack()
    #midiFileToReturn.tracks.append(track)
    tmpTime = 0
    # for element in midiFileInput:
    #    print("notrack: "+ str(element))

    for element in midiFileInput.tracks:
        tmpTrack = MidiTrack()
        midiFileToReturn.tracks.append(tmpTrack)
        for msg in element:
            if (msg.type == 'time_signature'):
                print("the predzddd is " + str(msg))
                msg.numerator = 4
                msg.denominator = 4
            msg.time = msg.time
            print("the postdzddd is " + str(msg.time))
            tmpTrack.append(msg)
        #track.append(element)
    # for element in midiFileInput.tracks:
    # if(element.type == "note_on" or element.type == "note_off"):
    # print("timoIs " + str(element.time))
    ##element.time = int(element.time*480)
    # element.time = int(element.time*480)
    # tmpTime+=1
    # track.append(element)

    # else:
    #    track.append(element)
    # print("for message + " + str(messageInput) + " type " + str(messageInput.type))
    # print("from updatevalue " + str(message.channel))
    # print("from uV2 " + str(Message(message.type, message.channel, message.note, message.velocity, int(message.time))))
    # message.time = int(message.time)
    # return Message(message.type,message.channel,message.note,message.velocity,int(message.time))
    # if(messageInput.type == "note_on" or messageInput.type == "note_off"):
    #    message =
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
                mid = updateValue(mid)
                print("the quantizedMid is " + str(mid.tracks[0]))
                for element in mid.tracks[0]:
                    print("elementdqsd is " + str(element.type))
                #time_sig_msgs = [msg for msg in mid.tracks[0] if msg.type == 'time_signature']
                for msg in mid.tracks[0]:
                    if msg.type == 'time_signature':
                        time_sig_msgs = [msg]
                        break
                print("lffhf "+str(len(time_sig_msgs)))
                if len(time_sig_msgs) >= 1:
                    time_sig = time_sig_msgs[0]
                    if not (time_sig.numerator == 4 and time_sig.denominator == 4):
                        print('Time signature not 4/4. Skipping...')
                        continue
                else:
                    print('No time signature. Skipping...')
                    continue

                array = midi_to_arrayWithPitch(mid, int(args.quantization))
                for i, val in enumerate(array):
                    print("for i " + str(i) + " val : " + str(val))
                print("len of array is "+ str(len(array)))
                print("array is " + str(array))
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                print ('Saving' + str(out_file))
                np.save(out_file, array)






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