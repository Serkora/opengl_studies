#!/usr/bin/env python3
#  - * -  coding: UTF - 8  - * - 

from math import pi, sin, cos

import pyglet
from pyglet.gl import *
from pyglet.window import *

from random import random

import numpy as np

import pickle

import time

import matplotlib.pylab as plt

try:
	# Try and create a window with multisampling (antialiasing)
	config = Config(sample_buffers=1, samples=4, 
					depth_size=16, double_buffer=True,)
	window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
# Fall back to no multisampling for old hardware
	window = pyglet.window.Window(resizable=True)


@window.event
def on_resize(width, height):
	# Override the default on_resize handler to create a 3D projection
	'''
	определяем что то вроде поля зрения, часть плоскости с началом 
	в левом нижнем угле окна и концом в правом верхнем
	'''
	glViewport(0, 0, width, height) 
	glMatrixMode(GL_PROJECTION) #эта строчка говорит о том, что сейчас мы работаем
	#с матрицей "проекции"
	glLoadIdentity()#эта строчка как бы читает эту матрицу в буфер обмена или что
	#то подобное, ее надо вызыватьв сякий раз, как хочешь что-то сделать
	"""
	Как было там в комментах написано, эта функция как "сбрасывает" матрицу,
	загружая единичную (которая identity matrix по-английски).
	"""
	gluPerspective(60., width / float(height), .1, 100.)#это устанавливает как
	#бы угол зрения что-ли
	"""
	Первое да, угол, вот только почему-то его изменение ведёт к изменению размера
	рисуемого анального колечка. Чому так, лол? 
	А второе — соотноешние сторон для поля зрения по оси Х. Видимо, для правильной
	отрисовка круглых объектов на неквадратных плоскостях, ведь все координаты ∈ [0,1]
	Последние две цифры — глубины прорисовки, то есть максимальное расстояние,
	на котором ещё будут рисоваться объекты. Например, в NeHe tutorial 10
	можешь в функции ReSizeGLScene в этой же gluPerspective (у меня 222 строка)
	поиграться с цифрами и увидишь, как поставив 10, 100 — не будут рисоваться близкие,
	а 0.1, 10 — когда далеко из "комнаты" выйдешь - быстро пропадёт всё.
	"""
	glMatrixMode(GL_MODELVIEW)#теперь опять работаем с матрицей модельки
	""" Надо бы почитать, что glMatrixMode делает вообще """
	return pyglet.event.EVENT_HANDLED
	'''
	Как будто в опенгле одна матрица для всего? 
	'''
	""" Мне думается, что glMatrixMode как бы выбирает матрицу, на которой потом функции
	вроде glLoadIndentity() и издеваются, но фиг знает."""
	

@window.event
def on_key_press(symbol,modifier):
	global rx, ry, rz, CAMDIST
	if symbol == key.Q:
		rx = (rx + 10)%360
	if symbol == key.A:
		rx = (rx - 10)%360
	if symbol == key.W:
		ry = (ry + 10)%360
	if symbol == key.S:
		ry = (ry - 10)%360
	if symbol == key.E:
		rz = (rz + 10)%360
	if symbol == key.D:
		rz = (rz - 10)%360
	if symbol == key.R:		
		CAMDIST += 1
		glTranslatef(0, 0, CAMDIST)
	if symbol == key.F:		
		CAMDIST -= 1
		glTranslatef(0, 0, CAMDIST)

@window.event
def on_draw():
	print("ad")
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) #это очищает так называемые 
	#буферы, в первом хранится информация о цвете, а во втором непонятно о чем,
	#но он очевидно связан с "глубиной".
	"""
	В одном из видео той серии, что я тееб скинул, как раз это обсуждалось.
	Грубо говоря, каждому пикселю присваивается "дальность" от viewport'а — "камеры зрения",
	и если в одной точке (проецируется же всё на плоскость) уже есть объект на 
	расстоянии 0.5, то если у того же пикселя рисуемого объекта эта глубина больше (то есть,
	он находится "за" уже нарисованным объектом), то пиксель отбрасывается и на экране
	остаётся тот, что был. Если же он ближе — то рисуется "поверх" имевшегося там объекта.
	"""
	glLoadIdentity()
	glTranslatef(0, 0, CAMDIST)#эта функция двигает "камеру". Сейчас она двигается 
	#"вверх", в сторону зрителя. Можно двигать относительно модели, можно 
	#относительно "перспективы" (туманная фраза, но суть в том, что движение
	#происходит в зависимости от текущей матрицы)
	""" Не очень понял, что там куда двигается. У меня всё на месте, только бублик крутится-вертится."""
	glRotatef(rz, 0, 0, 1)#встроенная функция поворота, первый аргумент говорит
	glRotatef(ry, 0, 1, 0)#на сколько градусов (м.б. отрицательным), остальные
	glRotatef(rx, 1, 0, 0)#в формате True/False по какой оси (x,y,z соответственно)
	batch.draw()

def setup():
#	glBlendFunc(GL_SRC_ALPHA, GL_ONE)          # Set the blending function for translucency (note off at init time)
	# One-time GL setup
	glClearColor(0.2, 0.2, 0.2, 1)#чем очищать буферы
	glColor3f(1, 1, 1)#ПРОСТО установка цвета. Чему - вообще непонятно. Но это - красный.
	glEnable(GL_DEPTH_TEST)#короче, если это выключить, объекты расположенные "ниже"
	#не будут перекрываться верхнимиОМСКОМСКОМСК
	""" Ну это вот как раз включает ту самую проверку глубины объекта/пикселя,
	чтобы наложение объектов друг на друга не зависело от порядка их отрисовки."""
	glEnable(GL_CULL_FACE)#не видимые поверхности вообще не рисуются. Произво-
	#дительность и т.д. Есть подводные камни.
	"""
	Отключил — мой треугольничек стал нормално рисоваться.
	Почему-то он считался "задней" частью, и поэтому не рисовал. Хотя когда я его
	поворачивал, он имел более тёмный цвет, чем кольцо.
	"""

	# Uncomment this line for a wireframe view
	#glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

	# Simple light setup.  On Windows GL_LIGHT0 is enabled by default,
	# but this is not the case on Linux or Mac, so remember to always 
	# include it.
	glEnable(GL_LIGHTING) 
	""" Главный фонарик. Без него не будет цвета у предмета """
	glEnable(GL_LIGHT0)	
	glEnable(GL_LIGHT1)
	"""
	Дополнительные источники, для всяких отражений/преломлений нужны.
	Всего 8 (до GL_LIGHT8), вот только хрен знает, какая в них разница.
	Вряд ли это ограничение на количество источников света.
	"""

	# Define a simple function to create ctypes arrays of floats:
	def vec(*args):
		return (GLfloat * len(args))(*args)
	'''
	Ниже включается освещение. Каждая функция создает источник света, указывает
	как и куда он будет светить. Собственно вектором задается именно направление.
	Для его создания используется маленькая функция выше. Мы будем использовать 
	numpy скорее всего
	'''
	# Ну там не просто маленькая функция, а именно передлка массива в вид С,
	# безо всяких оверхедов, в один буффер подряд все данные запихивает, чтобы не быть МЕДЛЕННЫМ :3
	# Нампи почти то же самое и делает, вроде как.
	glLightfv(GL_LIGHT0, GL_POSITION, vec(10, 10, 10, 0))
	glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, 1, 1))
	glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
	glLightfv(GL_LIGHT1, GL_POSITION, vec(-10, -10, -10, 0))
	glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(0, 1, .5, 1))
	glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 0, 0, 1)) 
	'''
	Это вообще. Ну тип свойства материала, как он реагирует на освещение.
	'''
	glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, vec(0.937, 0.647, 0.317, 1)) 
	glMaterialfv(GL_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0, 0.647, 0, 1)) 
	""" Цвет получаеющейся фигуры. """
#	glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 0, 1, 1))
	"""
	Тоже как-то связано с отржением света во время поворотов. Фигура как-то становится
	всё ярче и ярче, потом максимальная яркость (следующей функцией как-то управляется),
	а затем на секунду меняется цвет на тот, что указан в gl_specular.
	"""
#	glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 0)	
	""" 
	Блёстки всякие, когда предмет повёрнут сильно. Если ноль — просто меняет цвет мгновенно
	на более яркий. Если цифра — хуй знает. Я вижу разницу между 1 и всеми 
	другими — с 1 цвет в самый последний момент поворота намного ярче, чем с другим числом.
	Других отличий чота нет. Но максимальное значение — 1024. Может с большим количеством
	треугольников что-то будет изменяться.
	"""

class Torus(object):
	list = None
	def __init__(self, radius, inner_radius, slices, inner_slices, 
				 batch, group=None):
		# Create the vertex and normal arrays.
		'''
		Объект делят на ломтики что ли, внутри и снаружи, и вычисляют
		нормали и координтаы к каждому. Матан. Как ты любишь.
		'''
		"""
		Это я пока не читал/не разбирался, но обязательно сделаю.
		"""
		vertices = []
		normals = []

		u_step = 2 * pi / (slices - 1)
		v_step = 2 * pi / (inner_slices - 1)
		u = 0.
		for i in range(slices):
			cos_u = cos(u)
			sin_u = sin(u)
			v = 0.
			for j in range(inner_slices):
				cos_v = cos(v)
				sin_v = sin(v)

				d = (radius + inner_radius * cos_v)
				x = d * cos_u
				y = d * sin_u
				z = inner_radius * sin_v

				nx = cos_u * cos_v
				ny = sin_u * cos_v
				nz = sin_v

				vertices.extend([x, y, z])
				normals.extend([nx, ny, nz])
				v += v_step
			u += u_step

		# Create a list of triangle indices.
		'''
		Ну то есть создается нужное количество индексов (связанных с
		номерами внутренних и внешних "кусочков") треугольничков, из которых и
		будет объект составлен. 
		'''
		indices = []
		for i in range(slices - 1):
			for j in range(inner_slices - 1):
				p = i * inner_slices + j
				indices.extend([p, p + inner_slices, p + inner_slices + 1])
				indices.extend([p, p + inner_slices + 1, p + 1])
		'''
		А здесь блять одной командой все это рисуется. Во первых - сразу видно,
		что используется переданный в класс батч - к нему хитрой пиглетовской
		функцией добавляются все нужные объекты и более того, они проиндексированы 
		в соответствии со списком  indices! это можно использовать в нашем текущем
		проекте.
		Дальше- первый аргумент функции это количество объектов.
		Второй аргумент это тип объекта - в опенгл есть в принципе точки, линии,
		треугольники, квадратики и полигоны. Все это может быть н-мерным.
		Дальше  два аргумента указывают, что объекты должны быть объединены
		в группу с такими то индексами.
		Ну дальше... ('v3f/static', vertices) указывает координаты вершин.
		Стандартный опенгл может рисовать если указывать их построчно, как я пытался,
		здесь ему передается массив вершин. При этом передается еще один аргумент 
		- строка, указывающая как интерпритировать полученные вершины. v говорит
		что это вершины, 3 говорит что пространство трехмерное, f что они float,
		/static что они создаются и не меняются. С нормалями аналогично. Магическим
		образом пиглет все понимает и располагает треугольнички нарисованные по двум 
		координатам и относительно нормалей. 
		
		'''
		
		self.vertex_list = batch.add_indexed(len(vertices)//3, 
											 GL_TRIANGLES,
											 group,
											 indices,
											 ('v3f/static', vertices),
											 ('n3f/static', normals))
	   
	def delete(self):
		self.vertex_list.delete()

class Square(object):
	"""
	Квадрат из множества треугольников. Параметры:
	side - длина стороны (в тех же единицах, в которых всё измеряется. Километры, навреное.)
	triangles - количество пар треугольников на одну "полосу". Грубо говоря, разрешение
	квадрата, из скольких кусочков собирается.
	axis — две оси, плоскости которых принадлежит квадрат ('xy', 'xz', 'yz')
	level - в завимости от плоскости, это может быть зад/перед, лево/право, низ/верх,
	принимает значения -1 и 1.
	"""
	list = None
	def __init__(self, side, triangles, axis, level, batch, group=None):
		side = float(side)
		step = side/triangles # side уже float
		indices = []
		vertices = []
		"""		
		Вот так выглядит построение одного квадрата в одной плоскости (xy в данном
		случае). Центр в начале координат. Список состоит из координат точек
		по столбцам сверху вниз справа налево. Координате Z придаётся значение
		± половина стороны квадрата, чтобы сдвинуть его на нужно расстояние
		для создания куба
		for i in range(0,triangles):
			for j in range(0,triangles):
				vertices.extend([(side/2)-i*step, (side/2)-j*step,level*(side/2)])
		"""


		"""
		Чуть боллее сложный/запутанный способ для возможности создания квадрата
		в разных плоскостях без банального копирования кода три раза. Интересно жи.
		Принцип работы: создаётся лямба функция, в которой в зависимости от
		выбранной плоскости выбирается начало для трёх элементов.
		"""
		abs_axis = ['xy','xz','yz'].index(axis)
		verts = lambda: [(side/2)-i*step, (side/2)-j*step, level*(side/2),
							(side/2)-i*step, (side/2)-j*step][abs_axis:abs_axis+3]
	
		for i in range(0,triangles):
			for j in range(0,triangles):
				vertices.extend(verts())

		"""
		Ну и банальное с if'ами
		if axis == "xy":
			for i in range(0,triangles):
				for j in range(0,triangles):
					vertices.extend([(side/2)-i*step, (side/2)-j*step,level*(side/2)])
		elif axis == "xz":
			for i in range(0,triangles):
				for j in range(0,triangles):
					vertices.extend([(side/2)-i*step, level*(side/2), (side/2)-j*step])
		elif axis == "yz":
			for i in range(0,triangles):
				for j in range(0,triangles):
					vertices.extend([level*(side/2), (side/2)-i*step, (side/2)-j*step])
		"""			
					

		
		
		""" Индексы получаются одинаково независимо от плоскости/положения. Грубо говоря,
		первая строка получает тругольник А, вторая — B. Индексы выбираются 
		следующим образом, где А123 — первая строка, В123 — вторая:
		x A2 A1 ++ x B2 x  || x x  x  ++ x x  x  || A2 A1 x ++ B2 x  x || x  x  x ++ x  x  x
		x x  A3 ++ x B3 B1 || x A2 A1 ++ x B2 x  || x  A3 x ++ B3 B1 x || A2 A1 x ++ B2 x  x
		x x  x  ++ x x  x  || x X  A3 ++ x B3 B1 || x  x  x ++ x  x  x || x  A3 x ++ B3 B1 x
		Как можно заметить, особо не важно, построчно или постолбцово создавались
		вершины, поэтому смена местами двух значимых аргументов в vertices.extend([])
		не оказывает никакого влияения на построенную фигуру.
		"""

		for i in range(triangles-1):
			for j in range(triangles-1):
				indices.extend([triangles * i + j, triangles * (i+1) + j, triangles * i + j + 1])
				indices.extend([triangles * i + j + 1, triangles * (i+1) + j, triangles * (i+1) + j + 1])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

class Cube(object):
	"""
	Создаётся 8 вершин единичного куба, зачем либо умножается на необходимой размер,
	либо сначала сдвигается на 0.5 по всем осям, чтобы центр был в начале координат.
	Далее строятся 12 треугольников для 6 граней.
	"""
	def __init__(self, side, batch, center = True, group=None):
		vertices = np.array([	1,1,1, 1,0,1, 1,0,0, 1,1,0,
								0,1,1, 0,0,1, 0,0,0, 0,1,0	])
		if center:
			vertices = vertices-0.5
	
		vertices = list(vertices*side)
	
		indices = [	0,4,5, 0,5,1, 1,5,6, 1,6,2, 2,6,7, 2,7,3,
					3,7,4, 3,4,0, 4,7,6, 4,6,5, 3,0,1, 3,1,2]
		
		vr = vertices
		ic = indices
		
		norm = []
		
		for i in range(0,len(indices),3):
			p1 = [vr[ic[i]*3],vr[ic[i]*3+1],vr[ic[i]*3+2]]
			p2 = [vr[ic[i+1]*3],vr[ic[i+1]*3+1],vr[ic[i+1]*3+2]]
			p3 = [vr[ic[i+2]*3],vr[ic[i+2]*3+1],vr[ic[i+2]*3+2]]
			U = np.array(p2)-np.array(p1)
			V = np.array(p3)-np.array(p1)
			norm.extend(list(np.cross(U,V)))
			
		norm = [0,0.5,0, 0.5,0,0]*4
		
		
		self.vertex_list = batch.add_indexed(8, GL_TRIANGLES, group, indices, 
											('v3f',vertices),('n3f',norm))
		
class Cubetr(object):
	"""
	Строит куб исходя из необходимого размера стороны и количества треугольников
	на полоске грани (количество промежуточных точек между углами).
	К сожалению, достигается это путём построения двух "бездонных коробочек",
	квадратных каркасов, повёрнутых друг относительно друга, поэтому две пары
	граней сливаются в две.
	Нужно сделать две трёхгранных фигуры.
	Корявенько работает.
	"""
	def __init__(self, side, prec, batch, group=None):
		hside = float(side)/2
		step = float(side)/prec
		
		vertices = []
		indices = []
		normals = []
		

		for x in range(0,prec+1):
			for i in range(0,prec+1):
				vertices.extend([hside-step*x, hside-step*i, hside])
			for i in range(1,prec+1):
 				vertices.extend([hside-step*x, -hside, hside-step*i])
			for i in range(1,prec+1):
				vertices.extend([hside-step*x, -hside+step*i, -hside])		
			for i in range(1,prec+1):
				vertices.extend([hside-step*x, hside, -hside+step*i])

		for z in range(0,prec+1):
			for i in range(0,prec+1):
				vertices.extend([-hside, hside-step*i, hside-step*z])
			for i in range(1,prec+1):
 				vertices.extend([hside-step*i, -hside, hside-step*z])
			for i in range(1,prec+1):
				vertices.extend([hside, -hside+step*i, hside-step*z])		
			for i in range(1,prec+1):
				vertices.extend([-hside+step*i, hside, hside-step*z])


		for i in range(prec):
			for j in range(prec*4):
				p = i*prec*4 + j + i
				indices.extend([p, p+prec*4+1, p+prec*4+2])
				indices.extend([p, p+prec*4+2, p+1])
				
		for i in range(prec,prec*2):
			for j in range(prec*4):
				p = i*prec*4 + j + i
				indices.extend([p, p+prec*4+1, p+prec*4+2])
				indices.extend([p, p+prec*4+2, p+1])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
											('v3f/static',vertices))

class Circle(object):
	"""
	Дело круг на много треугольников с одной общей вершиной (в центре).
	Создаётся всего slice+2 вершины, каждый новый труегольник строится по двум старым
	и одной новой вершинам (имеет общую сторону с предыдущим).
	depth — глубина по оси z. Используется для приближения/отдаления круга при построении 
	цилиндра или конуса.
	"""
	list = None
	def __init__(self, radius, slices, depth, batch, group=None):
		r = radius
		vertices = []
		indices = []
		step = (2 * pi) / (slices) # шаг построения треугольников
		
		vertices.extend([0, 0, depth])	# центр круга
		
		"""
		Грубо говоря, ставим точки на окружности с определённым шагом. 
		"""
		for i in range(0,slices+1):
			vertices.extend([r*sin(step*i),r*cos(step*i),depth])
		
		"""
		Центр и две соседние точки на окружности соединяются в один треугольник.
		Создаёт треугольники в двух порядках (по и против часовой стрелке),
		чтобы кружок был "двусторонным" при включенном gl(GL_CULL_FACE)
		"""		
		for i in range(0,slices):
			indices.extend([0, i+2, i+1])
			indices.extend([0, i+1, i+2])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

class Belt(object):
	"""
	Создаёт кольцо, имеющее некоторую плошадь.
	"""
	list = None
	def __init__(self, radius, slices, width, batch, group=None):
		r = radius
		vertices = []
		indices = []
		normals = []
		step = (2 * pi) / (slices)
		width = width 	# ширина кольца
		
		"""
 		Почти то же самое, что и в случае с кругом, только тут ставятся
 		точки на две как бы чуть отстоящие друг от друга окружности.
 		"""
		for i in range(0,slices+1):
			vertices.extend([r*sin(step*i),r*cos(step*i),-width/2.])
			vertices.extend([r*sin(step*i), r*cos(step*i),width/2.])

		"""
		Создаёт два треугольника на "поверхности" кольца, образующих маленький
		прямоугольник. Разумно было бы перенять алгоритм из квадрата, он логичней, вроде как.
		Два раза по две строки из-за gl(GL_CULL_FACE)
		"""
		for i in range(0,slices):
			p11 = i*2+1
			p12 = i*2+2
			p13 = i*2
			p21 = i*2+1
			p22 = i*2+3
			p23 = i*2+2
			
			indices.extend([p11,p12,p13])
			indices.extend([p21,p22,p23])
			
			U = np.array(vertices[p11*3:p11*3+3])-np.array(vertices[p12*3:p12*3+3])
			V = np.array(vertices[p12*3:p12*3+3])-np.array(vertices[p13*3:p13*3+3])
			normal = np.cross(U,V)
			normal = normal/np.linalg.norm(normal)
#			print(list(normal))
			normals.extend(list(normal))
#			print(normals)
		

			indices.extend([p11,p13,p12])
			indices.extend([p21,p23,p22])
			
			U = np.array(vertices[p21*3:p21*3+3])-np.array(vertices[p22*3:p22*3+3])
			V = np.array(vertices[p22*3:p22*3+3])-np.array(vertices[p23*3:p23*3+3])
			normal = np.cross(U,V)
			normal = normal/np.linalg.norm(normal)
			normals.extend(list(normal))
		
		normals.extend([0,.5,1,0,1,1])
		
		print(len(normals))
		print(len(vertices))


		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices),
   											 ('n3f/static', normals))

	def delete(self):
		self.vertex_list.delete()

class Belt2(object):
	"""
	Колько в другой плоскости.
	"""
	list = None
	def __init__(self, radius, slices, width, batch, group=None):
		r = radius
		vertices = []
		indices = []
		step = (2 * pi) / (slices)
		width = width 	# ширина кольца
		
		"""
 		Почти то же самое, что и в случае с кругом, только тут ставятся
 		точки на две как бы чуть отстоящие друг от друга окружности.
 		"""
		for i in range(0,slices+1):
			vertices.extend([r*sin(step*i),-width/2., r*cos(step*i)])
			vertices.extend([r*sin(step*i),width/2., r*cos(step*i)])

		"""
		Создаёт два треугольника на "поверхности" кольца, образующих маленький
		прямоугольник. Разумно было бы перенять алгоритм из квадрата, он логичней, вроде как.
		"""
		for i in range(0,slices):
			indices.extend([i*2+1,i*2+2,i*2])
			indices.extend([i*2+1,i*2+3,i*2+2])

			indices.extend([i*2+1,i*2,i*2+2])
			indices.extend([i*2+1,i*2+2,i*2+3])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

class Belt3(object):
	"""
	Колько в другой плоскости.
	"""
	list = None
	def __init__(self, radius, slices, width, batch, group=None):
		r = radius
		vertices = []
		indices = []
		step = (2 * pi) / (slices)
		width = width 	# ширина кольца
		
		"""
 		Почти то же самое, что и в случае с кругом, только тут ставятся
 		точки на две как бы чуть отстоящие друг от друга окружности.
 		"""
		for i in range(0,slices+1):
			vertices.extend([-width/2.,r*sin(step*i),r*cos(step*i)])
			vertices.extend([width/2.,r*sin(step*i),r*cos(step*i)])

		"""
		Создаёт два треугольника на "поверхности" кольца, образующих маленький
		прямоугольник. Разумно было бы перенять алгоритм из квадрата, он логичней, вроде как.
		"""
		for i in range(0,slices):
			indices.extend([i*2+1,i*2+2,i*2])
			indices.extend([i*2+1,i*2+3,i*2+2])

			indices.extend([i*2+1,i*2,i*2+2])
			indices.extend([i*2+1,i*2+2,i*2+3])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

class Cone(object):
	"""
	Типа верхушка конуса. Единственно отличие от круга — центральная точка
	сдвинута по оси Z от остальных.
	"""
	list = None
	def __init__(self, radius, slices, depth, batch, group=None):
		r = radius
		vertices = []
		indices = []
		step = (2 * pi) / (slices) # Шаг построения треугольников.
		
		vertices.extend([0, 0, 0])	# Кончик конуса.
		
		"""
		Грубо говоря, ставим точки на окружности с определённым шагом. 
		"""
		for i in range(0,slices+1):
			vertices.extend([r*sin(step*i),r*cos(step*i),depth])
		
		"""
		Центр и две соседние точки на окружности соединяются в один треугольник.
		"""		
		for i in range(0,slices):
			indices.extend([0, i+1, i+2])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
   											 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

class Ring(object):
	
	def __init__(self, radius, inner_radius, slices, inner_slices, depth, batch, group=None):
		r = radius
		ir = inner_radius
		vertices = []
		indices = []
		step = (2*pi) / slices
		istep = (2*pi) / inner_slices
		
		#vertices.extend([0, 0, 0])
		for i in range(0,slices+1):
			vertices.extend([r*sin(step*i),r*cos(step*i),depth])
		#for j in range(0,islices+1):
			vertices.extend([ir*sin(istep*i),ir*cos(istep*i),depth])
			
		for i in range(0,slices*2):
			indices.extend([i, i+2, i+1])
			indices.extend([i, i+1, i+2])

		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
																	('v3f/static', vertices))

class Sphere(object):
	"""
	Сфера
	"""
	list = None
	def __init__(self, radius, slices, type, batch, offset=(0,0,0), group=None):
		r = radius
		vertices = []
		indices = []
		normals = []
		step = (2 * pi) / (slices)
		
		for i in range(0, slices):
			for j in range(0,slices):
				if type=="konvertik":
					vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), r*sin(step*i)*cos(step*j)])
				elif type=="krugtochki":
					vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), 0])
				elif type=="vietnam":
					vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), r*sin(step*j)-abs(r*sin(step*j)*cos(step*i))])
				else:
					pass
		
		if type=="krugkub":
			"""
			Грубо говоря, коэффициент x уменьшается (имитация проекции и т.д.), потом
			увеличивается. Ну ты понимаешь, думаю.
			А коээфициент z начинает в нул, достигает максимума (когда нужно рисовать
			окружность в плоскости yz), и снова до 0 спадает.
			В идеале, какая-то фунция от i должна создавать подобные списки с
			косинусом/синусом, тогда будет сфера, ведь на самом деле шаги изменения
			коэффициента x и y не равны.
			"""
			coeff_x = [1,0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1,0,-0.1,-0.2,-0.3,-0.4,-0.5,-0.6,0.7,-0.8,-0.9,-1]
			coeff_z = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1,0]
			for i in range(0,len(coeff_x)):
				for j in range(0,slices):
					vertices.extend([r*sin(step*j)*coeff_x[i], r*cos(step*j), coeff_z[i]*r*sin(step*j)]) 	

		if type=="sphere":
			"""
			Собственно, то же самое, что и в прошлом, только коэффициенты создаются
			косинусом и синусом. И ведь, чёрт побери, отличие от konvertik'а,
			с которым я полночи просидел, лишь в смене косинуса на синус в коэффициенте
			координаты z.
			В общем, i=0: рисуется окружность в плоскости xy.
			i = 1: рисуется "чуть повёрнутая" окружность, соответственно появляются
			маленькие значения z, а амплитуда x чуть уменьшается для того, чтобы не 
			становиться цилиндром.
			"""
			for i in range(0,slices):
				for j in range(0,slices):
					vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), sin(step*i)*r*sin(step*j)]) 

		if type=="spherenormals":
			"""
			Попытка добавить какие-то нормали для освещения.
			Пока что просто поставил их на тех же "углах", где и вершины (но без
			умножения на радиус). Я не знаю, просто, где именно и как их ставить.
			i in range(slices+1) нужно для "зацикливания" сферы. Без этого будет
			одна просвечивающая полоска где-то на правом боку сферы.
			"""
			for i in range(0,slices):
				for j in range(0,slices):
					vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), sin(step*i)*r*sin(step*j)]) 
					normals.extend([sin(step*j)*cos(step*i), cos(step*j), sin(step*i)*sin(step*j)]) 

		for i in range(0,len(vertices),3):
			vertices[i] = vertices[i]+offset[0]#*radius
			vertices[i+1] = vertices[i+1]+offset[1]#*radius
			vertices[i+2] = vertices[i+2]+offset[2]#*radius

		"""
		Индексы это вообще тема. Эта функция работает для всего. Я так понимаю,
		это что-то вроде стандартного алгоритма построения.
		"""
		for i in range(slices-1):
			for j in range(slices-1):
				p = i*slices + j # можно вставить туда.
				indices.extend([i*slices+j, (i+1)*slices+j, (i+1)*slices+j+1])
				indices.extend([i*slices+j, (i+1)*slices+j+1, i*slices+j+1])	
	
		if type=="spherenormals":
			self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
  												 ('v3f/static', vertices),
  												 ('n3f/static', normals))
		else:
			self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
  												 ('v3f/static', vertices))

	def delete(self):
		self.vertex_list.delete()

def update(dt):
	'''
	Тут все понятно — вычисляем приращения координат, но возвращает функция в 
	глобальное пространство и не сами координаты, а остаток их деления на 360.
	'''
	global rx, ry, rz
# 	rx += dt * 30
# 	ry += dt * 80
# 	rz += dt * 30
# 	rx %= 360
# 	ry %= 360
# 	rz %= 360
	pass
	
	
def cube(side,triangles,batch):
	""" Кубик такой себе получается, углы не очень. """
	Square(side,triangles,'xy',-1,batch=batch)
	Square(side,triangles,'xy',1,batch=batch)
	Square(side,triangles,'xz',-1,batch=batch)
	Square(side,triangles,'xz',1,batch=batch)
	Square(side,triangles,'yz',-1,batch=batch)
	Square(side,triangles,'yz',1,batch=batch)

def cylinder(radius,depth,slices,batch):
	""" И цилиндр, вроде, норм. """
	Belt(radius,slices,float(depth),batch)
	Circle(radius,slices,depth/2.,batch)
	Circle(radius,slices,-depth/2.,batch)

def cone(radius,slices, height, batch):
	""" Конус и конус. """
	Circle(radius, slices, height, batch)
	Cone(radius, slices, height, batch)
	
def wizard(radius, slices, height, batch):
	Cone(radius, slices, height, batch)
	Ring(radius*1.3, radius, slices, slices, height, batch)


pyglet.clock.schedule(update)

CAMDIST = -10

setup()
batch = pyglet.graphics.Batch()

""" Чужое """
#torus = Torus(5, 1, 20, 20, batch=batch) #можешь поиграться с количсетвом кусочков чтобы увидеть треугольнички 

""" Углы-уголки """
#square = Square(5,3,axis='yz',level=1,batch=batch)
#cube(7,50,batch)

""" Круглые предметы """
#circle = Circle(5, 10, 0, batch=batch)
#belt = Belt(4,50, 2, batch=batch)
#Contact = Belt(10,50, 2, batch=batch), Belt2(10,50, 2, batch=batch), Belt3(10,50, 2, batch=batch) 
#ring = Ring(5, 3, 50, 50, 0, batch=batch)
#cylinder(5,10,50,batch)
#cone(5,50,7,batch)
#wizzard(5, 30, 10, batch)

""" Флагман """
#sphere = Sphere(5,200, 'konvertik', batch=batch)
#sphere = Sphere(5,200, 'krugtochki', batch=batch)
#sphere = Sphere(5,200, 'vietnam', batch=batch)
sphere = Sphere(5,200, 'krugkub', batch=batch) # http://puu.sh/da0lO/1d4f524a7c.png
#sphere = Sphere(5,200, 'sphere', batch=batch)
#sphere = Sphere(5,200, 'spherenormals', batch=batch)

""" Новый куб """
#cube = Cube(1,batch)
#cubetr = Cubetr(5,10,batch)


rx = ry = rz = 0
# ry = 200
# rz = 50

pyglet.app.run()