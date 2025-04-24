# https://stackoverflow.com/a/74666366
# https://gist.github.com/reinhrst/2d693a16c04861a8fbc5253938312410
import numpy as np

def rgb_to_hls(rgb_array: np.ndarray) -> np.ndarray:
    """
    Expects an array of shape (X, 3), each row being RGB colours.
    Returns an array of same size, each row being HLS colours.
    Like `colorsys` python module, all values are between 0 and 1.

    NOTE: like `colorsys`, this uses HLS rather than the more usual HSL
    """
    assert rgb_array.ndim == 2
    assert rgb_array.shape[1] == 3
    assert np.max(rgb_array) <= 1
    assert np.min(rgb_array) >= 0

    r, g, b = rgb_array.T.reshape((3, -1, 1))
    maxc = np.max(rgb_array, axis=1).reshape((-1, 1))
    minc = np.min(rgb_array, axis=1).reshape((-1, 1))

    sumc = (maxc+minc)
    rangec = (maxc-minc)

    with np.errstate(divide='ignore', invalid='ignore'):
        rgb_c = (maxc - rgb_array) / rangec
    rc, gc, bc = rgb_c.T.reshape((3, -1, 1))

    h = (np.where(minc == maxc, 0, np.where(r == maxc, bc - gc, np.where(g == maxc, 2.0+rc-bc, 4.0+gc-rc)))
         / 6) % 1
    l = sumc/2.0
    with np.errstate(divide='ignore', invalid='ignore'):
        s = np.where(minc == maxc, 0,
                     np.where(l < 0.5, rangec / sumc, rangec / (2.0-sumc)))

    return np.concatenate((h, l, s), axis=1)


def hls_to_rgb(hls_array: np.ndarray) -> np.ndarray:
    """
    Expects an array of shape (X, 3), each row being HLS colours.
    Returns an array of same size, each row being RGB colours.
    Like `colorsys` python module, all values are between 0 and 1.

    NOTE: like `colorsys`, this uses HLS rather than the more usual HSL
    """
    ONE_THIRD = 1 / 3
    TWO_THIRD = 2 / 3
    ONE_SIXTH = 1 / 6

    def _v(m1, m2, h):
        h = h % 1.0
        return np.where(h < ONE_SIXTH, m1 + (m2 - m1) * h * 6,
                        np.where(h < .5, m2,
                                 np.where(h < TWO_THIRD, m1 + (m2 - m1) * (TWO_THIRD - h) * 6,
                                          m1)))


    assert hls_array.ndim == 2
    assert hls_array.shape[1] == 3
    assert np.max(hls_array) <= 1
    assert np.min(hls_array) >= 0

    h, l, s = hls_array.T.reshape((3, -1, 1))
    m2 = np.where(l < 0.5, l * (1 + s), l + s - (l * s))
    m1 = 2 * l - m2

    r = np.where(s == 0, l, _v(m1, m2, h + ONE_THIRD))
    g = np.where(s == 0, l, _v(m1, m2, h))
    b = np.where(s == 0, l, _v(m1, m2, h - ONE_THIRD))

    return np.concatenate((r, g, b), axis=1)


def hsv_to_rgb(hsv_array: np.ndarray) -> np.ndarray:
    """
    Expects an array of shape (X, 3), each row being HSV colours.
    Returns an array of same size, each row being RGB colours.
    Like `colorsys` python module, all values are between 0 and 1.

    """
    assert hsv_array.ndim == 2
    assert hsv_array.shape[1] == 3
    assert np.max(hsv_array) <= 1
    assert np.min(hsv_array) >= 0

    h, s, v = hsv_array.T.reshape((3, -1, 1))
    h = h % 1
    s = s.clip(0, 1)
    v = v.clip(0, 1)
    i = (h * 6).astype("uint8")
    f = (h * 6) - i

    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    # i = i%6
    wh = np.where

    return wh(
        i == 0, np.concatenate((v, t, p), axis=1),
        wh(i == 1, np.concatenate((q, v, p), axis=1),
           wh(i == 2, np.concatenate((p, v, t), axis=1),
              wh(i == 3, np.concatenate((p, q, v), axis=1),
                 wh(i == 4, np.concatenate((t, p, v), axis=1),
                    wh(i == 5, np.concatenate((v, p, q), axis=1),
                       np.full(hsv_array.shape, np.NaN)))))))


def rgb_to_hsv(rgb_array: np.ndarray) -> np.ndarray:
    """
    Expects an array of shape (X, 3), each row being RGB colours.
    Returns an array of same size, each row being HSV colours.
    Like `colorsys` python module, all values are between 0 and 1.

    """
    assert rgb_array.ndim == 2
    assert rgb_array.shape[1] == 3
    assert np.max(rgb_array) <= 1
    assert np.min(rgb_array) >= 0

    r, g, b = rgb_array.T.reshape((3, -1, 1))
    maxc = np.max(rgb_array, axis=1).reshape((-1, 1))
    minc = np.min(rgb_array, axis=1).reshape((-1, 1))
    v = maxc

    sumc = (maxc+minc)
    rangec = (maxc-minc)

    with np.errstate(divide='ignore', invalid='ignore'):
        rgb_c = (maxc - rgb_array) / rangec
    rc, gc, bc = rgb_c.T.reshape((3, -1, 1))

    h = (np.where(minc == maxc, 0,
                  np.where(r == maxc, bc - gc,
                           np.where(g == maxc, 2.0+rc-bc,
                                    4.0+gc-rc)))
         / 6) % 1
    with np.errstate(divide='ignore', invalid='ignore'):
        s = np.where(minc == maxc, 0, rangec / maxc)

    return np.concatenate((h, s, v), axis=1)


def _test_rgb_to_hls():
    import colorsys
    rgb_array = np.array([[.5, .5, .8], [.3, .7, 1], [0, 0, 0], [1, 1, 1], [.5, .5, .5]])
    hls_array = rgb_to_hls(rgb_array)
    for rgb, hls in zip(rgb_array, hls_array):
        assert np.all(abs(np.array(colorsys.rgb_to_hls(*rgb) - hls) < 0.001))
    new_rgb_array = hls_to_rgb(hls_array)
    for hls, rgb in zip(hls_array, new_rgb_array):
        assert np.all(abs(np.array(colorsys.hls_to_rgb(*hls) - rgb) < 0.001))
    assert np.all(abs(rgb_array - new_rgb_array) < 0.001)
    print("tests rgb_to_hls done")

def _test_hls_to_rgb():
    import colorsys
    hls_array = np.array([[0.6456692913385826, 0.14960629921259844, 0.7480314960629921], [.3, .7, 1], [0, 0, 0], [0, 1, 0], [.5, .5, .5]])
    rgb_array = hls_to_rgb(hls_array)
    for hls, rgb in zip(hls_array, rgb_array):
        assert np.all(abs(np.array(colorsys.hls_to_rgb(*hls) - rgb) < 0.001))
    new_hls_array = rgb_to_hls(rgb_array)
    for rgb, hls in zip(rgb_array, new_hls_array):
        assert np.all(abs(np.array(colorsys.rgb_to_hls(*rgb) - hls) < 0.001))
    assert np.all(abs(hls_array - new_hls_array) < 0.001)
    print("tests hls_to_rgb done")

def _test_hsv_to_rgb():
    import colorsys
    hsv_array = np.array([[0.6456692913385826, 0.14960629921259844, 0.7480314960629921], [.3, .7, 1], [0, 0, 0], [0, 0, 1], [.5, .5, .5]])
    rgb_array = hsv_to_rgb(hsv_array)
    for hsv, rgb in zip(hsv_array, rgb_array):
        assert np.all(abs(np.array(colorsys.hsv_to_rgb(*hsv) - rgb) < 0.001))
    new_hsv_array = rgb_to_hsv(rgb_array)
    for rgb, hsv in zip(rgb_array, new_hsv_array):
        assert np.all(abs(np.array(colorsys.rgb_to_hsv(*rgb) - hsv) < 0.001))
    assert np.all(abs(hsv_array - new_hsv_array) < 0.001)
    print("tests hsv_to_rgb done")

def _test():
    _test_rgb_to_hls()
    _test_hls_to_rgb()
    _test_hsv_to_rgb()
    print("All tests done")

if __name__ == "__main__":
    _test()

