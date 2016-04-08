#!/usr/bin/env python3
#  - * -  coding: UTF - 8  - * - 

import pyglet
from pyglet.gl import *
from pyglet.window import *
from obj import OBJ

import numpy as np
from math import copysign, sin, cos, pi, radians
from random import random, randint, uniform

import socket
from threading import Thread
from multiprocessing import Process, Queue
import asyncio

import ctypes
import time
import sys
import os

import pickle
import gzip

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
		self.ypos = -19.
		self.zpos = 0.
		
		self.xrot = 0.
		self.yrot = 90.
		self.zrot = 0.
		
		self.xstrafe = 0.
		self.ystrafe = 0.
		self.zstrafe = 0.
	
		self.xp = 0.
		self.yp = 0.
		self.zp = 0.
		
		self.height = 2
		self.stepheight = 1.
		self.speed = 10
		
		self.jumping = "walk"
		self.gravity = 10
		self.jumpheight = 0.2*self.gravity
		self.jumppoint = 0
		
	def sight_vector(self):
		v = cos(radians(self.xrot))
		x = sin(radians(self.yrot))*v
		y = -sin(radians(self.xrot))
		z = -cos(radians(self.yrot))*v
		self.sight_v = (x,y,z)
		self.sight_vtxt = "XVec: "+str(np.round(x,3))+" YVec: "+str(np.round(y,3))+" ZVec: "+str(np.round(z,3))
		
class Cubecol(object):
	"""
	Простой куб. 16 точек - чтобы текстуры можно было лепить (каждый вертекс может иметь
	лишь одну координату картинки, поэтому приходится дублировать. Впрочем, тут 
	текстур никаких нет, лол.
	inside/outside — какая из сторону куба является "лицевой" — то есть, рисуемой при
	включённом GL_CULL_FACE. (Комната или ящик, например.)
	"""
	def __init__(self, side, batch, offset=(0,0,0), center = True, type = 'outside', group = None):
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

class Cubesel(object):
	"""
	Простой куб. 16 точек - чтобы текстуры можно было лепить (каждый вертекс может иметь
	лишь одну координату картинки, поэтому приходится дублировать. Впрочем, тут 
	текстур никаких нет, лол.
	inside/outside — какая из сторону куба является "лицевой" — то есть, рисуемой при
	включённом GL_CULL_FACE. (Комната или ящик, например.)
	"""
	def __init__(self, size = 'small', colour = 'red', offset=(0,0,0), center = True, group = None, sizeint = False, colint = False):
		self.batch = pyglet.graphics.Batch()
		
		colours = {'red': (1,0,0,0),
				'green': (0,1,0,0),
				'blue': (0,0,1,0)
								}
		sizes = {'small': 1,
				'medium': 2,
				'large': 3
				}
		
		self.txtcolour = colour
		self.txtsize = size
		colour = colours[colour]
		self.colour = vec(*colour)
		side = sizes[size]
		self.side = side
	
	
		vertices = np.array([	1,0,0, 0,0,0, 1,1,0, 0,1,0, 1,1,1, 0,1,1, 1,0,1, 0,0,1,
								1,1,0, 1,1,1, 1,0,0, 1,0,1, 0,0,0, 0,0,1, 0,1,0, 0,1,1,
							])
		if center:
			vertices = vertices-np.tile(np.array((0.5,0,0.5)),len(vertices)/3)
		
		vertices = vertices.astype(float)
		
		vertices = vertices*side
	
		indices = 	[	0,1,2, 2,1,3, 2,3,4, 4,3,5, 4,5,6, 6,5,7, 
						8,9,10, 10,9,11, 10,11,12, 12,11,13, 12,13,14, 14,13,15,
					]

		self.vertex_list = self.batch.add_indexed(16, GL_TRIANGLES, group, indices, 
											('v3f',vertices))
		
		self.coords(vertices,offset,side)
		self.collision_box()
		print("X %s, Y %s, Z %s" % (self.x, self.y, self.z))
		print("xleft %s, xright %s" % (self.xleft, self.xright))
		print("ybot %s, ytop %s" % (self.ybot, self.ytop))
		print("zback %s, zfront %s" % (self.zback, self.zfront))
	
	def delete_v(self):
		self.vertex_list.delete()
	
	def coords(self,vertices,offset,side):
		self.x = (vertices[0]+vertices[3])/2. + offset[0]
		self.y = offset[1]
		self.z = (vertices[2]+vertices[-1])/2. + offset[2]
		self.xside = side
		self.yside = side
		self.zside = side
	
	def collision_box(self):
		"""
		Координаты расположения плоскостей сторон. Для проверки на столкновение нужно.
		"""
		self.zback = self.z - self.zside/2.
		self.zfront = self.z + self.zside/2.
		self.ybot = self.y
		self.ytop = self.y + self.yside
		self.xleft = self.x - self.xside/2.
		self.xright = self.x + self.xside/2.
	
	def move(self,x,y,z):
		self.x += x
		self.y += y
		self.z += z
		self.collision_box()
		
	def draw(self):
		self.batch.draw()

class Cubes(object):
	def __init__(self):
		self.objects = []

	def append(self,object):
		self.objects.append(object)
	
	def draw(self):
		for object in self.objects:
			glTranslatef(object.x,object.y,object.z)
			glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, object.colour)
			object.draw()
			glTranslatef(-object.x,-object.y,-object.z)

class World(Window):
	def __init__(self,player):
		"""
		Всё стандартно. Два батча — мир и коробки, для разных материалов.
		Игрок, вызывается функция создания коробочек.
		"""
		config = Config(sample_buffers=1, samples=1, 
						depth_size=16, double_buffer=True)
		try:
			super(World, self).__init__(config=config, resizable=True, fullscreen=False, vsync=False,width=1000,height=600)
		except:
			super(World, self).__init__(resizable=True, fullscreen=False, vsync=True)
		self.noground = False
		self.player = player
		self.fps = pyglet.clock.ClockDisplay()
		self.graphics_batches()
		self.make_cubes()
		self.textures_and_text()
		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.register_event_type('on_key_press_my')
		self.robot_fr = 0
		self.time = 0#time.time()
		self.iter = 0
		self.itertime = 0

	def graphics_batches(self):
		self.batch = pyglet.graphics.Batch()
		self.batch_box = pyglet.graphics.Batch()
		self.batch_ray = pyglet.graphics.Batch()
	
	def textures_and_text(self):
		self.coords = pyglet.text.Label(text="",x=10)
		self.rot = pyglet.text.Label(text="",x=10)
		self.times = pyglet.text.Label(text="",x=10)
		self.pljfw = pyglet.text.Label(text="",x=10)
		self.sight_vector = pyglet.text.Label(text = "",x=10)
		self.looking_at = pyglet.text.Label(text="",x=10)
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
			# sight_selection labels
		self.cubesight = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 10,anchor_x='right')
		self.det = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 30,anchor_x='right')
		self.alpha = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 50,anchor_x='right')
		self.beta = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 70,anchor_x='right')
		self.det_ = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 90,anchor_x='right')
		self.alpha_ = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 110,anchor_x='right')
		self.beta_ = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 130,anchor_x='right')
		self.timesight = pyglet.text.Label(text="",x=self.width - 10,y = self.height - 150,anchor_x='right')
		self.sightlabels = [self.cubesight, self.det, self.alpha, self.beta, self.det_, self.alpha_, self.beta_, self.timesight]

	def make_cubes(self):
		"""
		Создаётся несколько ящиков с разными сдвигами от начала координат
		и заносит их в список объектов.
		"""
# 		self.cubes = []
		self.box = Cubecol(40,self.batch_box,center = True, type = "inside")
		self.cubes = []
		self.objs = Cubes()
# 		for i in range(5):
		self.cube = Cubesel('small', 'red',offset = (-3,-20,0), center = True)
		self.cubes.append(self.cube)
		self.objs.append(self.cube)
		self.cube = Cubesel('medium','green',offset = (1,-20,0), center = True)
		self.cubes.append(self.cube)
		self.objs.append(self.cube)
		for i in range(1):
			self.cube = Cubesel('large','blue',offset = (5,-20,0), center = True)
			self.cubes.append(self.cube)
		self.objs.append(self.cube)

	def update(self, dt):
		"""
		Проверяет, какие из кнопок нажаты, и вызывает соответствующую команду.
		Чтобы можно было ходить при зажатых клавишах, а не тыкать по сто раз.
		"""
		for key in keystate:
			if keystate[key]:
				self.dispatch_event('on_key_press_my',key,False,dt)
		if keystate[65507]:
			self.dispatch_event('on_key_press_my',65507,False,dt)
		self.ground_collision(self.player,dt)
# 		self.dispatch_event('on_key_press',pyglet.window.key.T,False)
		self.time += dt
		self.on_draw1()
		
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
		glDepthFunc(GL_ALWAYS)		# функция depth_test'а. Рисует только если ближе к экрану.
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)		# Сглаживание больших поверхностей, имеющих мало 
									# вершин. GL_FLAT покажет все треугольники.
# 		glEnable(GL_CULL_FACE)		
			# Освещение
		l = True
		if l:
			glEnable(GL_LIGHTING)
			glEnable(GL_LIGHT0)
			glEnable(GL_LIGHT1)
			glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 5, 0, 1))
			glLightfv(GL_LIGHT0, GL_AMBIENT, vec(1,1,1,0))
			glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, vec(0))
			glLightfv(GL_LIGHT1, GL_AMBIENT, vec(1,1,1,0))
			glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(1,1,1,0))
			glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1,1,1,0))
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

	def ground_collision(self,player,dt):
		ypos = float(self.box.ybot)
		yposstep = 10
		for cube in self.cubes:
			if (cube.zback <= -player.zpos < cube.zfront and 
					cube.xleft <= player.xpos < cube.xright):
				if cube.ytop <= player.ypos:
					ypos = float(cube.ytop)
				if cube.ytop - player.stepheight <= player.ypos:
					yposstep = float(cube.ytop)
		if player.jumping == "jump":
			height = player.ypos - player.jumppoint
			sp = height/player.jumpheight
			sp = np.cos(sp*np.pi/2)
			if sp > 0.25:
				player.ypos += player.gravity*dt*sp
			else:
				player.jumppoint = player.ypos
				player.jumping = "fall"
		elif player.jumping == "fall":
			if player.ypos > ypos:
				distance = abs(player.ypos - (player.jumppoint+0.5))
				sp = min(distance/3,1)
				sp = np.sin(sp*np.pi/2)
				player.ypos -= player.gravity*dt*sp
				if player.ypos < ypos:
					player.ypos = ypos
					player.jumping = "walk"
					player.stepheight = player.height/2.
		elif self.player.jumping == "walk":
			if player.stepheight >= abs(yposstep-player.ypos):
				player.ypos = yposstep
			elif player.ypos > ypos:
				player.jumping = "fall"
				player.jumppoint = player.ypos		
	
	def object_collision(self,wsad):
		rot = (np.cos((self.player.yrot+wsad)*np.pi/180),np.sin((self.player.yrot+wsad)*np.pi/180))
		## North-East
		if rot[0]>=0 and rot[1]>=0:
			## Map limit
			if -self.player.zpos < self.box.zback + 0.4:
				self.player.zspeed = 0
				return
			if self.player.xpos > self.box.xright - 0.4:
				self.player.xspeed = 0
				return
			for cube in self.cubes:
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.xleft <= self.player.xpos <= cube.xright and 
						cube.zfront < -self.player.zpos < cube.zfront + 0.4):
					self.player.zspeed = 0
					return
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.zback <= -self.player.zpos <= cube.zfront and 
						cube.xleft - 0.4 < self.player.xpos < cube.xleft):
					self.player.xspeed = 0
					return
		## North-West
		if rot[0]>=0 and rot[1]<0:
			## Map limit
			if -self.player.zpos < self.box.zback + 0.4:
				self.player.zspeed = 0
				return
			if self.player.xpos < self.box.xleft + 0.4:
				self.player.xspeed = 0
				return
			for cube in self.cubes:
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.xleft <= self.player.xpos <= cube.xright and 
						cube.zfront < -self.player.zpos < cube.zfront + 0.4):
					self.player.zspeed = 0
					return
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.zback <= -self.player.zpos <= cube.zfront and 
						cube.xright + 0.4 > self.player.xpos > cube.xright):
					self.player.xspeed = 0
					return
		## South-West
		if rot[0]<0 and rot[1]<0:
			## Map limit
			if -self.player.zpos > self.box.zfront - 0.4:
				self.player.zspeed = 0
				return
			if self.player.xpos < self.box.xleft + 0.4:
				self.player.xspeed = 0
				return
			for cube in self.cubes:
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.xleft <= self.player.xpos <= cube.xright and 
						cube.zback - 0.4 < -self.player.zpos < cube.zback):
					self.player.zspeed = 0
					return
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.zback <= -self.player.zpos <= cube.zfront and 
						cube.xright + 0.4 > self.player.xpos > cube.xright):
					self.player.xspeed = 0
					return
		## South-East
		if rot[0]<0 and rot[1]>=0:
			## Map limit
			if -self.player.zpos > self.box.zfront - 0.4:
				self.player.zspeed = 0
				return
			if self.player.xpos > self.box.xright - 0.4:
				self.player.xspeed = 0
				return
			for cube in self.cubes:
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.xleft <= self.player.xpos <= cube.xright and 
						cube.zback - 0.4 < -self.player.zpos < cube.zback):
					self.player.zspeed = 0
					return
				if (cube.ybot - self.player.height <= self.player.ypos < cube.ytop - self.player.stepheight and
						cube.zback <= -self.player.zpos <= cube.zfront and 
						cube.xleft - 0.4 < self.player.xpos < cube.xleft):
					self.player.xspeed = 0
					return
		self.player.xspeed = self.player.zspeed = 5
		return
	
	def sight_object(self):
		# Schlick and Subrenat ray-quadrilateral intersection algorithm. (Ares Lagae & Philip Dutre implementation)
		# http://people.cs.kuleuven.be/~ares.lagae/publications/LD05ERQIT/LD05ERQIT.pdf
		self.batch_ray = pyglet.graphics.Batch()
		cubecol, cubesize = None, None
		O = np.array([self.player.xpos, self.player.ypos+self.player.height*0.99, -self.player.zpos])
		self.player.sight_vector()
		D = np.array(self.player.sight_v)
		RAY = np.concatenate((O,(O+D*5)))
		self.batch_ray.add(2,GL_LINES,None,('v3f',RAY))
# 		t1 = time.time()
# 		self.det.text, self.alpha.text, self.beta.text = "NA", "NA", "NA"
# 		self.det_.text, self.alpha_.text, self.beta_.text = "NA", "NA", "NA"
		t1 = time.time()
		self.batch = pyglet.graphics.Batch()
		for cube in self.cubes:
			if np.sqrt((cube.x - self.player.xpos)**2 + (cube.y - (self.player.ypos+self.player.height))**2 + (cube.z - self.player.zpos)**2) > 5*cube.side: continue
			self.cubesight.text = cube.txtsize+" "+cube.txtcolour
				# Вместо трёх сторн, будет две диагонали куба. В засимости от расположения
				# игрока относитель объекта, выбирается нужная (угол к которой 45-90 градусов)
			if (self.player.xpos - cube.x)*(self.player.zpos - cube.z)>0:
				V00 = np.array([cube.xleft,cube.ybot,cube.zback])
				V01 = np.array([cube.xright,cube.ybot,cube.zfront])
				V10 = np.array([cube.xleft,cube.ytop,cube.zback])
				V11 = np.array([cube.xright,cube.ytop,cube.zfront])
			else:
				V00 = np.array([cube.xleft,cube.ybot,cube.zfront])
				V01 = np.array([cube.xright,cube.ybot,cube.zback])
				V10 = np.array([cube.xleft,cube.ytop,cube.zfront])
				V11 = np.array([cube.xright,cube.ytop,cube.zback])
			VERTS = np.concatenate((V00,V10,V01,V11))
			self.verts_list = self.batch.add_indexed(4, GL_TRIANGLES, None, (0,1,2,1,3,2),('v3f',VERTS))
			# Reject rays using the barycentric coordinates of the 
			# intersection point with respect to T
			E01 = V10 - V00
			E03 = V01 - V00
			P = np.cross(D,E03)
			det = np.dot(E01,P)
			self.det.text = str(np.round(det,3))
			if abs(det) < 10**-6: continue
			T = O - V00
			alpha = np.dot(T,P)/det
			self.alpha.text = str(np.round(alpha,3))
			if not 0 < alpha < 1: continue
			Q = np.cross(T,E01)
			beta = np.dot(Q,D)/det
			self.beta.text = str(np.round(beta,3))
			if not 0 < beta < 1: continue

			# Reject rays using the barycentric coordinates of the 
			# intersection point with respect to T_
			if alpha+beta > 1:
				E23 = V01 - V11
				E21 = V10 - V11
				P_ = np.cross(D,E21)
				det_ = np.dot(E23, P_)
# 				self.det_.text = str(np.round(det_,3))
				if abs(det_) < 10**-6: continue
				T_ = O - V11
				alpha_ = np.dot(T_,P_)/det_
# 				self.alpha_.text = str(np.round(alpha_,3))
				if alpha_ < 0: continue
				Q_ = np.cross(T_,E23)
				beta_ = np.dot(D,Q_)/det_
# 				self.beta_.text = str(np.round(beta_,3))
				if beta_ < 0: continue

			cubecol = cube.txtcolour
			cubesize = cube.txtsize
			break
		self.iter +=1
		self.itertime += time.time() - t1
		if self.iter%30 == 0:
			self.timesight.text = str(self.itertime)
			self.iter = 0
			self.itertime = 0
		return cubecol, cubesize
		pass
	
	def reposition_labels(self):
		i = 0
		for label in self.sightlabels:
			label.x = self.width - 10
			label.y = self.height - 10 - i*20
			i+=1
	
	def on_draw1(self):
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
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,1,1,0))
		glPointSize(20)
# 		glColor3f(0.5,0,0.2)
# 		self.batch.draw()
# 		glColor3f(0,0,0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(self.boxtexture.target,self.boxtexture.id)
		self.batch_box.draw()
		glDisable(GL_TEXTURE_2D)
		self.objs.draw()
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0.3,0,0))
		self.batch.draw()
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(1,0,1,0))
		glColor3f(1,0.5,0)
		self.batch_ray.draw()
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0,0,0))
		self.setup2d()
			# лейблы с координатами. Округлено до трёх знаков после запятой, всё в одну строку чтобы показывалось.
		pltxt = "X: "+str(np.round(self.player.xpos,3))+" Y: "+str(np.round(self.player.ypos,3))+" Z: "+str(np.round(self.player.zpos,3))
		self.coords.text = pltxt
		self.coords.y = self.height-30
		plrottxt = "Xrot: "+str(np.round(self.player.xrot,3))+" Yrot: "+str(np.round(self.player.yrot,3))+" Zrot: "+str(np.round(self.player.zrot,3))
		self.rot.text = plrottxt
		self.rot.y = self.height-50
		self.player.sight_vector()
		self.sight_vector.text = self.player.sight_vtxt
		self.sight_vector.y = self.height-70
		self.looking_at.y = self.height-90
		self.pljfw.text = self.player.jumping
		self.pljfw.y = self.height-110
		self.times.text = str(np.round(self.time,3))
		self.times.y = self.height-130
		self.looking_at.draw()
		self.times.draw()
		self.pljfw.draw()
		self.sight_vector.draw()
		self.coords.draw()
		self.rot.draw()
		self.fps.draw()
		self.picspr.draw()
			# sight selection
		self.det.draw()
		self.alpha.draw()
		self.beta.draw()
		self.det_.draw()
		self.alpha_.draw()
		self.beta_.draw()
		self.cubesight.draw()
		self.timesight.draw()

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

	def on_key_press(self,symbol,modifier):
		if symbol == key._1 and keystate[key.V]:
			model.stepsize += 0.1
		if symbol == key._2 and keystate[key.V]:
			model.y += 0.5
		if symbol == key._3 and keystate[key.V]:
			self.enemy.zpos += 0.1
		if symbol == key._1 and keystate[key.C]:
			model.stepsize -= 0.1
		if symbol == key._2 and keystate[key.C]:
			model.y -= 0.5
		if symbol == key._3 and keystate[key.C]:
			self.enemy.zpos -= 0.1
		if symbol == key.T:
			keystate[key.T] = False
			col, size = self.sight_object()
			if col and size:
				self.looking_at.text = "You are looking at the "+size+" "+col+" cube."
			else:
				self.looking_at.text = ""
		if symbol == key.R and modifier == key.MOD_SHIFT:
			# рестарт игрока и зелёного прямоугольника
			self.player.xpos = self.player.ypos = self.player.zpos = 0.
			self.ypos = -30.
			self.player.xp = self.player.yp = self.player.zp = 0.
			self.yp = -30.
			self.player.xstrafe = self.player.ystrafe = self.player.zstrafe = 0.
			self.player.xrot = self.player.yrot = self.player.zrot = 0.
			self.player.yrot = 90.
			self.time = 1.
			self.player.jumping = "walk"
			self.dispatch_event('on_key_press',key.E,key.MOD_SHIFT,dt)
		if symbol == key.E and modifier == key.MOD_SHIFT:
			keystate[key.E] = False
			model.x=15
			model.y=-20
			model.roty=270
			model.frame = 0
			model.action = 'walk'
			model.animate = True
			return
		if symbol == key.A and modifier == key.MOD_SHIFT:
			keystate[key.A] = False
			model.animate = True^model.animate
		if symbol == key.F and modifier == key.MOD_SHIFT:
			keystate[key.F] = False
			model.frame += 1
			if model.frame == model.framesTOTAL:
				model.x -= model.stepsize
				model.frame = 0
			return
		if modifier == key.MOD_CTRL or symbol == 65507:
			# приседание
			self.player.height = 1
		if symbol == key.ESCAPE:
			keystate[symbol] = False
			self.close()
		if symbol == key.RETURN:
			# фуллскрин
			keystate[symbol] = False
			self.set_fullscreen(self.fullscreen^True)
			self.set_mouse_visible(self.visible^True)
			self.picspr.x, self.picspr.y = self.width//2, self.height//2
			self.reposition_labels()

	def compute(self):
		pass		

	def on_key_press_my(self,symbol,modifier,dt):
		"""
		Немного запутанное вычисление координат игрок (и движений мира в glTranslatef,
		соответствтенно) из-за наличия стрейфа, иначе можно было бы по две строчки
		в w/s вставить и готово. Объяснять их принцип проще на бумажке и с картинками.
		"""
		if symbol == key.R and modifier == key.MOD_SHIFT:
			# рестарт игрока и зелёного прямоугольника
			self.player.xpos = self.player.ypos = self.player.zpos = 0
			self.player.xp = self.player.yp = self.player.zp = 0
			self.player.xstrafe = self.player.ystrafe = self.player.zstrafe = 0
			self.player.xrot = self.player.yrot = self.player.zrot = 0
		if modifier == key.MOD_CTRL or symbol == 65507:
			# приседание
# 			self.player.ypos -= self.player.speed*dt
			self.player.height = 1
		if symbol == key.SPACE and self.player.jumping == "walk":
# 			self.player.ypos += self.player.speed
# 			self.jump(dt)
			keystate[key.SPACE] = False
			self.player.jumping = "jump"
			self.player.jumppoint = self.player.ypos
			self.player.stepheight = 0
			pass
		if symbol == key.T:
# 			q = Queue()
# 			p1 = Process(target=self.compute,args=())
# 			p1.start()
			pass
		if symbol == key.RETURN:
			# фуллскрин
			keystate[symbol] = False
			self.set_fullscreen(self.fullscreen^True)
			self.set_mouse_visible(self.visible^True)
			self.picspr.x, self.picspr.y = self.width//2, self.height//2
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
			self.player.xstrafe += np.sin((90-self.player.yrot)*np.pi/180)*self.player.xspeed*dt
			self.player.zstrafe -= np.cos((90-self.player.yrot)*np.pi/180)*self.player.zspeed*dt
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.A:
			# Влево. Независимо от направления камеры, будет всегда "идти" влево.
			self.object_collision(270)
			self.player.xstrafe -= np.sin((90-self.player.yrot)*np.pi/180)*self.player.xspeed*dt
			self.player.zstrafe += np.cos((90-self.player.yrot)*np.pi/180)*self.player.zspeed*dt
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.W:
			# Движение прямо. Независимо от направления камеры, будет всегда "идти" вперёд.
			self.object_collision(0)
			self.player.zp += np.cos(self.player.yrot*np.pi/180)*self.player.zspeed*dt
			self.player.xp += np.sin(self.player.yrot*np.pi/180)*self.player.xspeed*dt
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.S:
			# Движение назад. Независимо от направления камеры, будет всегда "идти" назад.
			self.object_collision(180)
			self.player.zp -= np.cos(self.player.yrot*np.pi/180)*self.player.zspeed*dt
			self.player.xp -= np.sin(self.player.yrot*np.pi/180)*self.player.xspeed*dt
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe

i = 0
	
player = Player()
world = World(player)
keystate = key.KeyStateHandler()
world.push_handlers(keystate)
world.set_fullscreen(False)
world.set_mouse_visible(False)
pyglet.app.run()