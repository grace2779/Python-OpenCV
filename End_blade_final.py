#The main goal of this script is to identify the end point of the blade. 
#First stage it searches for maximum on the histogram of greyscale image ( maximum belongs to sky).
#Masked the sky with black pixels. The blade pixels left not marked.
#Second stage - manupulation on the mask in order to find the row(Y) and column(X) of the tip of the blade.

#VERSION 1.2 - manipulation on the mask ( not on the image combined with mask). Erosion+dilation with different kernel
#few conditions:to check any interuption in blade's image, to check if there any sum of rows=0 not less than 30 rows.
#the last condition where the mask starts (top or bottom). Added the check for first and the last 500 rows.
#In order to know where is the blade located. Added the mask3 which is cover the first and the last quater of finak_mask in order to remove the white zigzag
#and NOT to use erosion and dilation, which are interrupting the image of blade with black dots.

###importing the libraries###
import cv2#for all functions in OpenCV
import numpy as np# to work with numpy arrays
import glob, os, sys#os module implements some useful functions on pathnames;
#glob module finds all the pathnames matching a specified pattern according to the rules used by the Unix shell.
#The program defines what arguments it requires. Used for demand of the path of folders from command line.
from matplotlib import pyplot as plt# The module for drawing the histogram 

#indicating the path to source folder and the folder wher the output will be saved
src_image= "C:\Python27\Topic_de_Stage\End_blade\False/"
outcome_image= "C:\Python27\Topic_de_Stage\End_blade/"
nok=r"\\CORNIS-DS\Stage-EK\Topics_STAGE\Tip_blade_identification\End_blade\NOK/" 

###The code starts here###

#Read each file from source folder
for filename in os.listdir(src_image):

    #extracting only name of file with extention
    filename_1= os.path.basename(filename)
    
    print filename_1
    #full path to file in order to read it
    filename= os.path.join(src_image,filename) 
    if filename.endswith(".jpg"):
        #reads image
        f=cv2.imread(filename)

        #converting from BGR into GRAY. Will be working with values of brightnes of each pixel
        gray = cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        
        #Building the histogram from most dark to most light (0 to 256)and for 256 bins
        #b- number of bins in histogram
        b=255
        #c- variable which depens on the number of bins and is used to indicate the
        #diapasone on mask (Xmax-c;Xmax+c)
        c=(b*13)/100
        #building histogram
        hist_full = cv2.calcHist([gray], [0], None, [b], [1, 256])

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
        mask2 = cv2.inRange(gray,10,256)

        #creating the mask_inv with bitwise_not (Inverts every bit of an array)
        mask_inv =cv2.bitwise_not(mask)

        #cv2.bitwise-and -Calculates the per-element bit-wise conjunction 
        #of two arrays or an array and a scalar. 
        #In our case: inverse mask(numpy array) and mask(numpy array) will be joined in one image.
        final_mask = cv2.bitwise_and(mask_inv, mask_inv, mask=mask2)

        #Adding mask3 to cover up the first quater and the last quater of the final mask.
        h=gray.shape[0]#hight of the image
        w=gray.shape[1]#width of the image
        w1=w/2#width of the white window
        y=0#the coordinates of the point where the white window will start
        x=w/4#the coordinates of the point where the white window will start
        
        #creating the mask the same size as original greyscale image and drawing the white rectangle.
        mask3 = np.zeros(gray.shape,np.uint8)
        mask3[y:y+h,x:x+w1] = final_mask[y:y+h,x:x+w1]

        
        #now image is ready to perform calculation
        #calculating the sum of brightness of all pixels in each row of image.
        #In order to find row where are only black pixels(brightness=0) of mask and where are pixels of blade.
        np.set_printoptions(threshold=np.nan) #- used for displaying full array istead of short version of array.

        summa=np.sum(mask3,axis=1)#axis=1- sum along the row
       
        #In order to find where is the mask is located ( top or bottom) checking the 
        #sum of first 500 rows and last 500 rows. 
        summa_first_500=np.sum(summa[0:499],axis=0)#summ for first 500 alongthe row

        last_elem_summa=summa.size - 1#last row number
        
        summa_last_500=np.sum(summa[last_elem_summa-500:last_elem_summa],axis=0)#sum of last 500 rows

        #Find all rows where sum > 1000. Which is belongs to blade.
        blade=np.where(summa > 1000)[0]

        #We can find the last element of blade array by blade.size-1.
        #But to be sure that it's a blade,not some part of the sky not covered by mask
        #use the following blade.size-1
        a=blade.size-1

        #We know all rows where is blade located. But it can be interupted by rows which sum=0.
        #For this we'll find the difference between each 2 neiboghr elements of the blade array.
        diff_array=np.ediff1d(blade)

        #In order not to take in consideration small gaps in the image of blade (due to poor mask or erosion),
        #we put that the gap > 50 is not in the blade image.
        #But more likely it's a gap between blade image and accidental white spots on black mask.
        diff_array_n1=np.where(diff_array > 50)[0]
        
        #now find all row with sum of brightness <50 (location of mask),
        #in order to avoid false positives when biggest part of the image covered with white spots.
        zeros=np.where(summa<600)[0]
        
        
        #We'll put few condition in order to be sure that the blade was found and
        #to indetify where is the location of the blade on image ( top or bottom).

        #First we check is there any row the sum of which =0.
        #And put the minimun amount of rows with sum=0 should be 100.
        if zeros.size < 100:
            print "Blade was not found"+" "+filename_1

            #saving the final_masl after erosion and dilation in output folder.
            cv2.imwrite(nok+filename_1,mask3)

        #in the  cases when there is no pixels of blade
        elif blade.size==0:
            print "Blade was not found"+" "+filename_1

            #saving the final_masl after erosion and dilation in output folder.
            cv2.imwrite(nok+filename_1,mask3)
            
                
        #in rest of the cases       
        else:     
            #In case when the blade starts from bottom and has direction to top -
            #mask will be in the top and the white pixel will be on the bottom.
            if summa_first_500 < summa_last_500 : 

                #Checks if there are any significant interuption of the blade image.If there are there, then
                #the first element of diff_array_n1 is the indice of the element of the blade array.
                #we don't take the first element k ( which is white dot on the black mask)
                #but the next k+1 which is blade( direction from top to bottom) and this is the row (Y) which we're looking for.
                if diff_array_n1.size > 0:
                    k=diff_array_n1[0]
                    row=blade[k+1]

                #In the cases when there are no significant interuption of the blade image
                #Then the row (Y) where is the tip of the blade is the first element of the blade array (direction from top to bottom)
                else:
                    row=blade[0]
                
            #In case when blade starts from top and has direction to bottom -
            #mask will be in the bottom 
            else:

                #Checks if there are any significant interuption of the blade image.If there are there, then
                #the first element of diff_array_n1 is the indice of the element of the blade array.
                #we don't take the first element k ( which is white dot on the black mask)
                #but the next k+1 which is blade( direction from top to bottom) and this is the row (Y) which we're looking for.
                if diff_array_n1.size > 0:
                    k=diff_array_n1[0]
                    row=blade[k]
                #In the cases when there are no significant interuption of the blade image
                #Then the row (Y) where is the tip of the blade is the first element of the blade array (direction from top to bottom)   
                else:
                    row=blade[a]
                    
            #Taking  image of final_mask after erosion and dilation 
            #and found the row number(identified on the previus steps)
            #and take only elements of this numpy nested array (row- numpy nested array)
            #which are not zero(belong to blade) and takeonly the first element of this nested array.
            #Output will be array.
            array_1=np.nonzero(mask3[row])[0]
               

            #find the number of elements in the last row of blade and divide by 2 to find the middle.
            #n-middle point of the last row of blade. It's indicise of column of the image
            n =(array_1.size)/2
            
            #colimn (X coordinate of the tip of blade) is n element of array_2
            column=array_1[n]

            
            #display the name of the file and coordinates of the tip of blade.
            
            print row
            print column
           
           
            
            #In a sorce image find the pixel with coordinatesfound on previous step
            #Pixel located on the middle of the last row of blade pixels.
            #Marking it by red (for visuall check)
            f[row,column]=[0,0,255]
            
          

            #drawing the square around the red pixel to make it more visible in image scale 1:1
            if row+10 < (f.shape[0]-1):#adding the check if the square will stay in the boundaries of image.
                if column+10 <(f.shape[1]-1):

                    f[row,column+10]=[0,0,255]
                    f[row+1,column+10]=[0,0,255]
                    f[row+2,column+10]=[0,0,255]
                    f[row+3,column+10]=[0,0,255]
                    f[row+4,column+10]=[0,0,255]
                    f[row+5,column+10]=[0,0,255]
                    f[row+6,column+10]=[0,0,255]
                    f[row+7,column+10]=[0,0,255]
                    f[row+8,column+10]=[0,0,255]
                    f[row+9,column+10]=[0,0,255]
                    f[row+10,column+10]=[0,0,255]
                    f[row-1,column+10]=[0,0,255]
                    f[row-2,column+10]=[0,0,255]
                    f[row-3,column+10]=[0,0,255]
                    f[row-4,column+10]=[0,0,255]
                    f[row-5,column+10]=[0,0,255]
                    f[row-6,column+10]=[0,0,255]
                    f[row-7,column+10]=[0,0,255]
                    f[row-8,column+10]=[0,0,255]
                    f[row-9,column+10]=[0,0,255]
                    f[row-10,column+10]=[0,0,255]
                    
                    

                    

                    f[row,column-10]=[0,0,255]
                    f[row+1,column-10]=[0,0,255]
                    f[row+2,column-10]=[0,0,255]
                    f[row+3,column-10]=[0,0,255]
                    f[row+4,column-10]=[0,0,255]
                    f[row+5,column-10]=[0,0,255]
                    f[row+6,column-10]=[0,0,255]
                    f[row+7,column-10]=[0,0,255]
                    f[row+8,column-10]=[0,0,255]
                    f[row+9,column-10]=[0,0,255]
                    f[row+10,column-10]=[0,0,255] 
                    f[row-1,column-10]=[0,0,255]
                    f[row-2,column-10]=[0,0,255]
                    f[row-3,column-10]=[0,0,255]
                    f[row-4,column-10]=[0,0,255]
                    f[row-5,column-10]=[0,0,255]
                    f[row-6,column-10]=[0,0,255]
                    f[row-7,column-10]=[0,0,255]
                    f[row-8,column-10]=[0,0,255]
                    f[row-9,column-10]=[0,0,255]
                    f[row-10,column-10]=[0,0,255]
                   
                    f[row+10,column]=[0,0,255] 
                    f[row+10,column+1]=[0,0,255]
                    f[row+10,column+2]=[0,0,255]
                    f[row+10,column+3]=[0,0,255]
                    f[row+10,column+4]=[0,0,255]
                    f[row+10,column+5]=[0,0,255]
                    f[row+10,column+6]=[0,0,255]
                    f[row+10,column+7]=[0,0,255]
                    f[row+10,column+8]=[0,0,255]
                    f[row+10,column+9]=[0,0,255]
                    f[row+10,column+10]=[0,0,255]
                    f[row+10,column-1]=[0,0,255]
                    f[row+10,column-2]=[0,0,255]
                    f[row+10,column-3]=[0,0,255]
                    f[row+10,column-4]=[0,0,255]
                    f[row+10,column-5]=[0,0,255]
                    f[row+10,column-6]=[0,0,255]
                    f[row+10,column-7]=[0,0,255]
                    f[row+10,column-8]=[0,0,255]
                    f[row+10,column-9]=[0,0,255]
                    f[row+10,column-10]=[0,0,255]
                    
                    f[row-10,column]=[0,0,255]
                    f[row-10,column+1]=[0,0,255]
                    f[row-10,column+2]=[0,0,255]
                    f[row-10,column+3]=[0,0,255]
                    f[row-10,column+4]=[0,0,255]
                    f[row-10,column+5]=[0,0,255]
                    f[row-10,column+6]=[0,0,255]
                    f[row-10,column+7]=[0,0,255]
                    f[row-10,column+8]=[0,0,255]
                    f[row-10,column+9]=[0,0,255]
                    f[row-10,column+10]=[0,0,255]
                    f[row-10,column-1]=[0,0,255]
                    f[row-10,column-2]=[0,0,255]
                    f[row-10,column-3]=[0,0,255]
                    f[row-10,column-4]=[0,0,255]
                    f[row-10,column-5]=[0,0,255]
                    f[row-10,column-6]=[0,0,255]
                    f[row-10,column-7]=[0,0,255]
                    f[row-10,column-8]=[0,0,255]
                    f[row-10,column-9]=[0,0,255]
                    f[row-10,column-10]=[0,0,255]        

                
                    #saving into output folder
                    cv2.imwrite(outcome_image+filename_1,final_mask)
                                      

                      

