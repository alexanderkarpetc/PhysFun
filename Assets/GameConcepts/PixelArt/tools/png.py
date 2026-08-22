import zlib,struct,sys
def load(p):
    d=open(p,'rb').read()
    pos=8; idat=b''; w=h=bd=ct=None; pal=None; trns=None
    while pos<len(d):
        ln=struct.unpack('>I',d[pos:pos+4])[0]; typ=d[pos+4:pos+8]; data=d[pos+8:pos+8+ln]; pos+=12+ln
        if typ==b'IHDR': w,h,bd,ct=struct.unpack('>IIBB',data[:10])
        elif typ==b'IDAT': idat+=data
        elif typ==b'PLTE': pal=data
        elif typ==b'tRNS': trns=data
    raw=zlib.decompress(idat)
    ch={0:1,2:3,3:1,4:2,6:4}[ct]
    bpp=ch*bd//8 or 1
    stride=(w*ch*bd+7)//8
    out=bytearray(); prev=bytearray(stride)
    i=0
    for y in range(h):
        f=raw[i]; i+=1
        line=bytearray(raw[i:i+stride]); i+=stride
        for x in range(stride):
            a=line[x-bpp] if x>=bpp else 0
            b=prev[x]
            c=prev[x-bpp] if x>=bpp else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+(a+b)//2)&255
            elif f==4:
                p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
                pr=a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
                line[x]=(line[x]+pr)&255
        out+=line; prev=line
    px=[]
    for y in range(h):
        row=[]
        for x in range(w):
            if ct==6: o=(y*w+x)*4; row.append(tuple(out[o:o+4]))
            elif ct==2:
                o=(y*w+x)*3; c3=tuple(out[o:o+3])
                a=255
                if trns and len(trns)>=6:
                    key=(trns[1],trns[3],trns[5])
                    if c3==key: a=0
                row.append(c3+(a,))
            elif ct==3:
                idx=out[y*stride+ (x*bd)//8]
                if bd<8:
                    shift=8-bd-((x*bd)%8); idx=(idx>>shift)&((1<<bd)-1)
                r,g,b=pal[idx*3:idx*3+3]
                a=trns[idx] if trns and idx<len(trns) else 255
                row.append((r,g,b,a))
            elif ct==4: o=(y*w+x)*2; v=out[o]; row.append((v,v,v,out[o+1]))
            else:
                v=out[y*stride+x]; row.append((v,v,v,255))
        px.append(row)
    return w,h,px
if __name__=='__main__':
    w,h,px=load(sys.argv[1]); print(w,h)
    for y in range(h):
        print(''.join('.' if p[3]==0 else '#' for p in px[y]))
