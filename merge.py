import midi
import os
import music21

def merger(arrayOfFileNameToMerge,fileNameToSave):
    instrument_type = arrayOfFileNameToMerge
    array_notes = len(instrument_type)
    from mido import MidiTrack,MidiFile,MetaMessage,Message
    newSong = MidiFile()


    for i in range(array_notes):
        if os.path.isfile('music/' + str(instrument_type[i]) + '.mid'):
            readingMidiFile = MidiFile('music/' + str(instrument_type[i]) + '.mid')
            for e,track in enumerate(readingMidiFile.tracks):
                newTrack = MidiTrack()
                newSong.tracks.append(newTrack)

                for msg in track:
                    newTrack.append(msg)


        else:
            print("the file " + str(instrument_type[i]) + "not exisit")

    newSong.save('music/'+fileNameToSave)


