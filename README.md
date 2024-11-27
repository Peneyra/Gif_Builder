This python program is designed to compress a weather image into as small a text file as possible without sacrificing accuracy.
 The goal for this progam is to:
 1. Read an input file
 2. If the input file is an image:
     a. Open a GUI to either build or select an existing template
     b. Simplify the image into an array of scalars based on a legend
     c. Build a DFT off of the scalar array
     d. Truncate the DFT
     e. Produce a naval message on compressed list of coefficients
 4. If the file is a text file:
     a. Rebuild the DFT from the naval message
     b. Perform an IDFT to reproduce a scalar array
     c. Interpret build the scalar array into the original input image
     d. Overlay a standard image template over the top of the scalar array
