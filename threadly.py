# Adaptable thread runner
# Mike Rich 2020
# MIT License

# standard packages
import logging
logger = logging.getLogger('Threadly')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

import threading
import queue
import time
import argparse
import re
import tqdm
import sys
import math

class Threadly:
    MODE_COUNT = 1
    MODE_TIME = 2
    MODE_UNKNOWN = 0

    def __init__(self):
        self.time = time.time()
        self.tnamePrefix = "threadly"
        pass

    def startsw(self):
        self.time = time.time()

    def currentsw(self):
        return time.time() - self.time

    def stopsw(self):
        return time.time() - self.time

    def countWorkerThreads(self):
        # function to affirmatively count worker threads
        # Though len(threading.enumerate()) or threading.active_count() should work
        # I discovered a random thread once (while testing signal handlers) that I didn't understand
        # Prefer a affirmative count of properly named threads
        countOfThreads = 0
        for thisthread in threading.enumerate():
            if (thisthread.name.find(self.tnamePrefix) > -1):
                countOfThreads += 1
        #logger.debug("CountWorkerThreads: {}".format(countOfThreads))
        return countOfThreads

    def runTest(self, **kwargs):
        """
        Keyword args:
        workerFunc = the function each thread will call
        workerKwargGenFunc = the function that provides the keyword arguments for the next thread
            workers need to accept a queue in var resultsQ and push their results there
        numberOfWorkers = total number of workers to be made OR
        lengthOfTest = time length of test in seconds
        numberOfThreads = max number of simultaneous threads
        finishFunc = function to call with results queue
        finishFuncKwargs = kwargs to send to finishFunc
            will add totalTime & resultsQ to kwargs
        delayBetweenThreads = time in seconds to wait between starts
        """
        # check the kwargs
        neededKwargs = ["workerFunc", "workerKwargGenFunc", "numberOfThreads", "finishFunc", "finishFuncKwargs", "delayBetweenThreads"]
        for akwarg in neededKwargs:
            if akwarg not in kwargs.keys():
                raise Exception("ThreadTester.runTest: missing mandatory kwarg {}".format(akwarg))
        # time or count
        self.mode = self.MODE_UNKNOWN
        self.plannedTotalTests = 0
        self.startProgBarLabel = "Unknown"
        startProgBar = None
        if "numberOfWorkers" in kwargs.keys():
            if "lengthOfTest" in kwargs.keys():
                raise Exception("ThreadTester.runTest: Choose either 'numberOfWorkers' or 'lengthOfTest', not both")
            else:
                self.mode = self.MODE_COUNT
                self.startProgBarLabel = "Workers started"
                self.plannedTotalTests = int(kwargs["numberOfWorkers"])
                print("Starting run of {} attempts with {} simultaneous threads".format(self.plannedTotalTests,kwargs["numberOfThreads"] ))
                startProgBar = tqdm.tqdm(total=self.plannedTotalTests, desc=self.startProgBarLabel)

        else:
            if "lengthOfTest" in kwargs.keys():
                self.mode = self.MODE_TIME
                self.startProgBarLabel = "Time elapsed"
                self.plannedTotalTests = int(kwargs["lengthOfTest"])
                print("Starting timed run of {} second with {} simultaneous threads".format(self.plannedTotalTests,kwargs["numberOfThreads"] ))
                startProgBar = tqdm.tqdm(total=self.plannedTotalTests, desc=self.startProgBarLabel, unit="s")

            else:
                raise Exception("ThreadTester.runTest: Must choose either 'numberOfWorkers' or 'lengthOfTest'")

        # wrap in keyboard KeyboardInterrupt catch
        resultsQ = queue.Queue()
        finishProgBar = tqdm.tqdm(desc="Workers completed")
        if self.mode == self.MODE_COUNT:
            finishProgBar.total = self.plannedTotalTests
        else:
            finishProgBar.total = 1


        testDone = False
        countOfTotalTests = 0
        threadsStarted = 0
        self.startsw()

        while not testDone:
            try:
                while self.countWorkerThreads() >= kwargs["numberOfThreads"]:
                    if self.mode == self.MODE_TIME:
                        # Need to keep timer bar moving in time mode if workers are slow to run
                        countOfTotalTests = self.currentsw()
                        startProgBar.update(math.floor(countOfTotalTests) - startProgBar.n)
                    time.sleep(0.01)
                # generate next kwargs
                workerKwargs = kwargs["workerKwargGenFunc"]()
                # add the resultsQ
                workerKwargs["resultsQ"] = resultsQ
                threading.Thread(target=kwargs["workerFunc"], kwargs=workerKwargs, name=self.tnamePrefix).start()
                threadsStarted += 1
                if self.mode == self.MODE_COUNT:
                    startProgBar.update(1)
                    countOfTotalTests += 1
                    if countOfTotalTests >= self.plannedTotalTests:
                        testDone = True
                elif self.mode == self.MODE_TIME:
                    # update possible total of threads
                    finishProgBar.total = threadsStarted
                    countOfTotalTests = self.currentsw()
                    startProgBar.update(math.floor(countOfTotalTests) - startProgBar.n)
                    if countOfTotalTests >= self.plannedTotalTests:
                        testDone = True
                else:
                    # just end test
                    testDone = True

                #update finish prog bar
                finishProgBar.update(resultsQ.qsize() - finishProgBar.n)
                time.sleep(kwargs["delayBetweenThreads"])
            except KeyboardInterrupt:
                startProgBar.write("Cancelling test, please wait for threads to finish")
                finishProgBar.total = threadsStarted
                testDone = True
            except Exception as badnews:
                raise Exception("ThreadTester.runTest(): Failed with {}".format(badnews))

        # End of while indent
        startProgBar.close()
        logger.debug("Pre loop qsize: {}".format(resultsQ.qsize()))
        logger.debug("Pre loop threadStarted: {}".format(threadsStarted))

        #while resultsQ.qsize() < threadsStarted:
        while self.countWorkerThreads() > 0:
            finishProgBar.update(resultsQ.qsize() - finishProgBar.n)
            time.sleep(0.01)

        finishProgBar.update(finishProgBar.total - finishProgBar.n)
        finishProgBar.close()
        totalTime = self.currentsw()
        kwargs["finishFuncKwargs"]["totalTime"] = totalTime
        kwargs["finishFuncKwargs"]["resultsQ"] = resultsQ
        logger.debug("calling finish func")
        kwargs["finishFunc"](**kwargs["finishFuncKwargs"])
        logger.debug("finish func returned")

        return
