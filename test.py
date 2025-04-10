import numpy as np
import cv2 as cv
import imageio

import ui
import plot
import textCompression as tc
import buildConfig as bc
from tkinter.filedialog import askopenfilename
from PIL import Image


n = 15
padding = 25

test = 5

if test == 0:
    image = imageio.mimread('./examples/EUCOM.gif')
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in image][0]

    scale = plot.build_scale(image[65,:,:])

    plt = plot.gen(image, scale)
    plt = np.pad(plt, pad_width = padding, mode='symmetric')
    cv.imwrite('./debug/yaml_test_plt_raw.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    plt = plot.smooth(plt,2)
    cv.imwrite('./debug/yaml_test_plt_smooth.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    max_coeff = int(np.max(plt - np.min(plt)) - 1)

    dft = cv.dft(cv.resize(plt,(plt.shape[1]//1,plt.shape[0]//1)))
    dft = dft * (1000/np.max(np.abs(dft)))

    dft_view = np.log(np.abs(dft))
    dft_view[dft_view < 0] = 0
    cv.imwrite('./debug/yaml_test_dft.png', dft_view * (200 / np.max(dft_view)))

    msg_data = tc.msgdata_write(dft,n)

    print("")
    print("")

    msg_data = '538/927/'+ str(n) + '/' + str(max_coeff) + '/000000ZJAN25/EUCOM/A1R1G2U3S5/\n' + msg_data

    dft_out, max_coeff, template, dtg = tc.msgdata_read(msg_data)

    dft_out_view = np.log(np.abs(dft_out))
    dft_out_view[dft_out_view < 0] = 0
    cv.imwrite('./debug/yaml_test_dft_out.png', dft_out_view * (200 / np.max(dft_out_view)))

    plt_out = cv.idft(dft_out)
    plt_out[plt_out < 0] = 0
    plt_out = (plt_out) * (max_coeff / np.max(plt_out))
    plt_out = plt_out[padding:-1*padding,padding:-1*padding]
    plt_out = np.round(plt_out).astype(int)
    cv.imwrite("./debug/yaml_test_idft.png", (plt_out - np.min(plt_out)) * (200 / np.max(plt_out * 2)))

    print(msg_data)
    print(len(msg_data))

    img = plot.restore(plt_out,template,scale,dtg)
    cv.imwrite("./debug/yaml_test_img.png", img)

    None

if test == 1:    # test change of basis

    x = tc.change_basis([0,0,0,3,0],3,10)
    print(x)

    None

if test == 2:    # test message read
    with open('./examples/EUCOM.txt','r') as file: msg = file.read()
    x, template, dtg = tc.msg_read(msg)

    None

if test == 3:
    image = imageio.mimread('./examples/EUCOM.gif')
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in image][0]

    scale = plot.build_scale(image[65,:,:])

    plt = plot.gen(image, scale)
    cv.imwrite('./debug/yaml_test_plt_raw.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    plt = plot.smooth(plt,2)
    cv.imwrite('./debug/yaml_test_plt_smooth.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    plt -= np.min(plt)

    max_coeff = int(np.max(plt - np.min(plt)) - 1)
    x,y = plt.shape

    shrink = 8
    plt = cv.resize(plt,(y//shrink,x//shrink))
    dft = cv.dft(plt)
    k = 10

    for i in range(k-10,k):
        dft_temp = dft.copy()

        dx = int(dft.shape[0] * (k - i)/(2*k))
        print(dx)

        dft_temp[:,2*dx:] = 0
        dft_temp[dx:dft.shape[0]-dx,:] = 0

        plt_out = cv.idft(dft_temp)
        plt_out[plt_out < 0] = 0
        plt_out = (plt_out) * (max_coeff / np.max(plt_out))
        plt_out = cv.resize(plt_out,(y,x))
        plt_out = plt_out.astype(int)

        dft_temp = np.log(dft_temp)
        dft_temp[dft < 0] = 0
        cv.imwrite('./debug/yaml_test_dft_out.png', dft_temp * (200 / np.max(dft_temp)))
        cv.imwrite("./debug/yaml_test_idft.png", (plt_out - np.min(plt_out)) * (200 / np.max(plt_out * 2)))

    plt_out = np.round(plt_out).astype(int)

    None

if test == 4:

    image = imageio.mimread('./examples/EUCOM.gif')
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in image][0]

    scale = plot.build_scale(image[65,:,:])

    from tkinter.filedialog import askopenfilename

    fp = ui.get_filepath(askopenfilename())

    c = bc.config_update(fp,{},'scale',scale)

    None

if test == 5:
    fp = ui.get_filepath(askopenfilename())
    image = imageio.mimread(fp.orig_fp)
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in image][0]
    ui.choose_template(image,fp)
    c = bc.config_get(fp)

    plt = plot.gen(image, np.array(c['scale']))
    cv.imwrite('./debug/yaml_test_plt_raw.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    plt = plot.smooth(plt,2)
    cv.imwrite('./debug/yaml_test_plt_smooth.png', (plt - np.min(plt)) * (200 / np.max(plt * 2)))
    plt -= np.min(plt)

    max_coeff = int(np.max(plt - np.min(plt)) - 1)
    x,y = plt.shape

    shrink = 8
    plt = cv.resize(plt,(y//shrink,x//shrink))
    dft = cv.dft(plt)
    k = 10

    for i in range(k-10,k):
        dft_temp = dft.copy()

        dx = int(dft.shape[0] * (k - i)/(2*k))
        print(dx)

        dft_temp[:,2*dx:] = 0
        dft_temp[dx:dft.shape[0]-dx,:] = 0

        plt_out = cv.idft(dft_temp)
        plt_out[plt_out < 0] = 0
        plt_out = (plt_out) * (max_coeff / np.max(plt_out))
        plt_out = cv.resize(plt_out,(y,x))
        plt_out = plt_out.astype(int)

        dft_temp = np.log(dft_temp)
        dft_temp[dft < 0] = 0
        cv.imwrite('./debug/yaml_test_dft_out.png', dft_temp * (200 / np.max(dft_temp)))
        cv.imwrite("./debug/yaml_test_idft.png", (plt_out - np.min(plt_out)) * (200 / np.max(plt_out * 2)))

    plt_out = np.round(plt_out).astype(int)

    None

if test == 6:    # convert png to ico
    img = Image.open('argus.png')
    sizes = [(16,16),(32,32),(48,48)]
    img.save('argus.ico',format='ICO',sizes=sizes)