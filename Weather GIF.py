import numpy as np
import cv2 as cv
import imageio
import os
import tkinter as Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
from time import gmtime


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

test_mode = False

#####################################################################
# B u i l d   C l a s s e s 
#####################################################################
# Start with the file and file path for everything you are doing
class File_Structure:
    def update(self, subject):
        self.subject = subject
        self.template = os.getcwd() + "/templates/" + subject + "/" + subject + "_template.jpg"
        self.config = os.getcwd() + "/templates/" + subject + "/" + subject + ".config"

    # all relevant files saved as strings
    def __init__(self, orig_path):
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
    # initializes the values for the config file
    def __init__(self):
        self.crop_x1, self.crop_x2, self.crop_y1, self.crop_y2, self.scale_x, self.scale_y = np.zeros(6).astype(int)
        self.scale = []

class msg_read:
    # input a message file and parse its contents
    def __init__(self,msg):
        header = True
        footer = False
        k_mr = 0
        for m in msg.splitlines():
            if header:
                if "A1R1G2U3S5" in m:
                    header = False
                    S = m.split("/")
                    x, y, n, max = [int(k) for k in S[0:4]]
                    self.x = x
                    self.y = y
                    self.n = n
                    self.max = max
                    self.dtg = m.split("/")[4]
                    self.subject = m.split("/")[5]
                    # initialize the DFT
                    self.DFT = np.zeros((x,y,2))
                    address = DFT_mapping(n)
                    DFT_flat = np.zeros(n * n * 8).astype(int)
            elif not footer:
                m_mr = aA12dec(m[0])
                m = m[1:]
                line_int = 0
                for a in m[::-1]:
                    if a == "/":
                        footer = True
                    else:
                        line_int = (62 * line_int) + aA12dec(a)
                        if test_mode: print(line_int)
                DFT_flat_dummy = []
                while line_int > 0:
                    if line_int == m_mr:
                        line_int = 0
                    else:
                        DFT_flat_dummy.append(int(line_int % (m_mr)))
                        line_int = int((line_int - (line_int % (m_mr))) // (m_mr))
                    if test_mode: print(line_int)
                if test_mode: print(DFT_flat_dummy)
                for dfd in DFT_flat_dummy[::-1]:
                    DFT_flat[k_mr] = dfd
                    k_mr += 1
        k_df = 0
        if test_mode:
            with open("./DFT_flat_read.txt",'w') as file:
                for f in DFT_flat:
                    if test_mode: print(f, file = file)                       
        for [i,j] in address:
            i_s, j_s, k_s = [i,x-i-1], [j,y-j-1], [0, 1]
            for i1 in i_s:
                for j1 in j_s:
                    for k1 in k_s:
                        self.DFT[i1,j1,k1] = coeff_unround(DFT_flat[k_df])
                        k_df += 1

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
        print("crop_x1 = " + str(c.crop_x1),                                                  file = file)
        print("crop_y1 = " + str(c.crop_y1),                                                  file = file)
        print("crop_x2 = " + str(c.crop_x2),                                                  file = file)
        print("crop_y2 = " + str(c.crop_y2),                                                  file = file)
        print("scale_x = " + str(c.scale_x),                                                  file = file)
        print("scale_y = " + str(c.scale_y),                                                  file = file)
        for s in c.scale:
            print("scale = " + str(s),                                                        file = file)

#####################################################################
# C h e c k   f i l e   t y p e
#####################################################################
# Verifies the file is of the correct type.  If not, pop up an error
# message
def check_type(orig_path):
    # define valid file extensions
    ext_good = ['.gif','.jpg','.txt','.eml']
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
    if c.crop_y1 !=0: arr[:c.crop_y1, :, :] = np.zeros(arr[:c.crop_y1, :, :].shape)
    if c.crop_y2 !=0: arr[c.crop_y2:, :, :] = np.zeros(arr[c.crop_y2:, :, :].shape)
    if c.crop_x1 !=0: arr[:, :c.crop_x1, :] = np.zeros(arr[:, :c.crop_x1, :].shape)
    if c.crop_x2 !=0: arr[:, c.crop_x2:, :] = np.zeros(arr[:, c.crop_x2:, :].shape)

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

# function to smooth out the colors and crop out the borders
def plot_smooth(arr,repeat):
    arr_out = np.copy(arr)
    # use queen smoothing to get rid of non-colored lines
    for r in range(repeat):
        arr_tmp = np.roll(np.roll(np.copy(arr_out), -1, axis = 0), -1, axis = 1).astype(np.float64)
        arr_tmp[0, :] = np.zeros_like(arr_tmp[0, :])
        arr_tmp[-1,:] = np.zeros_like(arr_tmp[-1,:])
        arr_tmp[:, 0] = np.zeros_like(arr_tmp[:, 0])
        arr_tmp[:,-1] = np.zeros_like(arr_tmp[:,-1])
        arr_add = np.zeros_like(arr_out).astype(np.float64)
        arr_cnt = np.zeros_like(arr_out).astype(np.float64)

        for (i, j) in [(1,0),(1,0),(1,1),(1,1),(-1,0),(-1,0),(-1,1),(-1,1)]:
            arr_tmp = np.roll(arr_tmp, i, axis = j)
            arr_add = arr_add + arr_tmp
            arr_cnt = arr_cnt + np.array(arr_tmp != 0).astype(type(arr_cnt[0,0]))

        arr_add = np.divide(arr_add, arr_cnt, out = np.zeros_like(arr_add), where=arr_cnt!=0)

        if test_mode: cv.imwrite('./test_add_' + str(r) + '.jpg', 10 * arr_add)
        if test_mode: cv.imwrite('./test_cnt_' + str(r) + '.jpg', 10 * arr_cnt)

        arr_out = arr_out + np.array(np.multiply(arr_add,arr_out == 0)).astype(np.uint8)

        if test_mode: cv.imwrite('./test_' + str(r) + '.jpg', 10 * arr_out)
    return arr_out

# function to smooth out the colors and crop out the borders
def plot_round(arr):
    repeat = 10
    arr_out = np.copy(arr)
    # use queen smoothing to get rid of non-colored lines
    for r in range(repeat):
        arr_tmp = np.roll(np.roll(np.copy(arr_out), -1, axis = 0), -1, axis = 1).astype(np.float64)
        # zero the edges
        arr_tmp[0, :] = np.zeros_like(arr_tmp[0, :])
        arr_tmp[-1,:] = np.zeros_like(arr_tmp[-1,:])
        arr_tmp[:, 0] = np.zeros_like(arr_tmp[:, 0])
        arr_tmp[:,-1] = np.zeros_like(arr_tmp[:,-1])
        arr_add = np.zeros_like(arr_out).astype(np.float64)
        arr_cnt = np.zeros_like(arr_out).astype(float)

        # queen smoothing
        for (i, j) in [(1,0),(1,0),(1,1),(1,1),(-1,0),(-1,0),(-1,1),(-1,1)]:
            arr_tmp = np.roll(arr_tmp, i, axis = j)
            arr_add = arr_add + arr_tmp
            arr_cnt = arr_cnt + np.array(arr_tmp != 0).astype(type(arr_cnt[0,0]))

        arr_cnt = arr_cnt * 6
        arr_add = np.divide(arr_add, arr_cnt, out = np.zeros_like(arr_add), where=arr_cnt!=0)

        if test_mode: cv.imwrite('./test_add_' + str(r) + '.jpg', 10 * arr_add)
        if test_mode: cv.imwrite('./test_cnt_' + str(r) + '.jpg', 10 * arr_cnt)

        arr_out = arr_out + np.array(np.multiply(arr_add,arr_out == 0)).astype(np.uint8)

        if test_mode: cv.imwrite('./test_' + str(r) + '.jpg', 10 * arr_out)
    return arr_out

def plot_mirror_edge(arr):
    # start by determining the top-bottom-left-right boundaries of the plot
    (x_pme, y_pme) = arr.shape
    crop_y1, crop_y2, crop_x1, crop_x2 = 0, 0, 0, 0

    for i in range(x_pme):
        if np.sum(arr[i,:]) != 0 and crop_x1 == 0:
            crop_x1 = i
        if np.sum(arr[i,:]) == 0 and crop_x1 != 0 and crop_x2 == 0:
            crop_x2 = i - 1

    for i in range(y_pme):
        if np.sum(arr[:,i]) != 0 and crop_y1 == 0:
            crop_y1 = i
        if np.sum(arr[:,i]) == 0 and crop_y1 != 0 and crop_y2 == 0:
            crop_y2 = i - 1

    arr[0:crop_x1, :] = np.flip(arr[crop_x1:2*crop_x1, :], axis = 0)
    arr[crop_x2:x_pme, :] = np.flip(arr[(2*crop_x2)-x_pme:crop_x2, :], axis = 0)

    arr[:,0:crop_y1] = np.flip(arr[:, crop_y1:2*crop_y1], axis = 1)
    arr[:,crop_y2:y_pme] = np.flip(arr[:, (2*crop_y2)-y_pme:crop_y2], axis = 1)
    return arr


def image_restore(plot,subject,scale):
    x, y = plot.shape
    image = np.zeros((x,y,3)).astype(int)
    empty = [0, 0, 124]
    var = 50
    if test_mode: cv.imwrite("./test_restore_plot.jpg", plot * (256 / np.max(plot)))

    image_template = cv.imread('./templates/' + subject + '/' + subject + "_template.jpg")

    plot_bool = np.ones((x,y)).astype(bool)
    for i in range(3): plot_bool = np.multiply(plot_bool, abs(image_template[:,:,i].astype(int) - empty[i]) < var)

    # change the scalar plot to an RGB image
    for i in range(len(scale))[1:]:
        im = np.zeros((x,y,3))
        for j in range(3):
            im[:,:,j] = np.array(plot == i).astype(int) * scale[i, j]
        image = image + im
        if test_mode: cv.imwrite("./test_restore_" + str(i) + ".jpg",image)

    for i in range(3): 
        image[:,:,i] = np.multiply(np.array(plot_bool).astype(int),image[:,:,i]) + np.multiply(np.array(~plot_bool).astype(int), image_template[:,:,i])
        if test_mode: cv.imwrite("./test_restore_f" + str(i) + ".jpg",image)

    # crop out a part of the image (namely the legend)
    ##################################################
    # config file: x1 = left most x, x2 = right most x
    #              y1 = top most y,  y2 = bottom most y

    # crop the image to remove the legend
    if c.crop_y1 !=0: image[:c.crop_y1, :, :] =  image_template[:c.crop_y1, :, :].copy()
    if test_mode:
        cv.imwrite("./test_restore_cropped1.jpg",image_template[:c.crop_y1, :, :].copy())
        cv.imwrite("./test_restore_crop1.jpg",image)
    if c.crop_y2 !=0: image[c.crop_y2:, :, :] =  image_template[c.crop_y2:, :, :].copy()
    if test_mode:
        cv.imwrite("./test_restore_cropped2.jpg",image_template[c.crop_y2:, :, :].copy())
        cv.imwrite("./test_restore_crop2.jpg",image)
    if c.crop_x1 !=0: image[:, :c.crop_x1, :] =  image_template[:, :c.crop_x1, :].copy()
    if test_mode:
        cv.imwrite("./test_restore_cropped3.jpg",image_template[:, :c.crop_x1, :].copy())
        cv.imwrite("./test_restore_crop3.jpg",image)
    if c.crop_x2 !=0: image[:, c.crop_x2:, :] =  image_template[:, c.crop_x2:, :].copy()
    if test_mode:
        cv.imwrite("./test_restore_cropped4.jpg",image_template[:, c.crop_x2:, :].copy())
        cv.imwrite("./test_restore_crop4.jpg",image)

    image = cv.putText(image, m.subject + " - " + m.dtg, (c.crop_x1, c.crop_y2 + 5), cv.FONT_HERSHEY_SIMPLEX,
                       .5, (0,0,0), 1, cv.LINE_AA, False)

    return image


#####################################################################
# C o n v e r t   b a s e   1 0   < - >   b a s e   6 2
#####################################################################
# function to compress each coefficient into a single character from
# a DFT array normalized to -1000 -> 1000
def dec2aA1(i):    
    if i < 10: return         str(i)
    if i < 36: return         chr(i + ord('A') - 10)
    return                    chr(i + ord('a') - 36)

def aA12dec(s):
    try:
        if int(s) < 10: return int(s)
    except:
        None
    if ord(s) < ord('a'): 
        return                 int(ord(s) + 10 - ord('A'))
    else: return               int(ord(s) + 36 - ord('a'))

def coeff_round(x):
    k_cr = 54
    n_cr = 3
    for i in range(n_cr):
        for j in range(9):
            if x > (9.5-j) * (10 ** (2 - i)): return k_cr
            k_cr -= 1
            if x < (j-9.5) * (10 ** (2 - i)): return k_cr
            k_cr -= 1
    return 0

def coeff_unround(x):
    if x == 0: return 0
    k_cu = 1
    n_cu = 3
    for i in range(n_cu):
        for j in range(2,11):
            if x == k_cu: return (-1) * j * (10 ** i)
            k_cu += 1
            if x == k_cu: return        j * (10 ** i)
            k_cu += 1
    return 0

def DFT_mapping(n):
    # save all coefficients to a single flattened array organized by:
    # 1 2 3 4 5 ...
    # 2 2 3 4 5 ...
    # 3 3 3 4 5 ...
    # 4 4 4 4 5 ...
    # 5 5 5 5 5 ...
    # This organization will assist with maximum compression of the follow on message
    # map all the addresses in the order you want them
    address = [[0,0]] * (n * n)
    k_a = 1
    for k in range(1,n):
        j = k
        for i in range(k):
            address[k_a] = [i, j]
            k_a += 1
        address[k_a] = [k, k]
        k_a += 1
        i = k
        for j in range(k):
            address[k_a] = [i, j]
            k_a += 1
    
    return address

def msg_nextline_build(flat):
    
    # define the maximum for the selected coefficients.  Add one
    # to allow the modulo function to produce the max value
    # (otherwise, when the code runs coeff % max = 0 when we want
    # the maximum out.)
    m = int(max(flat)) + 1
    line_str = dec2aA1(m)

    if flat[0] == 0:
        line_int = m
    else:
        line_int = int(0)

    for f in flat:
        line_int = (m * line_int) + int(f)
        if test_mode: print(line_int)

    while line_int > 0:
        line_str += dec2aA1(line_int % 62)
        line_int = (line_int - (line_int % 62)) // 62
        # if test_mode: print(f"{line_int:d}")

    return line_str

def month_name(m):
    if m == 1: return "JAN"
    elif m == 2: return "FEB" 
    elif m == 3: return "MAR" 
    elif m == 4: return "APR" 
    elif m == 5: return "MAY" 
    elif m == 6: return "JUN" 
    elif m == 7: return "JUL" 
    elif m == 8: return "AUG" 
    elif m == 9: return "SEP" 
    elif m == 10: return "OCT" 
    elif m == 11: return "NOV" 
    elif m == 12: return "DEC"
    else: return None

def allowalphanumeric(text):
    return text == "" or text.isalnum()

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
    c = Config_File()

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
            if test_mode:
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
            if test_mode: print("you clicked on (x,y) = (" + print(e.x) + ", " + print(e.y) + ")")

            button_next.pack(padx = 10, pady = 5, side = 'left')

            return([e.x, e.y])

    def show(im_name):
        global label_image
        global la_x
        global la_y
        im_dict[im_name + "_tk"] = ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(im_dict[im_name], cv.COLOR_BGR2RGB)).resize((la_x,la_y)))
        label_image.config(image = im_dict[im_name + "_tk"])

    def cancel_click():
        print("cancel clicked")
        global options
        if options == []:
            global quitter
            quitter = "quit"
            root.destroy()
        else:
            global image
            root.destroy()
            choose_template(image)

    def next_click():
        print("next clicked")
        global template_index
        global label_image

        template_index += 1

        #####################################################################
        # A d v a n c e   y o u r   t e m p l a t e
        if template_index < 6: 
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
            image_template[:c.crop_y1, :, :] = np.uint8(255)
            image_template[c.crop_y2:, :, :] = np.uint8(255)
            image_template[:, :c.crop_x1, :] = np.uint8(255)
            image_template[:, c.crop_x2:, :] = np.uint8(255)

            # build the scale
            for delta in [-10,-5,0,5,10]:
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
            plot_mask = np.repeat(np.array(plot_smooth(plot_template,2) == 0).astype(int)[:,:,np.newaxis], 3, axis = 2)

            image_template = np.multiply(image_template, plot_mask).astype(np.uint8)
            image_template[:,:,2] = image_template[:,:,2] + 125 * np.array(plot_mask[:,:,2] == 0).astype(int)
            
            # put the template color scale back in
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
            template_index -= 1
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
        global image
        if subject_name.get() != "":
            FS.update(subject_name.get())
            if os.path.isfile(FS.template):
                if askquestion_exists() == "no":
                    return
            if not os.path.exists(FS.templates_folder + FS.subject): os.mkdir(FS.templates_folder + FS.subject)
            cv.imwrite(FS.template,im_dict["image_template"])
            config_write(c)
            root.destroy()
            choose_template(image)
        else:
            Tk.messagebox.showerror("Missing AOR name","Please name your template.")

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
        global quitter
        print("cancel clicked")
        root.destroy()
        quitter = "quit"

    def new_click():
        # FIX build out what to do if the template does not exist
        global image
        print("new clicked")
        root.destroy()
        build_template(image)

    def select_click():
        global subject
        global dtg
        if not "Z" in entryDTG.get().upper():
            Tk.messagebox.showerror("Missing DTG","Input the DTG shown in the image. Entry must contain a Z.")
        else:
            dtg = entryDTG.get()
            print("select clicked")
            FS.update(selection.get())
            root.destroy()

    # set your global variables
    global quitter
    quitter = "never"
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
                            "Choose a template and enter the DTG the image shows.").pack(anchor = "w")
    instructions_text = Tk.Label(frame_0, justify = "left", wraplength = image_x,
                                font = ("Arial", 12), bg = bg_color,
                                text = "If a template doesn't already exist, create " +
                                "a new template.").pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   1   =   D r o p d o w n   M e n u,   
    # D T G ,   B u t t o n s
    frame_1 = Tk.Frame(root, bg = bg_color)
    frame_1.pack(pady = 5)

    # build and populate teh drowpdown menu
    global options
    options = []
    if os.path.exists("./templates"):
        for o in os.listdir("./templates"):
            o_path = "./templates/" + o + "/" + o
            if os.path.exists(o_path + ".config") and os.path.exists(o_path + "_template.jpg"):
                options.append(o)
    else:
        os.mkdir("./templates")

    if options == []:
        new_click()
    else:
        selection = Tk.StringVar()
        selection.set(options[0])
        # display the dropdown menu
        drop = Tk.OptionMenu(frame_1, selection, *options, command = show)
        drop.pack(padx = 10, pady = 5, side = 'left')
        
        # display the DTG entry.  Populate it with the current ZULU time
        zulu = f"{gmtime().tm_mday:02}" + f"{gmtime().tm_hour:02}" + "00Z" + \
            month_name(gmtime().tm_mon) + str(gmtime().tm_year)


        entryDTG = Tk.Entry(frame_1, validate = "key", validatecommand = (root.register(allowalphanumeric), "%P"))
        entryDTG.pack(padx = 10, pady = 5 , side = 'left')
        entryDTG.delete(0,Tk.END)
        entryDTG.insert(0,zulu)

        if not selection.get() == "":
            button0 = Tk.Button(frame_1, 
                                text = "Select Template", 
                                command = select_click)
            button0.pack(padx = 10, pady = 5, side = 'left')

        button1 = Tk.Button(frame_1, text = "New Template", 
                            command = new_click)
        button1.pack(padx = 10, pady = 5 , side = 'left')

        button2 = Tk.Button(frame_1, text = "Cancel", 
                            command = cancel_click)
        button2.pack(padx = 10, pady = 5 , side = 'left')

        #####################################################################
        # B u i l d   F r a m e   2   =   I m a g e s
        frame_2 = Tk.Frame(root, bg = bg_color)
        frame_2.pack(padx = 10, pady = 5)

        #####################################################################
        # B u i l d   F r a m e   2   T e m p l a t e
        # populate a dictionary of template images
        template_dict = {}
        for op in options:
            os.chdir(FS.cwd + "/templates/" + op)
            template_dict[op] = ImageTk.PhotoImage(Image.open(op + "_template.jpg").resize((image_x, image_y)))
        os.chdir(FS.cwd)
        frame_2_template = Tk.Frame(frame_2, height = image_y, width = image_x, bg = bg_color)
        frame_2_template.pack(padx = 10, pady = 5, side = 'left')
        global label_image
        label_image = Tk.Label(frame_2_template, image = template_dict[selection.get()])
        label_image.pack()

        #####################################################################
        # B u i l d   F r a m e   2   I m a g e
        # populate a dictionary of template images
        frame_2_image = Tk.Frame(frame_2, height = image_y, width = image_x, bg = bg_color)
        frame_2_image.pack(padx = 10, pady = 5, side = 'left')
        template_dict["orig"] = ImageTk.PhotoImage(Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB)).resize((image_x, image_y)))
        orig_image = Tk.Label(frame_2_image, image = template_dict["orig"])
        orig_image.pack()

        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", cancel_click)
        root.mainloop()

#####################################################################
# S t a r t   o f   _ _ m a i n _ _
#####################################################################
# open a file browser and save the file name as orig_path
orig_path = askopenfilename()

FS = File_Structure(orig_path)

#####################################################################
# i m a g e   - >   m e s s a g e
#####################################################################
if FS.ext.lower() == ".gif":
    gif = imageio.mimread(orig_path)
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in gif][0]
if FS.ext.lower() == ".jpg":
    image = cv.imread(orig_path)

#####################################################################
# i m a g e   - >   m e s s a g e
#####################################################################
# if we've defined an image, otherwise skip to except
if FS.ext.lower() == ".gif" or FS.ext.lower() == ".jpg":
    x, y, z = image.shape

    if test_mode:
        dtg = "000000ZJAN25"
    else:
        choose_template(image)

    if quitter == "never":
        if not "c" in globals(): c = config_read(FS.config)
        if not "scale" in globals(): scale = scale_build_RGB(c.scale)

        # turn the image into a scalar plot and then smooth it over
        plot = plot_scale(image.copy())
        plot = np.array(plot).astype(float)
        plot = plot_smooth(plot,2)
        plot = plot_mirror_edge(plot)
        plot = plot_round(plot)
        if test_mode: cv.imwrite("./test_build_plot_smooth.jpg", plot * (256 / np.max(plot)))

        ################################################################
        # r u n    D F T 
        ################################################################
        DFT = cv.dft(np.float32(plot),flags=cv.DFT_COMPLEX_OUTPUT)

        #################################################################
        # B u i l d   a   c u r t a i l e d   D F T 
        # Use the coefficient list to build out a new DFT
        # I have tried a few different shapes.  Turns out that a square
        # at each corner of the 
        (x_p, y_p) = plot.shape
        
        # only retain a nxn box in each quadrant of the DFT
        n = 12
        DFT[n:x_p-1-n,:,:] = np.zeros_like(DFT[n:x_p-1-n,:,:])
        DFT[:,n:y_p-1-n,:] = np.zeros_like(DFT[:,n:y_p-1-n,:])

        # normalize so all values are between -1000 and 1000
        DFT_max = 1000
        DFT = DFT * (DFT_max / np.max(np.abs(DFT)))

        # in test mode: build an image as a visual representation 
        # of the DFT coefficients
        if test_mode:
            dft_image_re = np.zeros((2*n + 1, 2*n + 1))
            dft_image_im = np.zeros((2*n + 1, 2*n + 1))

            dft_image_re[   :n,   :n] = DFT[-n: ,-n: ,0]
            dft_image_re[n+1: ,   :n] = DFT[  :n,-n: ,0]
            dft_image_re[   :n,n+1: ] = DFT[-n: ,  :n,0]
            dft_image_re[n+1: ,n+1: ] = DFT[  :n,  :n,0]

            dft_image_im[   :n,   :n] = DFT[-n: ,-n: ,1]
            dft_image_im[n+1: ,   :n] = DFT[  :n,-n: ,1]
            dft_image_im[   :n,n+1: ] = DFT[-n: ,  :n,1]
            dft_image_im[n+1: ,n+1: ] = DFT[  :n,  :n,1]

            dft_image_re_log = np.log10(np.abs(dft_image_re))
            dft_image_im_log = np.log10(np.abs(dft_image_im))

            cv.imwrite("./test_build_DFT_image_re.jpg", dft_image_re * (256 / np.max(dft_image_re)))
            cv.imwrite("./test_build_DFT_image_im.jpg", dft_image_im * (256 / np.max(dft_image_im)))
            cv.imwrite("./test_build_DFT_image_re_log.jpg", dft_image_re_log * (256 / np.max(dft_image_re_log)))
            cv.imwrite("./test_build_DFT_image_im_log.jpg", dft_image_im_log * (256 / np.max(dft_image_im_log)))
        

            # in test mode: calculate the RMS due to curtailment
            IDFT = cv.idft(DFT)
            IDFT = cv.magnitude(IDFT[:,:,0],IDFT[:,:,1])
            IDFT = IDFT * (np.max(plot) / np.max(IDFT))
            IDFT = np.round(IDFT).astype(int)
            IDFT = np.multiply(IDFT, plot >= 1)
            cv.imwrite("./test_build_DFT_small.jpg", IDFT * (256 / np.max(IDFT)))
            diff = ((plot - IDFT) ** 2) / len(plot.flatten())
            RMS = np.sqrt(np.sum(diff))
            print("##################################")
            print("# C u r t a i l e d   D F T")
            print("# n = " + str(n))
            print("# RMS = " + str(RMS))
                
            DFT_rounded = DFT.copy()
            for i in range(n):
                for j in range(n):
                    DFT_rounded[i,      j      ,0] = coeff_round(DFT_rounded[i,      j      ,0])
                    DFT_rounded[x_p-1-i,j      ,0] = coeff_round(DFT_rounded[x_p-1-i,j      ,0])
                    DFT_rounded[i,      y_p-1-j,0] = coeff_round(DFT_rounded[i,      y_p-1-j,0])
                    DFT_rounded[x_p-1-i,y_p-1-j,0] = coeff_round(DFT_rounded[x_p-1-i,y_p-1-j,0])
                    DFT_rounded[i,      j      ,1] = coeff_round(DFT_rounded[i,      j      ,1])
                    DFT_rounded[x_p-1-i,j      ,1] = coeff_round(DFT_rounded[x_p-1-i,j      ,1])
                    DFT_rounded[i,      y_p-1-j,1] = coeff_round(DFT_rounded[i,      y_p-1-j,1])
                    DFT_rounded[x_p-1-i,y_p-1-j,1] = coeff_round(DFT_rounded[x_p-1-i,y_p-1-j,1])

            for i in range(n):
                for j in range(n):
                    DFT_rounded[i,      j      ,0] = coeff_unround(DFT_rounded[i,      j      ,0])
                    DFT_rounded[x_p-1-i,j      ,0] = coeff_unround(DFT_rounded[x_p-1-i,j      ,0])
                    DFT_rounded[i,      y_p-1-j,0] = coeff_unround(DFT_rounded[i,      y_p-1-j,0])
                    DFT_rounded[x_p-1-i,y_p-1-j,0] = coeff_unround(DFT_rounded[x_p-1-i,y_p-1-j,0])
                    DFT_rounded[i,      j      ,1] = coeff_unround(DFT_rounded[i,      j      ,1])
                    DFT_rounded[x_p-1-i,j      ,1] = coeff_unround(DFT_rounded[x_p-1-i,j      ,1])
                    DFT_rounded[i,      y_p-1-j,1] = coeff_unround(DFT_rounded[i,      y_p-1-j,1])
                    DFT_rounded[x_p-1-i,y_p-1-j,1] = coeff_unround(DFT_rounded[x_p-1-i,y_p-1-j,1])

            dft_image_rounded_re = np.zeros((2*n + 1, 2*n + 1))
            dft_image_rounded_im = np.zeros((2*n + 1, 2*n + 1))

            dft_image_rounded_re[   :n,   :n] = DFT_rounded[-n: ,-n: ,0]
            dft_image_rounded_re[n+1: ,   :n] = DFT_rounded[  :n,-n: ,0]
            dft_image_rounded_re[   :n,n+1: ] = DFT_rounded[-n: ,  :n,0]
            dft_image_rounded_re[n+1: ,n+1: ] = DFT_rounded[  :n,  :n,0]

            dft_image_rounded_im[   :n,   :n] = DFT_rounded[-n: ,-n: ,1]
            dft_image_rounded_im[n+1: ,   :n] = DFT_rounded[  :n,-n: ,1]
            dft_image_rounded_im[   :n,n+1: ] = DFT_rounded[-n: ,  :n,1]
            dft_image_rounded_im[n+1: ,n+1: ] = DFT_rounded[  :n,  :n,1]

            dft_image_rounded_re_log = np.log10(np.abs(dft_image_rounded_re))
            dft_image_rounded_im_log = np.log10(np.abs(dft_image_rounded_im))

            cv.imwrite("./test_build_DFT_image_rounded_re.jpg", dft_image_rounded_re * (256 / np.max(dft_image_rounded_re)))
            cv.imwrite("./test_build_DFT_image_rounded_im.jpg", dft_image_rounded_im * (256 / np.max(dft_image_rounded_im)))
            cv.imwrite("./test_build_DFT_image_rounded_re_log.jpg", dft_image_rounded_re_log * (256 / np.max(dft_image_rounded_re_log)))
            cv.imwrite("./test_build_DFT_image_rounded_im_log.jpg", dft_image_rounded_im_log * (256 / np.max(dft_image_rounded_im_log)))

            IDFT = cv.idft(DFT_rounded)
            IDFT = cv.magnitude(IDFT[:,:,0],IDFT[:,:,1])
            IDFT = IDFT * (np.max(plot) / np.max(IDFT))
            IDFT = np.round(IDFT).astype(int)
            IDFT = np.multiply(IDFT, plot >= 1)
            cv.imwrite("./test_build_DFT_rounded_small.jpg", IDFT * (256 / np.max(IDFT)))
            diff = ((plot - IDFT) ** 2) / len(plot.flatten())
            RMS = np.sqrt(np.sum(diff))
            print("##################################")
            print("# R o u n d e d   D F T")
            print("# n = " + str(n))
            print("# RMS = " + str(RMS))       

            # in test mode: build an image as a visual representation 
            # of the DFT coefficients
            dft_image_round_re = np.zeros((2*n + 1, 2*n + 1))
            dft_image_round_im = np.zeros((2*n + 1, 2*n + 1))

            dft_image_round_re[   :n,   :n] = DFT_rounded[-n: ,-n: ,0]
            dft_image_round_re[n+1: ,   :n] = DFT_rounded[  :n,-n: ,0]
            dft_image_round_re[   :n,n+1: ] = DFT_rounded[-n: ,  :n,0]
            dft_image_round_re[n+1: ,n+1: ] = DFT_rounded[  :n,  :n,0]

            dft_image_round_im[   :n,   :n] = DFT_rounded[-n: ,-n: ,1]
            dft_image_round_im[n+1: ,   :n] = DFT_rounded[  :n,-n: ,1]
            dft_image_round_im[   :n,n+1: ] = DFT_rounded[-n: ,  :n,1]
            dft_image_round_im[n+1: ,n+1: ] = DFT_rounded[  :n,  :n,1]

            dft_image_round_re_log = np.log10(np.abs(dft_image_re))
            dft_image_round_im_log = np.log10(np.abs(dft_image_im))

            cv.imwrite("./test_build_DFT_image_re.jpg", dft_image_re * (256 / np.max(dft_image_re)))
            cv.imwrite("./test_build_DFT_image_im.jpg", dft_image_im * (256 / np.max(dft_image_im)))
            cv.imwrite("./test_build_DFT_image_re_log.jpg", dft_image_re_log * (256 / np.max(dft_image_re_log)))
            cv.imwrite("./test_build_DFT_image_im_log.jpg", dft_image_im_log * (256 / np.max(dft_image_im_log)))
        
        address = DFT_mapping(n)
        DFT_flat = np.zeros(n * n * 8).astype(int)
        k_df = 0
        for [i,j] in address:
            i_s, j_s, k_s = [i,x-i-1], [j,y-j-1], [0, 1]
            for i1 in i_s:
                for j1 in j_s:
                    for k1 in k_s:
                        DFT_flat[k_df] = int(coeff_round(DFT[i1,j1,k1]))
                        if test_mode: print(str(DFT[i1,j1,k1]) + " " + str(coeff_unround(coeff_round(DFT[i1,j1,k1]))))
                        k_df += 1
        if test_mode: 
            with open("./DFT_flat_write.txt",'w') as file:
                for f in DFT_flat:
                    print(f, file = file)

        # k_df below is used to mark the last written coefficent
        line_limit = 62 ** 68
        k_df = 0
        msg_bulk = ""
        for k in range(1,len(DFT_flat)):
            if int(max(DFT_flat[k_df:k]) + 1) ** (k - k_df) > line_limit:
                if test_mode:
                    print("coefficients " + str(k_df) + " through " + str(k-2))
                    print(DFT_flat[k_df:k-1])
                # start a new line with the character for the max coefficient
                # on the line
                if msg_bulk != "": msg_bulk = msg_bulk + "\n"
                msg_bulk += msg_nextline_build(DFT_flat[k_df:k-1])
                
                k_df = k - 1

        k = len(DFT_flat)
        if test_mode:
            print("coefficients " + str(k_df) + " through " + str(k-1))
            print(DFT_flat[k_df:k])
        if msg_bulk != "": msg_bulk = msg_bulk + "\n"
        msg_bulk += msg_nextline_build(DFT_flat[k_df:k]) 

        if len(msg_bulk.splitlines()[-1]) > 67: msg_bulk += "\n"
        msg_bulk += "//"

        # save the values of the DFT to a file
        message_file_path = FS.orig_folder + "/" + FS.subject + ".txt"

        with open(message_file_path,'w') as file:
            if os.path.exists(FS.cwd + "/Message Template.txt"):
                with open("Message Template.txt", "r") as file_r: message_template = file_r.read()
                message_template_intro = message_template.split("<message>\n")[0]
                message_template_outro = message_template.split("<message>\n")[1]
                for m_t in message_template_intro.splitlines(): print(m_t, file = file)
            print(str(x) + "/" + 
                str(y) + "/" + 
                str(n) + "/" + 
                str(int(np.max(plot))) + "/" + 
                dtg + "/" +
                FS.subject + "/A1R1G2U3S5/",                                 file = file)
            print(msg_bulk,                                                file = file)
            if os.path.exists(FS.cwd + "/Message Template.txt"):
                for m_t in message_template_outro.splitlines(): print(m_t, file = file)
        os.startfile(message_file_path)

#####################################################################
# m e s s a g e   - >   i m a g e
#####################################################################
elif FS.ext.lower() == ".txt" or FS.ext.lower() == ".eml":
    with open(orig_path,'r') as file: msg = file.read()
    m = msg_read(msg)
    plot_idft = cv.idft(m.DFT)

    FS.update(m.subject)
    c = config_read(FS.config)
    scale = scale_build_RGB(c.scale)

    # normalize the array and store as the output image
    plot_out = cv.magnitude(plot_idft[:,:,0], plot_idft[:,:,1])
    plot_out = np.array(m.max * (plot_out - np.min(plot_out)) / (np.max(plot_out) - np.min(plot_out))).astype(int)

    image = image_restore(plot_out,m.subject,scale)

    cv.imwrite(FS.orig_folder + m.subject + "_out.jpg",image)

    os.startfile(FS.orig_folder + m.subject + "_out.jpg")
