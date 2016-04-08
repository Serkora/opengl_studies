#!/usr/bin/env python3
#  - * -  coding: UTF - 8  - * - 

import pyglet
from pyglet.gl import *
from pyglet.window import *
from obj import OBJ

import numpy as np
from math import copysign, sin, cos, pi
from random import random, randint, uniform

import socket
from threading import Thread
from multiprocessing import Process, Queue
import asyncio

import ctypes
import time
import sys

ENC = 'utf-8'

def vec(*args):
	return (GLfloat * len(args))(*args)

class Player(object):
	"""
	Класс игрока. 4 группы координат по каждой из осей.
	pos — позиция в мире
	rot — направление, в которое смотрит
	strafe — для движения вбок.
	xp, yp, zp — промежуточные координаты, без них стрейф не сделать. Впрочем,
	и с ними что-то сбивается.
	height — высоа "головы" игрока над землёй.
	!!В collision detection'ах используются координаты ног!!
	"""
	def __init__(self):
		self.xpos = 0.
		self.ypos = 0.
		self.zpos = 0.
		
		self.xrot = 0.
		self.yrot = 0.
		self.zrot = 0.
		
		self.xstrafe = 0.
		self.ystrafe = 0.
		self.zstrafe = 0.
	
		self.xp = 0.
		self.yp = 0.
		self.zp = 0.
		
		self.height = 2
		self.stepheight = 1.
		self.speed = 0.3
		
class Cubecol(object):
	"""
	Простой куб. 16 точек - чтобы текстуры можно было лепить (каждый вертекс может иметь
	лишь одну координату картинки, поэтому приходится дублировать. Впрочем, тут 
	текстур никаких нет, лол.
	inside/outside — какая из сторону куба является "лицевой" — то есть, рисуемой при
	включённом GL_CULL_FACE. (Комната или ящик, например.)
	"""
	def __init__(self, side, batch, offset=(0,0,0), center = False, type = 'outside', group = None):
		vertices = np.array([	1,0,0, 0,0,0, 1,1,0, 0,1,0, 1,1,1, 0,1,1, 1,0,1, 0,0,1,
								1,1,0, 1,1,1, 1,0,0, 1,0,1, 0,0,0, 0,0,1, 0,1,0, 0,1,1,
#								1,1,0, 0,1,0, 1,1,1, 0,1,1
							])
		if center:
			vertices = vertices-0.5
		
		vertices = vertices.astype(float)
		
		for i in range(0,len(vertices),3):
			vertices[i] = vertices[i] + offset[0]
			vertices[i+1] = vertices[i+1] + float(offset[1])
			vertices[i+2] = vertices[i+2] + float(offset[2])
	
		vertices = vertices*side

		norm = np.array([	0,0,-1, 0,0,-1, 0,0,-1, 0,0,-1, 0,0,1, 0,0,1, 0,0,1, 0,0,1,
							1,0,0, 1,0,0, 1,0,0, 1,0,0, -1,0,0, -1,0,0, -1,0,0, -1,0,0,
							0,1,0, 0,1,0, 0,1,0, 0,1,0
						])
	
		if type == "outside":
			indices = 	[	0,1,2, 2,1,3, 2,3,4, 4,3,5, 4,5,6, 6,5,7, 
							8,9,10, 10,9,11, 10,11,12, 12,11,13, 12,13,14, 14,13,15,
 #							16,16,16, 17,17,17, 18,18,18, 19,19,19
						]
		elif type == "inside":
			indices = 	[	0,2,1, 2,3,1, 2,4,3, 4,5,3, 4,6,5, 6,7,5, 
							8,10,9, 10,11,9, 10,12,11, 12,13,11, 12,14,13, 14,15,13,	
# 							16,16,16, 17,17,17, 18,18,18, 19,19,19
						]
			norm = norm*-1

		textcoord = [.25,.75, 0,.75, .25,.5, 0,.5, .25,.25, 0,.25, .25,0, 0,0]*2
		
# 		norm = []
# 		vr = vertices
# 		ic = indices
# 		for i in range(0,len(indices),3):
# 			p1 = [vr[ic[i]*3],vr[ic[i]*3+1],vr[ic[i]*3+2]]
# 			p2 = [vr[ic[i+1]*3],vr[ic[i+1]*3+1],vr[ic[i+1]*3+2]]
# 			p3 = [vr[ic[i+2]*3],vr[ic[i+2]*3+1],vr[ic[i+2]*3+2]]
# 			U = np.array(p2)-np.array(p1)
# 			V = np.array(p3)-np.array(p1)
# #			print(np.cross(U,V))
# 			norm.extend(list(np.cross(U,V)))
# 			
#		print(len(norm))

		self.vertex_list = batch.add_indexed(16, GL_TRIANGLES, group, indices, 
											('v3f',vertices),('t2f',textcoord))#,('n3f',norm))
		
		self.collision_box(vertices,side)
	
	def collision_box(self,vertices,side):
		"""
		Координаты расположения плоскостей сторон. Для проверки на столкновение нужно.
		"""
		self.zback = vertices[2]
		self.zfront = self.zback + side
		self.ybot = vertices[1]
		self.ytop = self.ybot + side
		self.xleft = vertices[3]
		self.xright = self.xleft + side

class World(Window):
	def __init__(self,player):
		"""
		Всё стандартно. Два батча — мир и коробки, для разных материалов.
		Игрок, вызывается функция создания коробочек.
		"""
		config = Config(sample_buffers=1, samples=1, 
						depth_size=16, double_buffer=True)
		try:
			super(World, self).__init__(config=config, resizable=True, fullscreen=False, vsync=True)
		except:
			super(World, self).__init__(resizable=True, fullscreen=False, vsync=True)
		self.noground = False
		self.player = player
		self.fps = pyglet.clock.ClockDisplay()
		self.graphics_batches()
		self.make_cubes()
		self.textures_and_text()
		pyglet.clock.schedule_interval(self.update, 1.0 / 60) # чо-то не пашет, всё равно
		self.edx = []

	def graphics_batches(self):
		self.batch = pyglet.graphics.Batch()
		self.batch_box = pyglet.graphics.Batch()
		self.batch_cup = pyglet.graphics.Batch()
	
	def textures_and_text(self):
		self.coords = pyglet.text.Label(text="",x=10)
		self.rot = pyglet.text.Label(text="",x=10)
		self.times = pyglet.text.Label(text="",x=10)
		self.boximage = pyglet.image.load('DATA/ROOM.bmp')
		self.boxtexture = self.boximage.get_texture()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.boxtexture.width, self.boxtexture.height,
	    			0, GL_RGBA, GL_UNSIGNED_BYTE, self.boxtexture.get_image_data().get_data('RGBA',
					self.boxtexture.width * 4))
		self.pic = pyglet.image.load('DATA/cross.png')
		self.pic.anchor_x = self.pic.width//2
		self.pic.anchor_y = self.pic.height//2
		self.picspr = pyglet.sprite.Sprite(self.pic, x=self.width/2, y = self.height/2)
		self.picspr.scale = 0.2	
	
	def make_cubes(self):
		"""
		Создаётся несколько ящиков с разными сдвигами от начала координат
		и заносит их в список объектов.
		"""
		self.box = Cubecol(30,self.batch_box,center = True, type = "inside")
		self.cube = Cubecol(2,self.batch,offset=(3,-7,-7))
# 		self.sphere = Sphere(4,1000,self.batch)
# 		self.sphere = Sphere(6,1000,self.batch_cup)

	def update(self, dt):
		"""
		Проверяет, какие из кнопок нажаты, и вызывает соответствующую команду.
		Чтобы можно было ходить при зажатых клавишах, а не тыкать по сто раз.
		"""
		for key in keystate:
			if keystate[key]:
				self.dispatch_event('on_key_press',key,False)
		if keystate[65507]:
			self.dispatch_event('on_key_press',65507,False)
# 		self.on_draw1()
		
	def setup3d(self):
		"""
		Настройка на триДЭ. Лампа LIGHT1 линейно, затухает, поэтому светит
		лишь на какое-то расстояние.
		"""
		glViewport(0, 0, self.width, self.height) 
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(60., self.width / float(self.height), .1, 100.)
		glMatrixMode(GL_MODELVIEW)
		glClearColor(0.2, 0.2, 0.2, 1)
		glClearDepth(1.0)
		glDepthFunc(GL_LESS)		# функция depth_test'а. Рисует только если ближе к экрану.
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)		# Сглаживание больших поверхностей, имеющих мало 
									# вершин. GL_FLAT покажет все треугольники.
# 		glEnable(GL_CULL_FACE)		
			# Освещение
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_LIGHT1)
		glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 5, 0, 1))
		glLightfv(GL_LIGHT0, GL_AMBIENT, vec(1,1,1,0))
		glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, vec(0))
		glLightfv(GL_LIGHT1, GL_AMBIENT, vec(1,1,1,0))
		glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(1,1,1,0))
		glLightfv(GL_LIGHT1, GL_LINEAR_ATTENUATION, vec(0.05))
		pass
	
	def setup2d(self):
		"""
		2Д. gluPerspective заменяетсяна glOrtho. Чтобы рисовать лейблы, фпс,
		какие-нибудь текстурки типа меню и т.д., которые "в мире", а просто на экране.
		Есть проблемы — если загружать спрайты, текстуры с объектов пропадают.
		"""
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0,0,0,1))
		glColor3ub(255,255,255)
		glDisable(GL_DEPTH_TEST)
		glViewport(0, 0, self.width, self.height) 
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, self.width, 0, self.height, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def ground_collision(self,player):
		self.player.ypos = -10
		return
	
	def object_collision(self,wsad):
		rot = (np.cos((self.player.yrot+wsad)*np.pi/180),np.sin((self.player.yrot+wsad)*np.pi/180))
		## North-East
		if rot[0]>=0 and rot[1]>=0:
			## Map limit
			if (-self.player.zpos < self.box.zback + 0.4 or self.player.xpos > self.box.xright - 0.4):
				self.player.speed = 0
				return
		## North-West
		if rot[0]>=0 and rot[1]<0:
			## Map limit
			if (-self.player.zpos < self.box.zback + 0.4 or self.player.xpos < self.box.xleft + 0.4):
				self.player.speed = 0
				return
		## South-West
		if rot[0]<0 and rot[1]<0:
			## Map limit
			if (-self.player.zpos > self.box.zfront - 0.4 or self.player.xpos < self.box.xleft + 0.4):
				self.player.speed = 0
				return
		## South-East
		if rot[0]<0 and rot[1]>=0:
			## Map limit
			if (-self.player.zpos > self.box.zfront - 0.4 or self.player.xpos > self.box.xright - 0.4):
				self.player.speed = 0
				return
		self.player.speed = 0.1
					
	def on_draw(self):
		"""
		Устанавливается режим тридэ. Очищается буфер. Загружается единичная матрица.
		Поворачивается всё по оси x (направление вверх/вниз), затем поворачивается
		по оси y (влево/вправо). Затем вызывается функция опреления высоты игрока
		над уровнем моря. И после этого мир двигается куда нужно.
		Порядок матриц ВАЖЕН. ОЧЕНЬ.
		Затем выбирается материал ящиков, рисуются ящики, выбирается материал
		стен комнаты, рисуется комната.
		Перенастраивается в 2д, пишется фпс.
		"""
		self.setup3d()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glRotatef(self.player.xrot,1,0,0)
		glRotatef(self.player.yrot,0,1,0)
		glLightfv(GL_LIGHT1, GL_POSITION, vec(0,1,-1))
		glTranslatef(-self.player.xpos,-self.player.ypos-self.player.height,self.player.zpos)
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(1,0.3,0,0))
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0,0,0))
		glPointSize(20)
		glColor3f(0.5,0,0.2)
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0.75,0.52,0.15,0))
		self.batch.draw()
		glColor3f(0,0,0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(self.boxtexture.target,self.boxtexture.id)
# 		self.batch_box.draw()
		glDisable(GL_TEXTURE_2D)
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0.3,0,0))
		self.setup2d()
			# лейблы с координатами. Округлено до трёх знаков после запятой, всё в одну строку чтобы показывалось.
		pltxt = "X: "+str(np.round(self.player.xpos,3))+" Y: "+str(np.round(self.player.ypos,3))+" Z: "+str(np.round(self.player.zpos,3))
		self.coords.text = pltxt
		self.coords.y = self.height-30
		plrottxt = "Xrot: "+str(np.round(self.player.xrot,3))+" Yrot: "+str(np.round(self.player.yrot,3))+" Zrot: "+str(np.round(self.player.zrot,3))
		self.rot.text = plrottxt
		self.rot.y = self.height-50
			# положение зелёного прямоугольника
		self.coords.draw()
		self.rot.draw()
		self.fps.draw()
		self.picspr.draw()

	def on_mouse_motion(self,x,y,dx,dy):
		"""
		Поворот мира по движению мышки. yrot = dx, xrot = dy потому что
		движение мышкой влево/вправо (по оси x) должно поворачивать мир вокруг 
		вертикальной оси y.
		"""
		self.player.yrot += dx/3
		self.player.yrot%=360
		self.player.xrot -= dy/3
		if self.player.xrot >=90: self.player.xrot = 90
		if self.player.xrot <=-90: self.player.xrot = -90
		pass

	def on_key_release(self,symbol,modifier):
		if symbol == 65507:
			# при отпуске контрола "встаёт".
			self.player.height = 2
	
#	@asyncio.coroutine
	def compute(self,q,s):
		"""
		Типа топорное отложенное вычисление. Если время между определённым 
		количесвом операция (time.time() тоже ресурсы жрёт ведь) превосходит N мс,
		то тред приостанавливается на некоторое время. Таким образом вычисления
		растягиваются во времени, но не снижают сильно фпс. Можно запускать до того,
		как игрок дошёл то территории, запустить функцию просчёта подземелья, скажем,
		и к тому времени, как дойдёт — всё будет готово. В Morrowind'е, насколько я
		помню, именно так и сделали "революционное" отсутствие загрузочных экранов в
		громадном мире.
		"""
# 		loop = asyncio.get_event_loop()
		print(time.time() - self.time2)
		self.edx = []
		def func():
			time1 = time.time()
			sleep = 'no'
			for i in range(1):
				self.edx.append(cos(random()*np.pi/2))
# 				if i%10000 == 0:
# 					time2 = time.time()
# 					print(time.time()-time1)
# 					if time.time()-time1 > 0.01:
# 						time.sleep(0.05)
# 					time1 = time.time()
# 			print(time.time()-time1)
		func()
#		asyncio.async(func())
# 		loop.run_until_complete(func)
# 		print(len(self.edx))
		if not isinstance(q,int):
			q.put(len(self.edx))
	
	def generate_lines(self):
		self.batch = pyglet.graphics.Batch()
		glLineWidth(GLfloat(10))
		self.path = PathGenerator(1,1,1,20)
		self.batch.add(len(self.path.vertices)//3, GL_LINES, None, ('v3f',self.path.vertices))
# 		self.batch.add(3, GL_TRIANGLES, None, ('v3f',(0,0,-2,1,1,-4,2,1,-1)))
	
	def generate_wall(self):
		self.batch = pyglet.graphics.Batch()
# 		vertices = [0,1,0]
		vertices = []
		slices = 25
		hpoints = randint(1,10)
		vpoints = []
		indices = []
		protuberance = []
		normals = []
		side = 8.
		for i in range(slices):
			spacing = 1./slices
			z = i/slices
			for j in range(slices):
# 				print(protuberance)
				if i > 0 and j > 0:
					x_prot = np.mean((protuberance[i-1][j],protuberance[i][j-1]))+uniform(-0.1,0.1)
					protuberance[i].append(x_prot)
# 					print(protuberance)
				elif i > 0:
					x_prot = protuberance[i-1][0]+uniform(-0.02,0.02)
					protuberance.append([x_prot])
				elif j > 0:
					x_prot = protuberance[0][j-1]+uniform(-0.02,0.02)
					protuberance[0].append(x_prot)
				else:
					x_prot = 0
					protuberance.append([x_prot])
				vertices.extend([x_prot/side,1-uniform(j*spacing,(j+1)*spacing),z])
				if j%2 == 1:
					n = [-cos(x_prot),random()/4,sin(x_prot)]
				else:
					n = [-cos(x_prot),random()/4,-sin(x_prot)]
				normals.extend(n)
				
# 		for i in range(hpoints):
# 			vpoints.append(randint(1,10))
# 		for i in range(1,hpoints+1):
# 			z = 1./i
# 			spacing = 1./vpoints[i-1]
# 			for j in range(vpoints[i-1]):
# 				vertices.extend([uniform(0,0.2),1-uniform(j*spacing,(j+1)*spacing),z])
		
		for i in range(slices-1):
			for j in range(slices-1):
# 				slices = vpoints[i]
				p = i*slices + j # можно вставить туда.
				indices.extend([i*slices+j, (i+1)*slices+j, (i+1)*slices+j+1])
				indices.extend([i*slices+j, (i+1)*slices+j+1, i*slices+j+1])
		
# 		n = [-1,0,0]*(len(vertices)//3)
		
		v = np.array(vertices)
		v = v*side
		self.batch.add_indexed(len(vertices)//3,GL_TRIANGLES,None,indices,('v3f',v),('n3f',normals))
	
	def on_key_press(self,symbol,modifier):
		"""
		Немного запутанное вычисление координат игрок (и движений мира в glTranslatef,
		соответствтенно) из-за наличия стрейфа, иначе можно было бы по две строчки
		в w/s вставить и готово. Объяснять их принцип проще на бумажке и с картинками.
		"""
			# Управление зелёным прямоугольником
		if symbol == key._1 and keystate[key.V]:
			self.enemy.xpos += 0.1
		if symbol == key._2 and keystate[key.V]:
			self.enemy.ypos += 0.1
		if symbol == key._3 and keystate[key.V]:
			self.enemy.zpos += 0.1
		if symbol == key._1 and keystate[key.C]:
			self.enemy.xpos -= 0.1
		if symbol == key._2 and keystate[key.C]:
			self.enemy.ypos -= 0.1
		if symbol == key._3 and keystate[key.C]:
			self.enemy.zpos -= 0.1
		if symbol == key.R and modifier == key.MOD_SHIFT:
			# рестарт игрока и зелёного прямоугольника
			self.player.xpos = self.player.ypos = self.player.zpos = 0
			self.player.xp = self.player.yp = self.player.zp = 0
			self.player.xstrafe = self.player.ystrafe = self.player.zstrafe = 0
			self.enemy.ypos = self.enemy.zpos = 0
			self.player.xrot = self.player.yrot = self.player.zrot = 0
			self.enemy.xpos = -3
		if modifier == key.MOD_CTRL or symbol == 65507:
			# приседание
			self.player.ypos -= self.player.speed
		if symbol == key.SPACE:
			self.player.ypos += self.player.speed
		if symbol == key.RETURN:
			# фуллскрин
			keystate[symbol] = False
			self.set_fullscreen(self.fullscreen^True)
			self.set_mouse_visible(self.visible^True)
			self.picspr.x, self.picspr.y = self.width//2, self.height//2
		if symbol == key.Y and modifier == key.MOD_SHIFT:
# 			loop = asyncio.get_event_loop()
# 			thr = Thread(target=loop.run_forever,args=())
# 			thr.setDaemon(True)
# 			thr.start()
			print("R1: ",self.r1)
# 			print(self.r2)
			print("EDX: ",len(self.edx))
			pass
		if symbol == key.T and not modifier:
			self.time2 = time.time()
			keystate[symbol] = False
# 			for i in range(1):
# 				thr = Thread(target=self.compute,args=(1,self.time2))
# 				thr.setDaemon(True)
# 				thr.start()
# 			self.compute()
# 			asyncio.async(self.compute())
# 			loop.run_forever()
			q = Queue()
			for i in range(1):
				p = Process(target=self.compute,args=(1,self.time2))
				p.start()
# 			def test():
# 				self.r1 = q.get()
# 				self.r2 = q.get()
# 				self.r3 = q.get()
# 				self.r4 = q.get()
# 			thr = Thread(target=test,args=())
# 			thr.start()
# 			r1 = q.get()
# 			r2 = q.get()
# 			self.r1 = r1
# 			self.r2 = r2
			pass
		if symbol == key.G and modifier == key.MOD_SHIFT:	
			keystate[symbol] = False
# 			self.generate_lines()
			self.generate_wall()
			pass
		if symbol == key.ESCAPE:
			keystate[symbol] = False
			self.close()
		if symbol == key.R:
			# Взгляд вверх
			self.player.xrot -= 2
		if symbol == key.F:
			# Вниз. Мышкой можно.
			self.player.xrot += 2		
		if symbol == key.E:
			# Поворот вправо. Мышкой можно.
			self.player.yrot += 3
		if symbol == key.Q:
			# Поворот влево. Мышкой можно.
			self.player.yrot -= 3
		if symbol == key.D:
			# Стрейф вправо. Независимо от направления камеры, будет всегда "идти" вправо.
			self.object_collision(90)
			self.player.xstrafe += np.sin((90-self.player.yrot)*np.pi/180)*self.player.speed
			self.player.zstrafe -= np.cos((90-self.player.yrot)*np.pi/180)*self.player.speed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.A:
			# Влево. Независимо от направления камеры, будет всегда "идти" влево.
			self.object_collision(270)
			self.player.xstrafe -= np.sin((90-self.player.yrot)*np.pi/180)*self.player.speed
			self.player.zstrafe += np.cos((90-self.player.yrot)*np.pi/180)*self.player.speed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.W:
			# Движение прямо. Независимо от направления камеры, будет всегда "идти" вперёд.
			self.object_collision(0)
			self.player.zp += np.cos(self.player.yrot*np.pi/180)*self.player.speed
			self.player.xp += np.sin(self.player.yrot*np.pi/180)*self.player.speed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.S:
			# Движение назад. Независимо от направления камеры, будет всегда "идти" назад.
			self.object_collision(180)
			self.player.zp -= np.cos(self.player.yrot*np.pi/180)*self.player.speed
			self.player.xp -= np.sin(self.player.yrot*np.pi/180)*self.player.speed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe

class Sphere(object):
	"""
	Сфера
	"""
	list = None
	def __init__(self, radius, slices, batch, group=None):
		r = radius
		vertices = []
		indices = []
		normals = []
		step = (2 * pi) / (slices)
		
		for i in range(0,slices+1):
			for j in range(0,slices):
				vertices.extend([r*sin(step*j)*cos(step*i), r*cos(step*j), sin(step*i)*r*sin(step*j)]) 
				normals.extend([sin(step*j)*cos(step*i), cos(step*j), sin(step*i)*sin(step*j)]) 

		for i in range(slices+1):
			for j in range(slices):
				p = i*slices + j # можно вставить туда.
				indices.extend([i*slices+j, (i+1)*slices+j, (i+1)*slices+j+1])
				indices.extend([i*slices+j, (i+1)*slices+j+1, i*slices+j+1])

		print(str(len(vertices)/3)+" Vertices and "+str(len(indices)/3)+" Indices")
	
		self.vertex_list = batch.add_indexed(len(vertices)//3, GL_TRIANGLES, group, indices,
											 ('v3f/static', vertices),
											 ('n3f/static', normals))

	def delete(self):
		self.vertex_list.delete()

class PathGenerator(object):
	def __init__(self, size, width, length, max_trees):
		LINEF = np.array([[0,0,0], [0,0,-1]])
		LINER = np.array([[0,0,0], [1,0,0]])
		LINEB = np.array([[0,0,0], [0,0,1]])
		LINEL = np.array([[0,0,0], [-1,0,0]])
		TJUNCFB = np.array([[0,0,0], [0,0,-2], [0,0,-1], [1,0,-1]])
		TJUNCRL = np.array([[0,0,0], [2,0,0], [1,0,0], [1,0,1]])
		CROSSROAD = np.array([[0,0,0], [0,0,-2], [-1,0,-1], [1,0,-1]])
	
		self.ends = [[0,0,0,1]]
	
		vertices = []
	
		finished = False
	
		while len(self.ends)<max_trees:
			for j in range(len(self.ends)):
				if random()>0.5:
					if self.ends[j][3]==1:
						print("here")
						vertices.extend(np.add(LINEF[0],self.ends[j][:3]))
						vertices.extend(np.add(LINEF[1],self.ends[j][:3]))
					elif self.ends[j][3]==0.5:
						vertices.extend(np.add(LINER[0],self.ends[j][:3]))
						vertices.extend(np.add(LINER[1],self.ends[j][:3]))
					elif self.ends[j][3]==-0.5:
						vertices.extend(np.add(LINEL[0],self.ends[j][:3]))
						vertices.extend(np.add(LINEL[1],self.ends[j][:3]))
					self.ends[j][:3] = vertices[-3:]
				elif random()>0.5:
					if random()>0.5:
# 						print(self.ends[j])
						d = randint(-1,1)*2+1
						vertices.extend(np.add(TJUNCFB[0]*d,self.ends[j][:3]))
						vertices.extend(np.add(TJUNCFB[1]*d,self.ends[j][:3]))
						vertices.extend(np.add(TJUNCFB[2]*d,self.ends[j][:3]))
						vertices.extend(np.add(TJUNCFB[3]*d,self.ends[j][:3]))
						self.ends[j] = vertices[-9:-6]+[1]
						self.ends.append(vertices[-3:]+[0.5*d])
# 						print(self.ends[j])
						
					
		print(self.ends)
		self.vertices = vertices


i = 0
time1 = time.time()
	
player = Player()
world = World(player)
keystate = key.KeyStateHandler()
world.push_handlers(keystate)
# world.set_fullscreen(True)
# world.set_mouse_visible(False)
pyglet.app.run()