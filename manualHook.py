import logging
import ctypes
from dataclasses import dataclass

import nmspy.data.functions.hooks as hooks
from pymhf.core.hooking import disable, on_key_pressed, on_key_release
from pymhf.core.memutils import map_struct
import nmspy.data.structs as nms_structs
from pymhf.core.mod_loader import ModState
from nmspy import NMSMod
from nmspy.decorators import main_loop
from pymhf.core.calling import call_function
from pymhf.gui.decorators import gui_variable, gui_button, STRING
import pymhf.core.hooking
from pymhf import FUNCDEF
from nmspy.data.common import cTkFixedString

# Random Test Functions
@dataclass
class hookState(ModState):
    test = ""

@disable
class manualHook(NMSMod):
    __author__ = "ThatBomberBoi"
    __description__ = "Personal Tests"
    __version__ = "0.1"
    __NMSPY_required_version__ = "0.7.0"    

    state = hookState()

    def __init__(self):
        super().__init__()
        self.should_print = False

    # Disables the modded warning shown when using .pak mods.
    # TODO: Find another function to access the cTkFileSystem pointer, this one doesn't seem to hook properly. The offset for the checking bool seems fine though
    fileSystemConstructFuncDef = FUNCDEF(restype=ctypes.c_ulonglong, argtypes=[ctypes.c_ulonglong, ctypes.c_int])
    @pymhf.core.hooking.manual_hook("cTkFileSystem::Construct", pattern="48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 18 55 41 54 41 55 41 56 41 57 48 8B EC 48 83 EC 60 48", func_def=fileSystemConstructFuncDef, detour_time="after")
    def onFileSystemConstructed(self, this, flags):
        logging.info(f"cTkFileSystem Constructed at {this} with flags {flags}")
        isModded = map_struct(this + 0x467A, ctypes.c_bool)
        isModded.value = False 
    
    # Hooks to the function generating bottle messages. Useful in conjuction with the randomWord function hook to see what generated words map to a language word ID. 
    bottlegenerateFuncDef = FUNCDEF(restype=ctypes.c_char_p, argtypes=[ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong])
    @pymhf.core.hooking.manual_hook("cGcNameGenerator::GenerateMessageInABottleText", pattern="48 8B C4 48 89 50 10 48 89 48 08 55 53 56 57 41 54 41 56 48 8D A8 A8", func_def=bottlegenerateFuncDef, detour_time="after")
    def onBottleMsgGenerated(self, this, fixedString, seed, _result_):
        string = str(map_struct(fixedString, cTkFixedString[0x512]).value)
        usedSeed = map_struct(seed, ctypes.c_ulonglong).value
        returnedItem = str(_result_)
        logging.info(f"Bottle Generated With Seed {usedSeed} and string {string} returned: {returnedItem}")

    # Hooks to a function used to generate a randomized alien word based on a seed. When used for single-word bottle messages, it uses the seed of the bottle. Returns the Word ID.
    randomWordFuncDef = FUNCDEF(restype=ctypes.c_ulonglong, argtypes=[ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_int])
    @pymhf.core.hooking.manual_hook("cGcPlayerState::GetRandomWord", pattern="48 89 5C 24 10 48 89 6C 24 18 48 89 4C 24 08 56 57 41 56 48 81", func_def=randomWordFuncDef, detour_time="after")
    def onRandomWordAcquired(self, this, seed, raceInt, _result_):
        race = ""
        usedSeed = map_struct(seed, ctypes.c_ulonglong).value
        match(raceInt):
            case 0:
                race = "Traders"
            case 1:
                race = "Warriors"
            case 2:
                race = "Explorers"
            case 3:
                race = "Robots"
            case 4:
                race = "Atlas"
            case 5:
                race = "Diplomats"
            case 6: 
                race = "Exotics" 
            case 7:
                race = "None"
            case 8:
                race = "Builders"
        resultingWord = map_struct(_result_, ctypes.c_char * 0x800).value
        logging.info(f"Requested Random Word From The {race} language with seed {usedSeed}: {resultingWord}")                                                        






    