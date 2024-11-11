from dis import Instruction
import numpy as np
import cv2 as cv
import imageio
import os
import tkinter as Tk
import sys
from matplotlib import pyplot as plt
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image


# The goal for this progam is to:
# 1. Read an input image
# 2. Simplify the image into an array of scalars based on a legend
# 3. Build a DFT off of the scalar array
# 4. Truncate the DFT
# 5. Produce a naval message on compressed list of coefficients
# 6. Rebuild the DFT from the naval message
# 7. Perform an IDFT to reproduce a scalar array
# 8. Interpret build the scalar array into the original input image
# 9. Overlay a standard image template over the top of the scalar array

#####################################################################
# B u i l d   C l a s s e s 
#####################################################################
# Start with the file and file path for everything you are doing
class File_Structure:

    # all relevant files saved as strings
    def __init__(self,orig_path):
        subject = orig_path.split('/')[-1][:-4]
        self.subject = subject
        self.ext = check_type(orig_path)
        self.cwd = os.getcwd()
        self.templates_folder = os.getcwd() + "/templates/"
        self.template = os.getcwd() + "/templates/" + subject + "/" + subject + "_template.jpg"
        self.config = os.getcwd() + "/templates/" + subject + "/" + subject + ".config"
        self.orig_file = subject
        self.orig_folder = '/'.join(orig_path.split("/")[:-1]) + '/'

class Config_File:
    crop_x1 = int(0)
    crop_x2 = int(0)
    crop_y1 = int(0)
    crop_y2 = int(0)
    scale_x = int(0)
    scale_y = int(0)
    scale = []

class msg_read:
    # input a message file and parse its contents
    def __init__(self,msg):
        header = True
        footer = False
        for m in msg.splitlines():
            if header:
                if "WXYZ" in m:
                    header = False
                    x = int(m.split("/")[0])
                    self.x = x
                    y = int(m.split("/")[1])
                    self.y = y
                    n = int(m.split("/")[2])
                    self.n = n
                    self.max = int(m.split("/")[3])
                    self.subject = m.split("/")[4]
                    i, j, index = 0, 0, 0
                    i_s, j_s = [i,x-i-1], [j,y-j-1]
                    # initialize the DFT
                    self.DFT = np.zeros((x,y,2))
            else:
                n1 = 0
                while n1 + 2 <= len(m):
                    if not '/' in m[n1:n1+2] and not footer:
                        val = c_str(m[n1:n1+2])
                        # place c in the array
                        k1 = int(index % 2)
                        j1 = int(((index - k1) / 2) % 2)
                        i1 = int(((index - k1 - (2 * j1)) / 4) % 2)
                        self.DFT[i_s[i1],j_s[j1],k1] = val
                        index += 1
                        if index == 8:
                            j = (j + 1) % n
                            j_s = [j,y-j-1]
                            if j == 0:
                                i = i + 1
                                i_s = [i,x-i-1]
                            index = 0
                    else:
                        footer = True
                    n1 += 2

class config_read():
    def __init__(self, file_path):
        scale_start = False
        with open(file_path) as file: config_contents = file.read()
        for config in config_contents.splitlines():
            if "crop_x1 = " in config: self.crop_x1 = int(config.split("crop_x1 = ")[1])
            if "crop_x2 = " in config: self.crop_x2 = int(config.split("crop_x2 = ")[1])
            if "crop_y1 = " in config: self.crop_y1 = int(config.split("crop_y1 = ")[1])
            if "crop_y2 = " in config: self.crop_y2 = int(config.split("crop_y2 = ")[1])
            if "scale_x = " in config: self.scale_x = int(config.split("scale_x = ")[1])
            if "scale_y = " in config: self.scale_y = int(config.split("scale_y = ")[1])
            if "scale = " in config:
                if not scale_start: 
                    self.scale = []
                    scale_start = True
                self.scale.append(int(config.split("scale = ")[1]))

def config_write(c):
    with open(FS.config, 'w') as file:
        print("This config file is designed for use with the weather gif builing program.",   file = file)
        print("It is a list of variables which the program uses to translate information ",   file = file)
        print("onto a template. Each variable should be on its own line, with the variable ", file = file)
        print("name on one side of an equal sign, and its integer value on the other with ",  file = file)
        print("a single space on either side of the equal sign. The default values are ",     file = file)
        print("zero.",                                                                        file = file)
        print("crop_x2 = " + str(c.crop_x1),                                                    file = file)
        print("crop_y1 = " + str(c.crop_x2),                                                    file = file)
        print("crop_y2 = " + str(c.crop_y1),                                                    file = file)
        print("crop_x1 = " + str(c.crop_y2),                                                    file = file)
        print("scale_x = " + str(c.scale_x),                                                    file = file)
        print("scale_y = " + str(c.scale_y),                                                    file = file)
        for s in c.scale:
            print("scale = " + str(s),                                                        file = file)

#####################################################################
# C h e c k   f i l e   t y p e
#####################################################################
# Verifies the file is of the correct type.  If not, pop up an error
# message
def check_type(orig_path):
    # define valid file extensions
    ext_good = ['.gif','.jpg','.txt','.msg']
    if orig_path == "":
        quit()
    else:
        for e in ext_good:
            if orig_path[len(orig_path)-4:] == e: return e

    root = Tk.Tk()
    root.wm_withdraw()
    messagebox.showinfo(title="Wrong type of file", message="Please choose a .jpg, .gif, .txt, or .msg")
    root.destroy()
    quit()

#####################################################################
# B u i l d   R G B   s c a l e
#####################################################################
# use a slice of RGB values to return an array of BGR integers
def scale_build_int(raw):
    scale_out = []
    s = 0
    r_last = np.astype(np.array([0,0,0]),np.uint8)
    for r in raw:
        # first, filter out black and white
        if not all(r > 250) and not all(r < 5):
            # next, check if the RGB value matches the last RGB
            if sum(np.abs(np.subtract(r_last,r))) >= 5:
                for BGR in r:
                    s = s * 256 + int(BGR)
                scale_out.append(s)
                s = 0
                r_last = r.copy()
    return scale_out

# use an array of BGR intgers to return the BGR values as an array
def scale_build_RGB(scale_from_config):
    scale = []
    for sc in scale_from_config:
        scale_element = [0,0,0]
        scale_element[2] = sc % 256
        sc = int((sc - scale_element[0]) / 256)
        scale_element[1] = sc % 256
        sc = int((sc - scale_element[1]) / 256)
        scale_element[0] = sc
        scale.append(scale_element)
    return np.astype(np.array(scale),np.uint8)

#####################################################################
# C r e a t e   a   p l o t   o f   s c a l a r   v a l u e s 
#####################################################################
def plot_scale(image):
    arr = image.copy()
    # crop out a part of the image (namely the legend)
    ##################################################
    # config file: x1 = left most x, x2 =  right most x
    #              y1 =  top most y, y2 = bottom most y
    # crop the image to remove the legend
    if c.crop_x1 !=0: arr[:,0:c.crop_x1,:    ] = np.zeros((x,  c.crop_x1,z))
    if c.crop_x2 !=0: arr[:,  c.crop_x2:y,:  ] = np.zeros((x,y-c.crop_x2,z))
    if c.crop_y1 !=0: arr[0:  c.crop_y1,:,:  ] = np.zeros((    c.crop_y1,y,z))
    if c.crop_y2 !=0: arr[    c.crop_y2:x,:,:] = np.zeros((x-  c.crop_y2,y,z))

    # create a blank canvas and import RGB values for the scale
    plot_out = np.zeros((x, y)).astype(int)
    
    # build a scalar plot for each level of the scale
    for i in range(len(scale)):
        # build a bool array based on what is still blank in the output
        plot_bool = plot_out == 0
        # remove all pixels which do not match the given BGR value
        for j in range(3): plot_bool = np.multiply(plot_bool, abs(arr[:,:,j]-scale[i,j]) < 5)
        plot_out = plot_out + (plot_bool.astype(int) * (i + 1))
    return plot_out

# function to smooth out the colors
def plot_smooth(arr,repeat):
    arr_out = np.copy(arr)
    for r in range(repeat):
        arr_num = np.zeros(arr.shape)
        arr_den = np.zeros(arr.shape)
        arr_bol = arr_out == 0
        for i_psa in [0,1]:
            for j_psa in [-1,1]:
                arr_num = arr_num + np.roll(arr_out,           j_psa,axis = i_psa)
                arr_den = arr_den + np.roll(np.invert(arr_bol),j_psa,axis = i_psa)
        arr_out = arr_out + np.multiply(np.divide(arr_num,arr_den,where = arr_den != 0),arr_bol)
    return arr_out

def image_restore(plot,subject,scale):
    x, y = plot.shape
    image = np.zeros((x,y,3)).astype(int)
    empty = [0, 0, 124]
    var = 50

    image_template = cv.imread('./templates/' + subject + '/' + subject + "_template.jpg")

    plot_bool = np.ones((x,y)).astype(bool)
    for i in range(3): plot_bool = np.multiply(plot_bool, abs(image_template[:,:,i].astype(int) - empty[i]) < var)

    # change the scalar plot to an RGB image
    for i in range(len(scale))[1:]:
        im = np.zeros((x,y,3))
        for j in range(3): im[:,:,j] = np.array(plot == i).astype(int) * scale[i, j]
        image = image + im

    for i in range(3): 
        image[:,:,i] = np.multiply(np.array(plot_bool).astype(int),image[:,:,i]) + np.multiply(np.array(~plot_bool).astype(int), image_template[:,:,i])

    # crop out a part of the image (namely the legend)
    ##################################################
    # config file: x1 = left most x, x2 = right most x
    #              y1 = top most y,  y2 = bottom most y

    # crop the image to remove the legend
    if c.crop_x1 !=0: image[:,0:c.crop_x1,    :] = image_template[:,0:c.crop_x1,    :].copy()
    if c.crop_x2 !=0: image[:,  c.crop_x2:y,  :] = image_template[:,  c.crop_x2:y,  :].copy()
    if c.crop_y1 !=0: image[0:  c.crop_y1,  :,:] = image_template[0:  c.crop_y1,  :,:].copy()
    if c.crop_y2 !=0: image[    c.crop_y2:x,:,:] = image_template[    c.crop_y2:x,:,:].copy()

    return image


#####################################################################
# C o n v e r t   b a s e   1 0   < - >   b a s e   6 2
#####################################################################
# function to compress integers [-990000000, 990000000] into 2 digits
def c_int(i):
    ##################################################
    # User Defined: start of negative chr codes
    # define the chr() function displacement (ASCII code) for 'A' and 'a'

    # check if less than 100
    if abs(i) < 100: return '00'

    # D = chr(A) and d = chr(a)
    D = 65
    d = 97

    # check if it is negative
    neg = i < 0

    # the goal is to reduce 'i' to a number less than 2000 so it can be 
    # converted to a base 62 (0-9,A-Z,a-z) and reduced to two characters
    # so the first two numbers will be the first two significant digits
    # and the last number will be the exponent. if negative, we add 1000.
    r_str = str(int(abs(i)))[:2] + str(len(str(int(abs(i))-1)))
    if neg: r = int(r_str) + 1000
    else: r = int(r_str)

    # now convert r to a base 62 number
    r0_62 = int(np.floor(r / 62))
    r1_62 = r - r0_62 * 62

    if   r0_62 >= 36: r0 = chr(r0_62 + d - 36)
    elif r0_62 >= 10: r0 = chr(r0_62 + D - 10)
    else:             r0 = str(r0_62)

    if   r1_62 >= 36: r1 = chr(r1_62 + 97 - 36)
    elif r1_62 >= 10: r1 = chr(r1_62 + 65 - 10)
    else:             r1 = str(r1_62) 

    # print(i)
    # print(str(r) + " " + str(r0) + " " + str(r1))

    return str(r0) + str(r1)

# function to uncompress the message wall of text
def c_str(i):
    ##################################################
    # Must Match! : start of negative chr codes from dft.py
    # define the chr() function displacement

    if i == "00": return 0

    D = 65
    d = 97

    # work backwards from the compression in dft.py
    # start by converting to decimal
    if   ord(i[0]) >= d: r0 = int(ord(i[0]) - d + 36)
    elif ord(i[0]) >= D: r0 = int(ord(i[0]) - D + 10)
    else:                r0 = int(i[0])

    if   ord(i[1]) >= d: r1 = int(ord(i[1]) - d + 36)
    elif ord(i[1]) >= D: r1 = int(ord(i[1]) - D + 10)
    else:                r1 = int(i[1])

    r_64 = (62 * r0) + r1
    if r_64 > 1000: r_64 = (-1) * (r_64 - 1000)

    r_str = str(r_64)
    l = len(r_str)

    r = int(r_str[:(l-1)]) * (10 ** (int(r_str[-1]) - 2))

    return r


#####################################################################
# G U I   f o r   t h e   s e n d e r   o f   t h e   g i f
#####################################################################
def build_template(image):
    # populate a dictionary of template images
    im_dict = {}
    im_dict["image_orig"] = image.copy()

    bg_color = "light gray"
    global la_x
    la_x = 500
    global la_y
    la_y = 400
    global template_index
    template_index = 0

    global c
    c = Config_File

    inst_dict = {}
    inst_dict[0] =  "Find the low end of the color scale on the image by clicking on the image. Click Next to continue"
    inst_dict[1] = "Find the high end of the color scale on the image by clicking on the image. Make sure the whole color scale is highlighted. Press Back to reset. Click Next to continue."
    inst_dict[2] =    "Find the top edge of the map by clicking on the image. Then press Next. Do not cut off the coordinates."
    inst_dict[3] = "Find the bottom edge of the map by clicking on the image. Then press Next. Do not cut off the coordinates."
    inst_dict[4] =   "Find the left edge of the map by clicking on the image. Then press Next. Do not cut off the coordinates."
    inst_dict[5] =  "Find the right edge of the map by clicking on the image. Then press Next. Do not cut off the coordinates."

    #####################################################################
    # C l i c k   b e h a v i o r
    # Click 0 = Low end of scale  | image 0 -> 1
    # Click 1 = High end of scale | image 1 -> 2
    # Click 2 = Top of map        | image 2 -> 3
    # Click 3 = Bottom of map     | etc.
    # Click 4 = Left of map
    # Click 5 = Right of map
    def image_click(e):
        global template_index
        global la_x
        global la_y
        global c
        if e.widget.winfo_parent() == '.!frame2' and template_index < 6:
 
            print(e.widget.winfo_parent())
            print("x = " + str(e.x))
            print("y = " + str(e.y))

            im_x, im_y = im_dict["image_0"].shape[:2]
            r_highlight = 20

            #####################################################################
            # I n d e x   =   0
            # adjust behavior based on which template index we are on
            if template_index == 0:
                im_dict["image_1"] = im_dict["image_0"].copy()

                # set x, y for the start of the color scale
                im_dict["scale_sta_x"] = int(np.floor(e.y * im_x / la_y))
                im_dict["scale_sta_y"] = int(np.floor(e.x * im_y / la_x))

                im_dict["scale_box"] = [im_dict["scale_sta_x"] - r_highlight,
                                        im_dict["scale_sta_x"] + r_highlight,
                                        im_dict["scale_sta_y"] - r_highlight,
                                        im_dict["scale_sta_y"] + r_highlight]

            #####################################################################
            # I n d e x   =   1
            elif template_index == 1:
                im_dict["image_2"] = im_dict["image_0"].copy()

                # set x, y for the end of the color scale
                im_dict["scale_end_x"] = int(np.floor(e.y * im_x / la_y))
                im_dict["scale_end_y"] = int(np.floor(e.x * im_y / la_x))

                # decide whether the scale is horizontal or vertical
                if abs(im_dict["scale_sta_x"] - abs(im_dict["scale_end_x"])) >= abs(im_dict["scale_sta_y"] - abs(im_dict["scale_end_y"])):
                    im_dict["scale_end_y"] = int(np.floor(np.average([im_dict["scale_sta_y"],im_dict["scale_end_y"]])))
                    c.scale_x = im_dict["scale_end_y"]
                    im_dict["scale_box"][2] = im_dict["scale_end_y"] - r_highlight
                    im_dict["scale_box"][3] = im_dict["scale_end_y"] + r_highlight
                    im_dict["scale_box"][0] = min(im_dict["scale_sta_x"],im_dict["scale_end_x"]) - r_highlight
                    im_dict["scale_box"][1] = max(im_dict["scale_sta_x"],im_dict["scale_end_x"]) + r_highlight
                else:
                    im_dict["scale_end_x"] = int(np.floor(np.average([im_dict["scale_sta_x"],im_dict["scale_end_x"]])))
                    c.scale_y = im_dict["scale_end_x"]
                    im_dict["scale_box"][0] = im_dict["scale_end_x"] - r_highlight
                    im_dict["scale_box"][1] = im_dict["scale_end_x"] + r_highlight
                    im_dict["scale_box"][2] = min(im_dict["scale_sta_y"],im_dict["scale_end_y"]) - r_highlight
                    im_dict["scale_box"][3] = max(im_dict["scale_sta_y"],im_dict["scale_end_y"]) + r_highlight


            #####################################################################
            # I n d e x   =   2
            elif template_index == 2:
                im_dict["image_3"] = im_dict["image_orig"].copy()
                c.crop_y1 = int(np.floor(e.y * im_x / la_y))
                im_dict["image_3"][:c.crop_y1,:,:] = np.zeros((c.crop_y1,im_y,3))

            else:
                im_dict["image_" + str(template_index + 1)] = im_dict["image_" + str(template_index)].copy()

            #####################################################################
            # I n d e x   =   3
            if template_index == 3:
                c.crop_y2 = int(np.floor(e.y * im_x / la_y))
                im_dict["image_4"][c.crop_y2:,:,:] = np.zeros((im_x - c.crop_y2,im_y,3))        

            #####################################################################
            # I n d e x   =   4
            if template_index == 4:
                c.crop_x1 = int(np.floor(e.x * im_y / la_x))
                im_dict["image_5"][:,:c.crop_x1,:] = np.zeros((im_x,c.crop_x1,3))

            #####################################################################
            # I n d e x   =   5
            if template_index == 5:
                c.crop_x2 = int(np.floor(e.x * im_y / la_x))
                im_dict["image_6"][:,c.crop_x2:,:] = np.zeros((im_x,im_y - c.crop_x2,3))

            # put the scale back
            im_dict["image_" + str(template_index + 1)][
                im_dict["scale_box"][0]:im_dict["scale_box"][1], 
                im_dict["scale_box"][2]:im_dict["scale_box"][3],:] = \
                    im_dict["image_orig"][
                        im_dict["scale_box"][0]:im_dict["scale_box"][1], 
                        im_dict["scale_box"][2]:im_dict["scale_box"][3],:]

            # display the most recent image
            show("image_" + str(template_index + 1))
            print(e.x)
            print(e.y) 

            button_next.pack(padx = 10, pady = 5, side = 'left')

            return([e.x, e.y])

    def allowalphanumeric(text):
        if text == "": 
            im_dict["template_name"] = text
            return True
        return text.isalnum()

    def show(im_name):
        global label_image
        global la_x
        global la_y
        im_dict[im_name + "_tk"] = ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(im_dict[im_name], cv.COLOR_BGR2RGB)).resize((la_x,la_y)))
        label_image.config(image = im_dict[im_name + "_tk"])

    def cancel_click():
        print("cancel clicked")
        root.destroy()
        return "quit"

    def next_click():
        print("next clicked")
        global template_index
        global label_image

        #####################################################################
        # A d v a n c e   y o u r   t e m p l a t e
        if template_index < 5: 
            template_index += 1
            if template_index == 2: show("image_orig")
            inst_text.config(text = inst_dict[template_index])
            print("template_index = " + str(template_index))

        #####################################################################
        # F i n i s h   y o u r   t e m p l a t e
        else:
            global c
            global scale
            inst_title.pack_forget()
            inst_text.pack_forget()
            button_next.pack_forget()

            button_back.config(text = "Create New Template", command = newtemplate_click)
            subject_prompt = Tk.Label(frame_0, bg = bg_color, text = "Name your template:")
            subject_prompt.pack()

            global subject_name
            subject_name = Tk.Entry(frame_0, validate = "key", validatecommand=(root.register(allowalphanumeric),"%P"))
            subject_name.pack()
            image_template = im_dict["image_orig"].copy()

            # crop the image template
            image_template[:c.crop_y1, :,                   :] = np.uint8(255)
            image_template[ c.crop_y2:,:,                   :] = np.uint8(255)
            image_template[:,                   :c.crop_x1, :] = np.uint8(255)
            image_template[:,                    c.crop_x2:,:] = np.uint8(255)
            
            # build the scale
            for delta in [-10,0,10]:
                if c.scale == []:
                    if c.scale_x != 0: 
                        c.scale = scale_build_int(im_dict["image_orig"][im_dict["scale_box"][0]:im_dict["scale_box"][1],delta + c.scale_x,:])
                        if im_dict["scale_sta_x"] > im_dict["scale_end_x"]: c.scale = c.scale[::-1]
                    else: 
                        c.scale = scale_build_int(im_dict["image_orig"][delta + c.scale_y,im_dict["scale_box"][2]:im_dict["scale_box"][3],:])
                        if im_dict["scale_sta_y"] > im_dict["scale_end_y"]: c.scale = c.scale[::-1]

            scale = scale_build_RGB(c.scale)

            # get a plot of the image
            plot_template = plot_scale(image_template)
            plot_mask = np.repeat(np.array(plot_smooth(plot_template,3) == 0).astype(int)[:,:,np.newaxis], 3, axis = 2)

            image_template = np.multiply(image_template, plot_mask).astype(np.uint8)
            image_template[:,:,2] = image_template[:,:,2] + 125 * np.array(plot_mask[:,:,2] == 0).astype(int)
            
            # put the template back in
            image_template[
                im_dict["scale_box"][0]:im_dict["scale_box"][1], 
                im_dict["scale_box"][2]:im_dict["scale_box"][3],:] = \
                    im_dict["image_orig"][
                        im_dict["scale_box"][0]:im_dict["scale_box"][1], 
                        im_dict["scale_box"][2]:im_dict["scale_box"][3],:]

            im_dict["image_template"] = image_template
            show("image_template")
        button_next.pack_forget()

    def back_click():
        print("back clicked")
        global template_index
        if template_index > 0: 
            template_index += -1
            if template_index == 2: 
                show("image_orig")
            else:
                show("image_" + str(template_index))
            inst_text.config(text = inst_dict[template_index])
        else:
            global image
            root.destroy()
            choose_template(image)

    def newtemplate_click():
        global subject_name
        if subject_name.get() != "":
            FS.subject = subject_name.get()
            FS.template = os.getcwd() + "/templates/" + FS.subject + "/" + FS.subject + "_template.jpg"
            FS.config = os.getcwd() + "/templates/" + FS.subject + "/" + FS.subject + ".config"
            if os.path.isfile(FS.template):
                if askquestion_exists() == "no":
                    return
            if not os.path.exists(FS.templates_folder + FS.subject): os.mkdir(FS.templates_folder + FS.subject)
            cv.imwrite(FS.template,im_dict["image_template"])
            config_write(c)
            root.destroy()

    def askquestion_exists():
        answer = Tk.messagebox.askquestion("File Already Exists", "A template with this name already exists. Do you want to replace it?", icon = "error")
        return answer

    #####################################################################
    # B u i l d   t h e   r o o t   U I
    root = Tk.Tk()
    root.title = "Build your template"
    root.config(bg = bg_color)

    #####################################################################
    # B u i l d   F r a m e   0   =   I n s t r u c t i o n s
    frame_0 = Tk.Frame(root, bg = bg_color)
    frame_0.pack(pady = 10)
    inst_title = Tk.Label(frame_0, justify = "left", wraplength = la_x, 
                            font = ("Arial",16), bg = bg_color,
                            text = 
                            "Build your template:.")
    inst_title.pack(anchor = "w")
    inst_text = Tk.Label(frame_0, justify = "left", wraplength = la_x,
                                font = ("Arial", 12), bg = bg_color,
                                text = inst_dict[0])
    inst_text.pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   2   =   T h e   I m a g e

    frame_2 = Tk.Frame(root, height = la_y, width = la_x, bg = bg_color)
    frame_2.pack(padx = 10, pady = 5)
    
    im_dict["image_0"] = np.floor_divide(im_dict["image_orig"],2)

    global label_image
    label_image = Tk.Label(frame_2)
    show("image_0")
    label_image.pack()
    
    #####################################################################
    # B u i l d   F r a m e   3   =   B u t t o n s
    frame_3 = Tk.Frame(root, bg = bg_color)
    frame_3.pack()

    button_next = Tk.Button(frame_3, 
                        text = "Next", 
                        command = next_click)
    # button_next.pack(padx = 10, pady = 5, side = 'left')

    button_back = Tk.Button(frame_3, text = "Back", 
                        command = back_click)
    button_back.pack(padx = 10, pady = 5 , side = 'left')

    button_canc = Tk.Button(frame_3, text = "Cancel", 
                        command = cancel_click)
    button_canc.pack(padx = 10, pady = 5 , side = 'left')


    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", cancel_click)
    root.bind("<Button 1>", image_click)
    root.mainloop()



def choose_template(image):
    def show(sub):
        global label_image
        label_image.config(image = template_dict[sub])

    def cancel_click():
        print("cancel clicked")
        root.destroy()
        return "quit"

    def new_click():
        # FIX build out what to do if the template does not exist
        global image
        print("new clicked")
        root.destroy()
        build_template(image)

    def select_click():
        global subject
        print("select clicked")
        FS.subject = selection.get()
        FS.template = os.getcwd() + "/templates/" + selection.get() + "/" + selection.get() + "_template.jpg"
        FS.config = os.getcwd() + "/templates/" + selection.get() + "/" + selection.get() + ".config"
        root.destroy()

    # set your global variables
    bg_color = "light gray"
    image_x = 500
    image_y = 400

    #####################################################################
    # B u i l d   t h e   r o o t   U I
    root = Tk.Tk()
    root.title = "Select your template"
    root.config(bg = bg_color)

    #####################################################################
    # B u i l d   F r a m e   0   =   I n s t r u c t i o n s
    frame_0 = Tk.Frame(root, bg = bg_color)
    frame_0.pack(pady = 10)
    instructions_title = Tk.Label(frame_0, justify = "left", wraplength = image_x, 
                            font = ("Arial",16), bg = bg_color,
                            text = 
                            "Choose a template.").pack(anchor = "w")
    instructions_text = Tk.Label(frame_0, justify = "left", wraplength = image_x,
                                font = ("Arial", 12), bg = bg_color,
                                text = "If a template doesn't already exist, create " +
                                "a new template. Note: units will not have access to " +
                                "a new template until you upload a new template folder " +
                                "and they subsequently download the new template folder.").pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   1   =   D r o p d o w n   M e n u
    frame_1 = Tk.Frame(root, bg = bg_color)
    frame_1.pack(pady = 5)

    # build and populate teh drowpdown menu
    if os.path.exists("./templates"):
        options = os.listdir("./templates")
    else:
        os.mkdir("./templates")
        options = []

    if options == []:
        new_click()
    else:
        selection = Tk.StringVar()
        selection.set(options[0])
        drop = Tk.OptionMenu(frame_1, selection, *options, command = show)
        drop.pack()

        #####################################################################
        # B u i l d   F r a m e   2   =   T h e   T e m p l a t e
        # populate a dictionary of template images
        template_dict = {}
        for op in options:
            os.chdir(FS.cwd + "/templates/" + op)
            template_dict[op] = ImageTk.PhotoImage(Image.open(op + "_template.jpg").resize((image_x, image_y)))
        os.chdir(FS.cwd)
        frame_2 = Tk.Frame(root, height = image_y, width = image_x, bg = bg_color)
        frame_2.pack(padx = 10, pady = 5)
        global label_image
        label_image = Tk.Label(frame_2, image = template_dict[selection.get()])
        label_image.pack()

        #####################################################################
        # B u i l d   F r a m e   3   =   T h e   I m a g e
        # populate a dictionary of template images
        frame_3 = Tk.Frame(root, height = image_y, width = image_x, bg = bg_color)
        frame_3.pack(padx = 10, pady = 5)
        template_dict["orig"] = ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB)).resize((image_x, image_y)))
        orig_image = Tk.Label(frame_3, image = template_dict["orig"])
        orig_image.pack()

        #####################################################################
        # B u i l d   F r a m e   4   =   B u t t o n s
        frame_4 = Tk.Frame(root, bg = bg_color)
        frame_4.pack()

        if not selection.get() == "":
            button0 = Tk.Button(frame_4, 
                                text = "Select Template", 
                                command = select_click)
            button0.pack(padx = 10, pady = 5, side = 'left')

        button1 = Tk.Button(frame_4, text = "New Template", 
                            command = new_click)
        button1.pack(padx = 10, pady = 5 , side = 'left')

        button2 = Tk.Button(frame_4, text = "Cancel", 
                            command = cancel_click)
        button2.pack(padx = 10, pady = 5 , side = 'left')

        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", cancel_click)
        root.mainloop()


#####################################################################
# S t a r t   o f   _ _ m a i n _ _
#####################################################################

# open a file browser and save the file name as orig_path
orig_path = askopenfilename()
# file_path = 

FS = File_Structure(orig_path)

#####################################################################
# i m a g e   - >   m e s s a g e
#####################################################################
if FS.ext == ".gif":
    gif = imageio.mimread(orig_path)
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in gif][0]
if FS.ext == ".jpg":
    image = cv.imread(orig_path)

#####################################################################
# i m a g e   - >   m e s s a g e
#####################################################################
# if we've defined an image, otherwise skip to except
if FS.ext == ".gif" or FS.ext == ".jpg":
    x, y, z = image.shape

    choose_template(image)

    if not "c" in globals(): c = config_read(FS.config)
    if not "scale" in globals(): scale = scale_build_RGB(c.scale)

    # turn the image into a scalar plot and then smooth it over
    plot = plot_scale(image.copy())
    plot = plot_smooth(plot,100)

    ################################################################
    # r u n    D F T 
    ################################################################
    DFT = cv.dft(np.float32(plot),flags=cv.DFT_COMPLEX_OUTPUT)

    #################################################################
    # User defined: # DFT coefficients
    # number of terms will be ((n * 2) ^ 2) * 2
    n = 10

    # Remove higher frequency coefficients
    DFT[n:x-n,:,:] = np.zeros((x-2*n,y,2))
    DFT[:,n:y-n,:] = np.zeros((x,y-2*n,2))

    # save the values of the DFT to a file

    message_file_path = FS.orig_folder + "/" + FS.subject + ".txt"

    with open(message_file_path,'w') as file:
        print("R XXXXXXZ MMM YY",                                                 file = file)
        print("FM COMSUBPAC PEARL HARBOR HI",                                     file = file)
        print("TO SSBN PAC",                                                      file = file)
        print("BT",                                                               file = file)
        print("UNCLAS",                                                           file = file)
        print("SUBJ/VLF WEATHER GIF FOR " + FS.subject.upper() + "//",            file = file)
        print("RMKS/SEE INSTRUCTIONS ON CSP WEBSITE ON HOW TO USE THIS MESSAGE.", file = file)
        print(str(x) + "/" + 
              str(y) + "/" + 
              str(n) + "/" + 
              str(int(np.max(plot))) + "/" + 
              FS.subject + "/WXYZ//", file = file)
        S = ""
        for i in range(n):
            for j in range(n):
                i_s, j_s, k_s = [i,x-i-1], [j,y-j-1], [0, 1]
                for i1 in i_s:
                    for j1 in j_s:
                        for k1 in k_s:
                            S = S + c_int(DFT[i1,j1,k1])
                            if len(S) > 67:
                                print(S,                                          file = file)
                                S = ""
        print(S + "//",                                                           file = file)
        print("BT",                                                               file = file)
        print("#0001",                                                            file = file)
        print("NNNN",                                                             file = file)
    os.startfile(message_file_path)


#####################################################################
# m e s s a g e   - >   i m a g e
#####################################################################
elif FS.ext == ".txt":
    with open(orig_path,'r') as file: msg = file.read()
    m = msg_read(msg)
    plot_idft = cv.idft(m.DFT)

    # FIX this is sloppy.  Figure out how to update these without
    # going through each one
    FS.subject = m.subject
    FS.template = os.getcwd() + "/templates/" + m.subject + "/" + m.subject + "_template.jpg"
    FS.config = os.getcwd() + "/templates/" + m.subject + "/" + m.subject + ".config"
    c = config_read(FS.config)
    scale = scale_build_RGB(c.scale)

    # normalize the array and store as the output image
    plot_out = cv.magnitude(plot_idft[:,:,0], plot_idft[:,:,1])
    plot_out = np.array(m.max * (plot_out - np.min(plot_out)) / (np.max(plot_out) - np.min(plot_out))).astype(int)

    image = image_restore(plot_out,m.subject,scale)

    cv.imwrite(FS.orig_folder + m.subject + "_out.jpg",image)

    os.startfile(FS.orig_folder + m.subject + "_out.jpg")
