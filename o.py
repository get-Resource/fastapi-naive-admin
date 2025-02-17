k=""
with open(r"E:\moneys\ai\papers\Etichetta-Dream-Team\fastapi-naive-admin\core\NiceguiWeb\components\interactive_image.vue",mode='rb', ) as f: #  codec can't decode byte 0xa6 in position 381: illegal multibyte sequence
    for i in range(500):
        a = f.read(381)


        if a == b"":
            break
        for c in a:
            if c == 0xa2:
                continue
            if c == 0xe7:
                continue
            if c == 0x94:
                continue
            if c == 0xbb:
                continue
            if c == 0xac:
                continue
            if c == 0x95:
                continue
            if c == 0xbf:
                continue
            if c == 0xe6:
                continue
            k += chr(c)
            print(chr(c),end="")
        print()
with open(r"E:\moneys\ai\papers\Etichetta-Dream-Team\fastapi-naive-admin\core\NiceguiWeb\components\interactive_image.vue",mode='w', encoding="gbk") as f: #  codec can't decode byte 0xa6 in position 381: illegal multibyte sequence
    f.write(k)
