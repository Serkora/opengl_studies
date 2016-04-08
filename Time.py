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
		self.speed = 10
		
		self.jumping = "walk"
		self.gravity = 10
		self.jumpheight = 0.2*self.gravity
		self.jumppoint = 0
		
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
			super(World, self).__init__(config=config, resizable=True, fullscreen=False, vsync=False)
		except:
			super(World, self).__init__(resizable=True, fullscreen=False, vsync=True)
		self.noground = False
		self.player = player
		self.fps = pyglet.clock.ClockDisplay()
		self.graphics_batches()
		self.make_cubes()
		self.textures_and_text()
# 		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.register_event_type('on_key_press_my')
		self.robot_fr = 0
		self.time = 0#time.time()
		pyglet.clock.schedule(self.loading)
		pyglet.clock.schedule(self.start)

	def graphics_batches(self):
		self.batch = pyglet.graphics.Batch()
		self.batch_box = pyglet.graphics.Batch()
		self.batch_cup = pyglet.graphics.Batch()
	
	def textures_and_text(self):
		self.coords = pyglet.text.Label(text="",x=10)
		self.rot = pyglet.text.Label(text="",x=10)
		self.times = pyglet.text.Label(text="",x=10)
		self.pljfw = pyglet.text.Label(text="",x=10)
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
		self.LOADSCREEN = []
		for i in range(4):
			pic = pyglet.image.load("DATA/loading"+str(i+1)+".png")
			pic.anchor_x, pic.anchor_y = pic.width//2, pic.height//2
			spr = pyglet.sprite.Sprite(pic,0,0)
			self.LOADSCREEN.append(spr)
	
	def make_cubes(self):
		"""
		Создаётся несколько ящиков с разными сдвигами от начала координат
		и заносит их в список объектов.
		"""
# 		self.cubes = []
		self.box = Cubecol(20,self.batch_box,center = True, type = "inside")
# 		self.cube = Cubecol(2,self.batch,offset=(3,-7,-7))
		self.cubes = []
		cube = Cubecol(4, self.batch, offset=(-0.5, -2, -0.25))
		self.cubes.append(cube)
		for i in range(1,4):
			cube = Cubecol(2,self.batch, offset=(-0.5,-i*0.5-4,-i-0.5))
			self.cubes.append(cube)
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
		cube = Cubecol(0.5,self.batch,offset=(-5,-5,0))
		self.cubes.append(cube)
# 		self.sphere = Sphere(4,1000,self.batch)
# 		self.sphere = Sphere(6,1000,self.batch_cup)

	def loading(self,dt):
		self.clear()
		glClearColor(0,0,0,0)		
		i = self.time%4
		self.LOADSCREEN[i].x, self.LOADSCREEN[i].y = self.width/2, self.height/2
		self.LOADSCREEN[i].draw()
		self.time += 1

	def start(self,dt):
# 		model.frames[model.frame].draw()
# 		model.frame += 1
# 		if model.frame >= model.framesTOTAL:
# 			model.frame = 0
		pyglet.clock.unschedule(self.loading)
		pyglet.clock.unschedule(self.start)
		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.picspr.x, self.picspr.y = self.width/2, self.height/2
		self.time = 0

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
		self.time += dt
# 		for i in range(0,len(robot)):
# 			if i*0.04 < self.time-int(self.time) < (i+1)*0.04:
# 			if i*0.05 < self.time-int(self.time) < (i+1)*0.05:
# 		model.clock2(dt)
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
		glDepthFunc(GL_LESS)		# функция depth_test'а. Рисует только если ближе к экрану.
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)		# Сглаживание больших поверхностей, имеющих мало 
									# вершин. GL_FLAT покажет все треугольники.
		glEnable(GL_CULL_FACE)		
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
		yposstep = 10**5
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
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0,0,0))
		glPointSize(20)
		glColor3f(0.5,0,0.2)
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0.75,0.52,0.15,0))
		self.batch.draw()
		glColor3f(0,0,0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(self.boxtexture.target,self.boxtexture.id)
		self.batch_box.draw()
		glDisable(GL_TEXTURE_2D)
		glColor3f(0.5,0,0.2)
# 		model.draw()
# 		glTranslatef(0,-20,0)
# 		robot[self.robot_fr].draw()
# 		glTranslatef(-5,0,0)
# 		robot[self.robot_fr].draw()
# 		glTranslatef(10,0,0)
# 		robot[self.robot_fr].draw()
# 		glTranslatef(-15,0,0)
# 		robot[self.robot_fr].draw()
# 		glTranslatef(20,0,0)
# 		robot[self.robot_fr].draw()
# 		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,0.3,0,0))
		self.setup2d()
			# лейблы с координатами. Округлено до трёх знаков после запятой, всё в одну строку чтобы показывалось.
		pltxt = "X: "+str(np.round(self.player.xpos,3))+" Y: "+str(np.round(self.player.ypos,3))+" Z: "+str(np.round(self.player.zpos,3))
		self.coords.text = pltxt
		self.coords.y = self.height-30
		plrottxt = "Xrot: "+str(np.round(self.player.xrot,3))+" Yrot: "+str(np.round(self.player.yrot,3))+" Zrot: "+str(np.round(self.player.zrot,3))
		self.rot.text = plrottxt
		self.rot.y = self.height-50
		self.pljfw.text = self.player.jumping
		self.pljfw.y = self.height-70
		self.times.text = str(np.round(self.time,3))
		self.times.y = self.height-90
		self.times.draw()
		self.pljfw.draw()
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
		if symbol == key._1 and keystate[key.V]:
# 			self.enemy.xpos += 0.1
			model.stepsize += 0.1
		if symbol == key._2 and keystate[key.V]:
			self.enemy.ypos += 0.1
		if symbol == key._3 and keystate[key.V]:
			self.enemy.zpos += 0.1
		if symbol == key._1 and keystate[key.C]:
# 			self.enemy.xpos -= 0.1
			model.stepsize -= 0.1
		if symbol == key._2 and keystate[key.C]:
			self.enemy.ypos -= 0.1
		if symbol == key._3 and keystate[key.C]:
			self.enemy.zpos -= 0.1
		if symbol == key.R and modifier == key.MOD_SHIFT:
			# рестарт игрока и зелёного прямоугольника
			self.player.xpos = self.player.ypos = self.player.zpos = 0
			self.player.xp = self.player.yp = self.player.zp = 0
			self.player.xstrafe = self.player.ystrafe = self.player.zstrafe = 0
			self.player.xrot = self.player.yrot = self.player.zrot = 0
			self.time = 1
			self.player.jumping = "walk"
		if symbol == key.E and modifier == key.MOD_SHIFT:
			keystate[key.E] = False
			model.x=15
			model.y=-20
			model.roty=270
			model.frame = 0
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
# 		self.netsend()

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

class Model(object):
	"""
	Создаётся класс-контейнер для нашего человечка. Содержит список "кадров" (отдельных
	моделек, на самом деле, blender каждый кадр отдельн так можно сохранять),
	координаты, повороты, период, в секундах, за который все кадры должны пройти,
	а также "шаг" — на сколько нужно подвинуть модельку после каждого периода анимации.
	"""
	def __init__(self,x=0,y=0,z=0,rotx=0,roty=0,rotz=0):
		self.frames = []
		self.frame = 0
		self.x = x
		self.y = y
		self.z = z
		self.rotx = rotx
		self.roty = roty
		self.rotz = rotz
		
		self.time = 0.
		self.period = 1.
		
		self.stepsize = 1.5
		
		self.animate = True
	
	def init(self):
		"""
		Как только все модели были записаны, считаем количество кадров и длительность
		каждого кадра.
		"""
		self.framesTOTAL = len(self.frames)
		self.tick = self.period/self.framesTOTAL
	
	def clock(self,time):
		"""
		Счётчик анимации. При каждом тике update(), сюда передаётся время, прошедшее с
		последнего вызова update(). Это время добавляется к self.time.
		Затем прибавляется такое число кадров, столько должно было пройти за это время.
		Затем проверяется, не прошла ли вся анимация, и если прошла, то кадр сбрасывается
		на 0, а позиция сдвигается на новую. (В данном случае это только x, но на деле,
		разумеется, придётся опять высчитывать синусы/косинусы в зависимости от
		направления движения, как и с игроком.)
		Наконец, от self.time отнимается такое количество времени, на сколько были
		инкрементированы кадры. 
		Маленькая такая интерполяция получается.
		Первая строка для отмены анимации и покадрового просмотра.
		"""
		if not self.animate: return
		self.time += time
		increment_frame = int(self.time/self.tick)
		self.frame += increment_frame
		if self.frame >= self.framesTOTAL:
			self.x -= self.stepsize
			self.frame = 0
		self.time -= self.tick*increment_frame
	
	def clock2(self,time):
		if not self.animate: return
		self.time += time
		increment_frame = int(self.time/self.tick)
		self.frame += increment_frame
		self.x -= (self.stepsize/self.framesTOTAL)*increment_frame
		if self.frame >= self.framesTOTAL:
			self.frame = 0
		self.time -= self.tick*increment_frame
	
	
	def append(self,FRAME):
		"""
		Просто добавляет кадр в список.
		"""
		self.frames.append(FRAME)
	
	def draw(self):
		"""
		Lвигает мир куда надо, gоворачивает модельку, рисует нужный кадр (используя 
		встроенную в obj.OBJ() команду), затем возвращает мир на место.
		Возвращение на место обязательно, иначе отрисовка последующих объектов
		пойдёт нутыпонел.
		"""
		glTranslatef(self.x,self.y,-self.z)
		glRotatef(self.rotx,1,0,0)
		glRotatef(self.roty,0,1,0)
		glRotatef(self.rotz,0,0,1)
		self.frames[self.frame].draw()
		glRotatef(-self.rotx,1,0,0)
		glRotatef(-self.roty,0,1,0)
		glRotatef(-self.rotz,0,0,1)
		glTranslatef(-self.x,-self.y,self.z)
	
model = Model(x=15,y=-20,roty=270)

pathobj = "DATA/female_body/female_body_0000"
pathmodel = "DATA/female_body.model"
t1 = time.time()

t = "2"
if t == "i":
	imp = OBJ(pathobj)
	model.append(imp)
if t == "r":
	for i in range(1,5):
		file = "DATA/robot/robot"+str(i)+".obj"
		robot_fr = OBJ(file)
		model.append(robot_fr)

if t == "n" or t == "s":
	for i in range(1,21):
		"""
		добавляются последние две цифры, с ноликом перед единицей, открывается файл,
		парсится, добавляется в список кадров.
		"""
		print(i)
		model.append(OBJ(pathobj+("0"+str(i))[-2:]+".obj",'r'))
	print("LOADED")
	
	if t == "s":
		t1 = time.time()
		byte_model = pickle.dumps(model)
		print("PICKLED IN: ",time.time() - t1)
		t1 = time.time()
		path = pathmodel
		with open(path,'a'):
			os.utime(path,None)
		with gzip.open(path, 'wb') as f:
		    f.write(byte_model)
		print("COMPRESSED AND WROTE IN: ",time.time() - t1)

if t == "l":
	print("STARTING TO DECOMPRESS")
	path = pathmodel
	with gzip.open(path, 'rb') as f:
		bytemodel = f.read()
	print("DECOMPRESSED AND READ IN: ",time.time() - t1)
	t1 = time.time()
	model = pickle.loads(bytemodel)
	print("UNPICKLED IN: ",time.time() - t1)

# model.animate = False
# model.period = 1.
# model.stepsize = 3
# model.framesTOTAL = len(model.frames)
# model.tick = model.period/model.framesTOTAL
# print(model.framesTOTAL)
# print(model.tick)


i = 0
	
player = Player()
world = World(player)
keystate = key.KeyStateHandler()
world.push_handlers(keystate)
world.set_fullscreen(False)
world.set_mouse_visible(False)
pyglet.app.run()