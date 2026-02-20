# polymyalgia-analysis
This software takes scanned pdfs of paper pain drawings, automatically crops and aligns them, and can create a csv
file listing the predefined body regions that contain marks, as well as pixel maps of the pain locations. The pixel
maps can be used to calculate the pain area and generate heatmaps of average pain location across a group of manikins.

Most of the important code is in the digitisation package. There are two ways to run the digitisation code: the
command line interface and the gui. Most operations are simpler to run using the command line interface, but the GUI
can be used to generate a filename map if the scanned pdfs need to be renamed during preprocessing. See the GUI
section of the readme for more information.

##Basic steps to run the code

1) Scanned PDFs for conversion should all be saved in one directory. Make sure PdfDir in the config file points to
this directory.

2) Preprocessing
The first stage of preprocessing is alignment.
First, make sure there is a blank manikin template pdf, and that AlignmentTemplate in the RESOURCES
section of the config file points to this file.

Second, use image editing software to find the (x,y) coordinates of the rectangle that encloses the manikin part of the
pdf, excluding things like explanatory text. You will need the upper left and lower right coordinate of the box.
Set the values in MANIKINAREA to these coordinates, separated by a comma. Check that you are happy with the values for
the CroppedTemplate, OutputDir and DataDir. You can specify a FilenameMap in the config file to automatically rename the
 files as they are aligned - use the --rename command line option to do this. If you don't specify the --rename option,
 the names of the aligned files will match the source pdf files.

Run the script with run.py --align or run.py --align --rename, and wait for it to finish.

Next, run the script with run.py --preprocessing. Check that the files in CleanedDir show the marks made by participants
but with the manikin template removed. Look at the cleaned_example.png file in the example directory to see what this
should look like. If there are still parts of the manikin template visible, or the marks made by participants have also
been removed, check the information on BackgroundColourLowerBound and BackgroundColourUpperBound in the Advanced
settings section. If the issue is only present on some of the files, then they may not have aligned properly, which
can happen if the blank template is too different to the scanned drawings (e.g. printed with different intro text). If
this is only happening for a few files, you can try cropping them to approximately the correct area and using the
--realign command line option to manually realign these specific files. Otherwise, contact me for help.

3) Creation of template files. After the alignment code has run, a file will be saved in the location specified in the
CroppedTemplate config option. Different template files are needed depending on whether you are detecting predefined
pain regions, or generating pixel maps of pain locations. Both these tasks need the original CroppedTemplate file,
so make sure the original file remains unedited.

To detect pain in predefined body regions, you will need to create an image file for each body region that should be
detected. Look at the example files in the resources/widespreadpain_sections folder for an example of what these should
 look like.
Each file should have one body region marked in red (255, 0, 0), saved as an RGB png file (not RGBA). These regions
need to match the alignment of the CroppedTemplate file. If you have a pre-existing map of body regions, you can crop
it to approximately the correct size and use the --realign command line option to align it precisely to the
CroppedTemplate file. Once you're happy with the alignment, use image editing software to create a file for each
predefined region, and save them together in one directory with no other files. Change SectionsDir in the RESOURCES
section of the config file to point to this directory. Each file should be named with the identifier of that section,
e.g. if your sections are named 1, 2 and 3, you would name your files 1.png, 2.png and 3.png. These are the only
additional template files needed for the predefined body regions detection.

To generate pixel maps of the pain locations marked by participants, you need to create a template file of the manikin
area. This will be used to crop the final pain regions so that they don't extend outside the bounds of the manikin. Open
the CroppedTemplate file in image editing software, and mark the area inside the manikin boundaries in red (255, 0, 0).
If you want to allow marks extending outside the manikin boundaries, you can simply mark a larger area in red. A fully
red image means that pain regions will be permitted anywhere on the drawing. Save this image as a separate file,
making sure that it is an RGB png file (not RGBA). Update the PixelTemplate setting in the RESOURCES section of the
config file to point at this file. This is the only additional template file needed for the pixel map generation.

4) Pain location detection.

To generate a csv file showing which predefined body regions were marked as painful, run the code with
run.py --sections.

To generate the pixel maps of the detected pain locations, run the code with run.py --hull. You can add the option
--visualise to also output the detected pain locations draw over the original drawings. The pixel maps will be
saved in the PainRegionsDir folder specified in the OUTPUTS section of the config file, and the visualisations will be
saved in the VisualisationsDir.

5) Metrics and heatmap.

Once you have generated the pain regions, you can generate a heatmap showing the overall average, using the --heatmap
command line option. Use the command run.py --heatmap [heatmapfilename].

You can calculate the pain extent on each drawing using the --extent command line option. The config options in the
EXTENT section of the config file should be set first. Dir should point to the directory with the pain pixel maps.
LogFile is the path to the csv file that will be created with the results. Template should point to a template file
of the manikin area as described in the section on the creation of template files.

notes:
all template images should be saved as RGB, not RGBA
if something isn't working and it's not obvious why, check all images in resource are saved without an alpha channel.


## Advanced Settings
BackgroundColourLowerBound and BackgroundColourUpperBound give the range of colours that should be treated as the
background colour. E.g. if the manikin was printed on white paper and scanned, reasonable default values would be
BackgroundColourLowerBound = 253, 253, 253
BackgroundColourUpperBound = 255, 255, 255
Note that these values are BGR not RGB: so red would be 0, 0, 255

If there is a lot of noise (e.g. from photocopying the template manikin multiple times) and the markings are drawn
 fairly clearly (e.g. using a dark pen and not a pencil or a ballpoint that is half out of ink) then decreasing the
 lower bound may help remove some noise. Using too low of a value for the lower bound may remove some of the actual
 marks made. Using the --debug command line option will output a debug folder showing the marks detected. This can be
 used to help set an appropriate value for the upper and lower bounds - if actual marks from the drawings are not
 shown in the debug images, the lower bound likely needs to be raised.

If the pain drawings were photographed rather than scanned, it is likely necessary to increase the range of background
colours.

The ClusteringThreshold controls how close together individual lines must be to be treated as one group when drawing
the pain regions. A low clustering threshold (e.g. 5) will tend to treat each individual line drawn as one pain region,
and a higher clustering threshold (e.g. 50) will tend to group nearby lines together and may merge multiple regions.
The best results will generally come from pain regions being fully shaded in with a dark pen, and a low clustering
 threshold (in the 5 to 10 range). If pain regions are more loosely shaded (e.g. a leg is marked with a few
 horizontal lines) then a higher clustering threshold (e.g. 40) will help correctly capture these regions, but may merge
 independent regions which are closely grouped together. Using the -v command line option can help with choosing an
 appropriate clustering threshold. This will output a visualisation showing the detected pain regions drawn over the
 original images. If distinct pain regions are circled as one group, the threshold needs to be lowered. If individual
 marks that are all part of one pain region are circled as separate groups, the threshold should be raised.

## GUI
I would generally recommend using the CLI rather than the GUI, but I've left the GUI code in. You will need to install
several extra libraries including tkinter and pytesseract to use the GUI as it currently is. I might make a more
 generically useful version of the GUI at some point in the future if time allows.
The GUI can be used to generate a filename map. The GUI has not been maintained as much as the CLI so might output to
 directories that are not specified in the config file. It was made for renaming a specific batch of files that were
 either pain or stiffness manikins, and has some specific assumptions built in. To use the GUI, run the run_gui.py file
 with no arguments. The "align and crop pdfs" button will allow you to align and crop each pdf in the pdf dir while
 renaming them. Ticking the "resume" box before clicking the "align and crop pdfs" button will allow you to resume in
 the middle of a batch - this should not be clicked the first time you start processing a batch, but should be clicked
 each subsequent time.