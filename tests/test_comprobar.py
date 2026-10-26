import unittest

from app.comprobar import ccaa_de_provincia, comprobar, contraste_m2, itp_general, umbral_sospechoso, veredicto

MOTOR = {"valor_central": 200000, "valor_min": 160000, "valor_max": 250000, "superficie_m2": 80,
         "cierre_estimado": 180000, "provincia": "MURCIA"}


class TestComprobar(unittest.TestCase):
    def test_veredictos(self):
        self.assertEqual(veredicto(200000, 160000, 200000, 250000), "justo")
        self.assertEqual(veredicto(150000, 160000, 200000, 250000), "gran_precio")
        self.assertEqual(veredicto(260000, 160000, 200000, 250000), "caro")
        self.assertEqual(veredicto(110000, 160000, 200000, 250000), "sospechoso")

    def test_umbral(self):
        self.assertEqual(umbral_sospechoso(160000, 200000), 120000)   # manda la mediana
        self.assertEqual(umbral_sospechoso(100000, 200000), 85000)    # manda el p25

    def test_m2(self):
        self.assertFalse(contraste_m2(90, 80)["aviso"])      # +12 %: zonas comunes, normal
        self.assertTrue(contraste_m2(100, 80)["aviso"])      # +25 %
        self.assertTrue(contraste_m2(60, 80)["aviso"])       # −25 %
        self.assertIsNone(contraste_m2(None, 80))

    def test_itp(self):
        self.assertEqual(ccaa_de_provincia("Murcia"), "MC")
        self.assertEqual(ccaa_de_provincia("ALICANTE"), "VC")
        self.assertEqual(ccaa_de_provincia("Santa Cruz de Tenerife"), "CN")
        self.assertIsNone(ccaa_de_provincia("Gipuzkoa"))    # foral: sin dato
        self.assertAlmostEqual(itp_general("MD", 200000)[0], 12000)
        # Aragón progresivo: 400.000 al 8 % + 50.000 al 8,5 %
        self.assertAlmostEqual(itp_general("AR", 450000)[0], 32000 + 4250)
        # Asturias tipo único según valor total
        self.assertAlmostEqual(itp_general("AS", 400000)[0], 36000)

    def test_resultado(self):
        r = comprobar(MOTOR, 150000, 92)
        self.assertEqual(r["veredicto"], "gran_precio")
        self.assertEqual(r["diferencia_pct"], -25)
        self.assertEqual(r["itp"]["ccaa"], "Región de Murcia")
        self.assertEqual(r["itp"]["cuota"], round(150000 * 0.0775))
        self.assertFalse(r["m2"]["aviso"])


if __name__ == "__main__":
    unittest.main()
