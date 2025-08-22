# -*- coding: utf-8 -*-
"""
A pure Python DXF reader for R12 and later versions, without any external libraries.
"""

from ..geometry.geometry2d import Geometry2D


class DxfReader:
    """
    A simple DXF reader implemented in pure Python.
    Reads a DXF file and parses its ENTITIES section into a Geometry2D object.
    """

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._lines = self._load_file()
        self.geom = self._parse()

    def _load_file(self):
        try:
            with open(self._filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return iter(f.readlines())
        except IOError as e:
            raise IOError(f"Cannot open or read DXF file: {self._filepath}") from e

    def get_geometry(self) -> Geometry2D:
        """Returns the parsed Geometry2D object."""
        return self.geom

    def _parse(self) -> Geometry2D:
        """Main parsing method that populates a Geometry2D object."""
        geom = Geometry2D()
        tag_stream = self._tag_generator()

        try:
            # Find the ENTITIES section
            in_entities_section = False
            for code, value in tag_stream:
                if code == 2 and value == 'ENTITIES':
                    in_entities_section = True
                    break
            if not in_entities_section:
                return geom

            # Process entities until ENDSEC
            current_entity_tags = []
            for code, value in tag_stream:
                if code == 0:
                    if current_entity_tags:
                        self._process_entity_tags(current_entity_tags, geom)

                    if value == 'ENDSEC':
                        break
                    current_entity_tags = [(code, value)]
                else:
                    current_entity_tags.append((code, value))
        except ValueError as e:
            # Log a warning if a value can't be parsed, but continue.
            print(f"Warning: A value error occurred during DXF parsing: {e}")

        return geom

    def _tag_generator(self):
        """Yields (code, value) tuples from the DXF file lines."""
        line_iter = self._lines
        while True:
            try:
                code_line = next(line_iter).strip()
                value_line = next(line_iter).strip()
                yield (int(code_line), value_line)
            except StopIteration:
                break
            except (ValueError, IndexError):
                # Skip malformed tag pairs
                continue

    def _process_entity_tags(self, tags: list, geom: Geometry2D):
        """Converts raw tags into a dictionary and adds to Geometry2D."""
        if not tags:
            return

        entity_type_str = tags[0][1].upper()
        entity_dict = {'type': entity_type_str}
        points, temp_coords = [], {}

        for code, value in tags:
            try:
                if code == 8: entity_dict['layer'] = value
                elif code == 62: entity_dict['color'] = int(value)
                # --- Geometry specific codes ---
                elif entity_type_str == 'LINE':
                    if code == 10: temp_coords['x1'] = float(value)
                    elif code == 20: temp_coords['y1'] = float(value)
                    elif code == 30: temp_coords['z1'] = float(value)
                    elif code == 11: temp_coords['x2'] = float(value)
                    elif code == 21: temp_coords['y2'] = float(value)
                    elif code == 31: temp_coords['z2'] = float(value)
                elif entity_type_str in ['CIRCLE', 'ARC']:
                    if code == 10: temp_coords['cx'] = float(value)
                    elif code == 20: temp_coords['cy'] = float(value)
                    elif code == 30: temp_coords['cz'] = float(value)
                    elif code == 40: entity_dict['radius'] = float(value)
                    if entity_type_str == 'ARC':
                        if code == 50: entity_dict['start_angle'] = float(value)
                        if code == 51: entity_dict['end_angle'] = float(value)
                elif entity_type_str == 'TEXT':
                    if code == 1: entity_dict['text_string'] = value
                    if code == 10: temp_coords['x'] = float(value)
                    elif code == 20: temp_coords['y'] = float(value)
                    elif code == 40: entity_dict['height'] = float(value)
                elif entity_type_str == 'LWPOLYLINE':
                    if code == 70: entity_dict['closed'] = (int(value) & 1) != 0
                    elif code == 10: points.append({'x': float(value)})
                    elif code == 20:
                        if points and 'y' not in points[-1]:
                            points[-1]['y'] = float(value)
            except (ValueError, KeyError):
                continue

        self._finalize_entity_geometry(entity_dict, temp_coords, points)

        # Add to Geometry2D object using its dedicated methods
        if entity_type_str == 'LINE': geom.add_line(entity_dict)
        elif entity_type_str == 'CIRCLE': geom.add_circle(entity_dict)
        elif entity_type_str == 'ARC': geom.add_arc(entity_dict)
        elif entity_type_str == 'LWPOLYLINE': geom.add_lwpolyline(entity_dict)
        elif entity_type_str == 'TEXT': geom.add_text(entity_dict)

    def _finalize_entity_geometry(self, entity_dict, temp_coords, points):
        """Helper to structure the final geometry data from parsed temp values."""
        entity_type = entity_dict.get('type')
        if entity_type == 'LINE':
            p1_z = temp_coords.get('z1', 0.0)
            p2_z = temp_coords.get('z2', 0.0)
            entity_dict['start_point'] = (temp_coords.get('x1',0), temp_coords.get('y1',0), p1_z)
            entity_dict['end_point'] = (temp_coords.get('x2',0), temp_coords.get('y2',0), p2_z)
        elif entity_type in ['CIRCLE', 'ARC']:
            z = temp_coords.get('cz', 0.0)
            entity_dict['center'] = (temp_coords.get('cx',0), temp_coords.get('cy',0), z)
        elif entity_type == 'TEXT':
            z = temp_coords.get('z', 0.0)
            entity_dict['insertion_point'] = (temp_coords.get('x',0), temp_coords.get('y',0), z)
        elif entity_type == 'LWPOLYLINE':
            z = temp_coords.get('z', 0.0)
            entity_dict['vertices'] = [(p.get('x',0), p.get('y',0), z)
                                       for p in points if 'x' in p and 'y' in p]