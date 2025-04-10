import numpy as np
import cv2 as cv
import imageio
import os
import tkinter as Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
from time import gmtime
import yaml
import plot

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

class msg_read:
    # input a message file and parse its contents
    def __init__(self,msg):
        header, footer = True, False
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
            with open("./debug/DFT_flat_read.txt",'w') as file:
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
def check_type(orig_path):
    # Verifies the file is of the correct type.  If not, pop up an error
    # message
    # define valid file extensions
    ext_good = ['.gif','.jpg','.txt','.eml']
    if orig_path == "":
        quit()
    else:
        for e in ext_good:
            if orig_path[len(orig_path)-4:] == e: return e
    root = Tk.Tk()
    root.wm_withdraw()
    messagebox.showinfo(
        title="Wrong type of file", 
        message="Please choose a .jpg, .gif, .txt, or .msg"
    )
    root.destroy()
    quit()

def msg_nextline_build(flat):
    # define the maximum for the selected coefficients.  Add one
    # to allow the modulo function to produce the max value
    # (otherwise, when the code runs coeff % max = 0 when we want
    # the maximum out.)
    # FIX: need to add a second mapping character to express
    # how many coefficients are written to the line
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
def allowalphanumeric(text):
    return text == "" or text.isalnum()
# open a file browser and save the file name as orig_path
orig_path = askopenfilename()

print(orig_path)
if not orig_path == "":
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

        if test_mode:
            dtg = "000000ZJAN25"
            quitter = "never"
        else:
            choose_template(image)

        if quitter == "never":
            if not "c" in globals(): c = config_read(FS.config)
            if not "scale" in globals(): scale = scale_build_RGB(c.scale)

            t, b, l, r = get_tblr(image)

            # turn the image into a scalar plot and then smooth it over
            plot = np.array(plot_scale(image[t:b,l:r,:])).astype(float)
            x, y = plot.shape
            if test_mode: cv.imwrite("./debug/test_build_plot_raw.jpg", plot * (256 / np.max(plot)))
            plot = plot_smooth(plot,2)
            if test_mode: cv.imwrite("./debug/test_build_plot_smooth.jpg", (plot + 1 - np.min(plot)) * (256 / np.max(plot * 2)))

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

            if test_mode:            
                # in test mode: build an image as a visual representation 
                # of the DFT coefficients
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

                cv.imwrite("./debug/test_build_DFT_image_re.jpg", dft_image_re * (256 / np.max(dft_image_re)))
                cv.imwrite("./debug/test_build_DFT_image_im.jpg", dft_image_im * (256 / np.max(dft_image_im)))
                cv.imwrite("./debug/test_build_DFT_image_re_log.jpg", dft_image_re_log * (256 / np.max(dft_image_re_log)))
                cv.imwrite("./debug/test_build_DFT_image_im_log.jpg", dft_image_im_log * (256 / np.max(dft_image_im_log)))
            
                # write the full DFT
                DFT_0 = cv.dft(np.float32(plot),flags=cv.DFT_COMPLEX_OUTPUT)
                # dft_image_full_re = np.roll(np.roll(np.log(DFT[:,:,0]), len(DFT)//2, axis = 0), len(DFT[0])//2, axis = 1)
                # dft_image_full_im = np.roll(np.roll(np.log(DFT[:,:,1]), len(DFT)//2, axis = 0), len(DFT[0])//2, axis = 1)
                dft_image_full_re = np.roll(np.roll(np.log10(np.abs(DFT_0[:,:,0])), len(DFT_0)//2, axis = 0), len(DFT_0[0])//2, axis = 1)
                dft_image_full_im = np.roll(np.roll(np.log10(np.abs(DFT_0[:,:,1])), len(DFT_0)//2, axis = 0), len(DFT_0[0])//2, axis = 1)
                cv.imwrite("./debug/test_build_DFT_image_full_re_log.jpg", dft_image_full_re * (256 / np.max(dft_image_full_re)))
                cv.imwrite("./debug/test_build_DFT_image_full_im_log.jpg", dft_image_full_im * (256 / np.max(dft_image_full_im)))

                # in test mode: calculate the RMS due to curtailment
                IDFT = cv.idft(DFT)
                IDFT = IDFT[:,:,0]
                IDFT = IDFT * (np.max(np.abs(plot)) / np.max(np.abs(IDFT)))
                IDFT = np.round(IDFT).astype(int)
                cv.imwrite("./debug/test_build_IDFT_small.jpg", (IDFT - np.min(IDFT)) * (256 / np.max(IDFT * 2)))
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

                cv.imwrite("./debug/test_build_DFT_image_rounded_re.jpg", dft_image_rounded_re * (256 / np.max(dft_image_rounded_re)))
                cv.imwrite("./debug/test_build_DFT_image_rounded_im.jpg", dft_image_rounded_im * (256 / np.max(dft_image_rounded_im)))
                cv.imwrite("./debug/test_build_DFT_image_rounded_re_log.jpg", dft_image_rounded_re_log * (256 / np.max(dft_image_rounded_re_log)))
                cv.imwrite("./debug/test_build_DFT_image_rounded_im_log.jpg", dft_image_rounded_im_log * (256 / np.max(dft_image_rounded_im_log)))

                IDFT = cv.idft(DFT_rounded)
                IDFT = IDFT[:,:,0]
                IDFT = IDFT * (np.max(np.abs(plot)) / np.max(np.abs(IDFT)))
                IDFT = np.round(IDFT).astype(int)
                cv.imwrite("./debug/test_build_IDFT_rounded_small.jpg", (IDFT - np.min(IDFT)) * (256 / (2*np.max(IDFT))))
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

                cv.imwrite("./debug/test_build_DFT_image_re.jpg", dft_image_re * (256 / np.max(dft_image_re)))
                cv.imwrite("./debug/test_build_DFT_image_im.jpg", dft_image_im * (256 / np.max(dft_image_im)))
                cv.imwrite("./debug/test_build_DFT_image_re_log.jpg", dft_image_re_log * (256 / np.max(dft_image_re_log)))
                cv.imwrite("./debug/test_build_DFT_image_im_log.jpg", dft_image_im_log * (256 / np.max(dft_image_im_log)))
            
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
                with open("./debug/DFT_flat_write.txt",'w') as file:
                    for f in DFT_flat:
                        print(f, file = file)

            # k_df below is used to mark the last written coefficent
            line_limit = 62 ** 66
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
                if os.path.exists(FS.cwd + "/templates/Message Template.txt"):
                    with open("./templates/Message Template.txt", "r") as file_r: message_template = file_r.read()
                    message_template_intro = message_template.split("<message>\n")[0]
                    message_template_outro = message_template.split("<message>\n")[1]
                    for m_t in message_template_intro.splitlines(): print(m_t, file = file)
                
                # The boat needs the following information:
                # - length of the plot
                # - width of the plot
                # - n for nxn DFT retained
                # - template used
                # - DTG of the image
                print(str(x) + "/" + 
                    str(y) + "/" + 
                    str(n) + "/" + 
                    str(int(np.max(plot))) + "/" + 
                    dtg + "/" +
                    FS.subject + "/A1R1G2U3S5/",                                 file = file)
                print(msg_bulk,                                                file = file)
                if os.path.exists(FS.cwd + "./templates//Message Template.txt"):
                    for m_t in message_template_outro.splitlines(): print(m_t, file = file)
            os.startfile(message_file_path)

    #####################################################################
    # m e s s a g e   - >   i m a g e
    #####################################################################
    elif FS.ext.lower() == ".txt" or FS.ext.lower() == ".eml":
        with open(orig_path,'r') as file: msg = file.read()
        m = msg_read(msg)

        # read the message and save the relevant variables
        header, footer = True, False
        k_mr = 0

        for m in msg.splitlines():
            if header:
                if "A1R1G2U3S5" in m:
                    header = False
                    S = m.split("/")
                    x_str, y_str, n_str, max_str, dtg, subject = S[0:6]
                    max = 0

                    # initialize the DFT
                    DFT = np.zeros((int(x_str),int(y_str),2))
                    address = DFT_mapping(int(n_str))
                    DFT_flat = np.zeros(8*(int(n_str) ** 2)).astype(int)
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
                        DFT_flat_dummy.append(int(line_int % m_mr))
                        line_int = int((line_int - (line_int % m_mr)) // m_mr)
                    if test_mode: print(line_int)
                if test_mode: print(DFT_flat_dummy)
                for dfd in DFT_flat_dummy[::-1]:
                    DFT_flat[k_mr] = dfd
                    k_mr += 1
        k_df = 0

        if test_mode:
            with open("./debug/DFT_flat_read.txt","w") as file:
                for f in DFT_flat:
                    print(f, file = file)

        for [i,j] in address:
            i_s, j_s, k_s = [i,int(x_str)-i-1], [j,int(y_str)-j-1], [0, 1]
            for i1 in i_s:
                for j1 in j_s:
                    for k1 in k_s:
                        DFT[i1,j1,k1] = coeff_unround(DFT_flat[k_df])
                        k_df += 1

        plot_idft = cv.idft(DFT)

        FS.update(subject)
        c = config_read(FS.config)
        scale = scale_build_RGB(c.scale)

        # normalize the array and store as the output image
        plot_out = cv.magnitude(plot_idft[:,:,0], plot_idft[:,:,1])
        plot_out = np.array(int(max_str) * (plot_out - np.min(plot_out)) / (np.max(plot_out) - np.min(plot_out))).astype(int)

        image = image_restore(plot_out,subject,dtg,scale)

        cv.imwrite(FS.orig_folder + subject + "_out.jpg",image)

        os.startfile(FS.orig_folder + subject + "_out.jpg")
