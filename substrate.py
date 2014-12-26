import PIL.Image
import math
import os, os.path

def make_black(size) :
    return PIL.Image.new("RGB", size, (0,0,0))

def fingerprint(img, bits=8) :
    xw, yw = img.size

    divisor = int(math.pow(2, 8-bits))
    mult = int(math.pow(2, bits))
    colors = int(math.pow(2, bits*3))
    
    values = [0] * colors
    print 'using %d colors...' % colors

    for x in range(xw) :
        for y in range(yw) :
            r,g,b = img.getpixel((x, y))

            r //= divisor
            g //= divisor
            b //= divisor

            color = r * mult * mult + g * mult + b

            values[color] += 1

    return values

def similarity(f1, f2) :
    # this assumes both images had the same number of pixels...
    total_pixels = 0
    matched_pixels = 0
    for i in range(len(f1)) :
        a = f1[i]
        b = f2[i]
        total_pixels += a
        matched_pixels += min(a, b)

    return float(matched_pixels) / float(total_pixels)


class Photo(object) :
    IMAGES = dict()
    BITS = 3
    
    @classmethod
    def get_image(cls, filename) :
        if filename not in cls.IMAGES :
            cls.IMAGES[filename] = cls(filename)
        return cls.IMAGES[filename]

    def __init__(self, filename) :
        self.filename = filename
        self.image = PIL.Image.open(filename)
        self.fingerprint = fingerprint(self.image, bits=self.BITS)
        self.similarity_to = dict()

    def similar(self, o) :
        if id(self) < id(o) :
            return o.similar(self)

        if o not in self.similarity_to :
            self.similarity_to[o] = similarity(self.fingerprint, o.fingerprint)

        return self.similarity_to[o]


def layout(directory, xc, yc) :
    image_fns = os.listdir(directory)
    image_fns.sort()
    image_fns = image_fns[0:xc*yc]
    images = [Photo.get_image(os.path.join(directory, fn)) for fn in image_fns]

    if len(set([i.image.size for i in images])) != 1 :
        print 'Sizes do not all match, aborting'
        sys.exit(1)

    xw, yw = images[0].image.size
    padding_x = int(xw * .618 * 0.5)
    padding_y = int(xw * .618 * 0.5)
    
    xwt = xw * xc + padding_x * (xc + 1) + padding_x * xc
    ywt = yw * yc + padding_y * (yc + 1) + padding_y * yc

    composite_img = make_black((xwt, ywt))

    def get_imgcorner(_x, _y) :
        #local xw, yw, padding_x, padding_y
        _x = _x * xw + (padding_x * _x) + (padding_x * (_x + 1))
        _y = _y * xw + (padding_y * _y) + (padding_y * (_y + 1))
        return (_x, _y)

    def get_img(_x, _y) :
        #local yc, xc, xii, yii, images
        if _x < 0 or _y < 0 :
            return None
        if _x >= xc or _y >= yc :
            return None
        return images[xii * yc + yii]

    for xii in range(xc) :
        for yii in range(yc) :
            # copy the image into the composite
            img = get_img(xii, yii)
            corner = get_imgcorner(xii, yii)
            for xp in range(xw) :
                for yp in range(yw) :
                    composite_img.putpixel((corner[0] + xp, corner[1] + yp), img.image.getpixel((xp, yp)))

    return composite_img
