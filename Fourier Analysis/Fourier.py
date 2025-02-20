from mpl_toolkits import mplot3d
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv

def get_dft_coef(z,k,l):
    M = len(z)
    N = len(z[0])
    ek = np.exp(-2j*np.pi*k/M)
    el = np.exp(-2j*np.pi*l/N)
    coef = 0
    for i in range(M):
        for j in range(N):
            if z[i,j] != 0:
                coef += z[i,j] * (ek**i) * (el**j)
    return coef

t = np.arange(-np.pi,np.pi,0.1)
tL = len(t)//2
x = t.copy()
y = t.copy()
x, y = np.meshgrid(x,y)
z = np.zeros((len(t),len(t)))
z[tL-2:tL+2,tL-2:tL+2] = np.ones_like(z[tL-2:tL+2,tL-2:tL+2])

DFT = cv.dft(z,flags=cv.DFT_COMPLEX_OUTPUT)
DFT_test = np.zeros((len(z),len(z[0]),2))
for ir in range(len(z)):
    for jr in range(len(z[0])):
        coef = get_dft_coef(z,ir,jr)
        DFT_test[ir,jr,0], DFT_test[ir,jr,1] = np.real(coef), np.imag(coef)

z = cv.idft(DFT_test)
z = cv.magnitude(z[:,:,0],z[:,:,1])

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
ax.plot_surface(x,y,z,vmin = z.min() * 2, cmap=cm.Blues)

plt.show()