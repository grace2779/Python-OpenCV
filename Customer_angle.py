#The main goal of this script is to identify the  blade on the image. 
#First it change the image from color to greyscale. Then building histiogram,
#find the max in histogram and then black out the mask inverse in the range(Xmax-c;Xmax+c).
#Then the script checkes what was black out the blade or the sky.
#Based on the idea that blade is always in the cenre of image:
#1. Recieve the input of angle of the blade in the image from excel file
#2. the script sum up the value of brightness of the pixels which are along the line of custom angle.
#3. The array of values of sum is split in 3 arrays.
#4. Then there is an input (taken from excel) file with position of blade in the image. 1-left,2-middle, 3-right.
#5.If the location of the blade coinside with the max sum of array - then mask was applied correctly (keeping mask_inv).
#If not - apply mask.
#The result is masked sky and blade as origin.Then it calculates the luminosity of blade. 
#Depending on the level file is save in ok-dir( for well-exposed) and nok_dir (for over and under exposed).
#The decision to proceed whole folder or not is based on the percentage of successfully proceed files from this folder.

#VERSION 0.1 - Histogram maximum and decision based on the location of the blade on image.

#How to run  the code: 
# In Command Prompt WINDOWS: python C:/Python27/Def_luminosity.py(or other path) [-h] after this you will see available options
#so in order to perfom the test of certain folder of images need to run the following:
#python C:/Python27/Def_luminosity.py(or other path) -CR2 (path to folder with CR2 files) example \\Cornis-ds\eol-basetest\201506171850-5511429cfa2adccbc2000010\20150318-eoleres\7-B-TE-P1s
# -src (path to folder where you will save JPEG files extracted from CR2) -ok (path to folder where the imagiges with OK luminosity will be saved) 
#-nonok (path to folder where images with NOK luminosity will be saved)

#in UBUNTU terminal in command line:
#python C:/Python27/Def_luminosity.py(or other path) -CR2 <path> -src <path> -ok <path> -nonok <path>



###importing the libraries###
import cv2#for all functions in OpenCV
import numpy as np# to work with numpy arrays
import glob, os, sys#os module implements some useful functions on pathnames;
#glob module finds all the pathnames matching a specified pattern according to the rules used by the Unix shell.
import subprocess #to run the subprocess of Exiv2
import getopt # It parses an argument sequence, such as sys.argv and returns a sequence of (option, argument)
# pairs and a sequence of non-option arguments.
#Used in the part for getting the path for all necessary directories through command line.
import argparse #The module makes it easy to write user-friendly command-line interfaces.
#The program defines what arguments it requires. Used for demand of the path of folders from command line.
from matplotlib import pyplot as plt# The module for drawing the histogram 
from numpy import cos, sin# importing the trigonomatry functions
from math import *# module for pi number
import xlrd# The module  to read and write to excel files

###Creating the demand for arguments from command line.
parser = argparse.ArgumentParser(description='This is path finder to folders from command line')
#Adding argument 
parser.add_argument('-CR2','--CR2_dir', help='CR2 folder',required=True)
parser.add_argument('-src','--src_dir',help='Jpeg folder', required=True)
parser.add_argument('-ok','--ok_dir',help='OK luminosity folder', required=True)
parser.add_argument('-nonok','--nonok_dir',help='NOK luminosity folder', required=True)
args = parser.parse_args()
## show values ##
print ("CR2 folder: %s" % args.CR2_dir )
print ("Jpeg folder: %s" % args.src_dir )
print ("OK luminosity folder: %s" % args.ok_dir )
print ("NOK luminosity folder: %s" % args.nonok_dir )

# each argument correspond to the path
CR2_dir=args.CR2_dir
src_dir=args.src_dir
ok_dir=args.ok_dir
nonok_dir=args.nonok_dir



#Function for counting amount of files in directory. It will be used to find the
#percentage of successfully proceed files out of whole folder. Then the decision to proceed folder or not
#will be taken based on this percent.
def count_files(path,extension):
    list_dir = []
    list_dir = os.listdir(path)
    count = 0
    for file in list_dir:
        if file.endswith(".jpg"): 
            count += 1
    return count

def luminosity(image):
    #As an input we have the image(openCV object), so in order to get the data of BGR of
    #each pixel converting the images into numpy array. Output: numpy nested array.
    my_array=np.array((image), np.uint8)

    # find the sum of R,G,B(twice because nested array - array in array)
    #in order to get in the end array [sum B,sum G, sum R]
    my_array1 = np.sum(my_array, axis=0)
    my_array2 = np.sum(my_array1, axis=0)



    #According to the position in array define R, G, B
    B=my_array2[0]
    G=my_array2[1]
    R=my_array2[2]

    #find the dominant color
    maxi=my_array2.max()


    #my_array - it's the image converted into array.It containes also the mask or mask_inv which has B=0,G=0,R=0
    #So using np.count_nonzero gives us the number of values which belongs to non-black (non-zero) pixels.
    #Input - numpy nested array;output - intrger with amount of element which are not = 0
    C = np.count_nonzero(my_array)

    #deviding them by 3 in order to find
    #the number of pixels of the blade. Because each pixel has 3 values (B, G, R)
    counter=C/3
              

    #calculating the luminance. Source of formula is Panoblade Software by A. Dosda.
    luminance= (5*maxi +R +G +B)/(8* counter)

    return luminance
#The function splitting the images ( which level of luminosity has been estimated by luminosity function) in 3 categories:
#<140 - under exposed
#>=140 nut <230 well-exposed
#>230-overexposed
#and saves the in certaines folders (well-exposed in to ok_dir) and over and under-exposed into nonok_dir.
#takes as input: lum - level of luminosty of image( as a result of the luminosity function applied before to this image)
#2-nd input: basename - the name of the file with jpg extension(201412151036_raw.jpg)
#output - prints name of file +luminosity + light OK (0) (or light OK(1)) +lightNOK(1) (or light OK(0)
def thresh_lum (lum,basename):
    #putting the threshold for luminance
    if lum <140:
      
      #printing output in the form which will be used in exel file of results
      #filename + pixels of mask+luminosity + light OK (0) +lightNOK(1)
      print basename+ " "+"%2.0f" % (lum)+" "+"0"+" " +"1"
      #In order to  compare visually the original image and modified one with mask or mask_inv
      #putting the image with applied mask_inv or mask (res1) under the original image (f)by function vstack . Vstack  is applicable only for arrays.
      #res1 - global variable calculated below
      res = np.vstack((f,res1))
      #saving into nonok_dir
      cv2.imwrite(nonok_dir+basename,res)
      
    elif lum > 230:
      
      #printing output in the form which will be used in exel file of results
      #filename +luminosity + light OK (0) +lightNOK(1)
      print basename+ " "+"%2.0f" % (lum)+" "+"0"+" " +"1"
      #In order to  compare visually the original image and modified one with mask or mask_inv
      #putting the image with applied mask_inv or mask (res1) under the original image (f)by function vstack . Vstack  is applicable only for arrays.
      #res1 - global variable calculated below
      res = np.vstack((f,res1))
      #saving into nonok_dir
      cv2.imwrite(nonok_dir+basename,res)
      
    else:
      #In order to  compare visually the original image and modified one with mask or mask_inv
      #putting the image with applied mask_inv or mask (res1) under the original image (f)by function vstack . Vstack  is applicable only for arrays.
      #res1 - global variable calculated below
      res = np.vstack((f,res1))
      #saving into ok_dir
      cv2.imwrite(ok_dir+basename,res)
      #printing output in the form which will be used in exel file of results
      #filename + pixels of mask+luminosity + light OK (0) +lightNOK(1)
      print  basename+ " "+ "%2.0f" % (lum)+" "+"1"+" " +"0"



#####The code starts here###	
###Read each file from source folder and with Exiv2 extract JPEG. OpenCV works with JPEG and PNG.
for filename in os.listdir(CR2_dir):

    filename= os.path.join(CR2_dir,filename)
    if filename.endswith(".CR2"):      
        subprocess.check_call (['exiv2','-ep3','-l',src_dir, filename])

###Count amount of files in source directory. Necessary for calculation of percentage of successfully proceed images.
A= count_files (src_dir,".jpg")


#Read each file from source folder
for filename in os.listdir(src_dir):

    
    #extracting only name of file with extention
    filename_1= os.path.basename(filename)
    
    #full path to file in order to read it
    filename= os.path.join(src_dir,filename)

    #reads image
    f=cv2.imread(filename)
    
    #shrinking image 10 times.Reduce calculation time for sum of each diagonal
    height, width = f.shape[:2]
    f = cv2.resize(f,(width/10, height/10), interpolation = cv2.INTER_CUBIC)
    
    #converting from BGR into GRAY. Will be working with values of brightnes of each pixel
    gray = cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)

   

    #Building the histogram from most dark to most light (0 to 256)and for 256 bins
    #n- number of bins in histogram
    b=25
    #c- variable which depens on the number of bins and is used to indicate the
    #diapasone on mask (Xmax-c;Xmax+c)
    c=(b*10)/100
    #building histogram
    hist_full = cv2.calcHist([gray], [0], None, [b], [0, 256])
    
    #find max, min and their location in histogram.
    #For us interesting only max of histogram
    min_val, max_val, min_loc, max_loc=cv2.minMaxLoc(hist_full)


    #max_loc gives coordinates(y,x) corresponds to max of histogram
    #x - correspond to the brightness of max of histogram
    x1= max_loc[1]
    float(x1)

    #putting borders of threshold to cut out the mask
    lower = (x1-c)*(256/b)
    upper = (x1+c)*(256/b)
    
    #cutting out the mask
    mask=cv2.inRange(gray,lower,upper)
    #creating the mask_inv with bitwise_not (Inverts every bit of an array)
    mask_inv =cv2.bitwise_not(mask)

    #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
    #of two arrays or an array and a scalar. 
    #In our case: inverse mask(numpy nested array) and original image(numpy nested array).
    res1 = cv2.bitwise_and(gray,gray, mask= mask_inv)
    
    
    #Need to read the angle  from input excel file. The data with filename, angle and location should be on the second sheet.
    #File should contains exactly the same filename as in a  src_dir folder. The column with filename is 2 (column C. Numeration starts from 0)
    # but the column with standartized angles (full description of modification of angles in file "roulis.xlsx" on the sheet "READ ME")
    #should be 2+2 ( it's column E or 4) and next after it  is the column with location  of blade (values:1 -left, 2-middle or diagonal, 3-right)
    # so it's 2+3 (column F or 5)
    
    
    #putting path to file
    file_location =r"C:\Users\MorenoFamily\Downloads\roulis.xlsx"
    #opens the excel file
    book = xlrd.open_workbook(file_location)
    # Get the second sheet
    sheet = book.sheet_by_index(1) 
   
    #loop over all columns and rows
    for current_row in range(sheet.nrows):
        for col in range(sheet.ncols):
            #find the cell with filename on which working now
            if sheet.cell(current_row,col).value==filename_1:

                #from the cell of filename shift +2 col will be angle and +3 col will be location of the blade on image
                angle = sheet.cell_value(current_row,col+2)
                location=sheet.cell_value(current_row,col+3)
                #for further calculation will need angle in radians. 
                angle_in_rad = angle * (pi / 180)
                #getting the number of rows and columns in image
                rows,columns = res1.shape


                #Angle should be from 0 to 180 degrees.
                ##CASE 1.   more than 90 degrees ( around 120)##              ##CASE 2. less than 90 degrees (60 degrees)
                
                # ######       #                                             #       ########
                # #######      #                                             #      ####### #
                #   ######     #                                             #     #######  #
                #    ######    #                                             #    #######   #
                #     ######   #                                             #   #######    #
                #      ######  #                                             #  #######     #
                #       ###### #                                             # #######      #
                

                #split all agles in 3 categories: <=80, >=110 and >80 but <110

                #condition for angle less than 80 degrees or equal.
                #Starts from left top corner towards left bottom corner and then from left bottom towards right bottom corner.
                #For CASE 1.
                if angle <= 80:
                    # get the first pixels on the bottom line of image 
                    first_pixels_bottom = [[rows-1,x] for x in range(0,columns)]
                    #get the first column of pixels on the left
                    first_pixels_left = [[y,0] for y in range(0,rows)]

                    #join the 2 lists of coordinates. These are the starting points of each line of custom angle
                    first_pixels = np.concatenate([first_pixels_left,first_pixels_bottom])
                    

                    #the direction of line along which the sum will be performed is calculated based on sin and cos trigonometry functions.
                    sum_direction = [-sin(angle_in_rad),cos(angle_in_rad)]
                    
                    #ctrating the empty list to which will add  coordinates of pixels laid on the line of custom angle
                    output = []

                    #looping over the coordinates in the list or starting points of each line of custom angle
                    #in order to draw the line from each starting point 
                    for y,x in first_pixels:
                        actual_point = [y,x] # initialisation of the first point
                        actual_sum = 0  # putting the sum to 0 and in order to add to it all the following  sums of brightness values of pixels laid on the line.
                        number_of_pixels_i_sumed = 0 # initialisation of the number of pixels sumed
                       
                        while (actual_point[0] < rows) & (actual_point[1] < columns) & (actual_point[1] >= 0) & (actual_point[0] >= 0): # loop on the pixels to sum
                            actual_point_in_image = [int(v) for v in actual_point] # get the actual point we want in the image
                            actual_sum += res1[actual_point_in_image[0],actual_point_in_image[1]] # sum up the previous sum with the sum which we've just got 
                            number_of_pixels_i_sumed += 1 # moving to the next pixel along the line
                            actual_point = np.sum([actual_point, sum_direction], axis=0) # go to the next point
                            
                            
                        # adding the sum to the output and normalise the  value by deviding the sum on the amount of pixels on this line
                        output.append(float(actual_sum) / float(number_of_pixels_i_sumed))
                        
             
                #condition for angle more than 110 degrees or equal.
                #Starts from left bottom corner towards right bottom corner and then from right bottom towards top right corner.
                #For CASE 2.
                elif angle >= 110 :
                    # get the first pixels on the bottom line of image
                    first_pixels_bottom = [[rows-1,x] for x in range(0,columns)]
                    #get the first column of pixels on the right
                    first_pixels_right = [[y,columns-1] for y in range(0,rows)]
                    #reversing the list of coordinates. To keep the correct order of coordinates and to have correctly ploted histogram
                    first_pixels_right = list(reversed(first_pixels_right))
                    
                    #join the 2 lists of coordinates. These are the starting points of each line of custom angle
                    first_pixels = np.concatenate([first_pixels_bottom,first_pixels_right])

                    #the direction of line along which the sum will be performed is calculated based on sin and cos trigonometry functions.
                    sum_direction = [-sin(angle_in_rad),cos(angle_in_rad)]
                    

                   #ctrating the empty list to which will add  coordinates of pixels laid on the line of custom angle
                    output = []

                    #looping over the coordinates in the list or starting points of each line of custom angle
                    #in order to draw the line from each starting point 
                    for y,x in first_pixels:
                        actual_point = [y,x] # initialisation of the first point
                        actual_sum = 0  # putting the sum to 0 and in order to add to it all the following  sums of brightness values of pixels laid on the line.
                        number_of_pixels_i_sumed = 0 # initialisation of the number of pixels sumed
                       
                        while (actual_point[0] < rows) & (actual_point[1] < columns) & (actual_point[1] >= 0) & (actual_point[0] >= 0): # loop on the pixels to sum
                            actual_point_in_image = [int(v) for v in actual_point] # get the actual point we want in the image
                            actual_sum += res1[actual_point_in_image[0],actual_point_in_image[1]] # sum up the previous sum with the sum which we've just got 
                            number_of_pixels_i_sumed += 1 # moving to the next pixel along the line
                            actual_point = np.sum([actual_point, sum_direction], axis=0) # go to the next point
                            
                            
                        # adding the sum to the output and normalise the  value by deviding the sum on the amount of pixels on this line
                        output.append(float(actual_sum) / float(number_of_pixels_i_sumed)) 

                #the case when the angle aproximatly =90 degrees (from 80 to 110). We donn't need the most left or the most right  column of the coordinates.
                #They are equal to 0 and only distort the histogram of brightness values. Instead of middle the peak of brightness is located on the first third.
                #It gives the false positives in the decision making stage.
                #For angle close to 90 degrees we'll sum up only the brightness value of columns of image.
                else:
                   #sum each column. result array 1 dimension 
                   output=np.sum(res1, axis=0) 
                    
                
                
                #need to read the location of the blade in this image from excel file.
                #1- left; 2-middle or by diagonal; 3-right

                
                #if the blade is in the centre or by diagonal
                if location ==2:
                    
                    #In order to check if the max of brightness is in the middle, slicing the array of sums (output) into 3 parts:
                    #left part of image, central part of image, right part of image. 
                    K=(len(output))/3
                    #Sum of brighness values for the lines along the custom angle ( from 0 to K-20 in first_pixels)
                    ar1=output[0:K-20:1]
                    # suming up all values
                    ar1=np.sum(ar1)
                    #Sum of brighness values for the lines along the custom angle ( from K+1 to (K*2)+10 in first_pixels)
                    ar2=output[K-19:(K*2)+130:1]#Taking wider range for middle part due to big variety of location of maximum of brightnes.
                    # suming up all values
                    ar2=np.sum(ar2)
                    #Sum of brighness values for the lines along the custom angle ( from (K*2)+1 to K*3 in first_pixels)
                    ar3=output[(K*2)+1:K*3:1]
                    # suming up all values
                    ar3=np.sum(ar3)
                   

                    #creating list with three sums
                    Alist=[ar1,ar2,ar3]
                    
                    

                    #checking if the max belongs to blade, which should be in the middle part
                    #and have a max value of brightness. The rest should be black. So the mask_inv was correctly applied.
                    
                    if Alist[1]==max(Alist):
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar. 
                        #In our case: inverse mask(numpy nested array) and original BGR image(numpy nested array)
                        #clip together in order to calculate the luminosity of the part which is not under the mask_inv.
                        res1 = cv2.bitwise_and(f,f, mask= mask_inv)
                        
                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1)


                    #In case when the max of the sum values of brightnes doesn't coincide with location of the blade => conclusion mask_inv was not
                    #applied correctly and we're going to apply mask.
                    else:
                           
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar. 
                        #In our case: inverse mask(numpy nested array) and original image(numpy nested array).
                        res1 = cv2.bitwise_and(f,f, mask= mask)
                        
                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1)

                #When the blade is located on the left side of image       
                elif location==1:

                    #In order to check if the max of brightness is on the left, slicing the array of sums (output) into 2 parts:
                    #left part of image,right part of image. 
                    K=(len(output))/2
                    #Sum of brighness values for the lines along the custom angle ( from 0 to K in first_pixels)
                    ar1=output[0:K:1]
                    # suming up all values
                    ar1=np.sum(ar1)
                    #Sum of brighness values for the lines along the custom angle ( from K+1 to K*2 in first_pixels)
                    ar2=output[K+1:K*2:1]
                    # suming up all values
                    ar2=np.sum(ar2)
                    

                    #creating list with all sums
                    Blist=[ar1,ar2]

                    #If the max sum coincides with location (from excel input file). It means mask_inv was applied correctly
                    if Blist[0]==max(Blist):
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar. 
                        #In our case: inverse mask(numpy nested array) and original BGR image(numpy nested array)
                        #clip together in order to calculate the luminosity of the part which is not under the mask_inv.
                        res1 = cv2.bitwise_and(f,f, mask= mask_inv)
                        
                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        
                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1)

                    #If max sum doesn't coinside with location, it means mask_inv was not applied correctly.
                    #Then applying mask
                    else:
                           
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar. 
                        #In our case: inverse mask(numpy nested array) and original image(numpy nested array).
                        res1 = cv2.bitwise_and(f,f, mask= mask)

                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1)

                #When the blade is on the right side of image        
                elif location == 3:
                    #In order to check if the max of brightness is on the left, slicing the array of sums (output) into 2 parts:
                    #left part of image,right part of image. 
                    K=(len(output))/2
                    #Sum of brighness values for the lines along the custom angle ( from 0 to K in first_pixels)
                    ar1=output[0:K:1]
                    # suming up all values
                    ar1=np.sum(ar1)
                    #Sum of brighness values for the lines along the custom angle ( from K+1 to K*2 in first_pixels)
                    ar2=output[K+1:K*2:1]
                    # suming up all values
                    ar2=np.sum(ar2)
                    

                    #creating list with all sums
                    Clist=[ar1,ar2]

                    #If the max sum coincides with location (from excel input file). It means mask_inv was applied correctly
                    if Clist[1]==max(Clist):
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar.
                        #In our case: inverse mask(numpy nested array) and original BGR image(numpy nested array)
                        #clip together in order to calculate the luminosity of the part which is not under the mask_inv.
                        res1 = cv2.bitwise_and(f,f, mask= mask_inv)
                        
                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1)


                    #If max sum doesn't coinside with location, it means mask_inv was not applied correctly.
                    #Then applying mask
                    else:
                        
                        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
                        #of two arrays or an array and a scalar. 
                        #In our case: inverse mask(numpy nested array) and original image(numpy nested array).
                        res1 = cv2.bitwise_and(f,f, mask= mask)

                        #calculating luminosity by function ( in the top of the script)
                        luminance=luminosity(res1)

                        #using function for threshold luminosity and is the image well-exposed or not.
                        thresh_lum (luminance,filename_1) 
                    
#amount of proceed file
B= count_files (ok_dir,".jpg")


#Percantage of successfully proceed images out of all image in source folder
C =(B*100)/float(A)
print C


#If more than 50% of images are proceed,apply the setting to all folder.
if C > 50:
        
    print "Folder has been proceed"
else:
    print "Folder was not proceed"
                



