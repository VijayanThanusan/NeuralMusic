import midi
import os
import music21

def merger(arrayOfFileNameToMerge,fileNameToSave):
    name = "test_SoundLikePro"
    ticks_per_quarter = 240
    quantization = 5
    instrument_type = arrayOfFileNameToMerge
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
    newSong.save('music/'+fileNameToSave)


