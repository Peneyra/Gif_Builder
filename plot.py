import numpy as np
import cv2 as cv

# The purpose of this file is to define functions to create and 
# manipulate a plot of scalars from an image file, particularly
# an image which uses a color scale to depict information on a
# map.

def build_scale(raw):
    # input: np array (x,3)  - slice of an image
    # output: np array (x,3) - return an array of BGR integers
    bw_count = len(raw)
    out = []
    out_temp = []
    r_last = [-1,-1,-1]
    for r in raw:
        # filter out black and white and check RGB not same as last
        if (not all(r > 250)
                and not all(r < 5)
                and np.linalg.norm(r-r_last) >= 5):
            if bw_count > 10: 
                out_temp = r.copy()
            else: 
                out_temp = np.vstack((out_temp,r))
            if len(out_temp) > len(out): 
                out = out_temp.copy()
            r_last = r.copy()
            bw_count = 0
        elif all(r > 250) or all(r < 5):
            bw_count += 1
    return out
def lrtb(image):
    # input: np array (x,y,3) - image with a black/white border
    # output: integers (4)    - top, bottom, left, right of the colorful area
    def bound(mask_bounds,offset):
        begin, end = len(mask_bounds[0,:]), 0
        found = False
        temp = 0
        for be in range(len(mask_bounds[0,:])):
            if sum(mask_bounds[:,be]) > 0 and not found:
                found = True
                temp = be
            elif sum(mask_bounds[:,be]) == 0 and found:
                found = False
                if be - temp > end - begin:
                    end = be
                    begin = temp
        if found:
            if be - temp > end - begin:
                end = be
                begin = temp
        return [begin + offset, end + offset]
    mask = np.zeros_like(image[:,:,0]).astype(bool)
    for i in range(3):
        mask = mask + np.multiply(image[:,:,i] > 10, image[:,:,i] < 245)
    l, r, t, b = 0, len(mask[0,:]) - 1, 0, len(mask[:,0]) - 1
    for i in range(3):
        [l,r] = bound(mask[t:b+1,l:r+1],l)
        [t,b] = bound(mask[t:b+1,l:r+1].T,t)
    return [l,r,t,b]
def gen(image, scale):
    # input: np array (x,y,3) - image with RGB values
    # input: np array (x,3)   - scale of RGB values in order of magnitude
    # output: np array (x,y)  - grayscale plot with values centered at zero
    l,r,t,b = lrtb(image)
    out = np.zeros_like(image[t:b,l:r,0].astype(int))
    for i in range(len(scale)):
        mask = out == 0
        for j in range(3): 
            mask = np.multiply(mask, abs(image[t:b,l:r,j] - scale[i,j]) < 25)
        out = out + (mask.astype(int) * (i + 1))
        cv.imwrite('./debug/yaml_test_plt_' + str(i) + '.png', 5 * (out - np.min(out)))
    out = out - (np.max(out)//2)
    return out
def smooth(plt, repeat):
    # input: np array (x,y) - grayscale plot
    # input: int            - number of times to repeat the smoothing fn
    out = np.array(plt - np.min(plt)).astype(int)
    cv.imwrite('./debug/yaml_test_smooth_raw.png', 10 * (out - np.min(out)))
    for r in range(repeat):
        tmp = np.pad(
            out[1:plt.shape[0]-1, 1:out.shape[1]-1],
            (1,),
            'constant',
            constant_values = 0
        )
        add = np.zeros_like(out).astype(np.float64)
        cnt = np.zeros_like(out).astype(np.float64)
        for (i,j) in [(1,0),(1,1),(-1,0),(-1,0),(-1,1),(-1,1),(1,0)]:
            tmp = np.roll(tmp, i, axis = j)
            add = add + tmp
            cnt = (cnt + np.array(tmp != 0).astype(type(cnt[0,0])))
        add = np.divide(add, cnt, out = np.zeros_like(add), where=cnt!=0)
        mask = np.array(out == 0).astype(np.float64)
        out = out + np.multiply(add, mask)
        # debug images
        cv.imwrite('./debug/yaml_test_add_' + str(r) + '.png', 10 * (add - np.min(add)))
        cv.imwrite('./debug/yaml_test_cnt_' + str(r) + '.png', 10 * (cnt - np.min(cnt)))
    return out - (np.max(out) // 2)
def restore(plt, template, scale, dtg):
    # input: np array (x,y)   - grayscale plot
    # input: string           - template name
    # input: np array (x,3)   - scale of RGB values in order of magnitude
    # input: string           - date, time, group
    # output: np array (x,y,3)- output image
    out = cv.imread(
        './templates/' + template + '/' + template + '_template.gif'
    )
    x, y = out.shape[:2]
    l, r, t, b = lrtb(out)
    mt = [0, 0, 124]
    var = 25
    mask = np.ones_like(out[:,:,0]).astype(int)
    for i in range(3):
        mask = np.multiply(
            mask,
            np.array(abs(out[:,:,i].astype(int) - mt[i]) < var).astype(int)
        )
    plt_color = np.zeros_like(plt).astype(int)
    for i in range(len(scale))[1:]:
        for j in range(3):
            plt_color[:,:,j] = np.array(plt == i).astype(int) * scale[i, j]
    plt_color = cv.resize(plt_color, out[t:b,l:r,i].shape[:2])
    for i in range(3):
        out[t:b,l:r,i] = np.multiply(
            np.array(mask[t:b,l:r,i] == 0).astype(int),out[t:b,l:r,i]
        ) + np.multiply(mask[t:b,l:r,i], plt_color)
    if t < y - b:
        y_text = b + (y - b)//2
    else:
        y_text = t//2
    out = cv.putText(
        out, 
        template+" - "+dtg, 
        (l, y_text + 5),
        cv.FONT_HERSHEY_SIMPLEX,
        .5,
        (0,0,0),
        1,
        cv.LINE_AA,
        False
    )
    return out