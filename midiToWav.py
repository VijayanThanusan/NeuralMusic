from collections import defaultdict

from mido import MidiFile
from pydub import AudioSegment
from pydub.generators import Sine
import glob
import pickle
import matplotlib.pyplot as plt
import numpy as np
import msgpack
import csv
from music21 import converter, instrument, note, chord
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
from mido import MidiFile,MidiTrack,MetaMessage,Message
from midi_util import midi_to_array, quantize

# def note_to_freq(note, concert_A=440.0):
#     '''
#     from wikipedia: http://en.wikipedia.org/wiki/MIDI_Tuning_Standard#Frequency_values
#     '''
#     return (2.0 ** ((note - 69) / 12.0)) * concert_A
#
#
# mid = MidiFile("./out_512_1.0_10.mid")
# output = AudioSegment.silent(mid.length * 1000.0)
#
# tempo = 100  # bpm
#
#
# def ticks_to_ms(ticks):
#     tick_ms = (60000.0 / tempo) / mid.ticks_per_beat
#     return ticks * tick_ms
#
#
# for track in mid.tracks:
#     # position of rendering in ms
#     current_pos = 0.0
#
#     current_notes = defaultdict(dict)
#     # current_notes = {
#     #   channel: {
#     #     note: (start_time, message)
#     #   }
#     # }
#
#     for msg in track:
#         current_pos += ticks_to_ms(msg.time)
#
#         if msg.type == 'note_on':
#             current_notes[msg.channel][msg.note] = (current_pos, msg)
#
#         if msg.type == 'note_off':
#             start_pos, start_msg = current_notes[msg.channel].pop(msg.note)
#
#             duration = current_pos - start_pos
#
#             signal_generator = Sine(note_to_freq(msg.note))
#             print("the signal is " + str(signal_generator))
#             rendered = signal_generator.to_audio_segment(duration=duration - 50, volume=-20).fade_out(100).fade_in(30)
#
#             output = output.overlay(rendered, start_pos)
#
# output.export("animal.wav", format="wav")


def changeInstrument():
    s = converter.parse("music/forGuitar.mid")
    for i, p in enumerate(s.parts):
        if i == 0:
            print("herrrrooooooo")
            p.insert(i, instrument.Guitar())
        print("i is " + str(i) + "the parrrrts is " + str(p) + " instrument is " + str(
            instrument.partitionByInstrument(p)))

    s.write('midi', 'music/Guitar1.mid')

def readTempo():
    readingMido = MidiFile("music/forDrums.mid")
    actualMidi = MidiFile()
    for i,track in enumerate(readingMido.tracks):
        actualTrack = MidiTrack()
        actualMidi.add_track(actualTrack)

        if i % 2 == 0:

            for msg in track:
               if msg.type == "note_on" or msg.type == "note_off":
                    if msg.channel == 9:
                         actualTrack.append(Message('program_change', program="10", time="0"))
                         break
    # for j,msg in enumerate(track):
    #    if j == 1 :
    #        track.append(Message('program_change', program=9, time=0))

    for msg in track:
      actualTrack.append(msg)
      print("the msg in track " + str(i) + " is : " + str(msg))




    #readingMido.save("TotalSoundNEWDGPTSound")

if __name__ == '__main__':
   # mid = MidiFile('music/soundTest_pinano.mid')
   # for i,track in enumerate(mid.tracks):
   #     for msg in track:
   #         print("the msg is " + str(msg) + " in track number " + str(i))
   readTempo()
