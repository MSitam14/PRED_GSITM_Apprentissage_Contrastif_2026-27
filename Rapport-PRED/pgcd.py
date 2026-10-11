def pgcd (a: int, b: int) -> int:
    "Plus grand commun diviseur de deux entiers naturels"
    assert a >= 0
    assert b >= 0
    if a < b:
        (a, b) = (b, a)
    while b > 0:
        (a, b) = (b, a % b)
    return a

# test unitaire
assert pgcd(8 * 3 * 5 * 13, 4 * 5 * 7 * 17) == 4 * 5
