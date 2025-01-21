This program is designed to compress a weather image into as small a text file as possible without sacrificing accuracy.  It was designed by AEVIX (aka Sean Peneyra, former submarine officer).

*************************************************
* F O R   T H E   B O A T S
If you are on a boat, you can use the following general procedure:

*** WHILE IN ACTIVE COMMS ***
1. Download the most recent version of ARGUS.exe as well as the most recent Template folder.  At the time of the program creation, these files were provided by JHU reps in port.
2. Put those files onto an approved system.  At the time of this program creation, only the JHU stand-alone laptop was approved for use with the program.  In the future, I hope this program is made available on CANES and NMCI computers.

*** WHILE IN EMCON ***
1. Recieve a weather gif message on VLF
    Note: his will be a message which contains the characters "A1R1G2U3S5" and whos body is promarily non-human readable gibberish made up of A-Z, a-z, and 0-9 characters.
2. Put the entire message into a text file (.txt) and transfer to the information system which can run the ARGUS.exe program
    Note: if that system is the JHU standalone laptop, this will entail burning a CD in radio and loading the message file onto the standalone laptop.  If the information system is CANES, there will be no need to burn a CD, but you will have to save the message as a .txt somewhere.
3. Open the ARGUS.exe program -> It will open a file browser
4. Navigate to the .txt file containing the VLF message and double click the .txt file
5. Your image should open -> the image will also be saved in the same folder as the .txt file.

If you get an error, the problem may be:
- you do not have the most recent template folder from the BCA.  The template used to create the message shoreside must be the same as the template onboard the boat for the image to compile correctly.
- you do not have the most recent ARGUS program.  I am actively working to make the program: more accurate, better at compression (smaller VLF messages), smoother functioning, more user friendly, more efficent, faster running.  Please excuse the active construction.
- the VLF message was garbled. This program uses complex mathematics (literally) to maximize compression of the information. If any of the characters are missing or substituted, the program will fail to rebuild the image

*************************************************
* F O R   S H O R E S I D E

*** BEFORE YOU START ***
1. Ensure you have the latest version of ARGUS.
2. Ensure the folder which contains the file "ARGUS.exe" contains:
- ARGUS.exe
- ARGUS.pdf
- README.md
- Message Template.txt (more details on how to use the message template below)
- a folder called templates (may not be there and that is okay)
------ and no others -----

*** CREATING A MESSAGE FOR THE UNITS ***
1. Verify initial conditions from "BEFORE YOU START"
2. Obtain a weather graphic from METOC
3. Open ARGUS.exe -> it will open a file explorer
4. Use the file explorer from ARGUS.exe to open the weather gif.
    Note: acceptable file types are .gif and .jpg
5. Select the correct template from the drop-down (if there is no correct template, follow instructions for creating a template below)
6. Enter the DTG for which the graphic is valid
7. Click "Select Template"
8. ARGUS will save a message which should be sent to the units as space allows on the broadcast -> it will also try and open this file for viewing

*** CREATING A TEMPLATE ***
    Warning: The boats will not be able to use a new template until they download the template while out of EMCON. I reccomend using existing templates whenever possible.
1. Follow steps 1-4 from CREATING A MESSAGE FOR THE UNITS
2. Click "New Template"
3. Follow the on-screen instructions
4. ARGUS will create a templates folder (if not already there) and create a template for the selected .gif in the templates folder
    Note: there should be two files in each folder in templates: a .gif where all the colors are a solid red and a .config file
5. ARGUS will save a message which should be sent to the units as space allows on the broadcast -> it will also try and open this file for viewing
6. Navigate to the folder which contains ARGUS.exe and the templates folder which contains the new template
7. Right click the folder containing all the files and folders listed in BEFORE YOU START
8. Hover over "compress to" and click ".zip" (for windows 11) - or - hover over "send to" and click "compressed (zipped) folder" (for earlier versions of windows)
9. Send the zipped file to the boats somehow (either post on a public CFFO website or send to the boats on a disc)

*** USING THE MESSAGE TEMPLATE ***


*************************************************
* G E N E R A L   N O T E S
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