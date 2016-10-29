import threading
import sys

import serial
import matplotlib.pyplot as plt
import numpy as np

import circular

PORT1 = sys.argv[1] if sys.argv[1:] else 'COM6'
PORT2 = sys.argv[1] if sys.argv[1:] else 'COM5'

def parse(msg):
	parts = [int(p) for p in msg.split()]
	if len(parts) != 4:
		raise ValueError("Malformed message: {}".format(parts))

	return tuple([ np.nan if parts[0] == -1 else parts[0] / 1000.0, parts[1:], np.linalg.norm(parts[1:])])

N = 500
dt = np.dtype([
	('t', np.float), ('a', (np.float64, 3)), ('mag', np.float64)
])

GROUP_BY = 'board'
AXES = ['x', 'y', 'z', '|a|']
BOARDS = '12'

DO_CONVOLVE = True

kernel = 0.95 ** np.arange(25)
kernel /= kernel.sum()

with circular.BackedSerial(circular.Buffer(N, dt), name=BOARDS[0], parse=parse, make_conn=lambda: serial.Serial(PORT1, baudrate=115200)) as backing1, \
	 circular.BackedSerial(circular.Buffer(N, dt), name=BOARDS[1], parse=parse, make_conn=lambda: serial.Serial(PORT2, baudrate=115200)) as backing2:

	lines = np.empty((2, 4), dtype=np.object_)
	if GROUP_BY == 'axis':
		fig, axes = plt.subplots(2, sharex=True)
		for line, ax, board in zip(lines, axes, BOARDS):
			line[0], = ax.plot([], [], label=AXES[0])
			line[1], = ax.plot([], [], label=AXES[1])
			line[2], = ax.plot([], [], label=AXES[2])
			line[3], = ax.plot([], [], label=AXES[3], linewidth=2, color='k')
			ax.legend()
			ax.set(ylim=[-1500, 1500], title=board)
	else:
		fig, axes = plt.subplots(4, sharex=True)
		for line, ax, name in zip(lines.T, axes, AXES):
			line[0], = ax.plot([], [], label=BOARDS[0])
			line[1], = ax.plot([], [], label=BOARDS[1])
			ax.legend()
			ax.set(ylim=[-1500, 1500], title=name)
		axes[-1].set(ylim=[0, 2000])


	plt.show(block=False)

	while True:
		with backing1.condition:
			# backing1.condition.wait()
			data1 = backing1.data
		with backing2.condition:
			backing2.condition.wait()
			data2 = backing2.data

		datas = [data1, data2]
		for data, line in zip(datas, lines):
			t = data['t']

			for d in range(3):
				y = data['a'][:,d]
				line[d].set_data(t, y)

			line[3].set_data(t, data['mag'])

		tmax = max(np.nanmax(data['t']) for data in datas)
		tmin = min(np.nanmin(data['t']) for data in datas)

		axes[0].set(xlim=(tmin, tmax), title='period = {} ms'.format(1000 * (tmax - tmin) / N))
		fig.canvas.draw()
		fig.canvas.flush_events()
