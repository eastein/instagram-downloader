import time
import os, os.path
import json
import sys
import subprocess
import random

VIEW_IMG = ['eog']

if __name__ == '__main__':
    photo_dir = os.path.abspath(sys.argv[1])
    if not os.path.exists(photo_dir):
        raise RuntimeError("%s does not exist." % photo_dir)
    
    ratings = {}
    ratings_filename = os.path.join(photo_dir, 'ratings.json')

    if os.path.exists(ratings_filename) :
        ratings = json.load(open(ratings_filename))

    ratings_added = 0
    files = os.listdir(photo_dir)
    random.shuffle(files)
    for fn in files :
        if fn in ratings :
            continue
        if fn == 'ratings.json' :
            continue

        filename = os.path.join(photo_dir, fn)
        print 'Showing you %s...' % fn
        time.sleep(1)
        
        subprocess.call(VIEW_IMG + [filename])

        n = None
        continue_anyway = False
        while n is None :
            print 'Rate %s' % fn
            c = raw_input('Enter number in range 1-10 or q to stop rating images: ')
            if c == 'q' :
                print 'goodbye.'
                break
            elif c == 'd':
                print 'Deleting %s...' % filename
                os.unlink(filename)
                continue_anyway = True
                break
            else :
                try :
                    n = int(c)
                except ValueError:
                    pass

            if n < 1 or n > 10 :
                print 'Rating out of range.'
                n = None

        if n is None :
            if not continue_anyway: 
                break

        else :
            ratings[fn] = {
                'ts': time.time(),
                'rating': n
            }
            ratings_added += 1
            print 'Rated %s as %d.\n' % (fn, n)

    print 'You rated %d images.' % ratings_added

    write_temp = ratings_filename + '.partial'
    fh = open(write_temp, 'w')
    json.dump(ratings, fh)
    fh.close()
    os.rename(write_temp, ratings_filename)
