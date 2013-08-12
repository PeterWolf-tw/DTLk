#!/usr/bin/env python
# -*- coding:utf-8 -*-
# FileName: DTLK.py
# Developer: Peter. w (peterwolf.wang@gmail.com), Oliver
# Modification log dates: 2012.07.20, 2013.03.10, 2013.04.28, 2013.06.14, 2013.08.05
# Last modification date: 2013.08.12
############################################################## LICENSE ##############################################################
# Copyright (C) <2012> <Droidtown Ling. Tech. Co., Ltd>
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#####################################################################################################################################

import pygame
import wx
import wx.lib.agw.peakmeter as PM
import pyaudio
import numpy
import math
import wave
import os
import sys
import random
import platform
import unicodedata
import time
from odf.opendocument import load as odf_load
from odf.table import TableRow,TableCell
from odf.text import P
import openpyxl
import xlrd

class TestSheet:
    """ TestSheet provides functions that read testSheets in formats such as ODT, XLS, XLSX, and CSV and make the entries listed in the files two types of dictionary.
        TestSheet.dictionaryDICT is one-key-to-one-value. (eg., {"key1":"value1"}
        TestSheet.randomizedDictionaryDICT is N-keys-to-one-value where N equals to repetitionINT (e.g., {"key1":"value1", "key2":"value1"..."keyN":"value1"})
    """
    def __init__(self):
        self.entryDICT = {0 : u"Get Ready!"}
        self.entryMaxNumberINT = 0
        self.randomCheckBOOL = True
        self.randomizedEntryLIST = []
        self.randomizedEntryDICT = {0 : u"Get Ready!"}
        self.errorMessageSTR = ""
        self.errorMessageSizeTUPLE = (0, 0)
        self.repetitionINT = 3
        #oliver
        self.mode="Default"

    def randomizer(self, repetitionINT=None):
        if repetitionINT == None:
            repetitionINT = self.repetitionINT
        else:
            pass

        for i in range(0, repetitionINT):
            for j in range(1, len(self.entryDICT)):
                self.randomizedEntryLIST.append(self.entryDICT[j])
        random.shuffle(self.randomizedEntryLIST)
        for i in range(0, len(self.randomizedEntryLIST)):
            self.randomizedEntryDICT[i+1] = self.randomizedEntryLIST[i]

    def dictMaker(self, entryLIST):
        random.shuffle(entryLIST)
        #Oliver
        if self.mode == "Default_Random" or self.mode == "Marathon_Random":
            entryLIST=entryLIST*self.repetitionINT
        for i in entryLIST:
            self.entryDICT[entryLIST.index(i)+1] = i[1]
            entryLIST[entryLIST.index(i)]=""
        # Peter: 減去 0:u"Get Ready!" 項
        self.entryMaxNumberINT = len(self.entryDICT)-1
    #[Oliver]
    def dictMaker_LastWork(self, entryLIST):
        #random.shuffle(entryLIST)
        for i in entryLIST:
            self.entryDICT[entryLIST.index(i)] = i[1]#Because LastWork already has "Get Ready"
        # Peter: 減去 0:u"Get Ready!" 項
        self.entryMaxNumberINT = len(self.entryDICT)-1
    def numberVarifier(self, entryLIST):
        for i in entryLIST:
            try:
                int(i[0])
            except ValueError:
                return ValueError
        return True

    def tokenVarifier(self, entryLIST):
        converter = Converter('./DTLK_Resources/BP_Table.csv')
        for i in entryLIST:
            if len(i[1]) <= 9:
                charType = []
                for j in i[1]:
                    if j == u" ":
                        pass
                    elif j == u"一":
                        if len(i[1]) == 1:
                            charType.append("BOPOMOFO")
                        else:
                            try:
                                counter = 0
                                tmpSTR = i[1]
                                while u"一" in tmpSTR:
                                    counter = counter + 1
                                    tmpSTR = tmpSTR[tmpSTR.index(j) + 1:]
                                if counter == 1:
                                    indexJ = i[1].index(j)
                                    if "BOPOMOFO" in unicodedata.name(i[1][indexJ+1]) or "BOPOMOFO" in unicodedata.name(i[1][indexJ-1]):
                                        charType.append("BOPOMOFO")
                                    elif i[1][indexJ+1] == u" " or i[1][indexJ-1] == u" ":
                                        charType.append("BOPOMOFO")
                                    else:
                                        charType.append("CJK")
                                else:
                                    for x in (u"ˊ", u"ˇ", u"ˋ", u"˙", u" "):
                                        if x in i[1]:
                                            charType.append("BOPOMOFO")
                                            break
                                    else:
                                        charType.append("CJK")
                            except IndexError:
                                charType.append("BOPOMOFO")
                    elif "CJK" in unicodedata.name(j):
                        charType.append("CJK")
                    elif "BOPOMOFO" in unicodedata.name(j) or j in (u"ˊ", u"ˇ", u"ˋ", u"˙"):
                        charType.append("BOPOMOFO")
                    elif "HANGUL" in unicodedata.name(j):
                        charType.append("KOREAN")
                    elif "HIRAGANA" in unicodedata.name(j) or "KATAKANA" in unicodedata.name(j):
                        charType.append("JAPANESE")
                    else: #Other language alphabets/symbols
                        charType.append("ALPHABET")
                if len(set(charType)) == 1:
                    if set(charType) == set(["CJK"]):
                        for x in i[1]:
                            if converter.lookup(x) != None:
                                pass
                            elif x == u" ":
                                #test 1
                                self.errorMessageSTR = "Redundant space found in token '" + i[1] + "' in #"+ str(int(i[0])) +". \nPlease remove the space(s) in the token before starting Clip Recorder."
                                self.errorMessageSizeTUPLE = (350, 120)
                                raise ValueError
                            else:
                                #test 2
                                self.errorMessageSTR = "A word in Token '" + i[1] + "' in #"+ str(int(i[0])) + " cannot be found in the convertion table. \nPlease make sure the word(s) in the token is listed in the convertion table before starting Clip Recorder."
                                self.errorMessageSizeTUPLE = (370, 150)
                                raise ValueError
                    elif set(charType) == set(["BOPOMOFO"]):
                        for m in i[1].split(u" "):
                            if converter.lookup(m) != None:
                                pass
                            else:
                                #test 3
                                self.errorMessageSTR = "Token '" + i[1] + "' in #"+ str(int(i[0])) + " cannot be found in the convertion table. \nPlease make sure the token is listed in the convertion table before starting Clip Recorder."
                                self.errorMessageSizeTUPLE = (300, 150)
                                raise ValueError
                    else: #Korean Japanese and other languages.
                        pass
                else: # len(set(charType)) > 1:
                    if  set(charType) == set(["CJK", "BOPOMOFO"]) and u" " in i[1]:
                        for k in i[1].split(u" "):
                            if converter.lookup(k) != None:
                                pass
                            else:
                                #test 4
                                self.errorMessageSTR = "Word '" + k + "' in token '" + i[1] + "' in #" + str(int(i[0])) + " cannot be found in the convertion table. \nPlease make sure the word is listed in the convertion table before starting Clip Recorder."
                                self.errorMessageSizeTUPLE = (370, 150)
                                raise ValueError
                    else:
                        #test 5
                        self.errorMessageSTR = "Format error found in token " + i[1] + " in #" + str(int(i[0])) + ". \nPlease refer to manual for proper token format and correct the token before starting Clip Recorder."
                        self.errorMessageSizeTUPLE = (370, 150)
                        raise ValueError
            else:
                #test 6
                self.errorMessageSTR = "The token " + i[1] + " in #" + str(int(i[0])) + " is too long. \nPlease redesign the token OR use Reply Recorder instead of Clip Recorder."
                self.errorMessageSizeTUPLE = (370, 150)
                raise ValueError
        return True

    def csvTestSheetReader(self, fileName):
        f = open(fileName, 'r')

        tmpEntryLIST = []
        for i in f.readlines():
            if '''"''' in i:
                i = i.replace('''"''', "", 2)
            else:
                pass
            tmpEntryLIST.append((i.split(",")[0], i.split(",")[1].decode("utf-8")[:-1]))

        if self.numberVarifier(tmpEntryLIST) == True and self.tokenVarifier(tmpEntryLIST) == True:
            self.dictMaker(tmpEntryLIST)
            #self.randomizer()
        else:
            raise ValueError
    #[Oliver]
    def csvTestSheetReader_LastWork(self, fileName):
        f = open(fileName, 'r')

        tmpEntryLIST = []
        whereStarINT=0
        CountINT=0
        for i in f.read().split("\n"):
            i=i.strip()
            if len(i)==0:continue
            if '''"''' in i:
                i = i.replace('''"''', "", 2)
            else:
                pass
            tmpEntryLIST.append((i.split(",")[0], i.split(",")[1].decode("utf-8")))
            CountINT+=1
            if ",*" in i:whereStarINT=CountINT
        if self.numberVarifier(tmpEntryLIST) == True and self.tokenVarifier(tmpEntryLIST[1:]) == True:
            self.dictMaker_LastWork(tmpEntryLIST)
        else:
            raise ValueError
        #Oliver
        if whereStarINT>=len(tmpEntryLIST):
            MsgBox(None, -1, title = u"Oops!", msg = u"This round is done.", size = (300, 100))
            exit(0)
        return whereStarINT

    def xlsxTestSheetReader(self, fileName):
        f = openpyxl.load_workbook(filename = fileName)
        sheetRanges = f.get_sheet_by_name(name = f.get_sheet_names()[0])

        tmpEntryLIST = []
        for i in sheetRanges.range(sheetRanges.calculate_dimension()):
            tmpEntryLIST.append((i[0].value, i[1].value))

        if self.numberVarifier(tmpEntryLIST) == True and self.tokenVarifier(tmpEntryLIST) == True:
            self.dictMaker(tmpEntryLIST)
            #self.randomizer()
        else:
            raise ValueError

    def xlsTestSheetReader(self, fileName):
        f = xlrd.open_workbook(fileName)
        sheet = f.sheet_by_name(f.sheet_names()[0])

        tmpEntryLIST = []
        for i in range(0, sheet.nrows):
            tmpEntryLIST.append((sheet.row_values(i)[0], sheet.row_values(i)[1]))

        if self.numberVarifier(tmpEntryLIST) == True and self.tokenVarifier(tmpEntryLIST) == True:
            self.dictMaker(tmpEntryLIST)
            #self.randomizer()
        else:
            raise ValueError

    def odsTestSheetReader(self, fileName):
        f = odf_load(fileName)
        sheet = f.spreadsheet
        rows = sheet.getElementsByType(TableRow)

        tmpEntryLIST = []
        for row in rows:
            cells = row.getElementsByType(TableCell)
            tmp = []
            for cell in cells:
                contentTree = cell.getElementsByType(P)
                for content in contentTree:
                    while u"\n" in unicode(content.firstChild):
                        content.firstChild = unicode(content.firstChild).replace(u"\n", u"")
                    tmp.append(unicode(content.firstChild).lstrip())
                    if len(tmp) == 2:
                        tmpEntryLIST.append(tuple(tmp))
                    else:
                        pass
        if self.numberVarifier(tmpEntryLIST) == True and self.tokenVarifier(tmpEntryLIST) == True:
            self.dictMaker(tmpEntryLIST)
            #self.randomizer()
        else:
            raise ValueError

    def entryGetter(self, number, mode="nromal"):
        if mode == "normal":
            return (number, self.entryDICT[number])
        else:
            return (number, self.randomizedEntryDICT[number])


class ItemControl:
    def __init__(self):
        self.currentNumINT = 0
        self.status = "ready"
        #self.span = 1 #(sec.)

    def plusKey(self):
        if self.status == "idle":
            self.currentNumINT = self.currentNumINT+1
            return self.currentNumINT
        else:
            pass

    def minusKey(self):
        if self.status == "idle":
            self.currentNumINT = self.currentNumINT-1
            return self.currentNumINT
        else:
            pass


class Buttons:
    def __init__(self):
        self.plusImg = "./DTLK_Resources/imgs/rubberPlusButton.png"
        self.plusPressedImg = "./DTLK_Resources/imgs/rubberPlusButton_pressed.png"
        self.minusImg = "./DTLK_Resources/imgs/rubberMinusButton.png"
        self.minusPressedImg = "./DTLK_Resources/imgs/rubberMinusButton_pressed.png"
        self.meters = "./DTLK_Resources/imgs/meters.png"
        self.redDarkImg = "./DTLK_Resources/imgs/redDark.png"
        self.redLightImg = "./DTLK_Resources/imgs/redLight.png"
        self.yellowDarkImg = "./DTLK_Resources/imgs/yellowDark.png"
        self.yellowLightImg = "./DTLK_Resources/imgs/yellowLight.png"
        self.greenDarkImg = "./DTLK_Resources/imgs/greenDark.png"
        self.greenLightImg = "./DTLK_Resources/imgs/greenLight.png"
        self.recImg = "./DTLK_Resources/imgs/rec_orb.png"
        self.recBusy = "./DTLK_Resources/imgs/rec_orb_busy.png"
        self.recPressedImg = "./DTLK_Resources/imgs/rec_orb_pressed.png"
        self.recGetReady = "./DTLK_Resources/imgs/rec_orb_getReady_ready.png"
        self.recGetReadyPressed = "./DTLK_Resources/imgs/rec_orb_getReady_pressed.png"
        self.recPause = "./DTLK_Resources/imgs/rec_orb_pause_ready.png"
        self.recPausePressed = "./DTLK_Resources/imgs/rec_orb_pause_pressed.png"
        self.recEnd = "./DTLK_Resources/imgs/rec_orb_end.png"
        self.recEndPressed = "./DTLK_Resources/imgs/rec_orb_end_pressed.png"
        self.lightStatus = {"red" : "off", "yellow" : "off", "green" : "off"}

    def redLight(self, status = "off"):
        if status == "off":
            self.lightStatus["red"] = "off"
            red = self.redDarkImg
        else:
            self.lightStatus["red"] = "on"
            red = self.redLightImg

        redLight = pygame.transform.smoothscale(pygame.image.load(red).convert_alpha(), (200, 86))
        return redLight

    def yellowLight(self, status = "off"):
        if status == "off":
            self.lightStatus["yellow"] = "off"
            yellow = self.yellowDarkImg
        else:
            self.lightStatus["yellow"] = "on"
            yellow = self.yellowLightImg
        yellowLight = pygame.transform.smoothscale(pygame.image.load(yellow).convert_alpha(), (200, 86))
        return yellowLight

    def greenLight(self, status = "off"):
        if status == "off":
            self.lightStatus["green"] = "off"
            green = self.greenDarkImg
        else:
            self.lightStatus["green"] = "on"
            green = self.greenLightImg
        greenLight = pygame.transform.smoothscale(pygame.image.load(green).convert_alpha(), (200, 86))
        return greenLight

    def plusButton(self, status = "ready"):
        if status == "ready":
            plus = self.plusImg
        else:
            plus = self.plusPressedImg
        plusButton = pygame.transform.smoothscale(pygame.image.load(plus).convert_alpha(), (80, 80))
        return plusButton

    def minusButton(self, status="ready"):
        if status == "ready":
            minus = self.minusImg
        else:
            minus = self.minusPressedImg
        minusButton = pygame.transform.smoothscale(pygame.image.load(minus).convert_alpha(), (80, 80))
        return minusButton

    def targetMeters(self):
        meters = self.meters
        targetMeters = pygame.transform.smoothscale(pygame.image.load(meters).convert_alpha(), (400, 200))
        return targetMeters

    def recButton(self, status="ready"):
        if status == "ready":
            rec = self.recImg
        elif status == "pressed":
            rec = self.recPressedImg
        #elif status == "busy":
        #    rec = self.recBusy
        elif status == "getReady":
            rec = self.recGetReady
        elif status == "getReadyPressed":
            rec = self.recGetReadyPressed
        elif status == "pause":
            rec = self.recPause
        elif status == "pausePressed":
            rec = self.recPausePressed
        elif status == "end":
            rec = self.recEnd
        elif status == "endPressed":
            rec = self.recEndPressed
        else: #status == "busy":
            rec = self.recBusy
        recButton = pygame.transform.smoothscale(pygame.image.load(rec).convert_alpha(), (200, 200))
        return recButton


class AppSelection:
    def __init__(self):
        self.clipRecorder = {"pointed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_ClipRecorder_pointed.png").convert_alpha(),
                             "pressed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_ClipRecorder_pressed.png").convert_alpha()}

        self.lipTracker = {"pointed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_LipTracker_pointed.png").convert_alpha(),
                           "pressed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_LipTracker_pressed.png").convert_alpha()}

        self.perception = {"pointed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_Perception_pointed.png").convert_alpha(),
                           "pressed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_Perception_pressed.png").convert_alpha()}

        self.replyRecorder = {"pointed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_ReplyRecorder_pointed.png").convert_alpha(),
                              "pressed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_ReplyRecorder_pressed.png").convert_alpha()}

        self.symbolTypewriter = {"pointed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_SymbolTypewriter_pointed.png").convert_alpha(),
                                 "pressed"   : pygame.image.load("./DTLK_Resources/imgs/MainWindow_SymbolTypewriter_pressed.png").convert_alpha()}

        self.app = {"clipRecorder"     : self.clipRecorder,
                    "lipTracker"       : self.lipTracker,
                    "perception"       : self.perception,
                    "replyRecorder"    : self.replyRecorder,
                    "symbolTypewriter" : self.symbolTypewriter}

        self.topBackground = pygame.image.load("./DTLK_Resources/imgs/MainWindowTOP.png").convert()
        self.bottomBackground = pygame.image.load("./DTLK_Resources/imgs/MainWindowDOWN.png").convert_alpha()
        self.emptyBackground = pygame.image.load("./DTLK_Resources/imgs/background.png").convert()

    def mouseOverApp(self, mouseOverApp):
        return self.app[mouseOverApp]["pointed"]

    def mouseClickApp(self, mouseClickApp):
        return self.app[mouseClickApp]["pressed"]

    def mouseUnpressed(self, mode):
        if mode == "TOP":
            return self.topBackground
        else:
            return self.bottomBackground


class Converter:
    def __init__(self, tableFile):
        self.guozi = {}
        self.zhuyin = {}
        if os.path.exists(tableFile):
            f = open(tableFile, "r")
            wordList = []
            for i in f.readlines():
                tmp = []
                for j in i.split(","):
                    tmp.append(j.decode("utf-8"))
                wordList.append(tmp)
            for i in wordList:
                if i[-1][-2:] == u"*\n":
                    self.zhuyin[i[0]+i[1]] = i[2] + i[3]
                else:
                    self.zhuyin[i[0]+i[1]] = i[2] + i[3]
                    self.guozi[i[-1][:-1]] = i[2] + i[3]
        else:
            raise IOERROR

    def lookup(self, inputEntry):
        result = ""
        if u" " in inputEntry:
            print "space found in ", inputEntry
            for i in inputEntry.split(u" "):
                if i in (u"一", u"一ˊ", u"一ˇ", u"一ˋ", u"一˙"):
                    try:
                        result = result + self.zhuyin[i]
                    except KeyError:
                        return None
                elif "BOPOMOFO" in unicodedata.name(i[0]):
                    try:
                        result = result + self.zhuyin[i]
                    except KeyError:
                        return None
                else:
                    try:
                        result = result + self.guozi[i]
                    except KeyError:
                        try:
                            result = result + self.zhuyin[i]
                        except KeyError:
                            return None
        else:
            #print "space not found in", inputEntry
            for i in (u"一", u"一ˊ", u"一ˇ", u"一ˋ", u"一˙"):
                if inputEntry == i:
                    result = self.zhuyin[i]
                    return result
                else:
                    pass
            if "BOPOMOFO" in unicodedata.name(inputEntry[0]) or "BOPOMOFO" in unicodedata.name(inputEntry[-1]):
                try:
                    result = result + self.zhuyin[inputEntry]
                except KeyError:
                    return None
            else:
                for i in range(0, len(inputEntry)):
                    try:
                        result = result + self.guozi[inputEntry[i]]
                    except KeyError:
                        try:
                            result = result + self.zhuyin[inputEntry[i]]
                        except KeyError:
                            try:
                                result = self.zhuyin[inputEntry]
                                return result
                            except KeyError:
                                return None
        return result


class Recorder:
    def __init__(self, directory, channelNumber=1):
        self.SaveAsDir = directory
        self.track = pyaudio.PyAudio()
        self.stream = self.track.open(format = pyaudio.paInt16,
                                      channels = channelNumber,
                                      rate = 44100,
                                      input = True,
                                      frames_per_buffer = 900,
                                     )
        self.bufferSpace = []

    def rec(self, duration):
        if duration == None:
            duration = 1
        #print "start recording"
        for i in range(0, int(44100/900*duration)):
            try:
                rawData = self.stream.read(900)
                self.bufferSpace.append(rawData)
            except IOError as ex:
                if ex[1] != pyaudio.paInputOverflowed:
                    raise
                data = '\x00'*900
        #print "stop recording"
        self.stream.close()
        self.track.terminate()

    def wavWriter(self, fileName):
        # write data to WAVE file
        WAVE_OUTPUT_FILENAME = self.SaveAsDir + fileName
        if os.path.exists(WAVE_OUTPUT_FILENAME):
            os.remove(WAVE_OUTPUT_FILENAME)
        else:
            pass

        #print "starting wavWriter"

        data = ''.join(self.bufferSpace)

        wv = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wv.setnchannels(1)
        wv.setsampwidth(self.track.get_sample_size(pyaudio.paInt16))
        wv.setframerate(44100)
        wv.writeframes(data)
        wv.close()


class MsgBox(wx.Dialog):
    def __init__(self, parent, id, title, msg, size):
        wx.Dialog.__init__(self, parent, id, title, size=size, style=wx.CAPTION|wx.CLOSE_BOX)

        framePanel = wx.Panel(self, -1)
        frameBoxV = wx.BoxSizer(wx.VERTICAL)

        contentPanel = wx.Panel(framePanel, -1)
        contentBoxV1 = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(contentPanel, -1, u"Details..."), orient = wx.VERTICAL)

        msg = wx.StaticText(contentPanel, -1, msg, (20, 15))
        msg.Wrap(size[0]-20)
        sizer.Add(msg, 1, wx.EXPAND|wx.BOTTOM, 5)

        #buttonOK = wx.Button(contentPanel, 1, u"OK")
        buttonOK = wx.Button(framePanel, 1, u"OK")
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=buttonOK.GetId())
        #sizer.Add(buttonOK, 0, wx.ALIGN_CENTER_HORIZONTAL)

        contentBoxV1.Add(sizer, 1, wx.EXPAND)
        contentPanel.SetSizer(contentBoxV1)

        frameBoxV.Add(contentPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        frameBoxV.Add(buttonOK, 0, wx.ALIGN_CENTER_HORIZONTAL)
        framePanel.SetSizer(frameBoxV)

        self.Centre()
        #self.SetClientSize(framePanel.GetBestSize())
        self.SetClientSize(size)
        self.ShowModal()
        self.Destroy()
        self.Show(True)

    def OnClose(self, event):
        self.Close(True)



class SelectionBox(wx.Dialog):
    def __init__(self, parent, id, title, msg, size, selectionList):

        wx.Dialog.__init__(self, parent, id, title, size=size)#, style=wx.CAPTION|wx.CLOSE_BOX)

        framePanel = wx.Panel(self, -1)
        frameBoxV = wx.BoxSizer(wx.VERTICAL)

        contentPanel = wx.Panel(framePanel, -1)
        contentBoxV1 = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(contentPanel, -1, u"Details..."), orient = wx.VERTICAL)
        ###
        msg = wx.StaticText(contentPanel, -1, msg, (10, 10))
        sizer.Add(msg, 1, wx.EXPAND|wx.BOTTOM, 9)
        #print "selectionList", selectionList
        self.selections = {}
        for i in range(0, len(selectionList)):
            self.selections[selectionList[i].split(".")[-1]] = wx.RadioButton(contentPanel, -1, selectionList[i])
            if i == 0:
                self.selections[selectionList[i].split(".")[-1]].SetValue(True)
            else:
                pass
            sizer.Add(self.selections[selectionList[i].split(".")[-1]], 1)

        #buttonOK = wx.Button(contentPanel, 1, u"OK")
        buttonOK = wx.Button(framePanel, 1, u"OK")
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=buttonOK.GetId())

        #sizer.Add(buttonOK, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, 5)
        ###
        contentBoxV1.Add(sizer, 1, wx.EXPAND)
        contentPanel.SetSizer(contentBoxV1)

        frameBoxV.Add(contentPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        frameBoxV.Add(buttonOK, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, 5)
        framePanel.SetSizer(frameBoxV)

        self.Centre()
        self.SetClientSize(framePanel.GetBestSize())
        self.SetClientSize(size)
        self.ShowModal()
        self.Destroy()
        self.Show(True)

    def OnClose(self, event):
        for i in self.selections:
            self.selections[i] = self.selections[i].GetValue()

        self.Close(True)

class YesNoBox(wx.Dialog):
    def __init__(self, parent, id, title, msgTopic, msg, size):
        self.selection = None
        wx.Dialog.__init__(self, parent, id, title, size=size, style=wx.CAPTION|wx.CLOSE_BOX)
        framePanel = wx.Panel(self, -1)
        frameBoxV = wx.BoxSizer(wx.VERTICAL)
        buttonBoxH = wx.BoxSizer(wx.HORIZONTAL)

        contentPanel = wx.Panel(framePanel, -1)
        contentBoxV1 = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(contentPanel, -1, msgTopic), orient = wx.VERTICAL)

        msg = wx.StaticText(contentPanel, -1, msg, (20, 15))
        msg.Wrap(size[0]-20)
        sizer.Add(msg, 1, wx.EXPAND|wx.BOTTOM, 5)

        buttonYES = wx.Button(framePanel, 1, u"Yes")
        self.Bind(wx.EVT_BUTTON, self.OnYes, id=buttonYES.GetId())
        buttonNO = wx.Button(framePanel, 2, u"No")
        self.Bind(wx.EVT_BUTTON, self.OnNo, id=buttonNO.GetId())
        buttonBoxH.Add(buttonYES, 0)
        buttonBoxH.Add(buttonNO, 0)

        contentBoxV1.Add(sizer, 1, wx.EXPAND)
        contentPanel.SetSizer(contentBoxV1)

        frameBoxV.Add(contentPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        frameBoxV.Add(buttonBoxH, 0, wx.ALIGN_CENTER_HORIZONTAL)
        framePanel.SetSizer(frameBoxV)

        self.Centre()
        self.SetClientSize(size)
        self.ShowModal()
        self.Destroy()
        self.Show(True)

    def OnYes(self, event):
        self.selection = True
        self.Close(True)

    def OnNo(self, event):
        self.selection = False
        self.Close(True)


class MICtest(wx.Dialog):
    def __init__(self, parent, id, msg, size, style=wx.CAPTION|wx.CLOSE_BOX):
        wx.Dialog.__init__(self, parent, -1, title="Microphone Test", size=size)
        self.micStatus = None


        framePanel = wx.Panel(self, -1)
        frameBox = wx.BoxSizer(wx.VERTICAL)


        # Layout the two PeakMeterCtrl
        meterPanel = wx.Panel(framePanel, -1)
        meterBox = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.StaticBoxSizer(wx.StaticBox(framePanel, -1, u"Microphone Volume Level (Mono)"), orient = wx.VERTICAL)

        # Initialize Peak Meter control 1
        self.vertPeak = PM.PeakMeterCtrl(meterPanel, -1, style=PM.PM_VERTICAL)
        self.vertPeak.SetMeterBands(2, 25)
        sizer.Add(self.vertPeak, 1, wx.EXPAND|wx.ALL, 15)

        msg = wx.StaticText(meterPanel, -1, msg)
        msg.Wrap(size[0]-30)
        sizer.Add(msg, 1, wx.ALIGN_CENTER_HORIZONTAL)

        buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        buttonY = wx.Button(framePanel, 1, u"Yes!")
        buttonN = wx.Button(framePanel, 2, u"No!")
        self.Bind(wx.EVT_BUTTON, self.OnYes, id=buttonY.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnNo, id=buttonN.GetId())
        buttonBox.Add(buttonY, 1, wx.RIGHT, 3)
        buttonBox.Add(buttonN, 1, wx.LEFT, 3)
        #sizer.Add(buttonBox, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.BOTTOM, 5)

        meterBox.Add(sizer, -1, wx.EXPAND)
        meterPanel.SetSizer(meterBox)

        frameBox.Add(meterPanel, 1, wx.EXPAND)
        frameBox.Add(buttonBox, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.BOTTOM, 5)
        framePanel.SetSizer(frameBox)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        wx.CallLater(500, self.Start)

        self.Centre()
        self.SetClientSize(size)
        self.ShowModal()
        self.Destroy()
        self.Show(True)

    def Start(self):
        ''' Starts the PeakMeterCtrl. '''
        #print "starting timer"
        self.timer.Start(1000/4)            # 4 fps querry rate
        self.vertPeak.Start(1000/40)        # 40 fps refresh rate

    def OnTimer(self, event):
        # Get db for 2 meter bars
        barNumber = 2 #number of bars
        r = Recorder('./TEST_')
        r.rec(0.04)
        try:
            signal = numpy.fromstring("".join(r.bufferSpace), 'Int16')
            signal = signal + sum(signal)/len(signal)

            db = math.log10(sum((signal/32768.0)**2))*15
        except ValueError:
            db = 0

        if db >= 0:
            db = int(db)
        else:
            db = 0

        self.vertPeak.SetData([db, db], 0, barNumber)

    def OnYes(self, event):
        self.micStatus = True
        self.timer.Stop()
        self.vertPeak.Stop()
        #self.Destroy()
        self.Close(True)

    def OnNo(self, event):
        self.micStatus = False
        self.timer.Stop()
        self.vertPeak.Stop()
        #self.Destroy()
        self.Close(True)


class SettingBox(wx.Dialog):
    def __init__(self, parent, id, title=u"Clip Recorder Settings", size=(350, 250)):
        self.status = True
        self.mode = "Default"
        self.duration = 1.0
        self.repetition = 3
        if platform.system() == "Linux":
            font = wx.Font(12, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        else:
            pass
            #font = wx.Font(14, wx.NORMAL, wx.NORMAL, wx.NORMAL)

        wx.Dialog.__init__(self, parent, id, title=title, size=size)
        framePanel = wx.Panel(self, -1)


        ########
        modePanel = wx.Panel(framePanel, -1)
        modeSizer = wx.StaticBoxSizer(wx.StaticBox(modePanel, 1, u"Recording mode selections:"), orient=wx.VERTICAL)
        self.defaultMode = wx.RadioButton(modePanel, -1, "Manual mode: Entry Repeated (Default)", style=wx.RB_GROUP)
        #Oliver 20130531
        self.defaultRandomMode = wx.RadioButton(modePanel, -1, "Manual mode: Entry Randomized")
        self.marathonMode = wx.RadioButton(modePanel, -1, "Marathon mode: Entry Repeated")
        #Oliver 20130711
        self.marathonRandomMode = wx.RadioButton(modePanel, -1, "Marathon mode: Entry Randomized")
        self.defaultMode.SetValue(True) #Set as default value.
        modeSizer.Add(self.defaultMode, -1, wx.EXPAND)
        modeSizer.Add(self.defaultRandomMode, -1, wx.EXPAND)
        modeSizer.Add(self.marathonMode, -1, wx.EXPAND)
        modeSizer.Add(self.marathonRandomMode, -1, wx.EXPAND)

        modePanel.SetSizer(modeSizer)


        ########
        durationPanel = wx.Panel(framePanel, -1)
        durationSizer = wx.StaticBoxSizer(wx.StaticBox(durationPanel, 1, u"Setting clip length and loops:"), orient=wx.VERTICAL)
        ###
        durationText = wx.StaticText(durationPanel, -1, "Duration:   ")
        self.sec = wx.TextCtrl(durationPanel, -1, str(self.duration), size=(40, 20), style=wx.TE_READONLY|wx.ALIGN_RIGHT)
        self.sec.SetBackgroundColour('gray')
        secText = wx.StaticText(durationPanel, -1, " sec. ")
        secMinusButton = wx.Button(durationPanel, -1, u"-", size=(40, 20))
        self.Bind(wx.EVT_BUTTON, self.OnDurationMinus, id=secMinusButton.GetId())
        secPlusButton = wx.Button(durationPanel, -1, u"+", size=(40, 20))
        self.Bind(wx.EVT_BUTTON, self.OnDurationPlus, id=secPlusButton.GetId())
        ###
        repetitionText = wx.StaticText(durationPanel, -1, "Repetition:")
        self.rnd = wx.TextCtrl(durationPanel, -1, str(self.repetition),size=(40, 20), style=wx.TE_READONLY|wx.ALIGN_RIGHT)
        self.rnd.SetBackgroundColour('gray')
        rndText = wx.StaticText(durationPanel, -1, " rnd.")
        rndMinusButton = wx.Button(durationPanel, -1, u"-", size=(40, 20))
        self.Bind(wx.EVT_BUTTON, self.OnRepetitionMinus, id=rndMinusButton.GetId())
        rndPlusButton = wx.Button(durationPanel, -1, u"+", size=(40, 20))
        self.Bind(wx.EVT_BUTTON, self.OnRepetitionPlus, id=rndPlusButton.GetId())

        durationGrid = wx.FlexGridSizer(2, 5, 8, 5)
        durationGrid.AddMany([durationText, (self.sec, 1, wx.EXPAND), secText, secMinusButton, secPlusButton,
                               repetitionText, (self.rnd, 1, wx.EXPAND), rndText, rndMinusButton, rndPlusButton])
        durationSizer.Add(durationGrid, -1, wx.TOP, 8)

        durationPanel.SetSizer(durationSizer)
        ########
        buttonPanel = wx.Panel(framePanel, -1)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        StartButton = wx.Button(buttonPanel, -1, u"Start")
        self.Bind(wx.EVT_BUTTON, self.OnStart, id=StartButton.GetId())
        CancelButton = wx.Button(buttonPanel, -1, u"Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=CancelButton.GetId())
        buttonSizer.Add(StartButton, -1)
        buttonSizer.Add(CancelButton, -1)

        buttonPanel.SetSizer(buttonSizer)

        frameBoxV = wx.BoxSizer(wx.VERTICAL)
        frameBoxV.Add(modePanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        frameBoxV.Add(durationPanel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        frameBoxV.Add(buttonPanel, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        framePanel.SetSizer(frameBoxV)

        self.Centre()
        self.SetClientSize(size)
        self.ShowModal()
        self.Destroy()
        self.Show(True)

    def OnStart(self, event):
        #if self.defaultMode.GetValue() == False and self.marathonMode.GetValue() == False:
        #    self.defaultMode.SetValue(True)
        #else:
        #    pass

        #Oliver 201307
        if self.defaultMode.GetValue() == True:
            self.mode = "Default"
        elif self.defaultRandomMode.GetValue() == True:
            self.mode = "Default_Random"
        elif self.marathonMode.GetValue() == True:
            self.mode = "Marathon"
        elif self.marathonRandomMode.GetValue() == True:
            self.mode = "Marathon_Random"

        self.duration = float(self.sec.GetValue())
        self.repetition = int(self.rnd.GetValue())
        self.Close(True)

    def OnCancel(self, event):
        self.status = False
        self.Close(True)

    def OnDurationPlus(self, event):
        if float(self.sec.GetValue()) < 3:
            currentDuration = float(self.sec.GetValue())
            currentDuration = currentDuration + 0.5
            self.sec.SetValue(str(currentDuration))
        else:
            pass

    def OnDurationMinus(self, event):
        if float(self.sec.GetValue()) > 0.5:
            currentDuration = float(self.sec.GetValue())
            currentDuration = currentDuration - 0.5
            self.sec.SetValue(str(currentDuration))
        else:
            pass

    def OnRepetitionPlus(self, event):
        #print "RepetitionPlus clicked"
        if int(self.rnd.GetValue()) < 5:
            currentRepetition = int(self.rnd.GetValue())
            currentRepetition = currentRepetition + 1
            self.rnd.SetValue(str(currentRepetition))
        else:
            pass

    def OnRepetitionMinus(self, event):
        #print "RepetitionMinus clicked"
        if int(self.rnd.GetValue()) > 1:
            currentRepetition = int(self.rnd.GetValue())
            currentRepetition = currentRepetition - 1
            self.rnd.SetValue(str(currentRepetition))
        else:
            pass

#[Oliver]
def csvWriter(testSheet,clipRecorderOutputDir,now_count_int):
    csvFILE = open(clipRecorderOutputDir+'testRecord.csv','w')
    entryDICT = testSheet.entryDICT.copy() #Peter: 複製一份 entryDICT 寫 testRecord.csv 用。
    entryDICT[now_count_int] = entryDICT[now_count_int]+",*" #複製出來的 dictDICT 裡，把編號 1 的字串值加一 * 號標示起點。
    for key in entryDICT.keys():
        value = entryDICT[key]
        csvFILE.write("%d,%s\n"%(key,value.encode('utf-8')))
    csvFILE.close()


def wxReSpawn(app):
    #print "Respawning..."
    app.Destroy()
    app = wx.App()
    app.MainLoop()
    return app

def clipRecorder(screen, window):
    OS = platform.system()
    ## 檢查麥克風是否可正常收音
    app = wx.App()
    app.MainLoop()
    micTest = MICtest(None, -1, u"Please make some powerful sounds such as 'doodle' at your microphone slowly and observe if the meter level goes up as you speak. \nIf it does, click the 'Yes!' button below to start the experiment, if it only stays at a certain level which represents the background noise, click the 'No!' button and check your microphone connection before starting the experiment.", (250, 550))
    micTestStatus = micTest.micStatus
    app = wxReSpawn(app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows and Zombie window under OSX.
    
    #Fix OSX directory problem.
    if sys.platform == "darwin":
        dirPrefixSTR = "../../../"
    else:
        dirPrefixSTR = "./"
        
    if micTestStatus == True:
        try:#[Oliver]
            lastWorkSTR = sorted(os.listdir(dirPrefixSTR+"ClipRecorderOutput/"))[-1]#Big number is newer
            testRecordFILE = open(dirPrefixSTR+"ClipRecorderOutput/"+lastWorkSTR+"/testRecord.csv", "r")
            testRecordLIST = testRecordFILE.readlines()
            if testRecordLIST[-1].split(",")[-1] == "*\n":
                my_select = False
            else:
                ynbox = YesNoBox(None, -1, u"Warning", u"Do you want to continue the incompleted experiment found at:", lastWorkSTR, (450,150))
                my_select=ynbox.selection
        except:
            my_select=False

        lastWorkPathSTR=""
        if my_select:
            lastWorkPathSTR=dirPrefixSTR+"ClipRecorderOutput/"+lastWorkSTR+"/"
            setFILE=open(lastWorkPathSTR+"setting.txt")
            duration=float(setFILE.readline().replace("\n",""))
            repetition=int(setFILE.readline().replace("\n",""))
            mode=setFILE.readline().replace("\n","")
            setFILE.close()
        else:
            settings = SettingBox(None, -1)
            if settings.status == True:
                duration = settings.duration
                repetition = settings.repetition
                mode = settings.mode

                app = wxReSpawn(app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows and Zombie window under OSX.
            else:
                mainWindow(screen, window)
                return None
    else:
        mainWindow(screen, window)
        return None


    clipRecorderOutputDir = dirPrefixSTR+"ClipRecorderOutput/" + time.strftime("%Y%m%d_%Hh-%Mm-%Ss", time.localtime())+ "/"

    ## 加入 wx 的 msg box 檢查 clipRecorderTestSheetFile 是否存在，若存在的話，是否同時存有多種格式的數個檔同時存在。
    clipRecorderTestSheetFileList = []
    for i in os.listdir(dirPrefixSTR):
        if os.path.isfile(dirPrefixSTR+i):
            if "." in i:
                if i.split(".")[-2] == "ClipRecorderTestSheet" and i.split(".")[-1] in ("csv", "ods", "xls", "xlsx"):
                    clipRecorderTestSheetFileList.append(dirPrefixSTR+i)

    if len(clipRecorderTestSheetFileList) == 0:
        MsgBox(None, -1, u"ERROR!", u"File 'ClipRecorderTestSheet' does not exist. Please prepare the file and save it right next to the application for test before starting Clip Recorder.", (250, 160))
        app = wxReSpawn(app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows and Zombie window under OSX.
        mainWindow(screen, window)
    elif len(clipRecorderTestSheetFileList) == 1:
        clipRecorderTestSheetFile = clipRecorderTestSheetFileList[0]
    else:
        if len(clipRecorderTestSheetFileList) == 4:
            size = (330, 290)
        elif len(clipRecorderTestSheetFileList) == 3:
            size = (330, 250)
        elif len(clipRecorderTestSheetFileList) == 2:
            size = (330, 210)

        selection = SelectionBox(None, -1, u"WARNING!", u"Multiple Test Sheets Found!!! Please select a test sheet file from below and press 'OK.'", size, clipRecorderTestSheetFileList).selections
        app = wxReSpawn(app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows and Zombie window under OSX.
        for i in selection:
            if selection[i] == True:
                clipRecorderTestSheetFile = dirPrefixSTR+"ClipRecorderTestSheet." + i
                break
            else:
                clipRecorderTestSheetFile = None

    #Initiate background.
    screen.blit(window.emptyBackground, (0, 0))

    #Initiate buttons and two meters.
    buttons = Buttons()
    minusButton = buttons.minusButton(status = "ready")
    screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))
    #Oliver 201307
    if mode == "Default":
        plusButton = buttons.plusButton(status = "ready")
        screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))
        recButton = buttons.recButton(status = "ready")
        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
    elif mode == "Default_Random":
        plusButton = buttons.plusButton(status = "ready")
        screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))
        recButton = buttons.recButton(status = "ready")
        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
    elif mode == "Marathon":
        recButton = buttons.recButton(status = "getReady")
        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
    else:# mode = "Marathon_Random":
        recButton = buttons.recButton(status = "getReady")
        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))

    metersArea = buttons.targetMeters()
    screen.blit(metersArea, (windowSize[0]/2-200, windowSize[1]/10+100))


    redLight = buttons.redLight(status = "off")
    screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
    yellowLight = buttons.yellowLight(status = "off")
    screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
    greenLight = buttons.greenLight(status = "off")
    screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))
    pygame.display.update()
    #Load the item and the test sheet.
    item = ItemControl()
    testSheet = TestSheet()
    testSheet.repetitionINT = repetition
    #Oliver
    testSheet.mode=mode

    fileExtension = clipRecorderTestSheetFile.split(".")[-1]
    #[Oliver]jduge if continue last work
    if len(lastWorkPathSTR)>0:
        fileExtension="LastWork"
        clipRecorderOutputDir=lastWorkPathSTR
    try:
        if fileExtension == "csv":
            testSheet.csvTestSheetReader(clipRecorderTestSheetFile)
        elif fileExtension == "ods":
            testSheet.odsTestSheetReader(clipRecorderTestSheetFile)
        elif fileExtension == "xls":
            testSheet.xlsTestSheetReader(clipRecorderTestSheetFile)
        elif fileExtension == "xlsx":
            testSheet.xlsxTestSheetReader(clipRecorderTestSheetFile)
        elif fileExtension == "LastWork":
            item.currentNumINT=testSheet.csvTestSheetReader_LastWork(lastWorkPathSTR+"testRecord.csv")
        else:
            MsgBox(None, -1, u"ERROR!", u"File 'ClipRecorderTestSheet' cannot be read correctly. Please check the format of the file again and save it right next to the application for test before starting Clip Recorder.", (250, 160))
            app = wxReSpawn(OS, app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows
            mainWindow(screen, window)
    except ValueError:
        MsgBox(None, -1, title = u"Oops! An error has just occured!", msg = testSheet.errorMessageSTR, size = testSheet.errorMessageSizeTUPLE)
        app = wxReSpawn(app) #Fix wxWindow Dialog TEMPLATE ERROR under MS-Windows and Zombie window under OSX.
        mainWindow(screen, window)

    targetFont = pygame.font.Font("./DTLK_Resources/font/cwheib.ttf", 42)
    targetFontColor = (28, 28, 28)
    targetEraser = pygame.font.Font("./DTLK_Resources/font/cwheib.ttf", 42)
    targetEraserColor = (250, 250, 250)

    #Set up speed of the red-yellow-green lights.
    span = duration #item.span #(sec.)

    saveFileDirDict = {0:"1st Round/", 1:"2nd Round/", 2:"3rd Round/", 3:"4th Round/", 4:"5th Round/"}
    saveFileDir = ("1st Round", "2nd Round", "3rd Round", "4th Round", "5th Round")
    for i in range(0, repetition):
        if not os.path.exists(clipRecorderOutputDir+saveFileDir[i]):
            os.makedirs(clipRecorderOutputDir+saveFileDir[i])

    #Oliver:1 產生一個CSV(testRecord.csv)  format => key,value,*(目前進度)
    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT)

    #[Oliver]
    #write setting to file
    setFILE = open(clipRecorderOutputDir+'setting.txt','w')
    setFILE.write("%f\n"%duration)
    setFILE.write("%d\n"%repetition)
    setFILE.write("%s\n"%mode)
    setFILE.close()

    converter = Converter("./DTLK_Resources/BP_Table.csv")
    if mode == "Default":
        while True:
            targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
            target = testSheet.entryGetter(item.currentNumINT, mode="normal")
            #def entryGetter(self, number, mode="nromal"): return (number, self.entryDICT[number]), return a tuple
            targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
            screen.blit(targetNumber, (windowSize[0]/2-50, 204))

            if target[1] == u"Get Ready!":
                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
            else:
                if targetText.get_width() <= 260:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                else:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                    #print "Text Too long!"
                    #raise too text long warning

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    mainWindow(screen, window)
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mousePos = event.pos
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089: #minusButton is pressed
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "busy")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 720)**2 + (mousePos[1] - 204)**2 <= 1089: #plusButton is pressed
                        if item.status == "ready":
                            plusButton = buttons.plusButton(status = "busy")
                            screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))

                            #print "plus pressed"
                        else:
                            pass
                            #print "plus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.status == "ready":
                            #print "rec is clicked"
                            recButton = buttons.recButton(status = "pressed")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            pygame.display.update()

                        else:
                            pass
                            #print "rec is busy"

                elif event.type == pygame.MOUSEBUTTONUP:
                    #print item.status
                    mousePos = event.pos
                    mouseKey = event.button
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "ready")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))
                            #print "minus released"
                            if item.currentNumINT - 1 >= 0:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning
                                #[Oliver]
                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)

                                item.currentNumINT = item.currentNumINT - 1
                                #print "just cut down item.currentNumINT to", item.currentNumINT
                            else:
                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very first one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The item is already the very first one."
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 720)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            plusButton = buttons.plusButton(status = "ready")
                            screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))
                            #print "plus released"
                            if item.currentNumINT + 1 <= testSheet.entryMaxNumberINT:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning

                                #[Oliver]
                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT+1)

                                item.currentNumINT = item.currentNumINT + 1

                                #print "just added up item.currentNumINT to", item.currentNumINT
                            else:
                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very last one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The entry is alrady the very last one."
                        else:
                            pass
                            #print "plus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.currentNumINT == 0:
                            #print "please press + to jump to the first token."
                            item.status = "ready"
                            recButton = buttons.recButton(status = "ready")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                        else:
                            if item.status == "ready":
                                item.status = "busy"
                                #print "rec is released"
                                recButton = buttons.recButton(status = "busy")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                pygame.display.update()
                                time.sleep(0.5)


                                for i in range(0, repetition):


                                    redLight = buttons.redLight(status = "on")
                                    screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                    yellowLight = buttons.yellowLight(status = "off")
                                    screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                    greenLight = buttons.greenLight(status = "off")
                                    screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                    pygame.display.update() #Red light is on.
                                    time.sleep(span)

                                    redLight = buttons.redLight(status = "off")
                                    screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                    yellowLight = buttons.yellowLight(status = "on")
                                    screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                    greenLight = buttons.greenLight(status = "off")
                                    screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                    pygame.display.update() #Yellow light is on.

                                    time.sleep(span-0.03)
                                    #print "i:", i
                                    #print "dir:", clipRecorderOutputDir+saveFileDirDict[i]
                                    r = Recorder(clipRecorderOutputDir+saveFileDirDict[i])

                                    redLight = buttons.redLight(status = "off")
                                    screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                    yellowLight = buttons.yellowLight(status = "off")
                                    screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                    greenLight = buttons.greenLight(status = "on")
                                    screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                    pygame.display.update() #Green light is on.

                                    #convertedFileName = ""
                                    convertedFileName = converter.lookup(target[1])
                                    #Oliver
                                    if converter.lookup(target[1]) == None:
                                        wavFileName = target[1] + ".wav"
                                    else:
                                        wavFileName = convertedFileName + ".wav"
                                    r.rec(span+0.1)
                                    r.wavWriter(wavFileName)

                                redLight = buttons.redLight(status = "off")
                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                yellowLight = buttons.yellowLight(status = "off")
                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                greenLight = buttons.greenLight(status = "off")
                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))
                                item.status = "ready"
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                pass
                                #print "item is busy now"
                    else:
                        pass
    elif mode == "Default_Random": #[Peter.w]: 這個情況應該獨立出來。issue: 還有一些易用性和使用者操作邏輯的細節要修正。
        while True:
            targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
            target = testSheet.entryGetter(item.currentNumINT, mode="normal")
            #def entryGetter(self, number, mode="nromal"): return (number, self.entryDICT[number]), return a tuple
            targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
            screen.blit(targetNumber, (windowSize[0]/2-50, 204))

            if target[1] == u"Get Ready!":
                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
            else:
                if targetText.get_width() <= 260:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                else:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                    #print "Text Too long!"
                    #raise too text long warning

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    mainWindow(screen, window)
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mousePos = event.pos
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089: #minusButton is pressed
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "busy")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 720)**2 + (mousePos[1] - 204)**2 <= 1089: #plusButton is pressed
                        if item.status == "ready":
                            plusButton = buttons.plusButton(status = "busy")
                            screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))

                            #print "plus pressed"
                        else:
                            pass
                            #print "plus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.status == "ready":
                            #print "rec is clicked"
                            recButton = buttons.recButton(status = "pressed")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            pygame.display.update()

                        else:
                            pass
                            #print "rec is busy"

                elif event.type == pygame.MOUSEBUTTONUP:
                    #print item.status
                    mousePos = event.pos
                    mouseKey = event.button
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "ready")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))
                            #print "minus released"
                            if item.currentNumINT - 1 >= 0:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning
                                #[Oliver]
                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)

                                item.currentNumINT = item.currentNumINT - 1
                                #print "just cut down item.currentNumINT to", item.currentNumINT
                            else:

                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very first one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The item is already the very first one."
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 720)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            plusButton = buttons.plusButton(status = "ready")
                            screen.blit(plusButton, (windowSize[0]/2+200, windowSize[1]/10+100))
                            #print "plus released"
                            if item.currentNumINT + 1 <= testSheet.entryMaxNumberINT:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning

                                #[Oliver]
                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT+1)

                                item.currentNumINT = item.currentNumINT + 1

                                #print "just added up item.currentNumINT to", item.currentNumINT
                            else:
                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very last one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The entry is alrady the very last one."
                        else:
                            pass
                            #print "plus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.currentNumINT == 0:
                            #print "please press + to jump to the first token."
                            item.status = "ready"
                            recButton = buttons.recButton(status = "ready")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                        else:
                            if item.status == "ready":
                                item.status = "busy"
                                #print "rec is released"
                                recButton = buttons.recButton(status = "busy")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                pygame.display.update()
                                time.sleep(0.5)


                                #clear old text for into repetition at first
                                #targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                #screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                #try:
                                #    #next text
                                #    item.currentNumINT = item.currentNumINT + 1
                                #    targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
                                #    target = testSheet.entryGetter(item.currentNumINT, mode="normal")
                                #    #def entryGetter(self, number, mode="nromal"): return (number, self.entryDICT[number]), return a tuple
                                #    targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
                                #    screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                #    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                #    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT)
                                #except:
                                #    item.currentNumINT-=1
                                #    MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very last one", size = (300, 100))
                                #    app = wxReSpawn(app)
                                #    break
                                #def entryGetter(self, number, mode="nromal"): return (number, self.entryDICT[number]), return a tuple
                                #targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
                                #screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                #screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))


                                redLight = buttons.redLight(status = "on")
                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                yellowLight = buttons.yellowLight(status = "off")
                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                greenLight = buttons.greenLight(status = "off")
                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                pygame.display.update() #Red light is on.
                                time.sleep(span)

                                redLight = buttons.redLight(status = "off")
                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                yellowLight = buttons.yellowLight(status = "on")
                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                greenLight = buttons.greenLight(status = "off")
                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                pygame.display.update() #Yellow light is on.

                                time.sleep(span-0.03)
                                #print "i:", i
                                #print "dir:", clipRecorderOutputDir+saveFileDirDict[i]

                                #Oliver
                                #entryDICT's first entry is {0,"Get Ready"},
                                totalCharINT=(testSheet.entryMaxNumberINT)/repetition
                                i=(item.currentNumINT-1)/totalCharINT
                                r = Recorder(clipRecorderOutputDir+saveFileDirDict[i])

                                redLight = buttons.redLight(status = "off")
                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                yellowLight = buttons.yellowLight(status = "off")
                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                greenLight = buttons.greenLight(status = "on")
                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                pygame.display.update() #Green light is on.

                                #convertedFileName = ""
                                convertedFileName = converter.lookup(target[1])
                                #Oliver
                                #timefornameSTR=time.strftime("%m%d%H%M%S")
                                if converter.lookup(target[1]) == None:
                                    wavFileName = target[1] + ".wav"
                                else:
                                    wavFileName = convertedFileName + ".wav"
                                r.rec(span+0.1)
                                r.wavWriter(wavFileName)

                                redLight = buttons.redLight(status = "off")
                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                yellowLight = buttons.yellowLight(status = "off")
                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                greenLight = buttons.greenLight(status = "off")
                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))
                                item.status = "ready"
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                pass
                                #print "item is busy now"
                    else:
                        pass
    elif mode == "Marathon_Random":
        while True:
            targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
            target = testSheet.entryGetter(item.currentNumINT, mode="normal")
            targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
            screen.blit(targetNumber, (windowSize[0]/2-50, 204))

            if target[1] == u"Get Ready!":
                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
            else:
                if targetText.get_width() <= 260:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                else:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                    #print "Text Too long!"
                    #raise too text long warning

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    mainWindow(screen, window)
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mousePos = event.pos
                    #mouseKey = event.button
                    #print mousePos
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089: #minusButton is pressed
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "busy")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396: ## "Get Ready" rec button is clicked.
                        if item.status == "ready":
                            #print "rec is clicked"
                            if item.currentNumINT == 0:
                                recButton = buttons.recButton(status = "getReadyPressed")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                pass
                        elif item.status == "end":
                            recButton = buttons.recButton(status = "endPressed")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                        else: #item.status = "busy"
                            pass
                        pygame.display.update()
                            #print "rec is busy"
                elif event.type == pygame.MOUSEBUTTONUP:
                    #print item.status
                    mousePos = event.pos
                    mouseKey = event.button
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "ready")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))
                            #print "minus released"
                            if item.currentNumINT - 1 >= 0:

                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning

                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)
                                item.currentNumINT = item.currentNumINT - 1
                                if item.currentNumINT == 0:
                                    recButton = buttons.recButton(status = "getReady")
                                    screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                else:
                                    pass
                                #print "just cut down item.currentNumINT to", item.currentNumINT
                            else:
                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very first one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The item is already the very first one."

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.status == "ready":
                            #print "rec is released"

                            if item.currentNumINT == 0:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                item.currentNumINT = item.currentNumINT + 1
                                #print "item.currentNumINT", item.currentNumINT
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                pygame.display.update()
                                run = True
                                while run:
                                    if item.currentNumINT <= testSheet.entryMaxNumberINT:# and run == True:
                                        if item.status == "ready":
                                            #print "rec is activated"
                                            item.status = "busy"
                                            recButton = buttons.recButton(status = "pause")
                                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                            pygame.display.update()
                                            time.sleep(0.5)

                                            for i in range(0, 1):
                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            recButton = buttons.recButton(status = "pausePressed")
                                                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                            pygame.display.update()
                                                            break
                                                        else: #run == False
                                                            run = True

                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                recButton = buttons.recButton(status = "pausePressed")
                                                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                                pygame.display.update()
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "on")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "off")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "off")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Red light is on.
                                                time.sleep(span)

                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            break
                                                        else: #run == False
                                                            run = True
                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "off")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "on")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "off")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Yellow light is on.

                                                time.sleep(span-0.03)

                                                #Oliver
                                                #entryDICT's first entry is {0,"Get Ready"},
                                                totalCharINT=(testSheet.entryMaxNumberINT)/repetition
                                                i=(item.currentNumINT-1)/totalCharINT
                                                r = Recorder(clipRecorderOutputDir+saveFileDirDict[i])

                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            break
                                                        else: #run == False
                                                            run = True
                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "off")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "off")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "on")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Green light is on.

                                                convertedFileName = converter.lookup(target[1])
                                                #Oliver
                                                if converter.lookup(target[1]) == None:
                                                    wavFileName = target[1] + ".wav"
                                                else:
                                                    wavFileName = convertedFileName + ".wav"
                                                r.rec(span+0.1)
                                                r.wavWriter(wavFileName)

                                            redLight = buttons.redLight(status = "off")
                                            screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                            yellowLight = buttons.yellowLight(status = "off")
                                            screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                            greenLight = buttons.greenLight(status = "off")
                                            screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))
                                            item.status = "ready"


                                            targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                            targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                            screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                            screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                            if item.currentNumINT + 1 <= testSheet.entryMaxNumberINT:
                                                if run ==  True:
                                                    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT+1)
                                                    item.currentNumINT = item.currentNumINT + 1
                                                else:
                                                    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)
                                                    item.currentNumINT = item.currentNumINT - 1

                                                    if item.currentNumINT == 0:
                                                        recButton = buttons.recButton(status = "getReady")
                                                        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                    else:
                                                        recButton = buttons.recButton(status = "ready")
                                                        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
                                                target = testSheet.entryGetter(item.currentNumINT, mode="normal")
                                                targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
                                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                                if target[1] == u"Get Ready!":
                                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                else:
                                                    if targetText.get_width() <= 260:
                                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                    else:
                                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                        #print "Text Too long!"
                                                        #raise too text long warning
                                            else:
                                                item.status = "end"
                                                recButton = buttons.recButton(status = "end")
                                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very last one", size = (300, 100))
                                                app = wxReSpawn(app)
                                                run = False

                                            pygame.display.update()
                                        else:
                                            pass
                                            #print "rec is paused"
                                    else:
                                        pass
                                        #print "the end"
                        elif item.status == "end":
                            mainWindow(screen, window)
                            break
                        else:
                            pass
                            #print "item is busy now"
                    else:
                        pass
    else: #mode == "Marathon"
        #print "Marathon mode: On"

        while True:
            targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
            target = testSheet.entryGetter(item.currentNumINT, mode="normal")
            targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
            screen.blit(targetNumber, (windowSize[0]/2-50, 204))

            if target[1] == u"Get Ready!":
                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
            else:
                if targetText.get_width() <= 260:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                else:
                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                    #print "Text Too long!"
                    #raise too text long warning

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    mainWindow(screen, window)
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mousePos = event.pos
                    #mouseKey = event.button
                    #print mousePos
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089: #minusButton is pressed
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "busy")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396: ## "Get Ready" rec button is clicked.
                        if item.status == "ready":
                            #print "rec is clicked"
                            if item.currentNumINT == 0:
                                recButton = buttons.recButton(status = "getReadyPressed")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                pass
                        elif item.status == "end":
                            recButton = buttons.recButton(status = "endPressed")
                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                        else: #item.status = "busy"
                            pass
                        pygame.display.update()
                            #print "rec is busy"
                elif event.type == pygame.MOUSEBUTTONUP:
                    #print item.status
                    mousePos = event.pos
                    mouseKey = event.button
                    if (mousePos[0] - 240)**2 + (mousePos[1] - 204)**2 <= 1089:
                        if item.status == "ready":
                            minusButton = buttons.minusButton(status = "ready")
                            screen.blit(minusButton, (windowSize[0]/2-280, windowSize[1]/10+100))
                            #print "minus released"
                            if item.currentNumINT - 1 >= 0:

                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))

                                if target[1] == "Get Ready!":
                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                else:
                                    if targetText.get_width() <= 260:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                    else:
                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                        #print "Text Too long!"
                                        #raise too text long warning

                                csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)
                                item.currentNumINT = item.currentNumINT - 1
                                if item.currentNumINT == 0:
                                    recButton = buttons.recButton(status = "getReady")
                                    screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                else:
                                    pass
                                #print "just cut down item.currentNumINT to", item.currentNumINT
                            else:
                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very first one", size = (300, 100))
                                app = wxReSpawn(app)
                                #print "The item is already the very first one."

                            #print "minus pressed"
                        else:
                            pass
                            #print "minus is busy"
                    elif (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                        if item.status == "ready":
                            #print "rec is released"

                            if item.currentNumINT == 0:
                                targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                item.currentNumINT = item.currentNumINT + 1
                                #print "item.currentNumINT", item.currentNumINT
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                            else:
                                recButton = buttons.recButton(status = "ready")
                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                pygame.display.update()
                                run = True
                                while run:
                                    if item.currentNumINT <= testSheet.entryMaxNumberINT:# and run == True:
                                        if item.status == "ready":
                                            #print "rec is activated"
                                            item.status = "busy"
                                            recButton = buttons.recButton(status = "pause")
                                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                            pygame.display.update()
                                            time.sleep(0.5)

                                            for i in range(0, repetition):
                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            recButton = buttons.recButton(status = "pausePressed")
                                                            screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                            pygame.display.update()
                                                            break
                                                        else: #run == False
                                                            run = True

                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                recButton = buttons.recButton(status = "pausePressed")
                                                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                                pygame.display.update()
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "on")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "off")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "off")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Red light is on.
                                                time.sleep(span)

                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            break
                                                        else: #run == False
                                                            run = True
                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "off")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "on")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "off")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Yellow light is on.

                                                time.sleep(span-0.03)
                                                #print "i:", i
                                                #print "dir:", clipRecorderOutputDir+saveFileDirDict[i]
                                                r = Recorder(clipRecorderOutputDir+saveFileDirDict[i])

                                                for event in pygame.event.get():
                                                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                                        if run == True:
                                                            run = False
                                                            break
                                                        else: #run == False
                                                            run = True
                                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                                        mousePos = event.pos
                                                        #print "mouse clicked at", mousePos
                                                        if (mousePos[0] - 480)**2 + (mousePos[1] - 493)**2 <= 7396:
                                                            if run == True:
                                                                run = False
                                                                break
                                                            else: #run == False
                                                                run = True
                                                        else:
                                                            pass


                                                if run == True:
                                                    pass
                                                else:
                                                    break
                                                redLight = buttons.redLight(status = "off")
                                                screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                                yellowLight = buttons.yellowLight(status = "off")
                                                screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                                greenLight = buttons.greenLight(status = "on")
                                                screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))

                                                pygame.display.update() #Green light is on.

                                                convertedFileName = converter.lookup(target[1])
                                                if converter.lookup(target[1]) == None:
                                                    wavFileName = target[1] + ".wav"
                                                else:
                                                    wavFileName = convertedFileName + ".wav"
                                                r.rec(span+0.1)
                                                r.wavWriter(wavFileName)


                                            redLight = buttons.redLight(status = "off")
                                            screen.blit(redLight, (windowSize[0]/2-285, windowSize[1]/10))
                                            yellowLight = buttons.yellowLight(status = "off")
                                            screen.blit(yellowLight, (windowSize[0]/2-100, windowSize[1]/10))
                                            greenLight = buttons.greenLight(status = "off")
                                            screen.blit(greenLight, (windowSize[0]/2+85, windowSize[1]/10))
                                            item.status = "ready"


                                            targetNumber = targetEraser.render("%04d" % item.currentNumINT, False, targetEraserColor, targetEraserColor)
                                            targetText = targetEraser.render(target[1], False, targetEraserColor, targetEraserColor)
                                            screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                            screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                            if item.currentNumINT + 1 <= testSheet.entryMaxNumberINT:
                                                if run ==  True:
                                                    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT+1)
                                                    item.currentNumINT = item.currentNumINT + 1
                                                else:
                                                    csvWriter(testSheet,clipRecorderOutputDir,item.currentNumINT-1)
                                                    item.currentNumINT = item.currentNumINT - 1

                                                    if item.currentNumINT == 0:
                                                        recButton = buttons.recButton(status = "getReady")
                                                        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                    else:
                                                        recButton = buttons.recButton(status = "ready")
                                                        screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                targetNumber = targetFont.render("%04d" % item.currentNumINT, True, targetFontColor, targetEraserColor)
                                                target = testSheet.entryGetter(item.currentNumINT, mode="normal")
                                                targetText = targetFont.render(target[1], True, targetFontColor, targetEraserColor)
                                                screen.blit(targetNumber, (windowSize[0]/2-50, 204))
                                                if target[1] == u"Get Ready!":
                                                    screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                else:
                                                    if targetText.get_width() <= 260:
                                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                    else:
                                                        screen.blit(targetText, (960/2-(targetText.get_width()/2), 300))
                                                        #print "Text Too long!"
                                                        #raise too text long warning
                                            else:
                                                item.status = "end"
                                                recButton = buttons.recButton(status = "end")
                                                screen.blit(recButton, (windowSize[0]/2-100, windowSize[1]/10+330))
                                                MsgBox(None, -1, title = u"Oops!", msg = u"The token is already the very last one", size = (300, 100))
                                                app = wxReSpawn(app)
                                                run = False

                                            pygame.display.update()
                                        else:
                                            pass
                                            #print "rec is paused"
                                    else:
                                        pass
                                        #print "the end"
                        elif item.status == "end":
                            mainWindow(screen, window)
                            break
                        else:
                            pass
                            #print "item is busy now"
                    else:
                        pass


def mainWindow(screen, window):
    #now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    screen.blit(window.mouseUnpressed(mode="BOTTOM"), (0, -10))
    screen.blit(window.mouseUnpressed(mode="TOP"), (0, 0))
    while True: #windowID == "mainWindow":
            #if 787 <= mousePos[0]  and mouse[y]
        for event in pygame.event.get():
            mousePos = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                raise SystemExit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise SystemExit
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #print mousePos
                if 232 <= mousePos[0] <= 883 and 103 <= mousePos[1] <= 210:
                    if 232 <= mousePos[0] <= 330:
                        screen.blit(window.mouseClickApp(mouseClickApp = "symbolTypewriter"), (0, 0))
                        #print "clicking symbol typewriter icon..."
                    elif 369 <= mousePos[0] <= 467:
                        screen.blit(window.mouseClickApp(mouseClickApp = "replyRecorder"), (0, 0))
                        #print "clicking reply recorder icon..."
                    elif 508 <= mousePos[0] <= 606:
                        screen.blit(window.mouseClickApp(mouseClickApp = "perception"), (0, 0))
                        #print "clicking perception icon..."
                    elif 645 <= mousePos[0] <= 744:
                        screen.blit(window.mouseClickApp(mouseClickApp = "lipTracker"), (0, 0))
                        #print "clicking lipTracker icon..."
                    elif 785 <= mousePos[0] <= 883:
                        screen.blit(window.mouseClickApp(mouseClickApp = "clipRecorder"), (0, 0))
                        #print "clicking clip recorder..."

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                #print mousePos
                if 232 <= mousePos[0] <= 883 and 103 <= mousePos[1] <= 210:
                    if 232 <= mousePos[0] <= 330:
                        screen.blit(window.mouseOverApp(mouseOverApp = "symbolTypewriter"), (0, 0))
                        #print "releasing symbol typewriter icon..."
                    elif 369 <= mousePos[0] <= 467:
                        screen.blit(window.mouseOverApp(mouseOverApp = "replyRecorder"), (0, 0))
                        #print "releasing reply recorder icon..."
                    elif 508 <= mousePos[0] <= 606:
                        screen.blit(window.mouseOverApp(mouseOverApp = "perception"), (0, 0))
                        #print "releasing perception icon..."
                    elif 645 <= mousePos[0] <= 744:
                        screen.blit(window.mouseOverApp(mouseOverApp = "lipTracker"), (0, 0))
                        #print "releasing lipTracker icon..."
                    elif 785 <= mousePos[0] <= 883:
                        screen.blit(window.mouseOverApp(mouseOverApp = "clipRecorder"), (0, 0))
                        #print "releasing clip recorder..."
                        clipRecorder(screen, window)
                        break


            elif 232 <= mousePos[0] <= 883 and 103 <= mousePos[1] <= 210:
                if 232 <= mousePos[0] <= 330:
                    screen.blit(window.mouseOverApp(mouseOverApp = "symbolTypewriter"), (0, 0))
                elif 369 <= mousePos[0] <= 467:
                    screen.blit(window.mouseOverApp(mouseOverApp = "replyRecorder"), (0, 0))
                elif 508 <= mousePos[0] <= 606:
                    screen.blit(window.mouseOverApp(mouseOverApp = "perception"), (0, 0))
                elif 645 <= mousePos[0] <= 744:
                    screen.blit(window.mouseOverApp(mouseOverApp = "lipTracker"), (0, 0))
                elif 785 <= mousePos[0] <= 883:
                    screen.blit(window.mouseOverApp(mouseOverApp = "clipRecorder"), (0, 0))
            else:
                screen.blit(window.mouseUnpressed(mode="TOP"), (0, 0))
                screen.blit(window.mouseUnpressed(mode="BOTTOM"), (0, 0))
            pygame.display.update()


if __name__ == "__main__":
    #windowID = "mainWindow"

    pygame.init()
    windowSize = ((960, 640))
    screen = pygame.display.set_mode(windowSize)
    pygame.display.set_caption("-- Droidtown Linguistic Field Research Toolkit --")

    #Initiate background.
    window = AppSelection()
    mainWindow(screen, window)