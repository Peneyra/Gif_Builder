import numpy as np
import cv2 as cv
import imageio

# The purpose of this file is to define functions to create and 
# manipulate a plot of scalars from an image file, particularly
# an image which uses a color scale to depict information on a
# map.

def build_int(raw):
    # input: np array (x,3) - slice of an image
    # output: np array (x,3) - return an array of BGR integers
    scale_out = []
    r_last = np.zeros(3).astype(np.uint8)
    for r in raw:
        # filter out black and white and check RGB not same as last
        if (not all(r > 250)
                and not all(r < 5)
                and sum(np.abs(np.subtract(r_last,r))) >= 5):
            scale_out.append(r)
            r_last = r.copy()
    return scale_out
def tblr(image):
    # input: np array (x,y,3) - image with a black/white border
    # output: integers (4) - top, bottom, left, right of the colorful area
    def bound(mask_bounds):
        begin, end = len(mask_bounds[:,0]), 0
        found = False
        temp = 0
        for be in range(len(mask_bounds[:0])):
            if sum(mask_bounds[be,:]) > 0 and not found:
                found = True
                temp = be
            if sum(mask_bounds[be,:]) == 0 and found:
                found = False
                if be - temp > end - begin:
                    end = be - 1
                    start = temp
        if found:
            if be - temp > end - begin:
                end = be - 1
                start = temp
        return [begin, end]
    mask = np.zeros_like(image[:,:,0]).astype(bool)
    for i in range(3):
        mask = mask + np.multiply(image[:,:,i] > 15, image[:,:,i] < 240)
    t, b, l, r = 0, len(mask[:,0]), 0, len(mask[0,:])
    for i in range(3):
        [t,b] = bound(mask[t:b,l:r])
        [l,r] = bound(mask[t:b,l:r].T)
    return [t,b,l,r]
def generate(image, scale):
    # input: np array (x,y,3) - image with RGB values
    # input: np array (x,3) - scale of RGB values in order of magnitude
    # output: np array (x,y) - grayscale plot with values centered at zero
    out = np.zeros_like(image[:,:,0].astype(int))
    for i in range(len(scale)):
        mask = out == 0
        for j in range(3): 
            mask = np.multiply(mask, abs(image[:,:,j] - scale[i,j]) < 5)
        out = out + (mask.astype(int) * (i + 1))
    out = out - (max(out)//2)
    return out
def smooth(plt, repeat):
    # input: np array (x,y) - grayscale plot
    # input: int - number of times to repeat the smoothing function
    for r in range(repeat):
        tmp = np.pad(
            plt[1:plt.shape[0]-1, 1:plt.shape[1] - 1],
            (1,),
            'constant',
            constant_values = 0
        )
        add = np.zeros_like(plt).astype(np.float64)
        cnt = np.zeros_like(plt).astype(np.float64)
        for (i,j) in [(1,0),(1,1),(-1,0),(-1,0),(-1,1),(-1,1),(1,0)]:
            tmp = np.roll(tmp, i, axis = j)
            add = add + tmp
            cnt = (cnt + np.array(tmp != 0).astype(type(cnt[0,0])))
        add = np.divide(add, cnt, out = np.zeros_like(add), where=cnt!=0)
        mask = np.array(out == 0).astype(type(add))
        out = out + np.multiply(add, mask).astype(np.uint8)
        # debug images
        cv.imwrite('./debug/test_add_' + str(r) + '.jpg', 10 * add)
        cv.imwrite('./debug/test_cnt_' + str(r) + '.jpg', 10 * cnt)
    return out
