import threading
import numpy as np
import warnings

class Buffer:
	""" A circular buffer """
	def __init__(self, N, dtype):
		"""
		>>> b = Buffer(100, np.float32)
		"""
		self._backing = np.empty(N, dtype)
		self._N = N
		self._i = 0
		self._complete = False

	def __len__(self):
		if self._complete:
			return self._N
		else:
			return self._i

	def append(self, value):
		self._backing[self._i] = value
		ni = self._i + 1
		if ni >= self._N:
			self._complete = True
			ni = 0

		self._i = ni

	@property
	def array(self):
		return np.concatenate((
			self._backing[self._i:], self._backing[:self._i]
		))


	@property
	def full(self):
		return self._complete

class BackedSerial:
	""" A serial connection that runs in the background """
	def __init__(self, backing, name, *, make_conn, parse):
		"""
		Example use:

		    with BackedSerial(Buffer(...), make_conn=lambda: serial.Serial(...), parse=int) as backed:
		    	with backed.condition:
		    		backed.condition.wait()
		    		data = backed.data

		    	do_stuff_with(data)

		the condition fires every 20 samples
		"""
		self.name = name
		self._make_conn = make_conn
		self._buffer = backing
		self.run = True
		self.notify_every = 20
		self.parse = parse
		self.condition = threading.Condition()

	def __enter__(self):
		self.t = threading.Thread(target=self._background)
		self.t.start()
		return self

	def __exit__(self, *args):
		self.run = False
		self.t.join()

	@property
	def data(self):
		return self._buffer.array

	def _background(self):
		with self._make_conn() as conn:
			print("Setup")
			total_i = 0
			while self.run:
				try:
					row = self.parse(conn.readline())
				except Exception as e:
					print(e)
					continue

				self._buffer.append(row)

				if conn.in_waiting > 200:
					print("Warning for {}: lots of buffering - {}".format(self.name, conn.in_waiting))
					if conn.in_waiting > 4000:
						print("Warning for {}: threw out data".format(self.name))
						conn.read(conn.in_waiting)

				if total_i % self.notify_every == 0:
					conn.write(self.name.encode('ascii'))
					with self.condition:
						self.condition.notify_all()

				total_i += 1
