
import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans
import imutils
import matplotlib.pyplot as plt

####################################################################################3
from colorsys import rgb_to_hsv
"""
def convert(color,colors):
    colors = np.array(colors)
    color = np.array(color)
    distances = np.sqrt(np.sum((colors-color)**2,axis=1))
    index_of_smallest = np.where(distances==np.amin(distances))
    smallest_distance = colors[index_of_smallest]
    return smallest_distance 
"""


def remove(alist):
    new_list=[]
    for elem in alist:
        if elem not in new_list:
            new_list.append(elem)
    alist = new_list
    return alist

#all_colours_in_hsv = [colour1, colour2, colour3, colour4, colour5]

def closest_colour(selected_colour):
    # set the distance to be a reallly big number
    # initialise closest_colour to empty
    shortest_distance, closest_colour = sys.max(), None

    # iterate through all the colours
    # for each colour in the list, find the Euclidean distance to the one selected by the user
    for colour in all_colours_in_hsv:
        # since your colours are in 3D space, perform the calculation in each respective space
        current_distance = sqrt(pow(colour.H - selected_colour.H, 2) + pow(colour.S - selected_colour.S, 2) + pow(colour.V - selected_colour.V, 2))

        # unless you truly care about the exact length, then you don't need to perform the sqrt() operation.
        # it is a rather expensive one so you can just do this instead
        # current_distance = pow(colour.H - selected_colour.H, 2) + pow(colour.S - selected_colour.S, 2) + pow(colour.V - selected_colour.V, 2)

        # update the distance along with the corresponding colour
        if current_distance < shortest_distance:
            shortest_distance = current_distance
            closest_colour = colour

    return shortest_distance, closest_colour

def convertt(col,ref_list):
    colors = ref_list
    color_to_match = col
    
    ds ,k= (min((abs(rgb_to_hsv(*k)[0]-rgb_to_hsv(*color_to_match)[0]),k) for k in colors))
    print(k)
    return k

######################################################################################

def create_mask(image):
    width, height = image.shape[:2][::-1]

    # roi = image[ width//2 -20 : width//2 + 20 , height//2 -20 : height//2 + 20]
    roi = image[height//2 - 20: height//2 + 20, width//2 - 20: width//2 + 20]

    hsvRoi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # print('min H = {}, min S = {}, min V = {}; max H = {}, max S = {}, max V = {}'.format(hsvRoi[:,:,0].min(), hsvRoi[:,:,1].min(), hsvRoi[:,:,2].min(), hsvRoi[:,:,0].max(), hsvRoi[:,:,1].max(), hsvRoi[:,:,2].max()))

    lower = np.array(
        [hsvRoi[:, :, 0].min(), hsvRoi[:, :, 1].min(), hsvRoi[:, :, 2].min()])
    upper = np.array(
        [hsvRoi[:, :, 0].max(), hsvRoi[:, :, 1].max(), hsvRoi[:, :, 2].max()])

    image_to_thresh = image
    hsv = cv2.cvtColor(image_to_thresh, cv2.COLOR_BGR2HSV)

    # kernel = np.ones((3, 3), np.uint8)
    # for red color we need to masks.
    mask = cv2.inRange(hsv, lower, upper)
    ##mask = cv2.erode(mask, (3, 3))
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    #not_mask = cv2.bitwise_not(mask)
    # cv2.imshow("Mask", not_mask)

    # cv2.imshow('masked image' , cv2.bitwise_not(image , image , mask=not_mask))

    # cv2.imshow('roi', roi)
    # cv2.waitKey(0)

    return mask



def quantize_images(image):
    # image = cv2.imread('s1.png')
    (h, w) = image.shape[:2]

    image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    clt = MiniBatchKMeans(n_clusters=4)
    labels = clt.fit_predict(image)
    quant = clt.cluster_centers_.astype("uint8")[labels]
    quant = quant.reshape((h, w, 3))
    image = image.reshape((h, w, 3))

    quant = cv2.cvtColor(quant, cv2.COLOR_LAB2BGR)

    return quant


# preprocess the input image
def preProcessing(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    threshold = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((3, 3), np.uint8)
    closing = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
    canny = cv2.Canny(closing, 0, 400)
    cv2.imshow('threshold', canny)

    return threshold

# find the biggest contour and it's area


def biggestContour(contours):
    biggest = np.array([])
    max_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        # print(area)
        # if area > 500:
        length = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * length, True)

        if area > max_area and len(approx) == 4:
            biggest = approx
            max_area = area

    return biggest, max_area


# order points for warp prespective
def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), dtype=np.int32)
    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew


def prepare_images(original):

    image = original.copy()
    width, height = image.shape[:2][::-1]

    kernel = np.ones((3, 3), np.uint8)
    mask= create_mask(quantize_images(image))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    # dilated = cv2.dilate(canny, kernel)
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # contours  , heirarchy = cv2.findContours(canny , cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE)

    # print('number of contours :' , len(contours))

    biggest, max_area = biggestContour(contours)
    #print(max_area, biggest)
    cv2.drawContours(original, contours, -1, (0, 255, 0), 1)
    #cv2.imshow('masked image', original)
    #cv2.imshow('masked ', mask)
    cv2.waitKey(0)

    if biggest.size != 0:
        biggest = reorder(biggest)
        #cv2.drawContours(image , [biggest] , -1 , (0,255,0) , 3)
        #cv2.imshow('image' , image)
        # cv2.waitKey(0)
        pts1 = np.float32(biggest)
        pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        cropped = cv2.warpPerspective(original, matrix, (width, height))

        return cropped
"""
def color(alist, images):
    #sortedlist=[]
    colorList=[]
    for image in images:
        for c in alist:
            blue = image[alist[1],alist[0],0]
            colorList.append(blue)
            green= image[alist[1],alist[0],1]
            colorList.append(green)
            red = image[alist[1],alist[0],2]
            colorList.append(red)
        
    return colorList
"""
def pre_images(images):
    new_images = []
    (height, width) = images[1].shape[:2]

    for image in images:
        h, w = image.shape[:2]
        image = cv2.resize(image, (w, height))
        #print(image.shape)
        new_images.append(image)

    return new_images

def create(image):
        
        img = np.zeros(image.shape, np.uint8) 
        img = cv2.bitwise_not(img)
        #upper_list.append(img)

        return img 

if __name__ == "__main__":
    
    top = cv2.imread('s5.png')
    s2 = cv2.imread('s2.png')
    s3 = cv2.imread('s3.png')
    s4 = cv2.imread('s4.png')
    s1 = cv2.imread('s1.png')
    
    image_list=[]
    ls= [top,s4,s3,s1,s2]
    ls = pre_images(ls)

    listofColor = []
    listofColor2 = []
    listofColorT = []
    listofColorB = []
    width=[]
    sortedlist=[]
    sortedlist2=[]
    lower_list=[]
    upper_list=[]
    
    listoftupleT=[]
    uupper_list=[]

    for i in ls:
        cropped = prepare_images(i)
        image_list.append(cropped)
        #cv2.imshow("cropped1", cropped)
    #print(image_list)

    """
    for image in image_list:
        image = prepare_images(image)
        mask = cv2.bitwise_not(create_mask(quantize_images(image)))
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        cnts,_ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    """

    def resize(img):
        img = cv2.resize(img,(200,200))
        return img

    #upper_list = [(image_list[0]), (create(image_list[2])),(create(image_list[3])),(create(image_list[4]))] 

    
    for image in image_list:
        #image = cv2.resize(image,(500,500))
        
        
        ###########################prepare###################################
        """
        scale_percent = 60 # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        """
        ###################################################

        image = prepare_images(image)
         
        mask = cv2.bitwise_not(create_mask(quantize_images(image)))
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        cnts,_ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #print (len(cnts))

        contours =[]
       
        for con in cnts:
            arc_len = cv2.arcLength( con, True )
            approx = cv2.approxPolyDP( con, 0.1 * arc_len, True )
            if cv2.contourArea( con ) > 1000 :
                contours.append(con)
            
        
        length_of_contours = len(contours)
        #print(len(contours))

        if length_of_contours == 3:
            lower_list.append(image)
            #cv2.imshow('i',image)
        else:
            upper_list.append(image)
       
        #print(listoftuple)

        for x in lower_list:
            print(len(lower_list))
            #cv2.imshow("img",x)
            listoftuple=[]
            for c in contours:
                #cv2.drawContours(x, [c],-1, (0,255,0),2)
                #cv2.imshow("con", x)
                M = cv2.moments(c)
                center_x, center_y = (int(M['m10'] / (M['m00']+ 1e-5)), int(M['m01'] / (M['m00']+ 1e-5)))
                listoftuple.append((center_x, center_y))

            res =max(listoftuple, key = lambda i : i[0])[0]
            res2 = min(listoftuple, key = lambda i : i[0])[0]
            resT = min(listoftuple, key = lambda i : i[1])[0]

            for a in range(len(listoftuple)):
                if res == listoftuple[a][0]:
                    res= listoftuple[a]
                if res2 == listoftuple[a][0]:
                    res2= listoftuple[a]
                if resT == listoftuple[a][0]:
                    resT= listoftuple[a]

            blue = masked_image[res[1],res[0]][0]
            green= masked_image[res[1],res[0]][1]
            red = masked_image[res[1],res[0]][2]
            strr= (str(red)+','+str(green)+','+str(blue))
            listofColor.append((red,green,blue))
            #print(listofColor)
            #print(strr)

            blue = masked_image[res2[1],res2[0]][0]
            green= masked_image[res2[1],res2[0]][1]
            red = masked_image[res2[1],res2[0]][2]
            strr2= (str(red)+','+str(green)+','+str(blue))
            listofColor2.append((red,green,blue))
            #print(listofColor2)
            #print(strr2)

            blue = masked_image[resT[1],resT[0]][0]
            green= masked_image[resT[1],resT[0]][1]
            red = masked_image[resT[1],resT[0]][2]
            strrT= (str(red)+','+str(green)+','+str(blue))
            listofColorT.append((red,green,blue))
            #print(listofColorT)
            #print(strrT)

            listofColor=remove(listofColor)
            listofColor2=remove(listofColor2)
            listofColorT=remove(listofColorT)
            print(listofColor)
            print(listofColor2)
            print(listofColorT)

            for x in range(len(listofColor)):
                xx= convertt(listofColor[x],listofColor2)
                sortedlist.append(x)
                sortedlist.append(listofColor2.index(xx))
            print(sortedlist)
            final_list = []
            for y in sortedlist: 
                if y not in final_list: 
                    final_list.append(y)
            print(final_list)
            resulttt= [lower_list[i] for i in final_list]
            
            for image in upper_list:
                for c in contours:
                    M = cv2.moments(c)
                    center_x, center_y = (int(M['m10'] / (M['m00']+ 1e-5)), int(M['m01'] / (M['m00']+ 1e-5)))
                    listoftupleT.append((center_x, center_y))

            res =max(listoftupleT, key = lambda i : i[0])[0]
            res2 = min(listoftupleT, key = lambda i : i[0])[0]
            resT = min(listoftupleT, key = lambda i : i[1])[0]
            resB = max(listoftupleT, key = lambda i : i[1])[0]

            for a in range(len(listoftupleT)):
                if res == listoftupleT[a][0]:
                    res= listoftupleT[a]
                if res2 == listoftupleT[a][0]:
                    res2= listoftupleT[a]
                if resT == listoftupleT[a][0]:
                    resT= listoftupleT[a]
                if resB == listoftupleT[a][0]:
                    resB= listoftupleT[a]
            blue = masked_image[resB[1],resB[0]][0]
            green= masked_image[resB[1],resB[0]][1]
            red = masked_image[resB[1],resB[0]][2]
            strr= (str(red)+','+str(green)+','+str(blue))
            listofColorB.append((red,green,blue))
        
            indexx = 0
            for x in range(len(listofColorB)):
                xx= convertt(listofColorB[x],listofColorT)
                indexx =listofColorT.index(xx)
            print(indexx)
    
    for n in range(4):
        if n == indexx:
            uupper_list.append(upper_list[0])
        else:
            uupper_list.append(create(lower_list[n]))

    
    
            
       

        #uupper_list = [(image_list[0]), (create(image_list[2])),(create(image_list[3])),(create(image_list[4]))]


                
    """   
    listoftupleofupper=[]     
    for image in upper_list:
        M = cv2.moments(c)
        center_x, center_y = (int(M['m10'] / (M['m00']+ 1e-5)), int(M['m01'] / (M['m00']+ 1e-5)))
        listoftupleofupper.append((center_x, center_y))
            
        resB = max(listoftupleofupper, key = lambda i : i[1])[0]
        
        for a in range(len(listoftupleofupper)):
            if resB == listoftupleofupper[a][0]:
                resB= listoftupleofupper[a]
            
        blue = masked_image[resB[1],resB[0]][0]
        green= masked_image[resB[1],resB[0]][1]
        red = masked_image[resB[1],resB[0]][2]
        strrB= (str(red)+','+str(green)+','+str(blue))
        listofColorB.append((red,green,blue))
        print(strrB)
        
        for x in range(len(listofColorT)):

            xx= convert(listofColorB[x],listofColorT)
            #sortedlist2.append(upper_list[x])
            #sortedlist2.append(listofColorT.index(xx))
        img = np.zeros(image.shape, np.uint8) 
        img = cv2.bitwise_not(img)
        upper_list.append(img)
        print(sortedlist2)
        
        final_list = []
        for y in sortedlist2: 
            if y not in final_list: 
                final_list.append(y)
        print(final_list)
        #resultt= [upper_list[i] for i in final_list]
    
    """
     
    out = np.hstack(resulttt)
    cv2.imshow('Output', out)
    
    outt= np.hstack(uupper_list)
    cv2.imshow('OutputU', outt)
    
    #finnnnal=[upper_list, resulttt]

    #f = np.vstack(finnnnal)
    #cv2.imshow("ff",f)

    #cv2.imshow('oo',frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()