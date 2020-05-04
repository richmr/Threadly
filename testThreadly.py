import time

currentBot = 1
from threadly import Threadly

def worker(**kwargs):
    botID = kwargs["botID"]
    resultsQ = kwargs["resultsQ"]
    time.sleep(2)
    resultsQ.put({"botID":botID, "time":time.time()})

def workerKwargs():
    global currentBot
    tosend = {"botID":"bot {}".format(currentBot)}
    currentBot += 1
    return tosend

def finish(**kwargs):
    greeting = kwargs["greeting"]
    resultsQ = kwargs["resultsQ"]
    overallTime = kwargs["totalTime"]

    print("{}, It took {} seconds".format(greeting, overallTime))
    print("bot results")
    for i in range(resultsQ.qsize()):
        aresult = resultsQ.get()
        print("bot {botID} finished at {time}".format(**aresult))

print("Starting..")
mytest = Threadly()
testerkwargs = {"workerFunc":worker,
                "workerKwargGenFunc":workerKwargs,
                "numberOfWorkers":10,
                "numberOfThreads":2,
                "finishFunc":finish,
                "finishFuncKwargs":{"greeting":"Howdy"},
                "delayBetweenThreads":0.1}
testerkwargs2 = {"workerFunc":worker,
                "workerKwargGenFunc":workerKwargs,
                "lengthOfTest":15,
                "numberOfThreads":2,
                "finishFunc":finish,
                "finishFuncKwargs":{"greeting":"Howdy"},
                "delayBetweenThreads":0.1}
mytest.runTest(**testerkwargs2)

print("Done")
