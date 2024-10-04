import logging
import ctypes
from dataclasses import dataclass

from pymhf.core.hooking import disable, on_key_pressed, on_key_release
from pymhf.core.memutils import map_struct
from pymhf.core.mod_loader import ModState
from nmspy import NMSMod
from pymhf.core.calling import call_function
import pymhf.core.hooking
from pymhf import FUNCDEF
from nmspy.data.common import cTkFixedString

@dataclass
class WMState(ModState):
    test = ""

@disable
class WeekendMissionRE(NMSMod):
    __author__ = "ThatBomberBoi"
    __description__ = "Weekend Mission Reverse Engineering"
    __version__ = "0.1"
    __NMSPY_required_version__ = "0.7.0"    

    state = WMState()

    def __init__(self):
        super().__init__()
        self.should_print = False

    # Hook used to find the ScanEvent for a weekend mission. The returned scan event contains the Universal Address.
    # TODO: Figure out how the input for this function changes each week and predict the UA for future weekend missions before they occur. 
    findWeekendSEFuncDef = FUNCDEF(restype=ctypes.c_ulonglong, argtypes=[ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_bool, ctypes.c_bool])
    @pymhf.core.hooking.manual_hook("cGcScanEventManager::FindWeekendInterstellarEvent", pattern= "40 55 56 41 54 41 55 41 57 48 8D AC 24 20", func_def= findWeekendSEFuncDef, detour_time="after")
    def onWeekendSEFound(self, result, event, safeOnly, allowSystemsWithExpeditionsOrOtherPlayers, _result_):
        logging.info(f"Found Weekend Scan Event! UA: {hex(map_struct(_result_ + 8, ctypes.c_ulonglong).value)}")

    # Calls the hook above. Can be used to find the mission ID and seed for the weekend mission to help figure out how it changes each weekend.
    getMissionUAFuncDef = FUNCDEF(restype=ctypes.c_ulonglong, argtypes=[ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_char])
    @pymhf.core.hooking.manual_hook("cGcMPMissionSelectionHelper::GetMissionTargetUA", pattern= "48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 18 55 41 56 41 57 48 8D 6C 24 C9 48 81 EC B0", func_def= getMissionUAFuncDef, detour_time="after")    
    def onMissionUAAcquired(self, this, result, missionId, missionSeed, targetSeed, isWeekend):
        logging.info(f"Got Target UA For Mission {map_struct(missionId, ctypes.c_char * 0x128).value} with mission seed {map_struct(missionSeed, ctypes.c_ulonglong).value}")    

    # Causes crashes, might be a bad FUNCDEF...
    #getWeekendMissionListFuncDef = FUNCDEF(restype=None, argtypes=[ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong])
    #@pymhf.core.hooking.manual_hook("cGcFrontendPageMultiplayerMissionGiver::GetMultiplayerWeekendMissionsList", pattern="48 89 4C 24 08 55 57 41 55 48 8D 6C", func_def= getWeekendMissionListFuncDef, detour_time="after")    
    #def onWeekendMissionListAcquired(self, outputMissions, a2, a3):
    #    logging.info(f"Found Mission: {map_struct(outputMissions + 0x380, ctypes.c_char * 0x10).value}")    