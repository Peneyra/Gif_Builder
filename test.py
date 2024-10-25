import tkinter as Tk
import os

def show():
    print("You pressed a button!")
    template_image = Tk.PhotoImage(file = "./templates/" + subject.get() + "/" + subject.get() + "_template.jpg")
    print(subject.get())

root = Tk.Tk()
root.title("Select your template")
root.config(bg="skyblue")

frame_0 = Tk.Frame(root)
frame_0.grid(row=0,column=0,padx=5,pady=5)
frame_1 = Tk.Frame(root)
frame_1.grid(row=1,column=0,padx=5,pady=5)
frame_2 = Tk.Frame(root)
frame_2.grid(row=2,column=0,padx=5,pady=5)

options = os.listdir("./templates")
subject = Tk.StringVar()
subject.set(options[0])
drop = Tk.OptionMenu(frame_0, subject, *options)
drop.pack()

template_image = Tk.PhotoImage(file = "./templates/" + subject.get() + "/" + subject.get() + "_template.jpg")
Tk.Label(frame_1, image=template_image)


button0 = Tk.Button(frame_2, text = "Select Template", command = show)
button0.grid(row=0,column=0)
button1 = Tk.Button(frame_2, text = "New Template", command = show)
button1.grid(row=0,column=1)
button2 = Tk.Button(frame_2, text = "Cancel", command = show)
button2.grid(row=0,column=2)

label = Tk.Label(root, text = "")

root.mainloop()