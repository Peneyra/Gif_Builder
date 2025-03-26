import numpy as np
import cv2 as cv
import os
import tkinter as Tk
from tkinter import messagebox
from PIL import ImageTk, Image
from time import gmtime

import buildConfig as bc


def get_filepath(orig_fp):
    # Verifies the file is of the correct type.  If not, pop up an error message
    # define valid file extensions
    ext_good = ['.gif','.jpg','.txt','.eml']

    if orig_fp == "":
        quit()
    else:
        for e in ext_good:
            if orig_fp[len(orig_fp)-4:] == e:
                out = bc.File_Structure(orig_fp, e)
                return out

    root = Tk.Tk()
    root.wm_withdraw()
    messagebox.showinfo(
        title="Wrong type of file", 
        message="Please choose a .jpg, .gif, .txt, or .msg"
    )
    root.destroy()

    quit()


def allowalphanumeric(text):
    return text == "" or text.isalnum()


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
            t, b, l, r = get_tblr(image_template)
            plot_template = plot_scale(image_template[t:b,l:r,:])
            plot_mask = np.repeat(np.array(plot_smooth(plot_template,2) == 0).astype(int)[:,:,np.newaxis], 3, axis = 2)

            image_template[t:b,l:r,:] = np.multiply(image_template[t:b,l:r,:], plot_mask).astype(np.uint8)
            image_template[t:b,l:r,2] = image_template[t:b,l:r,2] + 125 * np.array(plot_mask[:,:,2] == 0).astype(int)
            
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