import plot
import textCompression as tc
import buildConfig as bc
import ui

import os
import imageio
import cv2 as cv
import numpy as np
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


# define constants
n, padding, dft_norm = 18, 25, 1000

# Open a file and save the filepath info
# Creates a templates folder if one doesn't already exist
fp = ui.get_filepath(askopenfilename(title="A R G U S"))

if fp.ext.lower() == '.gif' or fp.ext.lower() == '.jpg':
    image = imageio.mimread(fp.orig_fp)

    # if it is a gif, only take the first frame
    if fp.ext.lower() == '.gif': image = image[0]

    # Open the UI to choose/build a template
    # template, dtg = ui.choose6_template(image, fp)
    ui.choose_template(image,fp)

    if not fp.subject == 'temp':
        # Save the contents of the config file to c
        c = bc.config_get(fp)

        # Build a scalar plot off the image and condition it
        plt = plot.gen(image, np.array(c['scale']))
        plt = plot.condition(plt, padding)
        
        # Save the max_coefficient for normalizing the output
        max_coeff = int(np.max(plt - np.min(plt)) - 1)

        # Build a DFT matrix of the plot and normalize it for
        # writing into the messaage
        dft = cv.dft(plt)
        dft = dft * (dft_norm/np.max(np.abs(dft)))

        # Write the DFT coefficients to a variable in the final form we want
        msg_data = tc.msgdata_write(dft,n)

        # Write the framework for the message
        msg_intro, msg_outro = tc.msgcontent_write(fp)

        with open(fp.out_fp,'w') as file:
            for m in msg_intro.splitlines(): print(m, file=file)
            print(
                str(dft.shape[0]) + '/'
                + str(dft.shape[1]) + '/'
                + str(n) + '/'
                + str(max_coeff) + '/'
                + fp.dtg + '/'
                + fp.subject + '/'
                + 'A1R1G2U3S5/', 
                file=file
            )
            for m in msg_data.splitlines(): print(m, file=file)
            for m in msg_outro.splitlines(): print(m, file=file)
        
        os.startfile(fp.out_fp)

elif fp.ext.lower() == '.txt':
    with open(fp.orig_fp,'r') as file: msg = file.read()

    dft, max_coeff, template, dtg = tc.msg_read(msg)

    fp.update(template)
    c = bc.config_get(fp)
    c['scale'] = np.array(c['scale']).astype(np.uint8)

    plt = cv.idft(dft)

    plt[plt < 0] = 0
    plt = plt * max_coeff // np.max(plt)
    plt = plt[padding:-1*padding, padding:-1*padding]
    imageio.mimsave(
        fp.out_fp, 
        [plot.restore(plt, fp, c['scale'], dtg)]
    )

    os.startfile(fp.out_fp)