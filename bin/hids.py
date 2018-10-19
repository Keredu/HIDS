import hidslib
import time

if __name__ == '__main__':
	t = 2 # time between check
	n = 6  # Number of checks
	hidslib.reset()
	names, paths = hidslib.names_paths()
	hidslib.initialize(names, paths)
	for i in range(0,n):
		hidslib.checkIntegrity()
		hidslib.insertKPI()
		hidslib.restore()
		time.sleep(t)
		hidslib.imageCreator()
