import sys
import random
import PIL.Image
import math
import os
import os.path


def make_black(size):
    return PIL.Image.new("RGB", size, (0, 0, 0))


def fingerprint(img, bits=8):
    xw, yw = img.size

    divisor = int(math.pow(2, 8 - bits))
    mult = int(math.pow(2, bits))
    colors = int(math.pow(2, bits * 3))

    values = [0] * colors
    # print 'using %d colors...' % colors

    for x in range(xw):
        for y in range(yw):
            r, g, b = img.getpixel((x, y))

            r //= divisor
            g //= divisor
            b //= divisor

            color = r * mult * mult + g * mult + b

            values[color] += 1

    return values


def avg(vals):
    n = len(vals)
    return reduce(lambda a, b: a + b, vals) / float(n)


def similarity(f1, f2, bits=3):
    # this assumes both images had the same number of pixels...
    total_pixels = 0
    matched_pixels = 0

    div = int(math.pow(2, bits))
    for i in range(len(f1)):
        a = f1[i]
        b = f2[i]
        total_pixels += a

        colors = []
        c = i
        for j in range(3):
            colors.append(c % div)
            c //= div

        avg_val = avg(colors)
        divergences = [abs(c - avg_val) for c in colors]
        if avg_val < 0.1:
            saturation = 0.0
        else:
            saturation = max(divergences) / avg_val

        matched_pixels += min(a, b) * saturation  # lol not really matched anymore

    return float(matched_pixels) / float(total_pixels)


class Photo(object):
    IMAGES = dict()
    BITS = 3

    @classmethod
    def get_image(cls, filename):
        if filename not in cls.IMAGES:
            cls.IMAGES[filename] = cls(filename)
        return cls.IMAGES[filename]

    def __init__(self, filename):
        self.filename = filename
        self.image = PIL.Image.open(filename)
        self.fingerprint = fingerprint(self.image, bits=self.BITS)
        self.similarity_to = dict()

    def similar(self, o):
        if id(self) < id(o):
            return o.similar(self)

        if o not in self.similarity_to:
            self.similarity_to[o] = similarity(self.fingerprint, o.fingerprint, bits=self.BITS)

        return self.similarity_to[o]


def layout(directory, xc, yc):
    image_fns = os.listdir(directory)
    image_fns.sort()
    image_fns = image_fns[0:xc * yc]
    images = list()
    for i in range(len(image_fns)):
        images.append(Photo.get_image(os.path.join(directory, image_fns[i])))
        print 'Loaded %d images..' % (i + 1)

    xw = max([i.image.size[0] for i in images])
    yw = max([i.image.size[1] for i in images])

    #pad_ratio = 0.518
    pad_ratio = 0.318

    padding_x = int(xw * pad_ratio)
    padding_y = int(yw * pad_ratio)

    xwt = xw * xc + padding_x * (xc + 1)
    ywt = yw * yc + padding_y * (yc + 1)

    composite_img = make_black((xwt, ywt))

    def get_imgcorner(_x, _y):
        _x = _x * xw + (padding_x * (_x + 1))
        _y = _y * yw + (padding_y * (_y + 1))
        return (_x, _y)

    def get_img(_x, _y, just_idx=False):
        if _x < 0 or _y < 0:
            return None
        if _x >= xc or _y >= yc:
            return None
        idx = _x * yc + _y
        if just_idx:
            return idx
        else:
            return images[idx]

    def get_neighborimgs(_x, _y):
        for xd, yd in [(0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            i = get_img(_x + xd, _y + yd)
            if i is not None:
                yield i

    def maybeswap(pos1, pos2):
        neighbors_1 = list(get_neighborimgs(*pos1))
        neighbors_2 = list(get_neighborimgs(*pos2))

        def sum_sim(list_of_neighbors):
            sim = 0.0
            for a, list_of_b in list_of_neighbors:
                for b in list_of_b:
                    sim += a.similar(b)
            print 'similarity is: %f' % sim
            return sim

        img_1 = get_img(*pos1)
        img_2 = get_img(*pos2)
        no = [(img_1, neighbors_1), (img_2, neighbors_2)]
        yes = [(no[0][0], no[1][1]), (no[1][0], no[0][1])]

        if sum_sim(yes) > sum_sim(no):
            print 'do swap %s & %s' % (str(pos1), str(pos2))
            idx_1 = get_img(*pos1, just_idx=True)
            idx_2 = get_img(*pos2, just_idx=True)
            images[idx_1] = img_2
            images[idx_2] = img_1
        else:
            print 'no swap...'

    NUM_SWAPMOVES = xc * yc * 100

    for i in range(NUM_SWAPMOVES):
        x1 = random.randrange(0, xc)
        y1 = random.randrange(0, yc)
        x2 = random.randrange(0, xc)
        y2 = random.randrange(0, yc)

        pos1 = (x1, y1)
        pos2 = (x2, y2)

        maybeswap(pos1, pos2)

    imgs_pasted = 0

    # solidify layout
    for xii in range(xc):
        for yii in range(yc):
            # copy the image into the composite
            img = get_img(xii, yii)
            corner = get_imgcorner(xii, yii)
            # print 'pasting img of size %s at %s' % (str(img.image.size), str(corner))
            composite_img.paste(img.image, box=corner)
            imgs_pasted += 1

            print 'pasted %d images...' % imgs_pasted

            # for xp in range(xw) :
            #    for yp in range(yw) :
            #        composite_img.putpixel((corner[0] + xp, corner[1] + yp), img.image.getpixel((xp, yp)))

    print 'made image %d x %d' % (xwt, ywt)

    return composite_img


if __name__ == '__main__':
    c = layout(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    c.save(sys.argv[4])
