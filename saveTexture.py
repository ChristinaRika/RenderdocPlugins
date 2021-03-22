import sys

# Import renderdoc if not already imported (e.g. in the UI)
if 'renderdoc' not in sys.modules and '_renderdoc' not in sys.modules:
	import renderdoc

# Alias renderdoc for legibility
rd = renderdoc
#file path to save
savePath = 'E:/rd/saved/'
#file path
filePath = 'E:/rd/'
fileType = '.rdc'

def GetFileNames(path, filetype):
	names = []
	import os
	for root, dirs, files in os.walk(path):
		for file in files:
			if filetype in file:
				names.append(file.replace(filetype, ''))
	return names

# Recursively search for the drawcall with the most vertices
def biggestDraw(prevBiggest, d):

	ret = prevBiggest
	if ret == None or d.numIndices > ret.numIndices:
		ret = d

	for c in d.children:
		biggest = biggestDraw(ret, c)

		if biggest.numIndices > ret.numIndices:
			ret = biggest
	return ret
curFileName = ''
# use event id 0 is all right...
def sampleCode(controller):
	# Find the biggest drawcall in the whole capture
	draw = None
	for d in controller.GetDrawcalls():
		draw = biggestDraw(draw, d)

	# Move to that draw 0
	controller.SetFrameEvent(0, True)

	texsave = rd.TextureSave()

	# Select the first color output
	texsave.resourceId = draw.outputs[0]

	if texsave.resourceId == rd.ResourceId.Null():
		return

	# Blend alpha to a checkerboard pattern for formats without alpha support
	texsave.alpha = rd.AlphaMapping.BlendToCheckerboard

	# Most formats can only display a single image per file, so we select the
	# first mip and first slice
	texsave.mip = 0
	texsave.slice.sliceIndex = 0

	# For formats with an alpha channel, preserve it
	texsave.alpha = rd.AlphaMapping.Preserve

	texsave.destType = rd.FileType.PNG
	controller.SaveTexture(texsave, savePath + curFileName + ".png")

def loadCapture(filename):
	# Open a capture file handle
	cap = rd.OpenCaptureFile()

	# Open a particular file - see also OpenBuffer to load from memory
	status = cap.OpenFile(filename, '', None)

	# Make sure the file opened successfully
	if status != rd.ReplayStatus.Succeeded:
		raise RuntimeError("Couldn't open file: " + str(status))

	# Make sure we can replay
	if not cap.LocalReplaySupport():
		raise RuntimeError("Capture cannot be replayed")

	# Initialise the replay
	status,controller = cap.OpenCapture(rd.ReplayOptions(), None)

	if status != rd.ReplayStatus.Succeeded:
		raise RuntimeError("Couldn't initialise replay: " + str(status))

	return (cap, controller)

fileNames = GetFileNames(filePath, fileType)

for name in fileNames:
    fileName = filePath + name + fileType
    curFileName = name
    pyrenderdoc.LoadCapture(fileName, rd.ReplayOptions(), fileName, False, True)
    if 'pyrenderdoc' in globals():
	    pyrenderdoc.Replay().BlockInvoke(sampleCode)
    else:
	    rd.InitialiseReplay(rd.GlobalEnvironment(), [])
	    cap,controller = loadCapture(fileName)
	    sampleCode(controller)
	    controller.Shutdown()
	    cap.Shutdown()
	    rd.ShutdownReplay()
