# Write your code here :-)
import busio
import board
import digitalio
import time
import analogio
import pwmio
import usb_midi
import gc

import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend



import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line

import adafruit_ili9341



def check_range(val1,val2,range):
	diff=val1-val2
	if(abs(diff)>range):
		return True
	return False



#init Prog Switch
prog_sw = digitalio.DigitalInOut(board.GP15)
prog_sw.switch_to_input(pull=digitalio.Pull.UP)

prog = prog_sw.value ^ 1 



displayio.release_displays()


#Use for SPI
spi = busio.SPI(clock=board.GP2,MOSI=board.GP3)
oled_cs = board.GP5
oled_dc = board.GP1
display_bus = displayio.FourWire(spi, command=oled_dc, chip_select=oled_cs, reset=board.GP0,baudrate=32000000)
#                         


WIDTH = 320
HEIGHT = 240  # Change to 64 if needed
BORDER = 5

#display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White
if prog:
	color_palette[0] = 0xFF0000


bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

# Draw a label
text = "Ivan's \nMidi Interface\n(C) 2024"
if prog:
	text += "\n IN PROGRAMM MODE\nRelease the Button!!"
	
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=100, y=HEIGHT // 2 - 10
)
splash.append(text_area)
#circle_radius = 5
#circle = Circle(10, 10, circle_radius, fill=0x00FF00, outline=0xFF00FF)
#splash.append(circle)

time.sleep(5.0)

splash.remove(text_area)
splash.remove(bg_sprite)


# Initialisiere das MIDI-Interface
#print(usb_midi.ports)
midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0], in_channel=0, midi_out=usb_midi.ports[1], out_channel=0
)
#print("Midi test")

# Init onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True



#init analog mux
mux0 = digitalio.DigitalInOut(board.GP16)
mux0.direction = digitalio.Direction.OUTPUT

mux1 = digitalio.DigitalInOut(board.GP17)
mux1.direction = digitalio.Direction.OUTPUT

mux2 = digitalio.DigitalInOut(board.GP18)
mux2.direction = digitalio.Direction.OUTPUT

mux3 = digitalio.DigitalInOut(board.GP19)
mux3.direction = digitalio.Direction.OUTPUT




# Init switch 
button1 = digitalio.DigitalInOut(board.GP13)
button1.switch_to_input(pull=digitalio.Pull.DOWN)

button2 = digitalio.DigitalInOut(board.GP14)
button2.switch_to_input(pull=digitalio.Pull.DOWN)

#button3 = digitalio.DigitalInOut(board.GP15)
#button3.switch_to_input(pull=digitalio.Pull.DOWN)

# Initialisiere den analogen Eingang
potentiometer1 = analogio.AnalogIn(board.GP27)


prog_nr=0

midi_old = [0] * 16
for x in range(0, 16):
 midi_old[x] =0

sld = [0] * 16
line =[0] * 16
for x in range(0,16):
	line[x]=Line(20+((x & 7) *40),100* (((x & 8) >> 3)+1) ,20+((x & 7) *40),100*(((x & 8) >> 3)+1) - int(127/2),0xFFFFFF)
	splash.append(line[x])
	circle_radius = 5
	sld[x] = Circle(20+((x & 7) *40), 100 * (((x & 8) >>3)+1), circle_radius, fill=0x00FF00, outline=0x0000FF)
	splash.append(sld[x])
#	print("X %d  x %d " % (x,  100 * (((x & 8) >>3)+1) ) )


if prog:
	sld[prog_nr].fill=0xFF0000
	sld[prog_nr].outline=0xFF0000


while True:
	text=""
	for x in range(0, 16):
		# setup mux for the particular analog input 
		mux0.value = x & 1
		mux1.value = x & 2
		mux2.value = x & 4
		mux3.value = x & 8

		#Averiging A/D values to limit ad fluctuations 
		pot_value=0
		for t in range(0,16):
			# Read the analog value
			pot_value += potentiometer1.value
		pot_value /= 16

		# Scale to midi values (0-127)
		midi_value1 = int(pot_value / 512)
		sld[x].y = (100 + 100*((x & 8) >>3) - int(midi_value1 /2)+1)
	#    print(midi_value)
		# Draw a label
		# text += "CH {0} Val {1} prog {2} {3}\n".format(1+x,midi_value1, prog_sw.value, ~prog_sw.value)
		

		#if midi_value1 != midi_old[x] and prog != 1:
		
		# Send Midi event only if new value is higher compare to old value
		if check_range(midi_value1,midi_old[x],(.5)) and prog != 1:
		# Send the MIDI-Event for particular potentiometer
			midi.send([ControlChange(1+x, midi_value1)])
#			print("test1 {:d} {:d} {:d} {:d} ".format(x,midi_old[x], prog_sw.value, prog_sw.value ^ 1))

		if prog and prog_nr == x:
			midi.send([ControlChange(1+x, midi_value1)])
#			print("test1 {:d} {:d} {:d} {:d} ".format(x,midi_old[x], prog_sw.value, prog_sw.value ^ 1))

		
		midi_old[x]=midi_value1

		if prog and prog_sw.value == 0:
			time_out=1000
			sld[prog_nr].fill=0x00FF00
			sld[prog_nr].outline=0x0000FF
			prog_nr = (prog_nr + 1) & 15
			sld[prog_nr].fill=0xFF0000
			sld[prog_nr].outline=0xFF0000
			while prog_sw.value ==0 :
				if time_out==0:
					sld[prog_nr].fill=0x00FF00
					sld[prog_nr].outline=0x0000FF
					prog=0
				time_out=time_out-1
				time.sleep(0.01)


		

#	text_area = label.Label(
#			terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 24
#			)
#	display.show(text_area)
#	circle.x = int(midi_old[0] /12)
	# Warte für eine kurze Zeit, um den MIDI-Stream nicht zu überlasten
	time.sleep(0.005)
	gc.collect()
