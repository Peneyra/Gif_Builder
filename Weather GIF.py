import numpy as np
import cv2 as cv
import imageio
import os
import tkinter as Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image

# testing git

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
def plot_scale(arr):
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
def plot_smooth(arr,r):
    ##################################################
    # User defined: radius of smoothing
    x,y = arr.shape
    arr_out = np.copy(arr)
    for i1 in range(len(arr_out)):
        for j1 in range(len(arr_out[0])):
            if arr[i1,j1] == 0:
                x1, x2, y1, y2 = max(0,i1-r), min(x-1,i1+r+1), max(0,j1-r), min(y-1,j1+r+1)
                l = arr[x1:x2,y1:y2]
                if np.sum(l) > 0: arr_out[i1,j1] = int(np.sum(l) / np.sum(l != 0))
    return arr_out

def image_restore(plot,subject,scale):
    x, y = plot.shape
    image = np.zeros((x,y,3)).astype(int)
    empty = [0, 0, 125]
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
# function to compress integers [-990000000, 990000000] into 3 digits
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

    print(i)
    print(str(r) + " " + str(r0) + " " + str(r1))

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
def build_config_and_template(image):
    # FIX build a template and config file
    image_display = image.copy()

    bg_color = "light gray"
    image_x = 500
    image_y = 400

    def show(sub):
        global label_image
        label_image.config(image = template_dict[sub])

    def Cancel_click():
        print("cancel clicked")
        root.destroy()
        quit()

    def New_click():
        # FIX build out what to do if the template does not exist
        global image
        print("new clicked")
        build_config_and_template(image)
        root.destroy()

    def Select_click():
        global subject
        print("select clicked")
        root.destroy()

    #####################################################################
    # B u i l d   t h e   r o o t   U I
    root = Tk.Tk()
    root.title = "Build your templatea"
    root.config(bg = bg_color)

    #####################################################################
    # B u i l d   F r a m e   0   =   I n s t r u c t i o n s
    frame_0 = Tk.Frame(root, bg = bg_color)
    frame_0.pack(pady = 10)
    instructions_title = Tk.Label(frame_0, justify = "left", wraplength = image_x, 
                            font = ("Arial",16), bg = bg_color,
                            text = 
                            "Build your template:.").pack(anchor = "w")
    instructions_text = Tk.Label(frame_0, justify = "left", wraplength = image_x,
                                font = ("Arial", 12), bg = bg_color,
                                text = "Click above the top border of the map. " +
                                "Do not cut off any of the coordiantes along the " +
                                "side.").pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   2   =   T h e   I m a g e
    # populate a dictionary of template images
    template_dict = {}
    frame_2 = Tk.Frame(root, height = image_y, width = image_x, bg = bg_color)
    frame_2.pack(padx = 10, pady = 5)
    template_dict["orig"] = ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(image_display, cv.COLOR_BGR2RGB)).resize((image_x, image_y)))
    orig_image = Tk.Label(frame_2, image = template_dict["orig"])
    orig_image.pack()
    
    #####################################################################
    # B u i l d   F r a m e   3   =   B u t t o n s
    frame_3 = Tk.Frame(root, bg = bg_color)
    frame_3.pack()

    button0 = Tk.Button(frame_3, 
                        text = "Select Template", 
                        command = Select_click)
    button0.pack(padx = 10, pady = 5, side = 'left')

    button1 = Tk.Button(frame_3, text = "New Template", 
                        command = New_click)
    button1.pack(padx = 10, pady = 5 , side = 'left')

    button2 = Tk.Button(frame_3, text = "Cancel", 
                        command = Cancel_click)
    button2.pack(padx = 10, pady = 5 , side = 'left')

    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", Cancel_click)
    root.mainloop()

def choose_template(image):
    def show(sub):
        global label_image
        label_image.config(image = template_dict[sub])

    def Cancel_click():
        print("cancel clicked")
        root.destroy()
        quit()

    def New_click():
        # FIX build out what to do if the template does not exist
        global image
        print("new clicked")
        root.destroy()
        build_config_and_template(image)

    def Select_click():
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
                            "The name of your image file does not match a pre-" +
                            "existing template.").pack(anchor = "w")
    instructions_text = Tk.Label(frame_0, justify = "left", wraplength = image_x,
                                font = ("Arial", 12), bg = bg_color,
                                text = "Either rename your file to match (e.g." +
                                " LANT.gif), select from one of the templates" +
                                " below, or create a new template. Note: if you" +
                                " create a new template, no unit will be able to" +
                                " use the template until they download the new" +
                                " template and config file into their templates" + 
                                " folder.").pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   1   =   D r o p d o w n   M e n u
    frame_1 = Tk.Frame(root, bg = bg_color)
    frame_1.pack(pady = 5)

    # build and populate teh drowpdown menu
    options = os.listdir("./templates")
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

    button0 = Tk.Button(frame_4, 
                        text = "Select Template", 
                        command = Select_click)
    button0.pack(padx = 10, pady = 5, side = 'left')

    button1 = Tk.Button(frame_4, text = "New Template", 
                        command = New_click)
    button1.pack(padx = 10, pady = 5 , side = 'left')

    button2 = Tk.Button(frame_4, text = "Cancel", 
                        command = Cancel_click)
    button2.pack(padx = 10, pady = 5 , side = 'left')

    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", Cancel_click)
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
    c = config_read(FS.config)
    scale = scale_build_RGB(c.scale)

    # This has been moved to build_config.  It shoudl be accounted for when you
    # create a new template.
    # # if the scale wasn't already coded in the config file, code it now
    # # and save the results into the config file
    # if not "scale" in c:
    #     new_template = True
    #     if not c['scale_x'][0] == 0: scale_raw = image[:,c['scale_x'][0],:][::-1]
    #     elif not c['scale_y'][0] == 0: scale_raw = image[c['scale_y'][0],:,:]
    #     c["scale"] = scale_build_int(scale_raw)
    #     with open('./templates/' + subject + '/' + subject + '.config', 'a') as file:
    #         for s in c["scale"]:
    #             print("scale = " + str(s), file = file)
    #     scale = scale_build(c["scale"])

    # turn the image into a scalar plot and then smooth it over
    plot = plot_scale(image.copy())
    plot = plot_smooth(plot,20)
    plot = plot_smooth(plot,20)

    # FIX: this needs to move to "new template"
    # if we are creating a config file and new template then save the template
    # if not os.path.exists(FS.template):
    #     plot_temp = plot_smooth(plot,2) != 0
    #     image_template = image.copy()
    #     for i in range(3): image_template[:,:,i] = np.multiply(image[:,:,i],np.invert(plot_temp).astype(int))
    #     image_template[:,:,2] = image_template[:,:,2] + 125 * plot_temp.astype(int)

    #     # crop out a part of the image (namely the legend)
    #     ##################################################
    #     # config file: x1 = left most x, x2 =  right most x
    #     #              y1 =  top most y, y2 = bottom most y
    #     # crop the image to remove everything except the legend
    #     cv.imwrite(FS.template, image_template)
    #     if c['crop_x1'][0] !=0:
    #         if abs((c['scale_x'][0] - c['crop_x1'][0]) / x) > 0.1 or c['scale_x'] == [0]:
    #             image_template[:,0:c['crop_x1'][0],:] = \
    #                 255 * np.ones(image_template[:,0:c['crop_x1'][0],:].shape).astype(np.uint8)
    #     if c['crop_x2'][0] !=0: 
    #         if abs((c['scale_x'][0] - c['crop_x2'][0]) / x) > 0.1 or c['scale_x'] == [0]:
    #             image_template[:,c['crop_x2'][0]:y,:] = \
    #                 255 * np.ones(image_template[:,c['crop_x2'][0]:y,:].shape).astype(np.uint8)
    #     if c['crop_y1'][0] !=0: 
    #         if abs((c['scale_y'][0] - c['crop_y1'][0]) / y) > 0.1 or c['scale_y'] == [0]:
    #             image_template[0:c['crop_y1'][0],:,:] = \
    #                 255 * np.ones(image_template[0:c['crop_y1'][0],:,:].shape).astype(np.uint8)
    #     if c['crop_y2'][0] !=0: 
    #         if abs((c['scale_y'][0] - c['crop_y1'][0]) / y) > 0.1 or c['scale_y'] == [0]:
    #             image_template[c['crop_y2'][0]:x,:,:] = \
    #                 255 * np.ones(image_template[c['crop_y2'][0]:x,:,:].shape).astype(np.uint8)

    #     cv.imwrite(FS.template, image_template)


    ################################################################
    # r u n    D F T 
    ################################################################
    DFT = cv.dft(np.float32(plot),flags=cv.DFT_COMPLEX_OUTPUT)

    #################################################################
    # User defined: # DFT coefficients
    # number of terms will be ((n * 2) ^ 2) * 2
    n = 15

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
        print(str(x) + "/" + str(y) + "/" + str(n) + "/" + str(np.max(plot)) + "/" + FS.subject + "/WXYZ//", file = file)
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
