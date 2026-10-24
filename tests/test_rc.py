import unittest

from app.rc import digitos_control, normalizar_rc, validar_rc


class TestRC(unittest.TestCase):
    def test_validas(self):
        for rc in ("9872023VH5797S0001WX", "7837301VG8173B0001TT"[:18] + digitos_control("7837301VG8173B0001")):
            self.assertTrue(validar_rc(rc)[0], rc)

    def test_normaliza(self):
        self.assertEqual(normalizar_rc(" 9872023 vh5797s-0001.wx "), "9872023VH5797S0001WX")

    def test_parcela_14(self):
        ok, msg = validar_rc("9872023VH5797S")
        self.assertFalse(ok)
        self.assertIn("finca", msg)

    def test_control_mal(self):
        self.assertFalse(validar_rc("9872023VH5797S0001WY")[0])

    def test_longitud(self):
        self.assertFalse(validar_rc("9872023VH5797S000")[0])


if __name__ == "__main__":
    unittest.main()
