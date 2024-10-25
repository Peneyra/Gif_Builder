import numpy as np
import cv2 as cv
import imageio
import os
from tkinter import Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

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
# B u i l d   R G B   s c a l e
#####################################################################

# use a slice of RGB values to return an array of BGR integers
def scale_config(scale_raw):
    scale_out = []
    s = 0
    s_r_last = np.astype(np.array([0,0,0]),np.uint8)
    for s_r in scale_raw:
        # first, filter out black and white
        if not all(s_r > 250) and not all(s_r < 5):
            # next, check if the RGB value matches the last RGB
            if sum(np.abs(np.subtract(s_r_last,s_r))) >= 5:
                for BGR in s_r:
                    s = s * 256 + int(BGR)
                scale_out.append(s)
                s = 0
                s_r_last = s_r.copy()
    return scale_out

# use an array of BGR intgers to return the BGR values as an array
def scale_build(scale_config):
    scale = []
    for sc in scale_config:
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
    if c['crop_x1'][0] !=0: arr[:,0:c['crop_x1'][0],:    ] = np.zeros((x,  c['crop_x1'][0],z))
    if c['crop_x2'][0] !=0: arr[:,  c['crop_x2'][0]:y,:  ] = np.zeros((x,y-c['crop_x2'][0],z))
    if c['crop_y1'][0] !=0: arr[0:  c['crop_y1'][0],:,:  ] = np.zeros((    c['crop_y1'][0],y,z))
    if c['crop_y2'][0] !=0: arr[    c['crop_y2'][0]:x,:,:] = np.zeros((x-  c['crop_y2'][0],y,z))

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

def image_restore(plot,file_path,subject):
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
    if c['crop_x1'][0] !=0: image[:,0:c['crop_x1'][0],:] = image_template[:,0:c['crop_x1'][0],:].copy()
    if c['crop_x2'][0] !=0: image[:,c['crop_x2'][0]:y,:] = image_template[:,c['crop_x2'][0]:y,:].copy()
    if c['crop_y1'][0] !=0: image[0:c['crop_y1'][0],:,:] = image_template[0:c['crop_y1'][0],:,:].copy()
    if c['crop_y2'][0] !=0: image[c['crop_y2'][0]:x,:,:] = image_template[c['crop_y2'][0]:x,:,:].copy()

    return image


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

def choose_template():
    root = Tk()

    root.geometry("200x200")

    def show():
        Tk.label.config(text = clicked.get())

    options = ["stuff", "more stuff"]

    clicked = Tk.StringVar()

    clicked.set("stuff")

    drop = Tk.OptionsMenu(root, clicked, *options)
    drop.pack()

    button = Tk.Button( root, text = "click Me", command = show).pack()

    label = Tk.Label(root, text = "")
    label.pack()

    root.mainloop()


#####################################################################
# S t a r t   o f   _ _ m a i n _ _
#####################################################################
# define valid file extensions
ext_good = ['.gif','.jpg','.txt','.msg']
new_template = False

# open the image and save the dimensions
Tk().withdraw()
image_path = askopenfilename()
file_path = '/'.join(image_path.split("/")[:-1]) + '/'

if any(ext in image_path for ext in ext_good):
    # store the file name without the extension as 'subject'
    subject = image_path.split('/')[-1]
    for ext in ext_good: subject = subject.replace(ext,'')

    # if a config does not exist, create a new config file
    if not os.path.isfile('./templates/' + subject + '/' + subject + '.config'):
        if not os.path.exists('./templates/' + subject): os.mkdir('./templates/' + subject)
        with open('./templates/' + subject + '/' + subject + '.config', 'w') as file:
            # For future development: add in an option to select a pre-existing template if the template
            # does not exist.
            print("This config file is designed for use with the weather gif builing program.", file = file)
            print("It is a list of variables which the program uses to translate information ", file = file)
            print("onto a template. Each variable should be on its own line, with the variable", file = file)
            print("name on one side of an equal sign, and its integer value on the other with ", file = file)
            print("a single space on either side of the equal sign. The default values are ", file = file)
            print("zero.", file = file)
            print("crop_x1 = 0", file = file)
            print("crop_x2 = 0", file = file)
            print("crop_y1 = 0", file = file)
            print("crop_y2 = 0", file = file)
            print("scale_x = 0", file = file)
            print("scale_y = 0", file = file)
        window = Tk()
        window.wm_withdraw()
        messagebox.showinfo(title="Go fix your .config", message="We have created a config file for " + 
                            "you because your file name did not match a template. Either rename your " +
                            "file or edit the config file to input appropriate crop and scale values.")
        window.destroy()
        quit()
else:
    window = Tk()
    window.wm_withdraw()
    messagebox.showinfo(title="Wrong type of file", message="please choose a .jpg, .gif, .txt, or .msg")
    window.destroy()
    quit()
        


global c
global scale
if 'c' not in globals(): c = {}
with open('./templates/' + subject + '/' + subject + '.config', 'r') as file:
    config_contents = file.read()
    for config in config_contents.splitlines():
        if ' = ' in config:
            c_key = config.split(' = ')[0]
            c_value = config.split(' = ')[1]
            try:
                if not c_key in c: c[c_key] = []
                c[c_key].append(int(c_value))
            except:
                if not c_key in c: c[c_key] = []
                c[c_key].append(c_value)
if "scale" in c:
    scale = scale_build(c["scale"])

#####################################################################
# i m a g e   - >   m e s s a g e
#####################################################################
if ".gif" in image_path or ".jpg" in image_path:

    subject = image_path.split('/')[-1]

    if ".gif" in image_path:
        gif = imageio.mimread(image_path)
        image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in gif][0]
        subject = subject.replace(".gif","")
    else: 
        image = cv.imread(image_path)
        subject = subject.replace(".jpg","")
    x, y, z = image.shape

    # if the scale wasn't already coded in the config file, code it now
    # and save the results into the config file
    if not "scale" in c:
        new_template = True
        if not c['scale_x'][0] == 0: scale_raw = image[:,c['scale_x'][0],:][::-1]
        elif not c['scale_y'][0] == 0: scale_raw = image[c['scale_y'][0],:,:]
        c["scale"] = scale_config(scale_raw)
        with open('./templates/' + subject + '/' + subject + '.config', 'a') as file:
            for s in c["scale"]:
                print("scale = " + str(s), file = file)
        scale = scale_build(c["scale"])

    # turn the image into a scalar plot and then smooth it over
    plot = plot_scale(image.copy())

    # if we are creating a config file and new template then save the template
    if not os.path.exists('./templates/' + subject + '/' + subject + "_template.jpg"):
        plot_temp = plot_smooth(plot,2) != 0
        image_template = image.copy()
        for i in range(3): image_template[:,:,i] = np.multiply(image[:,:,i],np.invert(plot_temp).astype(int))
        image_template[:,:,2] = image_template[:,:,2] + 125 * plot_temp.astype(int)

        # crop out a part of the image (namely the legend)
        ##################################################
        # config file: x1 = left most x, x2 =  right most x
        #              y1 =  top most y, y2 = bottom most y
        # crop the image to remove everything except the legend
        cv.imwrite('./templates/' + subject + '/' + subject + "_template.jpg", image_template)
        if c['crop_x1'][0] !=0:
            if abs((c['scale_x'][0] - c['crop_x1'][0]) / x) > 0.1 or c['scale_x'] == [0]:
                image_template[:,0:c['crop_x1'][0],:] = \
                    255 * np.ones(image_template[:,0:c['crop_x1'][0],:].shape).astype(np.uint8)
        if c['crop_x2'][0] !=0: 
            if abs((c['scale_x'][0] - c['crop_x2'][0]) / x) > 0.1 or c['scale_x'] == [0]:
                image_template[:,c['crop_x2'][0]:y,:] = \
                    255 * np.ones(image_template[:,c['crop_x2'][0]:y,:].shape).astype(np.uint8)
        if c['crop_y1'][0] !=0: 
            if abs((c['scale_y'][0] - c['crop_y1'][0]) / y) > 0.1 or c['scale_y'] == [0]:
                image_template[0:c['crop_y1'][0],:,:] = \
                    255 * np.ones(image_template[0:c['crop_y1'][0],:,:].shape).astype(np.uint8)
        if c['crop_y2'][0] !=0: 
            if abs((c['scale_y'][0] - c['crop_y1'][0]) / y) > 0.1 or c['scale_y'] == [0]:
                image_template[c['crop_y2'][0]:x,:,:] = \
                    255 * np.ones(image_template[c['crop_y2'][0]:x,:,:].shape).astype(np.uint8)

        cv.imwrite('./templates/' + subject + '/' + subject + "_template.jpg", image_template)

    plot = plot_smooth(plot,20)
    plot = plot_smooth(plot,20)
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

    message_file_path = file_path + subject + ".txt"
    S = ""
    with open(message_file_path,'w') as file:
        print("R XXXXXXZ MMM YY",                                                 file = file)
        print("FM COMSUBPAC PEARL HARBOR HI",                                     file = file)
        print("TO SSBN PAC",                                                      file = file)
        print("BT",                                                               file = file)
        print("UNCLAS",                                                           file = file)
        print("SUBJ/VLF WEATHER GIF FOR " + subject.upper() + "//",               file = file)
        print("RMKS/SEE INSTRUCTIONS ON CSP WEBSITE ON HOW TO USE THIS MESSAGE.", file = file)
        print(str(x) + "/" + str(y) + "/" + str(n) + "/" + str(np.max(plot)) + "/" + subject + "/WXYZ//", file = file)
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
elif ".txt" in image_path or ".msg" in image_path:
    with open(image_path,'r') as file:
        msg = file.read()
    header = True
    footer = False
    for m in msg.splitlines():
        if header:
            if "WXYZ" in m:
                header = False
                x= int(m.split("/")[0])
                y = int(m.split("/")[1])
                n = int(m.split("/")[2])
                max = int(m.split("/")[3])
                subject = m.split("/")[4]
                i, j, index = 0, 0, 0
                i_s, j_s = [i,x-i-1], [j,y-j-1]
                # initialize the DFT
                DFT = np.zeros((x,y,2))
        else:
            n1 = 0
            while n1 + 2 <= len(m):
                if not '/' in m[n1:n1+2] and not footer:
                    val = c_str(m[n1:n1+2])
                    # place c in the array
                    k1 = int(index % 2)
                    j1 = int(((index - k1) / 2) % 2)
                    i1 = int(((index - k1 - (2 * j1)) / 4) % 2)
                    DFT[i_s[i1],j_s[j1],k1] = val
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
    plot_idft = cv.idft(DFT)


    # normalize the array and store as the output image
    plot_out = cv.magnitude(plot_idft[:,:,0], plot_idft[:,:,1])
    plot_out = np.array(max * (plot_out - np.min(plot_out)) / (np.max(plot_out) - np.min(plot_out))).astype(int)

    image = image_restore(plot_out,file_path,subject)

    cv.imwrite(file_path + subject + "_out.jpg",image)

    os.startfile(file_path + subject + "_out.jpg")