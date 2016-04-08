#!/usr/bin/env python3
#  - * -  coding: UTF - 8  - * - 

#from BASIC_SHAPES import Sphere

from math import pi, sin, cos

import pyglet
from pyglet.gl import *
from pyglet.window import *

import os
import ctypes
import sys

import obj

from random import random

import numpy as np

import pickle

import time

#import matplotlib.pylab as plt

lastpos=(0,0)

try:
	# Try and create a window with multisampling (antialiasing)
	config = Config(sample_buffers=1, samples=4, 
					depth_size=16, double_buffer=True,)
	window = pyglet.window.Window(resizable=True, config=config, fullscreen=False)
except pyglet.window.NoSuchConfigException:
	# Fall back to no multisampling for old hardware
	window = pyglet.window.Window(resizable=True)

#@window.event
def on_mouse_motion(x,y,dx,dy):
	global lastpos, rx, ry
	ry = ry - dx/5.0
# 	rx = rx - dy

@window.event
def on_key_press(symbol,modifier):
	global rx, ry, rz, CAMDIST, strx, stry, strz, xpos, ypos, zpos, xrot, zrot, yrot
	global v1, v2, v3, v4, v5, v6, v7, v8, v9
	if symbol == key.R:
		rx = (rx + 1)%360
	if symbol == key.F:
		rx = (rx - 1)%360
	if symbol == key.D:
		yrot += 3
#		ry = (ry - 5)#%360
	if symbol == key.A:
		yrot -= 3
#		ry = (ry + 5)#%360
	if symbol == key.E:
#		rz = (rz + 1)%360
		strx += sin((90-yrot)*0.017)*0.1
		strz -= cos((90-yrot)*0.017)*0.1
	if symbol == key.Q:
#		rz = (rz - 1)%360
		strx -= sin((90-yrot)*0.017)*0.1
		strz += cos((90-yrot)*0.017)*0.1
	if symbol == key.W:		
		zpos += cos(yrot*0.017)*0.1
		xpos += sin(yrot*0.017)*0.1
	if symbol == key.S:
		zpos -= cos(yrot*0.017)*0.1
		xpos -= sin(yrot*0.017)*0.1
	if symbol == key.Z:
		hy = (hy - 0.1)
	if symbol == key._1 and keystate[key.V]:
		v1 = v1+0.1
	if symbol == key._2 and keystate[key.V]:
		v2 = v2+0.1
	if symbol == key._3 and keystate[key.V]:
		v3 = v3+0.1
	if symbol == key._4 and keystate[key.V]:
		v4 = v4+0.1
	if symbol == key._5 and keystate[key.V]:
		v5 = v5+0.1
	if symbol == key._6 and keystate[key.V]:
		v6 = v6+0.1
	if symbol == key._7 and keystate[key.V]:
		v7 = v7+0.1
	if symbol == key._8 and keystate[key.V]:
		v8 = v8+0.1
	if symbol == key._9 and keystate[key.V]:
		v9 = v9+0.1
	if symbol == key.T and keystate[key.V]:
		v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = v9 = 0

def vec(*args):
	return (GLfloat * len(args))(*args)

@window.event
def on_draw():
	window.clear()
	setup3d()
	global i
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glLoadIdentity()
	glRotatef(yrot,0,1,0)
	glTranslatef(-xpos-strx,0,zpos+strz)
# 	if i > 15:
# 		glBindTexture(texture1.target,texture1.id)
# 	else:
# 		glBindTexture(texture2.target,texture2.id)
# 	i = (i+1)%30
#	sceneroty = 360 - ry
# 	glRotatef(rz, 0, 0, 1)
#	glRotatef(ry, 0, 1, 0)
#	glRotatef(rx, 1, 0, 0)
#	glRotatef(sceneroty, 0, 1.0, 0)
#	glTranslatef(-xpos, 0,-zpos)
	glLightfv(GL_LIGHT0, GL_POSITION, vec(-xpos, 3, zpos))
#	glMaterialfv(GL_FRONT, GL_EMISSION, vec(cos(v1),cos(v2),cos(v3),0))
#	glMaterialfv(GL_BACK, GL_DIFFUSE, vec(cos(v4),cos(v5),cos(v6),0))
#	glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0,1,0,1))
	batch1.draw()
	setup2d()
	fps.draw()
#	pyglet.clock.ClockDisplay().draw()
# 	batch2.draw()
#	glEnable(texture1.target)
#	batch2.draw()
#	object.draw()

fps = pyglet.clock.ClockDisplay()

def setup3d():
	glDisable(cross_p.target)
	glEnable(GL_TEXTURE_2D)
	glEnable(texture1.target)
	glViewport(0, 0, window.width, window.height) 
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(60., window.width / float(window.height), .1, 100.)
	glMatrixMode(GL_MODELVIEW)
	# One-time GL setup
	glClearColor(0.2, 0.2, 0.2, 1)
#	glColor3f(0, 0, 0)
	glClearDepth(1.0)
	glDepthFunc(GL_LESS)
	glEnable(GL_DEPTH_TEST)
	glShadeModel(GL_SMOOTH)
#	glEnable(GL_CULL_FACE)
	glEnable(GL_LIGHTING)
	glEnable(GL_LIGHT0)
#	glEnable(GL_LIGHT0)
# 	glEnable(GL_LIGHT2)
# 	glEnable(GL_LIGHT3)
#	glMatrixMode(GL_TEXTURE)
# 	glTranslatef(0,0,-6)
	
	# Define a simple function to create ctypes arrays of floats:
	glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 5, 0, 1))
	glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, vec(0.5))
# 	glLightfv(GL_LIGHT0, GL_AMBIENT, vec(1,1,1,0))
#	glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1,1,1,0))
#	glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(0,1,0,0))
# 	glLightfv(GL_LIGHT1, GL_SPECULAR, vec(.5, .5, 1, 0))
#	glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(1, 1, 1, 1))

def setup2d():
	glDisable(texture1.target)
	glDisable(GL_TEXTURE_2D)
	glColor3ub(255,255,255)
	glDisable(GL_DEPTH_TEST)
	glViewport(0, 0, window.width, window.height) 
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	glOrtho(0,window.width,0,window.height,-1,1)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


def update(dt):
	for key in keystate:
		if keystate[key]:
			window.dispatch_event('on_key_press',key,False)
	pass

class Cube(object):
	"""
	Создаётся 8 вершин единичного куба, зачем либо умножается на необходимой размер,
	либо сначала сдвигается на 0.5 по всем осям, чтобы центр был в начале координат.
	Далее строятся 12 треугольников для 6 граней.
	offset — для построения куба в разных частях мира. Из-за порядка оперцаий
	в единицах длины сторны куба. Так удобнее, навреное.
	"""
	def __init__(self, side, batch, offset = (0,0,0), center = True, group=None):
		vertices = np.array([	1,0,0, 0,0,0, 1,1,0, 0,1,0, 1,1,1, 0,1,1, 1,0,1, 0,0,1,
								1,1,0, 1,1,1, 1,0,0, 1,0,1, 0,0,0, 0,0,1, 0,1,0, 0,1,1
							])
		if center:
			vertices = vertices-0.5
		
		for i in range(0,len(vertices),3):
			vertices[i] = vertices[i] + offset[0]
			vertices[i+1] = vertices[i+1] + offset[1]
			vertices[i+2] = vertices[i+2] + offset[2]
	
		vertices = list(vertices*side)
	
		indices = 	[	0,1,2, 2,1,3, 2,3,4, 4,3,5, 4,5,6, 6,5,7, 
						8,9,10, 10,9,11, 10,11,12, 12,11,13, 12,13,14, 14,13,15	
					]
		
		textcoord = [.25,.75, 0,.75, .25,.5, 0,.5, .25,.25, 0,.25, .25,0, 0,0]*2
		
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
			
		norm = [0,0.5,0, 0.5,0,0]*8
		
# 		global pic, texture
# 		pic = pyglet.image.load("bstone12.bmp")
# 		texture = pic.get_texture()
# 		
# 		ix = pic.width
# 		iy = pic.height
# 		rawimage = pic.get_image_data()
# 		format = 'RGBA'
# 		pitch = rawimage.width * len(format)
# 		myimage = rawimage.get_data(format, pitch)
# 				
# 		glEnable(texture.target)
# 		glBindTexture(texture.target,texture.id)
# 		
# 		glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, myimage) 
# 		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
# 		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		
# 		self.sq_verts1 = batch1.add_indexed(4, GL_TRIANGLES, None, [0,2,1,0,3,2],
# 							('v3f',(0,1,0,1,1,0,1,0,0,0,0,0)),
# 							('t2f',(0,1,1,1,1,0,0,0)))
#							('c3B',(255,0,0,0,255,0,0,0,255,40,150,200)))
		
		self.vertex_list = batch.add_indexed(16, GL_TRIANGLES, group, indices, 
											('v3f',vertices),('n3f',norm),('t2f',textcoord))


pyglet.clock.schedule_interval(update,1/60)

CAMDIST = 0

# print("started import")
# object = obj.OBJ("cubet.obj")
# print("imported")

batchP = pyglet.graphics.Batch()
glPointSize(10)
#batchP.add(1,GL_POINTS,None, ('v3f',(0,0,CAMDIST+1)),('c3B',(255,0,0)))

#setup()
batch1 = pyglet.graphics.Batch()
batch2 = pyglet.graphics.Batch()

#label = pyglet.text.Label(text="test test",x=50,y=50,batch=batch2)

cross_p = pyglet.image.load("DATA/cross.png").get_texture()
#cross_p.anchor_x, cross_p.anchor_y = cross_p.width//2, cross_p.height//2
#cross_s = pyglet.sprite.Sprite(cross_p,window.width//2, window.height//2, batch=batch2)
#cross_s.scale = 0.2

i=0
# for x in range(-2,2):
# 	for y in range(-2,2):
# 		cube = Cube(3,batch1,offset = (x*1.5,0,y*1.5))
# 		i+=1
# print(i)

# cube1 = Cube(3,batch1,offset=(0,-3,0))
# cube1 = Cube(3,batch1,offset=(0,-1.5,0))
cube1 = Cube(3,batch1,offset=(1,0,-1))
cube1 = Cube(3,batch1,offset=(1,0,1))
cube1 = Cube(3,batch1,offset=(-1,0,-1))
cube1 = Cube(3,batch1,offset=(-1,0,1))

# sphere = Sphere(2,50,"spherenormals",batch1,offset=(-6,0,0))
# sphere = Sphere(2,50,"spherenormals",batch1,offset=(-3,0,0))
#sphere = Sphere(2,50,"spherenormals",batch1)
# sphere = Sphere(2,50,"spherenormals",batch1,offset=(3,0,0))
# sphere = Sphere(2,50,"spherenormals",batch1,offset=(6,0,0))




pic = pyglet.image.load("DATA/bstone12.bmp")
texture1 = pic.get_texture()
pic = pyglet.image.load("DATA/rstone12.bmp")
texture2 = pic.get_texture()


ix = pic.width
iy = pic.height
rawimage = pic.get_image_data()
format = 'RGBA'
pitch = rawimage.width * len(format)
myimage = rawimage.get_data(format, pitch)
		
glEnable(texture1.target)
#glBindTexture(texture1.target,texture1.id)


# sq_verts1 = batch1.add_indexed(4, GL_TRIANGLES, None, [0,2,1,0,3,2],
# 							('v3f',(0,1,0,1,1,0,1,0,0,0,0,0)),
# 							('t2f',(0,1,1,1,1,0,0,0)))
# #							('c3B',(255,0,0,0,255,0,0,0,255,40,150,200)))
# 
# sq_verts2 = batch2.add_indexed(4, GL_TRIANGLES, None, [0,2,1,0,3,2],
# 							('v3f',(0,.5,.5,1,1,.5,1,0,.5,0,0,.5)),
# 							('c3B',(190,120,255,255,0,0,0,255,0,40,150,200)))


# glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(1,0,0,0))



rx = ry = rz = 0
strx = stry = strz = 0
xpos = ypos = 0
zpos = 0

xrot = yrot = zrot = 0
yrot = 0

v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = v9 = 0

keystate = key.KeyStateHandler()
window.push_handlers(keystate)
# window.set_mouse_visible(False)

pyglet.app.run()