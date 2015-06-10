import json
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


def layout(directory, xc, yc, min_rating):
    ratings = json.load(open(os.path.join(directory, 'ratings.json')))

    image_fns = os.listdir(directory)
    image_fns.sort()

    image_fns = [f for f in image_fns if ((f in ratings) and (ratings[f]['rating'] >= min_rating))]

    need_images = xc * yc
    
    print 'Total %d usable images.' % len(image_fns)

    if len(image_fns) < need_images :
        raise RuntimeError('Not enough images. Abort.')

    image_fns = image_fns[0:need_images]
    images = list()
    for i in range(len(image_fns)):
        images.append(Photo.get_image(os.path.join(directory, image_fns[i])))
        print 'Loaded %d images..' % (i + 1)

    xw = max([i.image.size[0] for i in images])
    yw = max([i.image.size[1] for i in images])

    interstitial_pad_ratio = 0.318
    edge_pad_ratio = 1.5

    padding_x = int(xw * interstitial_pad_ratio)
    padding_y = int(yw * interstitial_pad_ratio)

    margin_x = int(edge_pad_ratio * xw)
    margin_y = int(edge_pad_ratio * yw)

    xwt = xw * xc + padding_x * (xc - 1) + margin_x * 2
    ywt = yw * yc + padding_y * (yc - 1) + margin_y * 2

    composite_img = make_black((xwt, ywt))

    def get_imgcorner(_x, _y):
        _x = _x * xw + (padding_x * _x + 1) + margin_x
        _y = _y * yw + (padding_y * _y + 1) + margin_y
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

        def raw_sim(list_of_neighbors):
            for a, list_of_b in list_of_neighbors:
                for b in list_of_b:
                    yield a.similar(b)
            
        def sum_sim(list_of_neighbors):
            sim = 0.0
            for simil in raw_sim(list_of_neighbors):
                sim += simil
            print 'similarity is: %f' % sim
            return sim
            
        def avg_sim(list_of_neighbors):
            n = float(len(list_of_neighbors))
            return sum(list(raw_sim(list_of_neighbors))) / n

        img_1 = get_img(*pos1)
        img_2 = get_img(*pos2)
        no = [(img_1, neighbors_1), (img_2, neighbors_2)]
        yes = [(no[0][0], no[1][1]), (no[1][0], no[0][1])]

        metric_function = avg_sim

        if metric_function(yes) > metric_function(no):
            idx_1 = get_img(*pos1, just_idx=True)
            idx_2 = get_img(*pos2, just_idx=True)
            images[idx_1] = img_2
            images[idx_2] = img_1
            return True
        else:
            return False

    RUN_NOSWAP_NEEDED = 110

    STATUS_EVERY = 100

    total_steps = 0
    total_swaps = 0
    noswap_run = 0
    run_hwm = 0

    try:
        while noswap_run < RUN_NOSWAP_NEEDED:
            x1 = random.randrange(0, xc)
            y1 = random.randrange(0, yc)
            x2 = random.randrange(0, xc)
            y2 = random.randrange(0, yc)

            pos1 = (x1, y1)
            pos2 = (x2, y2)

            if maybeswap(pos1, pos2):
                noswap_run = 0
                total_swaps += 1
            else:
                noswap_run += 1
                run_hwm = max(run_hwm, noswap_run)

            total_steps += 1

            if total_steps % STATUS_EVERY == 0:
                print 'steps=%d swaps=%d run_hwm=%d current_run=%d' % (total_steps, total_swaps, run_hwm, noswap_run)
    except KeyboardInterrupt:
        print 'Interrupted during optimization. Creating the output image...'

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
    c = layout(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    c.save(sys.argv[5])
