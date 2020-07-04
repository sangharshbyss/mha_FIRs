a = 29
while a > 1:
    if a <= 9:
        a = str(a)
        a = f"'0'{a}"

    a = a.strip('0')
    a = int(a)
    a += 1