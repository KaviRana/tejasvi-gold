import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from import_catalogue import candidates


class Weights(unittest.TestCase):
    def test_label_formats(self):
        cases = {"W2.28": [2.28], "W- 1.90": [1.9], "W- 2.6 Xv": [2.6], "w-2. 95 Ss": [2.95],
                 "10.240": [10.24], "12.210": [12.21], "Wt: 2.870 LR 22KT": [2.87]}
        for text, want in cases.items():
            self.assertEqual(candidates(text), want, text)

    def test_noise_gives_nothing(self):
        self.assertEqual(candidates("__ ee SS =< os"), [])


if __name__ == "__main__":
    unittest.main()


class Dilate(unittest.TestCase):
    def test_square_dilation(self):
        import numpy as np
        from import_catalogue import dilate
        m = np.zeros((9, 9), bool); m[4, 4] = True
        self.assertEqual(int(dilate(m, 2).sum()), 25)
        self.assertTrue(dilate(m, 2)[2, 2] and not dilate(m, 2)[1, 1])
