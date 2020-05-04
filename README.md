# Threadly
 An simple framework for multi-threading a task

 I've found myself needing simple way to run threads from the command line more than once.

 This is my framework for it.

 Basically you need to define:
 - A worker function (what each thread will do)
 - A function that provides keyword arguments (kwargs) to the worker thread
 - A finish function that is called when the run is complete with a queue of results

 Then some parameters to tell Threadly how much to do:
 - numberOfWorkers OR lengthOfTest (in seconds)
 - numberOfThreads to run simultaneously
 - delayBetweenThreads - how long to wait between starting threads

 Threadly will do the rest and provide some tqdm status bars to show you where you are in your test

 You can hit CTRL-C to stop making new threads and wait for existing to finish out

 Check testThreadly.py for a simple example

 Enjoy
