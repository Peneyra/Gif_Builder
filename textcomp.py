def char_list():
    out = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!-'
    return out
def dec2aA1(i):    
    if i < 10: return         str(i)
    if i < 36: return         chr(i + ord('A') - 10)
    return                    chr(i + ord('a') - 36)
def aA12dec(s):
    try:
        if int(s) < 10: return int(s)
    except:
        None
    if ord(s) < ord('a'): 
        return                 int(ord(s) + 10 - ord('A'))
    else: return               int(ord(s) + 36 - ord('a'))
def coeff_round(x):
    k_cr = 54
    n_cr = 3
    for i in range(n_cr):
        for j in range(9):
            if x > (9.5-j) * (10 ** (2 - i)): return k_cr
            k_cr -= 1
            if x < (j-9.5) * (10 ** (2 - i)): return k_cr
            k_cr -= 1
    return 0
def coeff_unround(x):
    if x == 0: return 0
    k_cu = 1
    n_cu = 3
    for i in range(n_cu):
        for j in range(2,11):
            if x == k_cu: return (-1) * j * (10 ** i)
            k_cu += 1
            if x == k_cu: return        j * (10 ** i)
            k_cu += 1
    return 0