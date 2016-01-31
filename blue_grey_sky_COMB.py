###importing the libraries###
import cv2
import numpy as np
import glob, os, sys
import math
import subprocess

#setting the source folder and destination folder
src_dir="C:/Python27/Blades/14"
target_dir="C:/Python27/Watershed_COMB/14/"
saving_dir="C:/Python27/Watershed_1/14/"

#Read each file from source folder and convert them with UFRAW into JPEG
for filename in os.listdir(src_dir):

    filename= os.path.join(src_dir,filename)
        
    subprocess.check_call(['ufraw-batch','--overwrite','--out-type=jpeg','--out-path=' + target_dir, filename])

#Function for counting amount of files in directory
def directory(path,extension):
  list_dir = []
  list_dir = os.listdir(path)
  count = 0
  for file in list_dir:
    if file.endswith(".jpg"): 
      count += 1
  return count

#amount of files in source directory
A=directory(target_dir,".jpg")

#Read each file from source folder
for filename in os.listdir(src_dir):

        filename= os.path.join(target_dir,filename)
        
        f=cv2.imread(filename)

        #converting from BGR into HSV
        hsvt = cv2.cvtColor(f,cv2.COLOR_BGR2HSV)

        # define range of blue color in HSV
        lower_blue = np.array([90,50,50])
        upper_blue = np.array([130,255,255])

        #Threshold the HSV image to get only blue colors
        mask1 = cv2.inRange(hsvt, lower_blue, upper_blue)

        #image moments helps to calculate contour area of mask
        #in order to define threshold against false positives
        #for moment http://en.wikipedia.org/wiki/Image_moment
        moments = cv2.moments(mask1) 
        area = moments['m00']
        
        
        # if mask contour area less than threshold 
        if area < 4000000:

            #Converting into greyscale in order to work with watershed
            imgray = cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)

            #threshold the image by the level 127
            ret, thresh = cv2.threshold(imgray,127,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

            #erosion for foreground and dialation for background
            fg = cv2.erode(thresh,None,iterations = 1)
            bgt = cv2.dilate(thresh,None,iterations = 1)

            #making background equal to 128
            ret,bg = cv2.threshold(bgt,1,128,1)

            #adding markers for watershed algorithm
            marker = cv2.add(fg,bg)
            #markers should be the same size as original image
            marker32 = np.int32(marker)
            #applying watershed
            cv2.watershed(f,marker32)
            
            #convert result back into uint8 image
            m = cv2.convertScaleAbs(marker32)
            
            #threshold it properly to get the mask
            ret,thresh = cv2.threshold(m,127,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

            #creating mask
            mask = thresh
            
            
            #creating inverse mask
            mask_inv =cv2.bitwise_not(mask)
            
            # Bitwise-AND mask and original image
            res1 = cv2.bitwise_and(f,f, mask= mask_inv)
            
            

            #converting res1(object of openCV) into numpy array
            my_array=np.array((res1), np.uint8)

            # find the sum of R,G,B(twice because nested array)
            my_array1 = np.sum(my_array, axis=0)
            my_array2 = np.sum(my_array1, axis=0)



            #According to the position in array define R, G, B
            B=my_array2[0]
            G=my_array2[1]
            R=my_array2[2]

            #find the dominant color
            maxi=my_array2.max()


            #find all element of nested array non zeros
            C = np.count_nonzero(my_array)

            #deviding them by 3 in order to find
            #the number of pixels of the blade
            counter=C/3
            



            #calculating the luminance
            luminance= (5*maxi +R +G +B)/(8* counter)
            
            
            #putting the threshold for luminance
            if luminance <140:
                print "%.0f" % (luminance)+" " "Blade is not well exposed in file" + " " +filename

            elif luminance > 230:
               
                print "%.0f" % (luminance)+" "+"Blade is overexposed in file" + " " +filename
            else:
                
                #Saving image in one file, for
                #this we need to take only the name of the file
                #from full path and destination folder
                res = np.vstack((f,res1))
                filename_1= os.path.basename(filename)
                cv2.imwrite(target_dir+filename_1,res)
                print "%.0f" % (luminance)+" "+"File is proceed"+" "+filename_1
        
        #otherwise it will apply inverse mask    
        elif area > 1850000000:
            mask_inv =cv2.bitwise_not(mask1)
            
            # Bitwise-AND mask and original image
            res1 = cv2.bitwise_and(f,f, mask= mask_inv)
            #Converting back to BGR 
            BGR = cv2.cvtColor(res1,cv2.COLOR_HSV2BGR)

            #converting res1(object of openCV) into numpy array
            my_array=np.array((res1), np.uint8)

            # find the sum of R,G,B
            my_array1 = np.sum(my_array, axis=0)
            my_array2 = np.sum(my_array1, axis=0)



            #According to the position in array define R, G, B
            B=my_array2[0]
            G=my_array2[1]
            R=my_array2[2]

            #find the dominant color
            maxi=my_array2.max()


            #find all element of nested array non zeros
            C = np.count_nonzero(my_array)

            #deviding them by 3 in order to find
            #the number of pixels of the blade
            counter=C/3
            



            #calculating the luminance
            luminance= (5*maxi +R +G +B)/(8* counter)
            
            
            #putting the threshold for luminance
            if luminance <140:
                print "%.0f" % (luminance)+" " "Blade is not well exposed in file" + " " +filename

            elif luminance > 230:
               
                print "%.0f" % (luminance)+" "+"Blade is overexposed in file" + " " +filename
            else:
                
                #Saving image in one file, for
                #this we need to take only the name of the file
                #from full path and destination folder
                filename_1= os.path.basename(filename)
                cv2.imwrite(saving_dir+filename_1,res1)
                print "%.0f" % (luminance)+" "+"File is proceed"+" "+filename_1     

        else:
            print "unknown category"
            
#amount of proceed file
B=directory(saving_dir,".jpg")

#Percantage of successfully proceed images out of all image in source folder
C=(B*100)/A
print C

#If more than 50% of images are proceed,apply the setting to all folder.
if C > 50:
    for filename in os.listdir(target_dir):
        filename= os.path.join(target_dir,filename)
        f=cv2.imread(filename)
        
        ##here should be manipulation with DxO##

        filename_1= os.path.basename(filename)
        cv2.imwrite(saving_dir+filename_1,f)
        
    print "Folder has been proceed"

else:
    print "Folder is not proceed"
    
