# """ Rassemble les musiques """
# import midi
# from mido import MidiFile,MidiTrack,MetaMessage
# import os
# instrument_type = ["outTest85_512_1.0", "soundTest_pinano","soundTest_Guitar", ]
# pattern = [[], [],[]]
# array_notes = len(instrument_type)
# total = midi.Pattern()
# for i in range(array_notes):
#     if os.path.isfile('music/' + str(instrument_type[i]) + '.mid'):
#         pattern = midi.read_midifile('music/' + str(instrument_type[i]) + '.mid')
#         for track in pattern:
#                for msg in track:
#                 #msg.tick = int(msg.tick/20)
#                 print("the track is " + str(msg) + " " +  str(msg.tick))
#                 total.append(track)
#
#
#
#         midoIs = MidiFile('music/' + str(instrument_type[i]) + '.mid')
#         for trackMido in midoIs.tracks:
#             for msg in trackMido:
#                 print("the mido track is " + str(msg))
# midi.write_midifile('music/TotalSoundTe3A.mid', total)


#
# import midi
# import os
#
# name = "test_SoundLikePro"
# ticks_per_quarter = 240
# quantization = 5
# instrument_type = ["soundTest_Drums", "soundTest_Guitar", "soundTest_pinano" ]
# pattern = [[]]
# array_notes = len(instrument_type)
# total = midi.Pattern()
# from mido import MidiTrack,MidiFile,MetaMessage,Message
# newSong = MidiFile()
#
# newTrack = MidiTrack()
# newSong.tracks.append(newTrack)
# #note_track.append(MetaMessage('track_name', name=name, time=0))
# for i in range(array_notes):
#     if os.path.isfile('music/' + str(instrument_type[i]) + '.mid'):
#         #pattern = midi.read_midifile('music/' + str(instrument_type[i]) + '.mid')
#         #for e,track in enumerate(pattern):
#         readingMidiFile = MidiFile('music/' + str(instrument_type[i]) + '.mid')
#         for e,track in enumerate(readingMidiFile.tracks):
#             #if i == 1:
#             #if e == 0:
#
#
#
#                 #newTrack.append(MetaMessage('track_name', name=str(instrument_type[i]), time=0))
#                 print("the number is " + str(e) + " in instrum " + str(instrument_type[i]))
#                 for msg in track:
#                     print("the msg is " + str(msg.type))
#                     #if msg.type == "note_on" or msg.type == "note_off":
#                     newTrack.append(msg)
#
#
#     else:
#         print("the file " + str(instrument_type[i]) + "not exisit")
# #midi.write_midifile('music/TotalSound13.mid', total)
# newSong.save('music/TotalSound1sddsd2.mid')
#
#
# import midi
# import os
#
# name = "test_SoundLikePro"
# ticks_per_quarter = 240
# quantization = 5
# instrument_type = ["forDrums", "forTrumpet", ]
# pattern = [[]]
# array_notes = len(instrument_type)
# total = midi.Pattern()
# from mido import MidiTrack,MidiFile,MetaMessage,Message
# newSong = MidiFile()
#
#
# #note_track.append(MetaMessage('track_name', name=name, time=0))
# for i in range(array_notes):
#     if os.path.isfile('music/' + str(instrument_type[i]) + '.mid'):
#         #pattern = midi.read_midifile('music/' + str(instrument_type[i]) + '.mid')
#         #for e,track in enumerate(pattern):
#         readingMidiFile = MidiFile('music/' + str(instrument_type[i]) + '.mid')
#         for e,track in enumerate(readingMidiFile.tracks):
#             #if i == 1:
#             #if e == 0:
#                 newTrack = MidiTrack()
#                 newSong.tracks.append(newTrack)
#
#
#                 #newTrack.append(MetaMessage('track_name', name=str(instrument_type[i]), time=0))
#                 print("the number is " + str(e) + " in instrum " + str(instrument_type[i]))
#                 for msg in track:
#                     print("the msg is " + str(msg.type))
#                     #if msg.type == "note_on" or msg.type == "note_off":
#                     newTrack.append(msg)
#
#
#     else:
#         print("the file " + str(instrument_type[i]) + "not exisit")
# #midi.write_midifile('music/TotalSound13.mid', total)
# newSong.save('music/onlyTrumpetAnd1.mid')




import midi
import os
import music21

name = "test_SoundLikePro"
ticks_per_quarter = 240
quantization = 5
instrument_type = ["DMGDRUMS","DMGPIANO", ]
pattern = [[]]
array_notes = len(instrument_type)
total = midi.Pattern()
from mido import MidiTrack,MidiFile,MetaMessage,Message
newSong = MidiFile()


#note_track.append(MetaMessage('track_name', name=name, time=0))
for i in range(array_notes):
    if os.path.isfile('music/' + str(instrument_type[i]) + '.mid'):
        #pattern = midi.read_midifile('music/' + str(instrument_type[i]) + '.mid')
        #for e,track in enumerate(pattern):
        readingMidiFile = MidiFile('music/' + str(instrument_type[i]) + '.mid')
        for e,track in enumerate(readingMidiFile.tracks):
            #if i == 1:
            #if e == 0:
                newTrack = MidiTrack()
                newSong.tracks.append(newTrack)


                #newTrack.append(MetaMessage('track_name', name=str(instrument_type[i]), time=0))
                print("the number is " + str(e) + " in instrum " + str(instrument_type[i]))
                for msg in track:
                    print("the msg is " + str(msg.type))
                    #if msg.type == "note_on" or msg.type == "note_off":
                    newTrack.append(msg)


    else:
        print("the file " + str(instrument_type[i]) + "not exisit")
#midi.write_midifile('music/TotalSound13.mid', total)
newSong.save('music/DMGPIANODRUMS.mid')


