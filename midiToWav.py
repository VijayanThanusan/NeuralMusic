from music21 import converter, instrument
from mido import MidiFile,MidiTrack, Message


def changeInstrument():
    s = converter.parse("music/forGuitar.mid")
    for i, p in enumerate(s.parts):
        if i == 0:
            p.insert(i, instrument.Guitar())

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

    for msg in track:
      actualTrack.append(msg)


if __name__ == '__main__':
   readTempo()
