import numpy as np

def char_list():
    out = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return out
def month_name(m):
    if m == 1: return "JAN"
    elif m == 2: return "FEB" 
    elif m == 3: return "MAR" 
    elif m == 4: return "APR" 
    elif m == 5: return "MAY" 
    elif m == 6: return "JUN" 
    elif m == 7: return "JUL" 
    elif m == 8: return "AUG" 
    elif m == 9: return "SEP" 
    elif m == 10: return "OCT" 
    elif m == 11: return "NOV" 
    elif m == 12: return "DEC"
    else: return None
def dft_mapping(n):
    # input: int - number of one side of coefficients
    # output: array of addresses where to put dft coefficients
    # save all coefficients to a single flattened array organized by:
    # 1 2 3 ...
    # 2 2 3 ...
    # 3 3 3 ...
    # This organization will assist with maximum compression of the follow 
    # on message map all the addresses in the order you want them.
    address = [[0,0]] * (n * n)
    k_a = 1
    for k in range(1,n):
        j = k
        for i in range(k):
            address[k_a] = [i, j]
            k_a += 1
            address[k_a] = [j, i]
            k_a += 1
        address[k_a] = [k, k]
        k_a += 1
    return address

def coeff_round(x):
    # input: int - number between -1000 and 1000
    # output: int - number between 0 and len(char_list)
    if abs(x) > 1000: return 0
    out = 0
    m_int = 1000
    m_char = (len(char_list()) - 1) // 2
    dx = np.log10(m_int) / m_char
    if x < 0: offset = 1
    else: offset = 0
    x_log = np.log10(abs(x))
    for i in range(1,m_char):
        if (i)*dx < x_log and x_log <= (i+1)*dx: out = i * 2
    return int(out + offset)
def coeff_unround(x):
    # input: int - number between 0 and len(char_list)
    # output: int - number between -1000 and 1000
    if x == 0 or x > len(char_list()): return 0
    out = 0
    m_int = 1000
    m_char = (len(char_list()) - 1) // 2
    dx = np.log10(m_int) / m_char
    offset = x % 2
    out = 10 ** ((((x-offset)/2)+.5)*dx)
    if offset == 1: out = out * (-1)
    return out
def change_basis(num,b1,b2):
    # Convert num in base b1 to a number in base b2
    # input: int array - an array of integers representing the digits in
    # a base b1 number
    # output: int array - an array of integers representing the digits in
    # a base b2 number
    dec = 0
    out = []
    exp = 1
    for n in num[::-1]:
        dec = dec + (n * exp)
        exp = exp * b1
    while dec > 0:
        out.append(dec % b2)
        dec = (dec - (dec % b2)) // b2
    return out[::-1]

def msgdata_write(dft,n):
    # input: float array - DFT
    # input: dict - configuration file
    # input: dict - plot specific variables (i.e. x, y, max, n, etc.)
    # output: string - message output
    dft_address = dft_mapping(n)
    dft_flat = []
    chars = char_list()
    x, y = dft.shape[:2]
    out = ''
    for [i1,j1] in dft_address:
        i2, j2, k2 = [i1,x-i1-1], [j1,y-j1-1], [0,1]
        for i3 in i2:
            for j3 in j2:
                for k3 in k2:
                    dft_flat.append(coeff_round(dft[i3,j3,k3]))
    beg = 0
    end = 2
    dump = False
    line_cap = '\n'
    while beg < len(dft_flat):
        if end >= len(dft_flat):
            line_cap = '/\n'
            dump = True
        elif 67 < len(change_basis(dft_flat[beg:end],
                                   max(dft_flat[beg:end]),
                                   len(chars))
                                   ):
            end -= 1
            dump = True
        if dump:
            m_d = max(dft_flat[beg:end])
            print(dft_flat[beg:end])
            out += str(chars[m_d + 1])
            for cb in change_basis(dft_flat[beg:end],m_d+1,len(chars)):
                out += str(chars[cb])
            out += line_cap
            beg = end
            end += 1
            dump = False
        end += 1
    return out
def msgdata_read(msg):
    # input: string - VLF ARGUS message
    # output: float array - DFT
    header, footer = True, False
    chars = char_list()
    for m in msg.splitlines():
        if header:
            if 'A1R1G2U3S5' in m:
                header = False
                S = m.split('/')
                x, y, n, max_coeff = [int(k) for k in S[0:4]]
                dtg = S[4]
                template = S[5]
                dft = np.zeros((x,y,2))
                dft_address = dft_mapping(n)
                dft_flat = []
        elif not footer:
            m_d = chars.find(m[0])
            line_int = []
            for a in m[1:]:
                if a == '/': footer = True
                else:        line_int.append(chars.find(a))
            line_int = change_basis(line_int,len(chars),m_d)
            print(line_int)
            for li in line_int: dft_flat.append(li)
            with open("./debug/DFT_flat_read.txt",'w') as file: 
                print(dft_flat, file = file)
    k = 0
    for [i,j] in dft_address:
        i_s, j_s, k_s = [i,x-i-1], [j,y-j-1], [0, 1]
        for i1 in i_s:
            for j1 in j_s:
                for k1 in k_s:
                    dft[i1,j1,k1] = coeff_unround(dft_flat[k])
                    k += 1
    return dft, template, dtg