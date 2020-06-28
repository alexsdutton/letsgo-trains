import os

from setuptools import find_packages, setup

g = {}
with open(os.path.join("letsgo", "version.py")) as fp:
    exec(fp.read(), g)
version = g['__version__']

setup(
    name='letsgo-trains',
    version=version,
    description='GTK application for designing and controlling Lego train layouts',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alex Dutton',
    author_email='letsgo-trains@alexdutton.co.uk',
    packages=find_packages(),
    package_data={
        'letsgo': [
            'data/letsgo.glade',
            'data/gschemas.compiled',
        ]
    },
    license='BSD-2-Clause',
    zip_safe=False,  # due to use of Gio.SettingsSchemaSource.new_from_directory in letsgo.gtk.__main__
    data_files=[
        ('share/applications', ['data/uk.dutton.letsgo-trains.desktop']),
        ('share/icons/hicolor/scalable', ['data/letsgo-trains.svg']),
    ],
    entry_points={
        'console_scripts': [
            'letsgo-trains-gtk = letsgo.gtk.__main__:main',
        ],
        'letsgo.piece': [
            'straight = letsgo.pieces:Straight',
            'half-straight = letsgo.pieces:HalfStraight',
            'quarter-straight = letsgo.pieces:QuarterStraight',
            'curve = letsgo.pieces:Curve',
            'half-curve = letsgo.pieces:HalfCurve',
            'r24-curve = letsgo.pieces:R24Curve',
            'r32-curve = letsgo.pieces:R32Curve',
            'r56-curve = letsgo.pieces:R56Curve',
            'r72-curve = letsgo.pieces:R72Curve',
            'r88-curve = letsgo.pieces:R88Curve',
            'r104-curve = letsgo.pieces:R104Curve',
            'r120-curve = letsgo.pieces:R120Curve',
            'left-points = letsgo.pieces:LeftPoints',
            'right-points = letsgo.pieces:RightPoints',
            'crossover = letsgo.pieces:Crossover',
            'short-crossover = letsgo.pieces:ShortCrossover',
        ],
        'letsgo.layout_parser': [
            'letsgo = letsgo.layout_parser:LetsGoLayoutParser',
            'ncontrol = letsgo.layout_parser:NControlLayoutParser',
        ],
        'letsgo.layout_serializer': [
            'letsgo = letsgo.layout_serializer:LetsGoLayoutSerializer',
            'ncontrol = letsgo.layout_serializer:NControlLayoutSerializer',
        ],
        'letsgo.controller': [
            'maestro = letsgo.control.MaestroController',
            'powered-up = letsgo.control.PoweredUpController',
        ],
        'letsgo.sensor': [
            'hall-effect = letsgo.sensor.HallEffectSensor',
        ],
    }
)
