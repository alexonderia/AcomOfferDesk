"""Convert the supplied Alabuga Sans collection into checked-in web assets.

One-time tooling dependency: python -m pip install 'fonttools[woff]'
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fontTools.ttLib import TTCollection


FONT_NAMES = {
    100: "thin",
    200: "extra-light",
    300: "light",
    400: "regular",
    500: "medium",
    700: "bold",
    800: "extra-bold",
    900: "black",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original .zip or .ttc file")
    args = parser.parse_args()
    if args.source.suffix.lower() == ".zip":
        with ZipFile(args.source) as archive:
            source = archive.read("alabuga-sans.ttc")
    else:
        source = args.source.read_bytes()

    destination = Path(__file__).resolve().parents[1] / "shared" / "fonts"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "alabuga-sans.ttc").write_bytes(source)
    collection = TTCollection(BytesIO(source))
    faces = []
    for font in sorted(collection.fonts, key=lambda face: face["OS/2"].usWeightClass):
        weight = font["OS/2"].usWeightClass
        filename = f"alabuga-sans-{FONT_NAMES[weight]}.woff2"
        font.flavor = "woff2"
        font.save(destination / filename, reorderTables=False)
        # The collection has no Semibold. Use its real Medium outlines for 600.
        css_weight = "500 600" if weight == 500 else str(weight)
        faces.append(
            "@font-face {\n"
            "  font-family: 'Alabuga Sans';\n"
            f"  src: url('./{filename}') format('woff2');\n"
            "  font-style: normal;\n"
            f"  font-weight: {css_weight};\n"
            "  font-display: swap;\n"
            "}\n"
        )
        print(filename, (destination / filename).stat().st_size)
    (destination / "alabuga-sans.css").write_text("\n".join(faces), encoding="utf-8")


if __name__ == "__main__":
    main()
