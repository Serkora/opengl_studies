#!/usr/bin/env python3
#  - * -  coding: UTF - 8  - * - 

import pyglet
from pyglet.gl import *
from pyglet.window import *
import numpy as np
from math import copysign

import socket
from threading import Thread

from random import random

import ctypes

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
		self.xspeed = self.zspeed = 0.1
		
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
								1,1,0, 0,1,0, 1,1,1, 0,1,1
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
 							16,16,16, 17,17,17, 18,18,18, 19,19,19
						]
		elif type == "inside":
			indices = 	[	0,2,1, 2,3,1, 2,4,3, 4,5,3, 4,6,5, 6,7,5, 
							8,10,9, 10,11,9, 10,12,11, 12,13,11, 12,14,13, 14,15,13,	
 							16,16,16, 17,17,17, 18,18,18, 19,19,19
						]
			norm = norm*-1
	
		print(len(norm),len(vertices))

		textcoord = [.25,.75, 0,.75, .25,.5, 0,.5, .25,.25, 0,.25, .25,0, 0,0, 0,0,0,0]*2
		
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

		self.vertex_list = batch.add_indexed(20, GL_TRIANGLES, group, indices, 
											('v3f',vertices),('n3f',norm),('t2f',textcoord))#,('n3f',norm))
		
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

class Rekt(object):
	def __init__(self, side, batch):
		vertices = np.array([	.25,1.5,.25, .25,1.5,-.25, -.25,1.5,.25, -.25,1.5, -.25,
								.25,-1.5,.25, .25,-1.5,-.25, -.25,-1.5,.25, -.25,-1.5 -.25, ])
		
		vertices = np.array([	.25,4,.25, .25,4,-.25, -.25,4,.25, -.25,4,-.25,
								.25,0,.25, .25,0,-.25, -.25,0,.25, -.25,0,-.25, ])

		
		vertices = vertices * side

		indices = [ 0,2,1, 1,2,3, 1,3,5, 5,3,7, 5,7,4, 4,7,6, 0,1,4, 4,1,5, 3,2,7, 7,2,6, 2,0,6, 6,0,4]
		
		self.vertex_list = batch.add_indexed(8, GL_TRIANGLES, None, indices, ('v3f',vertices))

		self.xpos = -3
		self.ypos = 0
		self.zpos = 0
		
		self.height = 4*side
		self.stepheight = 2*side
		

class World(Window):
	def __init__(self,player):
		"""
		Всё стандартно. Два батча — мир и коробки, для разных материалов.
		Игрок, вызывается функция создания коробочек.
		"""
		config = Config(sample_buffers=1, samples=4, 
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
		self.netstart()
		pyglet.clock.schedule_interval(self.update, 1.0 / 60) # чо-то не пашет, всё равно

	def graphics_batches(self):
		self.batch = pyglet.graphics.Batch()
		self.batch_box = pyglet.graphics.Batch()
		self.batch_enemy = pyglet.graphics.Batch()
		self.batchN = pyglet.graphics.Batch()
		self.batchE = pyglet.graphics.Batch()
		self.batchS = pyglet.graphics.Batch()
		self.batchW = pyglet.graphics.Batch()
	
	def textures_and_text(self):
		self.coords = pyglet.text.Label(text="",x=10)
		self.rot = pyglet.text.Label(text="",x=10)
		self.cubcor = pyglet.text.Label(text="",x=10)
		self.cubeimage = pyglet.image.load('DATA/bstone12.bmp')
		self.cubetexture = self.cubeimage.get_texture()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.cubetexture.width, self.cubetexture.height,
	    			0, GL_RGBA, GL_UNSIGNED_BYTE, self.cubetexture.get_image_data().get_data('RGBA',
					self.cubetexture.width * 4))
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
	
	def netstart(self):
		if len(sys.argv) > 1:
			if sys.argv[1] == "p1": 
				p1 = 8500
				self.p2 = 8400
			else: 
				p1 = 8400
				self.p2 = 8500
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.sock.bind(('0.0.0.0',p1))
			ThrListen = Thread(target=self.nw_listen, args=())
			ThrListen.setDaemon(True)
			ThrListen.start()	
	
	def nw_listen(self):
		global v1, v2, v3
		while True:
			msg, addr = self.sock.recvfrom(64)
			msg = msg.decode(ENC)
			msg = msg.split(" ")
			self.enemy.xpos = float(msg[0])
			self.enemy.ypos = float(msg[1])
			self.enemy.zpos = float(msg[2])
	
	def netsend(self):
		if len(sys.argv)>1:
			msg = str(self.player.xpos)+" "+str(self.player.ypos)+" "+str(self.player.zpos)
			msg = msg.encode(ENC)
			self.sock.sendto(msg,('127.0.0.1',self.p2))
	
	def make_cubes(self):
		"""
		Создаётся несколько ящиков с разными сдвигами от начала координат
		и заносит их в список объектов.
		"""
		self.cubes = []
		cube = Cubecol(4, self.batch, offset=(-0.5, -2, -0.25))
		self.cubes.append(cube)
		for i in range(1,4):
			cube = Cubecol(2,self.batch, offset=(-0.5,-i*0.5-4,-i-0.5))
			self.cubes.append(cube)
		self.box = Cubecol(20,self.batch_box,center = True, type = "inside")
		cube = Cubecol(2,self.batch,offset=(-4,-5,-3))
		self.cubes.append(cube)
		cube = Cubecol(2,self.batch,offset=(3,-5,-2))
		self.cubes.append(cube)
		cube = Cubecol(2,self.batch,offset=(4,-5,3))
		self.cubes.append(cube)
		cube = Cubecol(0.5,self.batch,offset=(0,-5,-5))
		self.cubes.append(cube)
		cube = Cubecol(0.5,self.batch,offset=(0,-5,5))
		self.cubes.append(cube)
		self.cubes.append(cube)
		cube = Cubecol(0.5,self.batch,offset=(-5,-5,0))
		self.cubes.append(cube)
		cube = Cubecol(0.5,self.batch,offset=(5,-5,0))
		self.enemy = Rekt(1,self.batch_enemy)
		cubeN = Cubecol(0.5,self.batchN,offset=(-4,-5,4))
		cubeE = Cubecol(0.5,self.batchE,offset=(4,-5,-4))
		cubeS = Cubecol(0.5,self.batchS,offset=(-4,-5,-4))
		cubeW = Cubecol(0.5,self.batchW,offset=(4,-5,4))
	
	def update(self, dt):
		"""
		Проверяет, какие из кнопок нажаты, и вызывает соответствующую команду.
		Чтобы можно было ходить при зажатых клавишах, а не тыкать по сто раз.
		"""
		for key in keystate:
			if keystate[key]:
				self.dispatch_event('on_key_press',key,False)
		
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
		glEnable(GL_CULL_FACE)		
			# Освещение
# 		glEnable(GL_LIGHTING)
# 		glEnable(GL_LIGHT0)
# 		glEnable(GL_LIGHT1)
# 		glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 5, 0, 1))
# 		glLightfv(GL_LIGHT0, GL_AMBIENT, vec(1,1,1,0))
# 		glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, vec(0))
# 		glLightfv(GL_LIGHT1, GL_AMBIENT, vec(1,1,1,0))
# 		glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(1,1,1,0))
# 		glLightfv(GL_LIGHT1, GL_LINEAR_ATTENUATION, vec(0.6))
	
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
		"""
		Проверят, стоит ли игрок на каком-нибудь из объектов.
		Если нет — высота становится высотой пола.
		"""
		for cube in self.cubes:
			if (cube.zback <= -player.zpos < cube.zfront and 
					cube.xleft <= player.xpos < cube.xright):
				if cube.ytop - player.stepheight <= player.ypos:
					player.ypos = float(cube.ytop)
					return
		player.ypos = float(self.box.ybot)
	
	def object_collision(self,wsad):
		"""
		Что-то я делаю неправильно.
		Если коротко, в зависимости от направления движения выбирает определённые стороны
		каждого кубика и проверяет, врезаюсь ли я в него. И не выхожу ли я за границы комнаты.
		По сути, 4 раза почти одно и то же повторяется, просто с разными знаками.
		wsad – дополнительный угол в зависимости от нажатой кнопки (в on_key_press,
		где эта функция и вызывается, стоит в аргументах). Потому что можно смотреть
		прямо, а идти вбок, в этом случае считается, будто ты смотришь в эту сторону.
		"""
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
		self.player.xspeed = self.player.zspeed = 0.3
		return
					
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
		if not self.noground:
			self.ground_collision(self.player)
			self.ground_collision(self.enemy)
# 		glLightfv(GL_LIGHT1, GL_POSITION, vec(0,1,0,1))
		glTranslatef(-self.player.xpos,-self.player.ypos-self.player.height,self.player.zpos)
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0,0,0))
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0.8,0,0.2,0))
		glEnable(GL_TEXTURE_2D)
		glBindTexture(self.cubetexture.target,self.cubetexture.id)
		self.batch.draw()
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0,0.4,0.5,0))
		glBindTexture(self.boxtexture.target,self.boxtexture.id)
		self.batch_box.draw()
		glDisable(GL_TEXTURE_2D)
		glTranslatef(self.enemy.xpos,self.enemy.ypos,-self.enemy.zpos)
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(1,1,1,0))
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0.3,0,0))
		glColor3f(0,1,0)
		self.batch_enemy.draw()
		self.setup2d()
			# лейблы с координатами. Округлено до трёх знаков после запятой, всё в одну строку чтобы показывалось.
		pltxt = "X: "+str(np.round(self.player.xpos,3))+" Y: "+str(np.round(self.player.ypos,3))+" Z: "+str(np.round(self.player.zpos,3))
		self.coords.text = pltxt
		self.coords.y = self.height-30
		plrottxt = "Xrot: "+str(np.round(self.player.xrot,3))+" Yrot: "+str(np.round(self.player.yrot,3))+" Zrot: "+str(np.round(self.player.zrot,3))
		self.rot.text = plrottxt
		self.rot.y = self.height-50
			# положение зелёного прямоугольника
		ctxt = "GeofX: "+str(np.round(self.enemy.xpos,3))+" GeofY: "+str(np.round(self.enemy.ypos,3))+" GeofZ: "+str(np.round(self.enemy.zpos,3))
		self.cubcor.text = ctxt
		self.cubcor.y = self.height-70
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0.9,0,0))
		self.cubcor.draw()
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,1,1,0))
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
		if modifier == key.MOD_CTRL:
			# приседание
			self.player.height = 0.5
		if symbol == key.RETURN:
			# фуллскрин
			keystate[symbol] = False
			self.set_fullscreen(self.fullscreen^True)
			self.set_mouse_visible(self.visible^True)
			self.picspr.x, self.picspr.y = self.width//2, self.height//2
		if symbol == key.T:
			keystate[symbol] = False
			def scrn(title):
				gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 1.0)  # don't transfer alpha channel
				image = pyglet.image.ColorBufferImage(0, 0, self.width, self.height)
				image.save('BOXTEST'+title+'.png')
				gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 0.0)  # restore alpha channel transfer
			scrn('start')
			self.player.xrot = 60
			self.on_draw()
			scrn('down')
			self.player.xrot = 0
			self.player.yrot = 70
			self.on_draw()
			scrn('right')
			self.player.xrot = 60
			self.on_draw()
			scrn('rightdown')
			self.player.xrot = 0
			self.player.xpos = -10
			self.player.zpos = -5
			self.on_draw()
			scrn('bottom')
			self.player.xrot = -30
			self.on_draw()
			scrn('bottomup')
			pass
# 			print("CUBES POSITIONS")
# 			for cube in self.cubes:
# 				print(cube.xleft, cube.ybot, cube.zback)
# 				print(cube.xright, cube.ytop, cube.zfront)
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
			self.player.xstrafe += np.sin((90-self.player.yrot)*np.pi/180)*self.player.xspeed
			self.player.zstrafe -= np.cos((90-self.player.yrot)*np.pi/180)*self.player.zspeed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.A:
			# Влево. Независимо от направления камеры, будет всегда "идти" влево.
			self.object_collision(270)
			self.player.xstrafe -= np.sin((90-self.player.yrot)*np.pi/180)*self.player.xspeed
			self.player.zstrafe += np.cos((90-self.player.yrot)*np.pi/180)*self.player.zspeed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.W:
			# Движение прямо. Независимо от направления камеры, будет всегда "идти" вперёд.
			self.object_collision(0)
			self.player.zp += np.cos(self.player.yrot*np.pi/180)*self.player.zspeed
			self.player.xp += np.sin(self.player.yrot*np.pi/180)*self.player.xspeed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		if symbol == key.S:
			# Движение назад. Независимо от направления камеры, будет всегда "идти" назад.
			self.object_collision(180)
			self.player.zp -= np.cos(self.player.yrot*np.pi/180)*self.player.zspeed
			self.player.xp -= np.sin(self.player.yrot*np.pi/180)*self.player.xspeed
			self.player.zpos = self.player.zp + self.player.zstrafe
			self.player.xpos = self.player.xp + self.player.xstrafe
		self.netsend()
	
player = Player()
world = World(player)
keystate = key.KeyStateHandler()
world.push_handlers(keystate)
# world.set_fullscreen(True)
# world.set_mouse_visible(False)
pyglet.app.run()