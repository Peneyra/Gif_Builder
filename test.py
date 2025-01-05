import numpy as np
import cv2 as cv
import imageio
import os
import tkinter as Tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image

# def plot_smooth(arr,repeat):
#     arr_out = np.copy(arr).astype(np.uint8)
#     for r in range(repeat):
#         arr_bol = np.copy(arr_out) != 0
#         cv.imwrite('./test_msk_bol_' + str(r) + '.jpg',128*np.array(arr_bol).astype(np.uint8))

#         arr_num = np.zeros_like(arr_out)
#         arr_den = np.zeros_like(arr_out)
#         for (i, j) in [(-1,1),(1,0),(1,1),(1,1),(-1,0),(-1,0),(-1,1),(-1,1)]:
#             arr_out = np.roll(arr_out, i, axis = j)
#             arr_num = arr_num + np.array(arr_out)
#             arr_den = arr_den + np.array(arr_out != 0)
#         arr_out = np.roll(np.roll(arr_out, 1, axis = 0), 1, axis = 1)
#         arr_num = np.multiply(arr_num, np.array(arr_bol == False).astype(type(arr_num)))
#         cv.imwrite('./test_num_' + str(r) + '.jpg', 128 * arr_num / 8)
#         arr_den = np.multiply(arr_den, np.array(arr_bol == False).astype(type(arr_den)))
#         cv.imwrite('./test_den_' + str(r) + '.jpg', 128 * arr_den)

#         arr_num = np.divide(arr_num, arr_den)
#         # arr_num = np.multiply(arr_num, np.array(arr_bol == False).astype(np.float64))
#         cv.imwrite('./test_msk_' + str(r) + '.jpg',128 * arr_num)

#         arr_out = arr_out + np.divide(arr_num, arr_den).astype(np.uint8)
#         cv.imwrite('./test_' + str(r) + '.jpg',128 * arr_out)

#     return arr_out

def plot_smooth(arr,repeat):
    arr_out = np.copy(arr)
    for r in range(repeat):
        arr_tmp = np.roll(np.roll(np.copy(arr_out), -1, axis = 0), -1, axis = 1).astype(np.float64)
        arr_add = np.zeros_like(arr_out).astype(np.float64)
        arr_cnt = np.zeros_like(arr_out).astype(np.float64)
        for (i, j) in [(1,0),(1,0),(1,1),(1,1),(-1,0),(-1,0),(-1,1),(-1,1)]:
            arr_tmp = np.roll(arr_tmp, i, axis = j)
            arr_add = arr_add + arr_tmp
            arr_cnt = arr_cnt + np.array(arr_tmp != 0).astype(type(arr_cnt[0,0]))
        arr_add = np.divide(arr_add, arr_cnt, out = np.zeros_like(arr_add), where=arr_cnt!=0)
        cv.imwrite('./test_add_' + str(r) + '.jpg', 10 * arr_add)
        cv.imwrite('./test_cnt_' + str(r) + '.jpg', 10 * arr_cnt)
        arr_out = arr_out + np.array(np.multiply(arr_add,arr_out == 0)).astype(np.uint8)
        cv.imwrite('./test_' + str(r) + '.jpg', 10 * arr_out)
    return arr_out

plot = cv.imread("./test_build_plot_raw.jpg",0)

plot = plot_smooth(plot,20)

cv.imshow('plot', plot)
cv.waitKey(0)
