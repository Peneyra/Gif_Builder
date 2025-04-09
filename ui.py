import os
import cv2 as cv
import numpy as np
import tkinter as Tk
from time import gmtime
from PIL import ImageTk, Image
import tkinter.messagebox as msgbox

import plot
import buildConfig as bc
import textCompression as tc

def get_filepath(orig_fp):
    # input: string - filepath via tkinter.filedialog.askopenfilename
    # output: File_Structure - file structure for the input
    # Verifies the file is of the correct type.  If not, pop up an error message
    # define valid file extensions
    exts = ['.gif','.jpg','.txt']
    ext = orig_fp[len(orig_fp)-4:]

    if ext in exts:
        return bc.File_Structure(orig_fp, ext)
    elif ext != "":
        root = Tk.Tk()
        root.wm_withdraw()
        msgbox.showinfo(
            title="Wrong type of file", 
            message="Please choose a .jpg, .gif, .txt, or .msg"
        )
        root.destroy()

    quit()


def ui_instructions():
    # input: none
    # output: a dict of instructions for building the template
    out = {}

    out[0] = """Find the low end of the color scale on the image by 
                clicking on the image. Click Next to continue."""
    
    out[1] = """Find the high end of the color scale on the image by 
                clicking on the image. Make sure the whole color scale is 
                highlighted. Press Back to reset. Click Next to continue."""
    out[2] = """Find the top edge of the map by clicking on the image. 
                Then press Next. Do not cut off the coordinates."""
    
    out[3] = """Find the bottom edge of the map by clicking on the image. 
                Then press Next. Do not cut off the coordinates."""
    
    out[4] = """Find the left edge of the map by clicking on the image. 
                Then press Next. Do not cut off the coordinates."""
    
    out[5] = """Find the right edge of the map by clicking on the image. 
                Then press Next. Do not cut off the coordinates."""
    
    return out


def ui_constants():
    bg_color = "light gray"
    x = 500
    y = 400
    return bg_color, x, y


def allowalphanumeric(text):
    return text == "" or text.isalnum()


def show(label_image, input_image):
    # input image must be ImageTk.PhotoImage
    label_image.config(image = input_image)


def cancel_click(root,template_type,image=None,fp=None):
    print("cancel clicked")
    root.destroy()
    if template_type == "build":
        choose_template(image,fp)
    else:
        exit()


def build_template(image,fp):

    def image_click(e):
         # C l i c k   b e h a v i o r
        # Click 0 = Low end of scale  | image 0 -> 1
        # Click 1 = High end of scale | image 1 -> 2
        # Click 2 = Top of map        | image 2 -> 3
        # Click 3 = Bottom of map     | etc.
        # Click 4 = Left of map
        # Click 5 = Right of map
        bg_color, x, y = ui_constants()
        c = bc.config_get(fp)

        print("build template step " + str(root.i))

        if e.widget.winfo_parent() == '.!frame3' and root.i < 6:

            x_im, y_im = root.images[0].shape[:2]
            r_highlight = 20
            root.images[root.i+1] = root.images[0].copy()

            # adjust behavior based on which template index we are on
            if root.i == 0:
                # store the four sides of the highlighted box = b[0:4]
                # and the center coordinates = b[4:8]
                b = [
                    ((e.y * x_im) // y) - r_highlight,
                    ((e.y * x_im) // y) + r_highlight,
                    ((e.x * y_im) // x) - r_highlight,
                    ((e.x * y_im) // x) + r_highlight,
                    ((e.y * x_im) // y),
                    ((e.y * x_im) // y),
                    ((e.x * y_im) // x),
                    ((e.x * y_im) // x)
                ] 
                root.scale_box0 = b

            elif root.i == 1:
                b = root.scale_box0.copy()

                # set x, y for the end of the color scale
                b[5] = (e.y * x_im) // y
                b[7] = (e.x * y_im) // x

                # decide whether the scale is horizontal or vertical
                if abs(b[4]-b[5]) >= abs(b[6]-b[7]):
                    b[6] = b[7] = (b[6] + b[7]) // 2
                    b[0] = min(b[0],b[4] - r_highlight)
                    b[1] = max(b[1],b[5] + r_highlight)
                    b[2] = ((b[6]+b[7])//2) - r_highlight
                    b[3] = ((b[6]+b[7])//2) + r_highlight
                else:
                    b[4] = b[5] = (b[4] + b[5]) // 2
                    b[0] = ((b[4]+b[5])//2) - r_highlight
                    b[1] = ((b[4]+b[5])//2) + r_highlight
                    b[2] = min(b[2],b[6] - r_highlight)
                    b[3] = max(b[3],b[7] + r_highlight)
                root.scale_box1 = b

            elif root.i == 2:
                b = root.scale_box1.copy()

                cr = [(e.y * x_im) // y,x_im,0,y_im]

                root.crop_box0 = cr
                root.images[root.i+1][cr[0]:cr[1],cr[2]:cr[3]] = root.images[-1][cr[0]:cr[1],cr[2]:cr[3]]

            elif root.i == 3:
                b = root.scale_box1.copy()
                cr = root.crop_box0.copy()

                cr[1] = (e.y * x_im) // y

                root.crop_box1 = cr
                root.images[root.i+1][cr[0]:cr[1],cr[2]:cr[3]] = root.images[-1][cr[0]:cr[1],cr[2]:cr[3]]       

            elif root.i == 4:
                b = root.scale_box1.copy()
                cr = root.crop_box1.copy()

                cr[2] = (e.x * y_im) // x

                root.crop_box2 = cr
                root.images[root.i+1][cr[0]:cr[1],cr[2]:cr[3]] = root.images[-1][cr[0]:cr[1],cr[2]:cr[3]]      

            elif root.i == 5:
                b = root.scale_box1.copy()
                cr = root.crop_box2.copy()

                cr[3] = (e.x * y_im) // x

                root.crop_box3 = cr
                root.images[root.i+1][cr[0]:cr[1],cr[2]:cr[3]] = root.images[-1][cr[0]:cr[1],cr[2]:cr[3]]   

            # put the scale back
            root.images[root.i+1][b[0]:b[1],b[2]:b[3]] = root.images[-1][b[0]:b[1],b[2]:b[3]]
            
            root.images_resized[root.i+1] = ImageTk.PhotoImage(
                Image.fromarray(root.images[root.i+1]).resize((x,y))
            )

            # display the most recent image
            show(frame_2_label,root.images_resized[root.i+1])
            button_next.pack(padx = 10, pady = 5, side = 'left')

            return([e.x, e.y])

    def next_click():
        print("next clicked")

        root.i += 1

        if root.i < 6: 
            inst_text.config(text = ui_instructions()[root.i])
            if root.i == 2: show(frame_2_label,root.images_resized[-1])

        else:
            finalize_template()
        
        button_next.pack_forget()

    def back_click():
        if root.i == 0:
            cancel_click(root,"build", image = root.images[-1], fp = fp)
        else: 
            root.i -= 1
            if root.i == 2: show(frame_2_label,root.images_resized[-1])
            else: show(frame_2_label,root.images_resized[root.i])
            inst_text.config(text = ui_instructions()[root.i])

    def create_template_click():
        if subject_name.get() != "":
            fp.update(subject_name.get())
            if os.path.isfile(fp.template):
                if askquestion_exists() == "no":
                    fp.update('temp')
                    return

            if not os.path.exists(fp.templates_folder + fp.subject): 
                os.mkdir(fp.templates_folder + fp.subject)

            cv.imwrite(fp.template,cv.cvtColor(root.images[6], cv.COLOR_BGR2RGB))
            bc.config_update(fp,root.c,None,None)
            root.destroy()
            choose_template(image, fp)
        else:
            Tk.messagebox.showerror("Missing AOR name","Please name your template.")

    def askquestion_exists():
        answer = msgbox.askquestion(
            "File Already Exists", "A template with this name already exists. Do you want to replace it?", 
            icon = "error"
        )
        return answer

    def finalize_template():
        inst_title.pack_forget()
        inst_text.pack_forget()
        button_next.pack_forget()
        button_back.pack_forget()
        button_canc.pack_forget()

        button_create.pack(padx = 10, pady = 5 , side = 'left')
        button_canc.pack(padx = 10, pady = 5 , side = 'left')
        subject_prompt.pack()
        subject_name.pack()

        root.images[6] = 255 * np.ones_like(root.images[-1]).astype(np.uint8)

        # crop the image template
        root.c = {}
        b = root.c['b'] = root.scale_box1.copy()
        cr = root.c['cr'] = root.crop_box3.copy()
        root.images[6][b[0]:b[1],b[2]:b[3]] = root.images[-1][b[0]:b[1],b[2]:b[3]]
        root.images[6][cr[0]:cr[1],cr[2]:cr[3]] = root.images[-1][cr[0]:cr[1],cr[2]:cr[3]]


        root.c['scale'] = []
        scale_box = np.array(root.images[-1][b[0]:b[1],b[2]:b[3]]).astype(int)
        # build the scale
        for d in [20,15,25,10,30]:
            if b[4] == b[5]: scale_slice = scale_box[d,:]
            else: scale_slice = scale_box[:,d]

            if b[6] > b[7] or b[4] > b[5]: scale_slice = scale_slice[::-1]

            if len(plot.build_scale(scale_slice)) > len(root.c['scale']): 
                root.c['scale'] = plot.build_scale(scale_slice)

        # get a plot of the image
        l, r, t, b = plot.lrtb(root.images[6])
        plt = plot.gen(root.images[6], root.c['scale'])
        plt = plot.smooth(plt, 2)
        plt = plt // 1
        mask = np.array(plt == np.min(plt)).astype(int)

        for i in range(3):
            root.images[6][t:b,l:r,i] = np.multiply(root.images[6][t:b,l:r,i], mask).astype(np.uint8)

        mask = np.array(plt > np.min(plt)).astype(int)
        root.images[6][t:b,l:r,0] = root.images[6][t:b,l:r,0] + np.array(125 * mask).astype(int)

        root.images_resized[6] = ImageTk.PhotoImage(
            Image.fromarray(root.images[6]).resize((x,y))
        )
        show(frame_2_label,root.images_resized[6])

    #####################################################################
    # B u i l d   t h e   r o o t   U I
    bg_color, x, y = ui_constants()
    c = bc.config_get(fp)
    root = Tk.Tk()
    root.i = 0
    root.images = {}
    root.images_resized = {}

    root.images[-1] = image
    root.images_resized[-1] = ImageTk.PhotoImage(
        Image.fromarray(root.images[-1]).resize((x, y))
    )
    root.images[root.i] = image // 2
    root.images_resized[root.i] = ImageTk.PhotoImage(
        Image.fromarray(root.images[root.i]).resize((x,y))
    )
    root.title("A R G U S - Build a template")
    root.iconbitmap('argus.ico')
    root.config(bg = bg_color)

    #####################################################################
    # B u i l d   F r a m e   0   =   I n s t r u c t i o n s
    instructions = ui_instructions()
    frame_0 = Tk.Frame(root, bg = bg_color)
    frame_0.pack(pady = 10)
    inst_title = Tk.Label(
        frame_0, 
        justify = "left", 
        wraplength = x, 
        font = ("Arial",16), 
        bg = bg_color,
        text = "Build your template:"
    )
    inst_title.pack(anchor = "w")
    inst_text = Tk.Label(
        frame_0, 
        justify = "left", 
        wraplength = x,
        font = ("Arial", 12), 
        bg = bg_color,
        text = instructions[root.i]
    )
    inst_text.pack(anchor = "w")
    
    subject_prompt = Tk.Label(frame_0, bg = bg_color, text = "Name your template:")
    subject_name = Tk.Entry(frame_0, validate = "key", validatecommand=(root.register(allowalphanumeric),"%P"))
    
    #####################################################################
    # B u i l d   F r a m e   1   =   B u t t o n s
    frame_1 = Tk.Frame(root, bg = bg_color)
    frame_1.pack()

    button_back = Tk.Button(
        frame_1, 
        text = "Back", 
        command = back_click
    )
    button_back.pack(padx = 10, pady = 5 , side = 'left')

    button_canc = Tk.Button(
        frame_1, 
        text = "Cancel", 
        command = lambda: cancel_click(root,"build",image=image,fp=fp)
    )
    button_canc.pack(padx = 10, pady = 5 , side = 'left')

    button_next = Tk.Button(
        frame_1, 
        text = "Next", 
        command = next_click
    )
    # not packed until the image is clicked
    
    button_create = Tk.Button(
        frame_1, 
        text = "Create New Template", 
        command = create_template_click
    )

    #####################################################################
    # B u i l d   F r a m e   2   =   T h e   I m a g e
    frame_2 = Tk.Frame(root, height = y, width = x, bg = bg_color)
    frame_2.pack(padx = 10, pady = 5)

    frame_2_label = Tk.Label(frame_2)
    show(frame_2_label,root.images_resized[root.i])
    frame_2_label.pack()

    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", lambda: cancel_click(root,"build",image=image,fp=fp))
    root.bind("<Button 1>", image_click)
    root.mainloop()


def choose_template(image,fp):

    def new_click(image,fp):
        # FIX build out what to do if the template does not exist
        print("new clicked")
        root.destroy()
        build_template(image,fp)

    def select_click():
        if not "Z" in entry_dtg.get().upper():
            Tk.messagebox.showerror("Missing DTG","Input the DTG shown in the image. Entry must contain a Z.")
        else:
            fp.dtg = entry_dtg.get()
            print("select clicked")
            fp.update(template.get())
            root.destroy()

    bg_color, x, y = ui_constants()

    # check if any tempaltes exist
    # if they do then start the choose_template ui
    # if they don't then start the build_template ui
    templates = []
    if os.path.exists("./templates"):
        root = Tk.Tk()
        root.images = {}
        root.images_resized = {}
        for o in os.listdir("./templates"):
            fp.update(o)
            if os.path.exists(fp.config) and os.path.exists(fp.template): 
                templates.append(o)
                root.images[o] = np.array(Image.open(fp.template))
                root.images_resized[o] = ImageTk.PhotoImage(
                    Image.fromarray(root.images[o]).resize((x, y))
                )
    else:
        os.mkdir("./templates")
    if templates == []: new_click(image,fp)

    root.images[-1] = image
    root.images_resized[-1] = ImageTk.PhotoImage(
        Image.fromarray(root.images[-1]).resize((x, y))
    )

    #####################################################################
    # B u i l d   t h e   r o o t   U I
    root.title("A R G U S - Choose a Template")
    root.iconbitmap('argus.ico')
    root.config(bg = bg_color)

    #####################################################################
    # B u i l d   F r a m e   0   =   I n s t r u c t i o n s
    print("build frame 0")
    frame_0 = Tk.Frame(root, bg = bg_color)
    frame_0.pack(pady = 10)
    Tk.Label(
        frame_0, 
        justify = "center", 
        wraplength = 2*x, 
        font = ("Arial",16), 
        bg = bg_color,
        text = "Choose a template and enter the DTG the image shows. Otherwise create a new template."
    ).pack(anchor = "w")

    #####################################################################
    # B u i l d   F r a m e   1   =   O p t i o n s
    print("build frame 1")
    frame_1 = Tk.Frame(root, bg = bg_color)
    frame_1.pack()

    # template selector    
    frame_11 = Tk.Frame(frame_1, bg = bg_color)
    frame_11.pack(padx = 5, pady = 0, side = 'left')
    Tk.Label(
        frame_11, 
        justify = "left", 
        bg = bg_color,
        text = "Template:"
    ).pack(side = 'left')

    template = Tk.StringVar()
    template.set(templates[0])
    Tk.OptionMenu(
        frame_11, 
        template, 
        *templates, 
        command = lambda x: show(frame_31_label, root.images_resized[template.get()])
    ).pack(side = 'left')
    
    # DTG entry.  Populate it with the current ZULU time
    frame_12 = Tk.Frame(frame_1, bg = bg_color)
    frame_12.pack(padx = 5, pady = 0, side = 'left')
    Tk.Label(
        frame_12, 
        justify = "left", 
        font = ("Arial", 10), 
        bg = bg_color,
        text = "DTG:"
    ).pack(side = 'left')
    
    zulu = f"{gmtime().tm_mday:02}" \
        + f"{gmtime().tm_hour:02}" \
        + "00Z" \
        + tc.month_name(gmtime().tm_mon) + str(gmtime().tm_year)

    entry_dtg = Tk.Entry(
        frame_12,
        validate = "key", 
        validatecommand = (root.register(allowalphanumeric), "%P")
    )
    
    def update_dtg(fp,dtg): fp.dtg = dtg
    entry_dtg.bind('<Return>', update_dtg(fp,entry_dtg.get()))
    entry_dtg.bind('<FocusOut>', update_dtg(fp,entry_dtg.get()))
    entry_dtg.pack(side = 'left')
    entry_dtg.delete(0,Tk.END)
    entry_dtg.insert(0,zulu)

    # character set encoding
    frame_13 = Tk.Frame(frame_1, bg = bg_color)
    frame_13.pack(padx = 5, pady = 0, side = 'left')
    Tk.Label(
        frame_13, 
        justify = "left", 
        font = ("Arial", 10), 
        bg = bg_color,
        text = "Character Set:"
    ).pack(side = 'left')

    char_sets = ["Num+UPPER", "Num+UPPER+lower"]
    char_set = Tk.StringVar()
    char_set.set(char_sets[0])
    Tk.OptionMenu(
        frame_13, 
        char_set, 
        *char_sets
    ).pack(side = 'left')


    #####################################################################
    # B u i l d   F r a m e   2   =   B u t t o n s
    print("build frame 2")
    frame_2 = Tk.Frame(root, bg = bg_color)
    frame_2.pack()
    print("   build button 0")
    Tk.Button(
        frame_2, 
        text = "Select Template", 
        command = select_click
    ).pack(padx = 10, pady = 5, side = 'left')

    print("    build button 1")
    Tk.Button(
        frame_2, 
        text = "New Template", 
        command = lambda: new_click(image,fp)
    ).pack(padx = 10, pady = 5 , side = 'left')

    print("    build button 2")
    Tk.Button(
        frame_2, 
        text = "Cancel",
        command = lambda: cancel_click(root,"choose")
    ).pack(padx = 10, pady = 5 , side = 'left')

    #####################################################################
    # B u i l d   F r a m e   3   =   I m a g e | T e m p l a t e
    print("build frame 3")
    frame_3 = Tk.Frame(root, bg = bg_color).pack(padx = 10, pady = 5)

    frame_31 = Tk.Frame(frame_3, height = y, width = x, bg = bg_color)
    frame_31.pack(padx = 10, side = 'left')
    frame_31_label = Tk.Label(frame_31)
    show(frame_31_label,root.images_resized[template.get()])
    frame_31_label.pack()

    frame_32 = Tk.Frame(frame_3, height = y, width = x, bg = bg_color)
    frame_32.pack(padx = 10, side = 'left')
    frame_32_label = Tk.Label(frame_32)
    show(frame_32_label,root.images_resized[-1])
    frame_32_label.pack()

    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", cancel_click)
    root.mainloop()