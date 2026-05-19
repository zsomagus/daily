# modulok/svg_to_png.py

import cairosvg

def svg_file_to_png(svg_path, png_path, scale=1.0):
    cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
