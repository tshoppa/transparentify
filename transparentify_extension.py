#!/usr/bin/env python
"""Adds transparency while preserving solid color value"""

import inkex
from inkex.elements import ShapeElement


ALPHA_INC = 1/256
OPACITY_MAP = {'fill':'fill-opacity', 'stroke': 'stroke-opacity', 'stop-color': 'stop-opacity'}


class Transparentify(inkex.ColorExtension):
    opacities = dict()
    elem = None

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--opacity", type=float, default=80.0)
        pars.add_argument("--force_transparency", type=inkex.Boolean, default=False)
        pars.add_argument("--background_color", type=inkex.Color, default=inkex.Color('#FFFFFF'))

    def effect(self):
        # ensure fill- and stroke-opacity are set for all shapes.
        # Sometimes this is not the case (and it needn't as it defaults to 1)
        # but ColorExtension will skip calling modify_opacity then (should be fixed there)
        for elem in self.svg.selection.get(ShapeElement):
            def ensure_opacity_attr(name):
                attr = elem.style.get(name)
                if attr is not None and attr != 'none':
                    opacity_attr = OPACITY_MAP[name]
                    if not opacity_attr in elem.style:
                        elem.style[opacity_attr] = 1
            ensure_opacity_attr("fill")
            ensure_opacity_attr("stroke")
        super().effect()

    def process_element(self, elem, gradients=None):
        # just to provide access to the currently processed element, needed in modify_color
        self.elem = elem
        super().process_element(elem, gradients)

    def modify_color(self, name, color):
        back = self.options.background_color
        opacity_key = OPACITY_MAP.get(name)
        #working on set of floats
        c = {'red':float(color.red), 'green':float(color.green), 'blue':float(color.blue)}
        # calculate color with desired transparency. If a channel drops below zero (transparency not reachable) set flag
        alpha = self.options.opacity/100
        inv = 1.0 - alpha
        below_zero = False
        def simple_transparentify (val):
            v = (c[val] - getattr(back, val) * inv) / alpha
            if v < 0:
                v = 0
                nonlocal below_zero
                below_zero = True
            return v if v < 255 else 255
        c['red'] = simple_transparentify('red')
        c['green'] = simple_transparentify('green')
        c['blue'] = simple_transparentify('blue')
        # check if all values could be set properly or if best fit should be calculated
        if below_zero and not self.options.force_transparency:
            #c = self.best_fit_transparent(color)
            # iterate to the best possible transparency
            r, g, b, alpha = -1.0, -1.0, -1.0, 0.0
            while alpha < 1 and (r < 0 or g < 0 or b < 0 or r > 255 or g > 255 or b > 255):
                alpha += ALPHA_INC
                inv = 1 / alpha
                complement = 1 - inv
                def inc_val(v):
                    return getattr(color, v) * inv + getattr(back, v) * complement
                r, g, b = inc_val('red'), inc_val('green'), inc_val('blue')
            c['red'], c['green'], c['blue'] = r, g, b
        def toInt(v):
            return round(v) if v < 255 else 255
        color.red, color.green, color.blue = toInt(c['red']), toInt(c['green']), toInt(c['blue'])
        # if element already has a transparency apply that transparency additionally
        if opacity_key is not None:
            alpha = alpha * float(self.elem.style.get(opacity_key) or 1)
        self.opacities[opacity_key] = alpha
        return color

    def modify_opacity(self, name, opacity):
        return self.opacities.get(name, opacity)


if __name__ == '__main__':
    Transparentify().run()
