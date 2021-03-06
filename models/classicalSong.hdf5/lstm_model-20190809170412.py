'''Model a sequence of MIDI data. Each point in the sequence is a
number from 0 to 2**p-1 that represents a configuration of p pitches
that may be on or off.'''

from datetime import datetime
import json
import os
import shutil

from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential
from keras.optimizers import RMSprop

from merge import merger
from data import *
from midi_util import array_to_midiN, array_to_midiWithProgramAndChannel
from mido import MidiFile,MidiTrack
np.random.seed(10)

# All the pitches represented in the MIDI data arrays.
# TODO: Read pitches from pitches.txt file in corresponding midi array
# directory.
PITCHES = [36, 37, 38, 40, 41, 42, 44, 45, 46, 47, 49, 50, 58, 59, 60, 61, 62, 63, 64, 66,72,76,79,74,71,69,67,77]
# The subset of pitches we'll actually use.
IN_PITCHES = [36, 38, 42, 58, 59, 61,44]  # [36, 38, 41, 42, 47, 58, 59, 61]
#IN_PITCHES = [72,76,79,74,71,69]
# The pitches we want to generate (potentially for different drum kit)
OUT_PITCHES = IN_PITCHES  # [54, 56, 58, 60, 61, 62, 63, 64]
# The minimum number of hits to keep a drum loop after the types of
# hits have been filtered by IN_PITCHES.
MIN_HITS = 12

########################################################################
# Network architecture parameters.
########################################################################
NUM_HIDDEN_UNITS = 128
# The length of the phrase from which the predict the next symbol.
#PHRASE_LEN = 64
PHRASE_LEN = 100
# Dimensionality of the symbol space.
SYMBOL_DIM = 2 ** len(IN_PITCHES)
NUM_ITERATIONS = 901
BATCH_SIZE = 64

VALIDATION_PERCENT = 0.1
#BASE_DIR = '/home/thanusan/NeuralMusic'
BASE_DIR = '/Users/vijayakulanathanthanushan/Downloads/NeuralMuusic'

MIDI_IN_DIR = os.path.join(BASE_DIR, 'array/')

MODEL_OUT_DIR = os.path.join(BASE_DIR, 'models')
MODEL_NAME = 'classicalSong.hdf5'
TRIAL_DIR = os.path.join(MODEL_OUT_DIR, MODEL_NAME)

MIDI_OUT_DIR = os.path.join(TRIAL_DIR, 'gen-midi')

LOAD_WEIGHTS = False

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


def modifyPITCHES(songName):
    global PITCHES
    PITCHES = getAllNotesFromTrackWithoutOccur(songName)
    global MIN_HITS
    MIN_HITS = len(PITCHES)
    global IN_PITCHES
    IN_PITCHES = getTheMostUsedNElement(MIN_HITS,songName)
    global OUT_PITCHES
    OUT_PITCHES = IN_PITCHES
    global SYMBOL_DIM
    SYMBOL_DIM = 2 ** len(IN_PITCHES)
    global encodings
    encodings = {
        config: i
        for i, config in enumerate(itertools.product([0, 1], repeat=len(IN_PITCHES)))
    }
    global decodings
    decodings = {
        i: config
        for i, config in enumerate(itertools.product([0, 1], repeat=len(IN_PITCHES)))
    }


def sample(a, temperature=1.0):
    # helper function to sample an index from a probability array
    a = np.log(a) / temperature
    dist = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(a))
    return np.random.choice(choices, p=dist)

def encode(midi_array):
    '''Encode a folded MIDI array into a sequence of integers.'''
    for time_slice in midi_array:
        print(tuple((time_slice > 0).astype(float)))
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


def prepare_dataForASpecificFileAndRandomly(fileName):
    # Load the data.
    # Concatenate all the vectorized midi files.

    # Sequence of configuration numbers representing combinations of
    # active pitches.
    config_sequences = []
    num_dirs = len([x for x in os.walk(MIDI_IN_DIR)])
    assert num_dirs > 0, 'No data found at {}'.format(MIDI_IN_DIR)
    in_pitch_indices = [PITCHES.index(p) for p in IN_PITCHES]
    filename = fileName+".npy"
    if filename.split('.')[-1] != 'npy':
        return
    if (fileName[0:len('music/')] == 'music/'):
        array = np.load(os.path.join("array/" + filename[len('music/'):]))
    else:
        array = np.load(os.path.join("array/" + filename))

    newArray = []
    for i,val in enumerate(array):
        for j, valJ in enumerate(val):
            if(valJ > 0):
                newArray.append(val)
                break
    newArray = np.asarray(newArray,dtype=np.float32)
    if np.sum(np.sum(array[:, in_pitch_indices] > 0)) < MIN_HITS:
        return

    config_sequences.append(np.array(encode(array[:, in_pitch_indices])))
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

def prepare_data():
    # Load the data.
    # Concatenate all the vectorized midi files.

    # Sequence of configuration numbers representing combinations of
    # active pitches.
    config_sequences = []
    num_dirs = len([x for x in os.walk(MIDI_IN_DIR)])
    assert num_dirs > 0, 'No data found at {}'.format(MIDI_IN_DIR)
    in_pitch_indices = [PITCHES.index(p) for p in IN_PITCHES]
    for dir_idx, (root, dirs, files) in enumerate(os.walk(MIDI_IN_DIR)):
        for filename in files:
            if filename.split('.')[-1] != 'npy':
                continue
            array = np.load(os.path.join(root, filename))
            newArray = []
            for i,val in enumerate(array):
                for j, valJ in enumerate(val):
                    if(valJ > 0):
                        newArray.append(val)
                        break
            newArray = np.asarray(newArray,dtype=np.float32)
            if np.sum(np.sum(array[:, in_pitch_indices] > 0)) < MIN_HITS:
                continue

            testArray = array[:,in_pitch_indices]
            config_sequences.append(np.array(encode(array[:, in_pitch_indices])))
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


def generateWithCAndPHipHop(model, seed, mid_name, temperature=1.0, length=512,channelInput = 14, programInput = 117,getArray=False,percussion=0,basse=0,guitare=0,violon=0,saxophone=0,piano=0,musicType=0):
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

    if(getArray == True):
        return generated
    if (musicType == 0):
            generatedForDrums=[]
            for x in range(4,len(generated),4):
                tmpGen = generated[x-4:x]
                for index,tmpX in enumerate(tmpGen):
                    if(tmpX > 0):
                        break
                    else:
                        if(index == len(tmpGen)-1):
                            tmpGen[index] = 1002
                generatedForDrums+=tmpGen
            numberOfActivatedNotes = findNumberOfActivatedNotes(generated)
            generatedForDrums2 = harMonize(generated,3)
            mid = array_to_midiWithProgramAndChannel(unfold(decode(generated), OUT_PITCHES), mid_name,channelInput=channelInput,programInput=programInput)

            mid = updateValue(mid)
            mid.save(os.path.join("music/pianoHiphop.mid"))
            if (percussion == 1):
                generatedForDrums3 = generateFromLoaded2HipHop("hdfFiveFiles/drumshiphop.hdf5",
                                                     "music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineDrums.mid", "Drums", 1,
                                                     True)
                generatedForDrums4 = harMonize(generatedForDrums3,numberOfActivatedNotes)
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineDrums.mid")
                mid2 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForDrums4), OUT_PITCHES), "drumsForMid_name.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
                mid2 = updateValue(mid2)
                mid2.save(os.path.join("music/drumsHiphop.mid"))
            else :
                generatedForDrums4 = [0]
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineDrums.mid")
                mid2 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForDrums4), OUT_PITCHES),
                                                          "music/drumsForMid_name.mid",
                                                          channelInput=tmpChan, programInput=tmpProgram)
                mid2 = updateValue(mid2)
                mid2.save(os.path.join("music/drumsHiphop.mid"))

            #GUITAR
            if (guitare == 1):
                generatedForGuitar = generateFromLoaded2HipHop("hdfFiveFiles/guitar2hiphop.hdf5",
                                                     "music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineGuitar.mid", "Guitar", 1,
                                                     True)
                generatedForGuitar2 = harMonize(generatedForGuitar, numberOfActivatedNotes)
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineGuitar.mid")
                mid3 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForGuitar2), OUT_PITCHES), "guitarForMid_name.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
                mid3 = updateValue(mid3)
                mid3.save(os.path.join("music/guitareHiphop.mid"))
            else:
                generatedForGuitar2 = [0]
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineGuitar.mid")
                mid3 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForGuitar2), OUT_PITCHES),
                                                          "music/guitarForMid_name.mid",
                                                          channelInput=tmpChan, programInput=tmpProgram)
                mid3 = updateValue(mid3)
                mid3.save(os.path.join("music/guitareHiphop.mid"))

            # Bass
            if (basse == 1):
                generatedForBass = generateFromLoaded2HipHop("hdfFiveFiles/basshiphop.hdf5",
                                                     "music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineBass.mid", "Bass", 1,
                                                     True)
                generatedForBass2 = harMonize(generatedForBass, numberOfActivatedNotes)
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineBass.mid")
                mid4 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForBass2), OUT_PITCHES), "bassForMid_name.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
                mid4 = updateValue(mid4)
                mid4.save(os.path.join("music/bassHiphop.mid"))

            else:
                generatedForBass2 = [0]
                tmpChan, tmpProgram = getChannelAndProgam("music/Marvin_Gaye_-_I_Heard_It_Through_the_GrapevineBass.mid")
                mid4 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForBass2), OUT_PITCHES), "bassForMid_name.mid",
                                                          channelInput=tmpChan, programInput=tmpProgram)
                mid4 = updateValue(mid4)
                mid4.save(os.path.join("music/bassHiphop.mid"))

            merger(["pianoHiphop","drumsHiphop","bassHiphop","guitareHiphop",],"HipHop.mid")
            return mid

    elif (musicType == 1):
        numberOfActivatedNotes = findNumberOfActivatedNotes(generated)
        mid = array_to_midiWithProgramAndChannel(unfold(decode(generated), OUT_PITCHES), mid_name,
                                                 channelInput=channelInput, programInput=programInput)
        mid = updateValue(mid)
        mid.save(os.path.join("music/pianoPop.mid"))
        if (guitare == 1):
            generatedForGuitare3 = generateFromLoaded2HipHop("hdfFiveFiles/london_bridge.hdf5",
                                                           "music/london_bridge.mid",
                                                           "Guitare", 1,
                                                           True)
            generatedForGuitare4 = harMonize(generatedForGuitare3, numberOfActivatedNotes)
            tmpChan, tmpProgram = getChannelAndProgam("music/london_bridge.mid")
            mid2 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForGuitare4), OUT_PITCHES),
                                                      "music/london_bridge.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
            mid2 = updateValue(mid2)
            mid2.save(os.path.join("music/guitarePop.mid"))
        else:
            generatedForGuitare4 = [0]
            tmpChan, tmpProgram = getChannelAndProgam("music/london_bridge.mid")
            mid2 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForGuitare4), OUT_PITCHES),
                                                      "music/london_bridge.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
            mid2 = updateValue(mid2)
            mid2.save(os.path.join("music/guitarePop.mid"))


        if (violon == 1):
            generatedForViolin = generateFromLoaded2HipHop("hdfFiveFiles/10_little_indiansvln.hdf5",
                                                           "music/10_little_indiansvln.mid",
                                                           "Violin", 1,
                                                           True)
            generatedForViolin2 = harMonize(generatedForViolin, numberOfActivatedNotes)
            tmpChan, tmpProgram = getChannelAndProgam("music/10_little_indiansvln.mid")
            mid3 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForViolin2), OUT_PITCHES),
                                                      "music/10_little_indiansvln.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
            mid3 = updateValue(mid3)
            mid3.save(os.path.join("music/violinPop.mid"))
        else:
            generatedForViolin2 = [0]
            tmpChan, tmpProgram = getChannelAndProgam("music/10_little_indiansvln.mid")
            mid3 = array_to_midiWithProgramAndChannel(unfold(decode(generatedForViolin2), OUT_PITCHES),
                                                      "music/10_little_indiansvln.mid",
                                                      channelInput=tmpChan, programInput=tmpProgram)
            mid3 = updateValue(mid3)
            mid3.save(os.path.join("music/violinPop.mid"))
        merger(["pianoPop","guitarePop","violinPop",],"Pop.mid")
        return  mid
    elif (musicType == 2):
        mid = array_to_midiWithProgramAndChannel(unfold(decode(generated), OUT_PITCHES), mid_name,
                                                     channelInput=channelInput, programInput=programInput)
        mid = updateValue(mid)
        mid.save(os.path.join("music/saxoJazz.mid"))
        merger(["saxoJazz", ], "Jazz.mid")
    elif(musicType == 3):
        mid = array_to_midiWithProgramAndChannel(unfold(decode(generated), OUT_PITCHES), mid_name,
                                                 channelInput=channelInput, programInput=programInput)
        mid = updateValue(mid)
        mid.save(os.path.join("music/classical.mid"))
        return mid

def moyenneNotePlayedByBigBar(generatedarray):
    num = 16
    nb = 1
    getpercussionnote = generatedarray[0:num]
    getnbfullbar = int(len(generatedarray) / num)
    nbOfActivatedNotes = findNumberOfActivatedNotes(getpercussionnote)
    while (nb < getnbfullbar):
        nb += 1
        getpercussionnote = generatedarray[num * nb:num * nb + num]
        nbOfActivatedNotes += findNumberOfActivatedNotes(getpercussionnote)

    return int(nbOfActivatedNotes/getnbfullbar)

def harMonize(arrayToHarmonize,nbOfMaxActivatedNotes):
    num = 16
    nb = 1
    getpercussionnote = arrayToHarmonize[0:num]
    getnbfullbar = int(len(arrayToHarmonize) / num)
    finalarray = []
    generatenewarray = harmonizerLoop(getpercussionnote,nbOfMaxActivatedNotes)
    finalarray += generatenewarray
    while (nb < getnbfullbar):
        nb += 1
        getpercussionnote = arrayToHarmonize[num * nb:num * nb + num]
        generatenewarray = harmonizerLoop(getpercussionnote, nbOfMaxActivatedNotes)
        finalarray += generatenewarray

    return finalarray


def forpercussion(generatedarray):

    num = 16
    nb = 1
    getpercussionnote = generatedarray[0:num]
    getnbfullbar = int(len(generatedarray)/num)
    finalarray = []

    generatenewarray,isfounded = loopPercussion(getpercussionnote)
    while(isfounded == 0):
        nb += 1
        getpercussionnote = generatedarray[num*nb:num*nb+num]
        generatenewarray, isfounded = loopPercussion(getpercussionnote)

    for n in range(getnbfullbar):
        finalarray += generatenewarray
    return finalarray


def loopPercussion(arrayGeneratedInLoop):
    generateNewArray = []
    isFounded = 0
    for x in arrayGeneratedInLoop:
        if (x > 0):
            isFounded = 1
        generateNewArray.append(x)
    return generateNewArray,isFounded

def findNumberOfActivatedNotes(arrayGeneratedInLoop):
    nbOfActivatedNotes = 0
    for x in arrayGeneratedInLoop:
        if (x > 0):
            nbOfActivatedNotes += 1
    return nbOfActivatedNotes

def harmonizerLoop(arrayToHarmonize,NbOfMaxActivatedNotes):
    NbOfMaxActivatedNotesToDecrease = NbOfMaxActivatedNotes
    generateNewArray = []
    for x in arrayToHarmonize:
        if (x > 0 and NbOfMaxActivatedNotesToDecrease > 0):
            generateNewArray.append(x)
            NbOfMaxActivatedNotesToDecrease -= 1
        else:
            generateNewArray.append(0)
    return generateNewArray

def harmonicLoopPercussion(arrayMain):
    isFounded = 0
    for x in arrayMain:
        if (x > 0):
            isFounded = 1
    if (isFounded == 0):
        return [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], isFounded
    else:
        return arrayMain, isFounded


def PercussionHarmonizer(arrayOfMain,arrayOfDrum):
    num  = 16
    getnbfullbar = int(len(arrayOfMain) / num)
    finalarray = []
    finalArrayOfDrum = arrayOfDrum
    i = 0
    while (i < getnbfullbar):
        i += 1
        getpercussionnote = arrayOfMain[num * i:num * i + num]
        generatenewarray, isfounded = harmonicLoopPercussion(getpercussionnote)
        if (isfounded == 1):
            finalarray += getpercussionnote
        else:
            finalarray += [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    for index,n in enumerate(arrayOfDrum):
        if (n > 0 and finalarray[index] == 0):
            finalArrayOfDrum[index] = 0

    return  finalArrayOfDrum

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
    mid = updateValue(mid)

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
    for i,element in enumerate(midiFileInput.tracks):
        tmpTrack = MidiTrack()
        midiFileToReturn.tracks.append(tmpTrack)
        for msg in element:
            msg.time = int(msg.time)
            print("track" + str(msg.time))
            tmpTrack.append(msg)
    return midiFileToReturn





def generateFromLoaded(hdf5Name,songRelatedToTheHdf5,temperature=1):
    # Initialize the model.
    modifyPITCHES(songRelatedToTheHdf5)
    model = init_model()
    print
    model.summary()
    model.load_weights(hdf5Name)
    channelToInput, programToInput = getChannelAndProgam(songRelatedToTheHdf5)
    config_sequences, train_generator, valid_generator = prepare_data()

    sequence_indices = idx_seq_of_length(config_sequences, PHRASE_LEN)
    seq_index, phrase_start_index = sequence_indices[
        np.random.choice(len(sequence_indices))]
    gen_length = 512
    phrase = list(
        config_sequences[seq_index][
        phrase_start_index: phrase_start_index + PHRASE_LEN])


    print('----- Generating with temperature:', temperature)

    generateWithCAndP(model,
                      phrase,
                      'DimMarvin_Gaye1Out_{}_{}.mid'.format(gen_length, temperature),
                      temperature=temperature,
                      length=gen_length, channelInput=channelToInput, programInput=programToInput)
    return model

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
            ('Best validation loss so far. Saving...'+str(i))
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
                     'Samedi1Out_{}_{}_{}.mid'.format(gen_length, temperature, i),
                     temperature=temperature,
                     length=gen_length)
    return model


def trainWithChannelAndProgram(config_sequences, train_generator, valid_generator, channelInput=14, programInput=117):
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
        print
        ('Best validation loss so far. Saving...'+str(i))
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
            phrase = list(
                config_sequences[seq_index][
                phrase_start_index: phrase_start_index + PHRASE_LEN])

            print('----- Generating with temperature:', temperature)
    return model

def run_trainWithSongName():
    train_song_name_array = ["music/10_little_indians.mid","music/10_little_indiansvln.mid","music/london_bridge.mid"]
    for n in train_song_name_array:
        songName = n
        songNameSplited = songName.split('.')
        global MODEL_NAME
        MODEL_NAME = "hdfFiveFiles/"+songNameSplited[0] + ".hdf5"
        modifyPITCHES(songName)
        channelToInput,programToInput = getChannelAndProgam(songName)
        config_sequences, train_generator, valid_generator = prepare_dataForASpecificFileAndRandomly(songName)
        trainWithChannelAndProgram(config_sequences, train_generator, valid_generator, channelInput=channelToInput, programInput=programToInput)


def run_train():
    config_sequences, train_generator, valid_generator = prepare_data()
    train(config_sequences, train_generator, valid_generator)

def readInforMationFromAMidi(midiFileName):
    MidoFile = MidiFile(midiFileName)
    for i,track in enumerate(MidoFile.tracks):
        for msg in track:
            print(" i : " + str(i) + "the msg is " + str(msg))

def run_generate():
    print
    'Loading model...'
    model = init_model()
    model.load_weights("hdfFiveFiles/2016-07-08.hdf5")
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



def songDiviser(songName):
    MidoFile = MidiFile(songName)
    MetaTrack = MidiTrack()

    for i,track in enumerate(MidoFile.tracks):
        if i < 1:
            for msg in track:
                MetaTrack.append(msg)


    for i,track in enumerate(MidoFile.tracks):
        if i > 0:
            fileName = ""
            songNameSplited = songName.split('.')
            print(str(songNameSplited[0]))
            mid = MidiFile()
            noteTrack = MidiTrack()
            mid.tracks.append(noteTrack)
            for metaMsg in MetaTrack:
                noteTrack.append(metaMsg)
            #mid.add_track(noteTrack)
            fileName = fileName+str(i)
            for msg in track:
                 noteTrack.append(msg)
                 if str(msg.type) == "track_name":
                    fileName = msg.name

            mid.save(songNameSplited[0]+fileName+".mid")

def getAllNotesFromTrackWithoutOccur(songName):
    notesArray = []
    print("music " + songName)
    if(songName[0:len('music/')] == 'music/'):
        MidoFile = MidiFile(songName)
    else :
        MidoFile = MidiFile('music/'+songName)
    for track in MidoFile.tracks:
        for msg in track:
            if msg.type == "note_on":
                notesArray.append(msg.note)
    return list(set(notesArray))

def getAllNotesFromTrackWithOccur(songName):
    notesArray = []
    if(songName[0:len('music/')] == 'music/'):
        MidoFile = MidiFile(songName)
    else :
        MidoFile = MidiFile('music/'+songName)
    for track in MidoFile.tracks:
        for msg in track:
            if msg.type == "note_on" or msg.type == "note_off":
                notesArray.append(msg.note)
    return notesArray


def most_common(lst):
    return max(set(lst), key=lst.count)

def getTheMostUsedNElement(n,songName):
    notesArray = getAllNotesFromTrackWithOccur(songName)
    mostRepresentedNNotes = []
    for i in range(n):
        mostCommon = most_common(notesArray)

        mostRepresentedNNotes.append(mostCommon)
        notesArray = [x for x in notesArray if x != mostCommon]

    return mostRepresentedNNotes

def getAllPitchesFromTrack(songName):
    pitchesAttay = []
    MidoFile = MidiFile(songName)
    for track in MidoFile.tracks:
        for msg in track:
            if msg.type == "pitchwheel":
                pitchesAttay.append(msg.pitch)


def getChannelAndProgam(songName):
    if(songName[0:len('music/')] == 'music/'):
        MidoFile = MidiFile(songName)
    else :
        MidoFile = MidiFile('music/'+songName)
    if(songName == "bob_catTenor_Saxophone.mid"):
        return 8,67
    for track in MidoFile.tracks:
        for msg in track:
            if msg.type == "program_change":
                return msg.channel,msg.program

def generateFromLoaded2HipHop(hdf5Name,songRelatedToTheHdf5,type,temperature=1,getArray=False,piano=0,percussion=0,basse=0,guitare=0,violon=0,saxophone=0,musicType=0):
    # Initialize the model.
    modifyPITCHES(songRelatedToTheHdf5)
    model = init_model()
    print
    model.summary()
    model.load_weights(hdf5Name)
    channelToInput, programToInput = getChannelAndProgam(songRelatedToTheHdf5)
    config_sequences, train_generator, valid_generator = prepare_dataForASpecificFileAndRandomly(songRelatedToTheHdf5)
    sequence_indices = idx_seq_of_length(config_sequences, PHRASE_LEN)
    seq_index, phrase_start_index = sequence_indices[
        np.random.choice(len(sequence_indices))]

    print("seq_index is " + str(seq_index) + " phrase_start_index is " + str(phrase_start_index))
    gen_length = 1024
    phrase = list(
        config_sequences[seq_index][
        phrase_start_index: phrase_start_index + PHRASE_LEN])


    print('----- Generating with temperature:', temperature)

    arrayGenerated = generateWithCAndPHipHop(model,
                      phrase,
                      'DimMarvin_Gaye1Out_{}_{}_{}.mid'.format(gen_length, temperature,type),
                      temperature=temperature,
                      length=gen_length, channelInput=channelToInput, programInput=programToInput,piano=piano,getArray=getArray,percussion=percussion,basse=basse,guitare=guitare,violon=violon,saxophone=saxophone,musicType=musicType)
    if(getArray == True):
        return arrayGenerated
    else:
        return model



run_trainWithSongName()