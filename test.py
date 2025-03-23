import numpy as np
import cv2 as cv
import imageio
import plot
import textCompression as tc

test = 2
if test == 0:
    image = imageio.mimread('./examples/EUCOM.gif')
    image = [cv.cvtColor(img, cv.COLOR_RGB2BGR) for img in image][0]
    scale = plot.build_scale(image[65,:,:])
    plt = plot.gen(image, scale)
    cv.imwrite('./debug/yaml_test_plt_raw.png', 10 * (plt - np.min(plt)))
    plt = plot.smooth(plt,2)
    cv.imwrite('./debug/yaml_test_plt_smooth.png', 10 * (plt - np.min(plt)))

if test == 1:
    print(tc.coeff_round(10))

if test == 2:
    with open('./examples/EUCOM.txt','r') as file: msg = file.read()
    x, template, dtg = tc.msgdata_read(msg)
    None