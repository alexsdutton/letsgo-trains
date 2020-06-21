import os

from setuptools import find_packages, setup

g = {}
with open(os.path.join("trains", "version.py")) as fp:
    exec(fp.read(), g)
version = g['__version__']

setup(
    name='letsgo-trains',
    version=version,
    description='GTK application for controlling Lego trains',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alex Dutton',
    author_email='lego-trains@alexdutton.co.uk',
    packages=find_packages(),
    license='BSD-2-Clause',
    entry_points={
        'trains.piece': [
            'straight = trains.pieces:Straight',
            'half-straight = trains.pieces:HalfStraight',
            'quarter-straight = trains.pieces:QuarterStraight',
            'curve = trains.pieces:Curve',
            'half-curve = trains.pieces:HalfCurve',
            'r24-curve = trains.pieces:R24Curve',
            'r32-curve = trains.pieces:R32Curve',
            'r56-curve = trains.pieces:R56Curve',
            'r72-curve = trains.pieces:R72Curve',
            'r88-curve = trains.pieces:R88Curve',
            'r104-curve = trains.pieces:R104Curve',
            'r120-curve = trains.pieces:R120Curve',
            'left-points = trains.pieces:LeftPoints',
            'right-points = trains.pieces:RightPoints',
            'crossover = trains.pieces:Crossover',
            'short-crossover = trains.pieces:ShortCrossover',
        ],
        'trains.layout_parser': [
            'letsgo = trains.layout_parser:LetsGoLayoutParser',
            'ncontrol = trains.layout_parser:NControlLayoutParser',
        ],
        'trains.layout_serializer': [
            'letsgo = trains.layout_serializer:LetsGoLayoutSerializer',
            'ncontrol = trains.layout_serializer:NControlLayoutSerializer',
        ],
        'trains.controller': [
            'maestro = trains.control.MaestroController',
            'powered-up = trains.control.PoweredUpController',
        ],
        'trains.sensor': [
            'hall-effect = trains.sensor.HallEffectSensor',
        ],
    }

)
