import os
import numpy as np

def char_list():
    out = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return out


def month_name(m):
    if m == 1:    return " JAN "
    elif m == 2:  return " FEB " 
    elif m == 3:  return " MAR " 
    elif m == 4:  return " APR " 
    elif m == 5:  return " MAY " 
    elif m == 6:  return " JUN " 
    elif m == 7:  return " JUL " 
    elif m == 8:  return " AUG " 
    elif m == 9:  return " SEP " 
    elif m == 10: return " OCT " 
    elif m == 11: return " NOV " 
    elif m == 12: return " DEC "
    else:         return None


def dft_mapping(n):
    # input: int - number of one side of coefficients
    # output: array of addresses where to put dft coefficients
    # save all coefficients to a single flattened array organized by:
    # 1 1 2 2 3 3 ...
    # 2 2 2 2 3 3 ...
    # 3 3 3 3 3 3 ...
    # This organization will assist with maximum compression of the follow 
    # on message map all the addresses in the order you want them.
    out = [[0,0],[0,1]]

    for k in range(1,n):
        j = k
        for i in range(k):
            out.append([i, 2 * j])
            out.append([i, 2 * j + 1])
            out.append([j, 2 * i])
            out.append([j, 2 * i + 1])
        out.append([k, 2 * k])
        out.append([k, 2 * k + 1])

    return out


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

    out = 10 ** ((((x-offset)/2)+1)*dx)

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
    # check for leading zeros
    lead_zeros = 0

    for n in num[::-1]:
        if n == 0: lead_zeros += 1
        else: lead_zeros = 0
        dec = dec + (n * exp)
        exp = exp * b1
    
    while dec > 0:
        out.append(dec % b2)
        dec = (dec - (dec % b2)) // b2

    for i in range(lead_zeros): out.append(0)    

    return out[::-1]


def msgcontent_write(fp):
    # input: fp   - file structure with msg_template defined
    # output: str - message intro
    # output: str - message outro
    # if the message doesn't already exist, load a generic file to read
    if not os.path.exists(fp.msg_template):
        with open(fp.msg_template,'w') as file:
            print("R XXXXXXZ MMM YY",             file = file)
            print("FM COMSUBPAC PEARL HARBOR HI", file = file)
            print("TO SSBN PAC",                  file = file)
            print("BT",                           file = file)
            print("UNCLAS",                       file = file)
            print("SUBJ/VLF WEATHER GIF//",       file = file)
            print("RMKS/REACH OUT TO ISIC FOR INSTRUCTIONS ON HOW TO USE THIS "
                  "MESSAGE.",                     file = file)
            print("<message>",                    file = file)
            print("BT",                           file = file)
            print("#0001",                        file = file)
            print("NNNN",                         file = file)
    with open(fp.msg_template,'r') as file: out = file.read()


    return out.split("<message>\n")[0], out.split("<message>\n")[1]


def msgdata_write(dft,n):
    # input: float array - DFT
    # input: dict - configuration file
    # input: dict - plot specific variables (i.e. x, y, max, n, etc.)
    # output: string - message output
    dft_address = dft_mapping(n)
    dft_flat = []
    chars = char_list()
    x = dft.shape[0]
    out = ''

    for [i,j] in dft_address:
        i1 = [i,x-i-1]
        for i2 in i1: dft_flat.append(coeff_round(dft[i2,j]))
    
    beg, end = 0, 2
    dump = False
    line_cap = '\n'

    while beg < len(dft_flat):
        m_d = max(dft_flat[beg:end]) + 1
        line = change_basis(dft_flat[beg:end], m_d, len(chars))
        if 67 < len(line):
            end -= 1
            m_d = max(dft_flat[beg:end]) + 1
            line = change_basis(dft_flat[beg:end], m_d, len(chars))
            dump = True
        elif end >= len(dft_flat):
            line_cap = '/\n'
            dump = True
        if dump:
            print(dft_flat[beg:end])

            out += str(chars[m_d])
            for cb in line:
                out += str(chars[cb])
            out += line_cap

            beg = end
            end += 1
            dump = False
        end += 1

    return out


def msg_read(msg):
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
                dft = np.zeros((x,y))
                dft_address = dft_mapping(n)
                dft_flat = []

        elif not footer:
            m_d = chars.find(m[0])
            line = []
            for a in m[1:]:
                if a == '/': footer = True
                else:        line.append(chars.find(a))
            line = change_basis(line,len(chars),m_d)
            print(line)
            for li in line: dft_flat.append(li)
    k = 0
    for [i,j] in dft_address:
        i1 = [i,x-i-1]
        for i2 in i1:
            if k < len(dft_flat): 
                dft[i2,j] = coeff_unround(dft_flat[k])
                # print(str(i2) + ", " + str(j) + ", " + str(dft_flat[k]))
            else:
                None
                # print(k)
            k += 1
            
    return dft, max_coeff, template, dtg