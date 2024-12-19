from urllib.request import urlopen

content = urlopen("https://curl.se/ca/cacert.pem").read().decode()

with open("ca_bundle.h", "w") as out:
    out.write("#pragma once\n\n")
    out.write("constexpr static char CA_BUNDLE_CONTENT[] =")

    for line in content.split('\n'):
        out.write(f'\n"{line}\\n"')

    out.write(';')
